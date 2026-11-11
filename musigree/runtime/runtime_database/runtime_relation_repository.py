import logging
from typing import TYPE_CHECKING, Any, cast

from sqlalchemy import ColumnElement, Result, Select, and_, delete, or_, select, union

from musigree.exceptions import DatabaseError, NotFoundError
from musigree.library.cache.role_cache import RoleCache
from musigree.runtime.runtime_database import RuntimeRelationTable
from musigree.runtime.runtime_database.runtime_base_repository import (
    RuntimeBaseRepository,
)
from musigree.runtime.runtime_database.runtime_base_table import mapped_entity
from musigree.runtime.runtime_domain.runtime_relation import (
    RuntimeRelationDB,
    RuntimeRelationInternal,
    RuntimeRelationUncommitted,
)

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Sequence

    from sqlalchemy.sql.base import Executable

log = logging.getLogger(__name__)

# Probes are read through the (entity, predicate) indexes. A short chunk keeps
# each lookup on that index instead of one statement covering the whole graph.
RELEASE_YEAR_PROBE_CHUNK_SIZE = 25


def year_bounds_clause(
    min_year: int | None,
    max_year: int | None,
) -> ColumnElement[bool] | None:
    """Keep undated rows and rows inside the inclusive year bounds.

    Either bound may be omitted. No bounds means the caller should not filter.
    """
    if min_year is None and max_year is None:
        return None

    column = RuntimeRelationTable.year
    comparisons: list[ColumnElement[bool]] = []
    if min_year is not None:
        comparisons.append(column >= min_year)
    if max_year is not None:
        comparisons.append(column <= max_year)
    in_range = comparisons[0] if len(comparisons) == 1 else and_(*comparisons)
    return or_(column.is_(None), in_range)


def _dated_year_clause(
    min_year: int | None,
    max_year: int | None,
) -> ColumnElement[bool]:
    """Keep rows that have a year, and only those inside the bounds."""
    column = RuntimeRelationTable.year
    comparisons: list[ColumnElement[bool]] = [column.is_not(None)]
    if min_year is not None:
        comparisons.append(column >= min_year)
    if max_year is not None:
        comparisons.append(column <= max_year)
    if len(comparisons) == 1:
        return comparisons[0]
    return and_(*comparisons)


def _release_year_selects(
    probe_ids: Sequence[int],
    partners: set[int],
    min_year: int | None,
    max_year: int | None,
) -> tuple[Select[int, int, int, int | None], Select[int, int, int, int | None]]:
    """Subject-side and object-side lookups for one chunk of probes."""
    year_clause = _dated_year_clause(min_year, max_year)
    columns = (
        RuntimeRelationTable.subject,
        RuntimeRelationTable.object,
        RuntimeRelationTable.release_id,
        RuntimeRelationTable.year,
    )
    subject_query = select(*columns).where(
        RuntimeRelationTable.subject.in_(probe_ids),
        RuntimeRelationTable.object.in_(partners),
        year_clause,
    )
    object_query = select(*columns).where(
        RuntimeRelationTable.object.in_(probe_ids),
        RuntimeRelationTable.subject.in_(partners),
        year_clause,
    )
    return subject_query, object_query


def _keep_probed_release_years(
    releases_by_pair: dict[tuple[int, int], dict[str, int | None]],
    probes: dict[int, set[int]],
    rows: Sequence[tuple[int, int, int, int | None]],
) -> None:
    """Store a row only when its ends are a requested probe and partner."""
    for subject, object_, release_id, year in rows:
        if year is None or subject == object_:
            continue
        subject_partners = probes.get(subject)
        object_partners = probes.get(object_)
        matched = (subject_partners is not None and object_ in subject_partners) or (
            object_partners is not None and subject in object_partners
        )
        if not matched:
            continue
        pair = (subject, object_) if subject < object_ else (object_, subject)
        releases_by_pair.setdefault(pair, {})[str(release_id)] = int(year)


# noinspection PyTypeChecker
class RuntimeRelationRepository(RuntimeBaseRepository["RuntimeRelationTable"]):
    """
    Repository for managing RuntimeRelation objects in the runtime runtime_database.

    This class provides async methods for interacting with the RuntimeRelationTable
    in the runtime runtime_database, including creating, retrieving, and deleting
    relations. It supports various query operations, such as finding relations
    by ID, key, or associated entity. It also includes bulk creation and
    deletion capabilities.

    Inherits from:
        RuntimeBaseRepository[RuntimeRelationTable]: Provides the basic runtime
            runtime_database interaction functionality.

    Attributes:
        schema_class (Type[RuntimeRelationTable]): The SQLAlchemy table class
            for runtime relations.
    """

    schema_class = mapped_entity(RuntimeRelationTable)
    """The SQLAlchemy table class for runtime relations."""

    async def _get_one_by_query(self, query: Select[tuple[RuntimeRelationTable]]) -> RuntimeRelationInternal:
        """
        Executes a query that should return a single RuntimeRelation.

        Args:
            query: The SQLAlchemy query to execute.

        Returns:
            RuntimeRelationInternal: The retrieved relation.

        Raises:
            NotFoundError: If no relation is found matching the query.
        """
        result: Result[Any] = await self._session.execute(query)

        if not (instance := result.scalars().one_or_none()):
            raise NotFoundError

        relation_db = RuntimeRelationDB.model_validate(instance)
        return relation_db.to_domain()

    async def _get_all_by_query(
        self,
        query: Executable,
    ) -> list[RuntimeRelationInternal]:
        """
        Executes a query that should return multiple RuntimeRelations.

        Args:
            query: The SQLAlchemy query to execute.

        Returns:
            List[RuntimeRelationInternal]: A list of retrieved relations.
        """
        result: Result[Any] = await self._session.execute(query)

        instances = result.scalars().all()
        relation_dbs = [RuntimeRelationDB.model_validate(instance) for instance in instances]
        relations = [relation_db.to_domain() for relation_db in relation_dbs]
        return relations

    async def all(self) -> AsyncGenerator[RuntimeRelationInternal]:
        """
        Retrieves all relations from the runtime runtime_database.

        Yields:
            AsyncGenerator[RuntimeRelationInternal]: An async iterator yielding
                each relation.
        """
        async for instance in self._all():
            relation_db = RuntimeRelationDB.model_validate(instance)
            yield relation_db.to_domain()

    async def get(self, relation_id: int) -> RuntimeRelationDB:
        """
        Retrieves a relation by its ID.

        Args:
            relation_id: The ID of the relation to retrieve.

        Returns:
            RuntimeRelationDB: The retrieved relation.

        Raises:
            NotFoundError: If no relation is found with the given ID.
        """
        query = select(mapped_entity(RuntimeRelationTable)).where(RuntimeRelationTable.id == relation_id)
        result: Result[Any] = await self._session.execute(query)

        if not (instance := result.scalars().one_or_none()):
            raise NotFoundError
        return RuntimeRelationDB.model_validate(instance)

    async def get_id_by_key(self, key: dict[str, Any]) -> int:
        """
        Retrieves the ID of a relation by its key.

        Args:
            key: A dictionary representing the key of the relation, containing
                'subject', 'role_id', and 'object'.

        Returns:
            int: The ID of the relation.

        Raises:
            NotFoundError: If no relation is found with the given key.
        """
        query = select(RuntimeRelationTable.id).where(
            (RuntimeRelationTable.subject == key["subject"])
            & (RuntimeRelationTable.predicate == key["role_id"])
            & (RuntimeRelationTable.object == key["object"])
        )
        result: Result[Any] = await self._session.execute(query)

        if not (instance := result.scalar()):
            raise NotFoundError
        # noinspection PyTypeChecker
        return int(instance)

    async def find_by_id(self, relation_id: int) -> RuntimeRelationInternal:
        """
        Retrieves a relation by its ID, with an option to lock the row for update.

        Args:
            relation_id: The ID of the relation to retrieve.

        Returns:
            RuntimeRelationInternal: The retrieved relation.

        Raises:
            NotFoundError: If no relation is found with the given ID.
        """
        query = (
            select(mapped_entity(RuntimeRelationTable))
            .with_for_update(of=mapped_entity(RuntimeRelationTable), nowait=True)
            .where(RuntimeRelationTable.id == relation_id)
        )
        return await self._get_one_by_query(query)

    async def find_by_key(self, key: dict[str, Any]) -> list[RuntimeRelationInternal]:
        """
        Retrieves a relation by its key components (subject, role, object).

        Args:
            key: A dictionary representing the key of the relation. It can
                contain 'role_id', 'role_name', or 'role'.

        Returns:
            RuntimeRelationInternal: The retrieved relation.

        Raises:
            NotFoundError: If no relation is found with the given key.
        """
        if "role_id" not in key:
            if "role_name" in key:
                role_name = key["role_name"]
                key["role_id"] = RoleCache.role_name_to_role_id_lookup[role_name]
            elif "role" in key:
                role_name = key["role"]
                key["role_id"] = RoleCache.role_name_to_role_id_lookup[role_name]
        query = select(mapped_entity(RuntimeRelationTable)).where(
            (RuntimeRelationTable.subject == key["subject"])
            & (RuntimeRelationTable.predicate == key["role_id"])
            & (RuntimeRelationTable.object == key["object"])
        )
        return await self._get_all_by_query(query)

    async def find_by_entity(self, id_: int) -> list[RuntimeRelationInternal]:
        """
        Retrieves all relations associated with a given entity ID.

        Args:
            id_: The ID of the entity.

        Returns:
            List[RuntimeRelationInternal]: A list of relations associated with
                the entity.
        """
        query = select(mapped_entity(RuntimeRelationTable)).where(
            (RuntimeRelationTable.subject == id_) | (RuntimeRelationTable.object == id_)
        )
        return await self._get_all_by_query(query)

    async def find_by_entity_and_roles(self, id_: int, role_ids: list[int]) -> list[RuntimeRelationInternal]:
        """
        Retrieves all relations associated with a given entity ID and specific roles.

        Args:
            id_: The ID of the entity.
            role_ids: A list of role IDs to filter by.

        Returns:
            List[RuntimeRelationInternal]: A list of relations associated with
                the entity and matching the specified roles.
        """
        if not role_ids:
            return []

        query = (
            select(mapped_entity(RuntimeRelationTable))
            .where(
                ((RuntimeRelationTable.subject == id_) | (RuntimeRelationTable.object == id_))
                & (RuntimeRelationTable.predicate.in_(role_ids))
            )
            .order_by(
                RuntimeRelationTable.predicate,
                RuntimeRelationTable.subject,
                RuntimeRelationTable.object,
            )
        )
        return await self._get_all_by_query(query)

    async def find_by_entities_and_roles(
        self,
        ids: list[int],
        role_ids: list[int],
        limit: int,
        min_year: int | None = None,
        max_year: int | None = None,
    ) -> list[RuntimeRelationInternal]:
        """
        Retrieves relations associated with any of the given entity IDs and roles.

        Uses a UNION of subject-side and object-side lookups so each branch can
        use the corresponding (entity, predicate) index, then applies ordering
        and ``limit`` to the combined result.

        Args:
            ids: The IDs of the entities.
            role_ids: A list of role IDs to filter by.
            limit: Maximum number of relations to return.
            min_year: Inclusive lower bound. Omitted when there is no lower bound.
            max_year: Inclusive upper bound. Omitted when there is no upper bound.

        Returns:
            List[RuntimeRelationInternal]: A list of relations associated with
                any of the entities and matching the specified roles, capped
                at ``limit``.
        """
        if not ids or not role_ids or limit <= 0:
            return []

        table = mapped_entity(RuntimeRelationTable)
        year_clause = year_bounds_clause(min_year, max_year)
        subject_filters: list[ColumnElement[bool]] = [
            RuntimeRelationTable.subject.in_(ids),
            RuntimeRelationTable.predicate.in_(role_ids),
        ]
        object_filters: list[ColumnElement[bool]] = [
            RuntimeRelationTable.object.in_(ids),
            RuntimeRelationTable.predicate.in_(role_ids),
        ]
        if year_clause is not None:
            subject_filters.append(year_clause)
            object_filters.append(year_clause)
        subject_query = select(table).where(*subject_filters)
        object_query = select(table).where(*object_filters)
        combined = union(subject_query, object_query)
        compound = combined.order_by(
            combined.selected_columns.predicate,
            combined.selected_columns.subject,
            combined.selected_columns.object,
        ).limit(limit)
        query = select(table).from_statement(compound)
        return await self._get_all_by_query(query)

    async def find_release_years_for_probes(
        self,
        probes: dict[int, set[int]],
        *,
        min_year: int | None = None,
        max_year: int | None = None,
    ) -> dict[tuple[int, int], dict[str, int | None]]:
        """Release years for the probed pairs, whatever role the row has.

        Each probe is the entity whose relation index is scanned. Only rows
        whose other end is one of that probe's partners are kept, so a busy
        entity does not return its whole discography.

        Args:
            probes: Probe entity id to the partner ids that share an undated link.
            min_year: Inclusive lower bound. Omitted when there is no lower bound.
            max_year: Inclusive upper bound. Omitted when there is no upper bound.

        Returns:
            Undirected entity pair to release id and year. Pairs with no dated
            release are absent.
        """
        probe_ids = [probe_id for probe_id, partners in probes.items() if partners]
        if not probe_ids:
            return {}

        releases_by_pair: dict[tuple[int, int], dict[str, int | None]] = {}
        for start in range(0, len(probe_ids), RELEASE_YEAR_PROBE_CHUNK_SIZE):
            chunk = probe_ids[start : start + RELEASE_YEAR_PROBE_CHUNK_SIZE]
            partners: set[int] = set()
            for probe_id in chunk:
                partners.update(probes[probe_id])
            if not partners:
                continue
            for query in _release_year_selects(chunk, partners, min_year, max_year):
                result = await self.execute(query)
                _keep_probed_release_years(
                    releases_by_pair,
                    probes,
                    cast("Sequence[tuple[int, int, int, int | None]]", result.all()),
                )
        return releases_by_pair

    async def create(
        self, relation: RuntimeRelationUncommitted, on_conflict_do_nothing: bool = False
    ) -> RuntimeRelationInternal:
        """
        Creates a new relation in the runtime runtime_database.

        Args:
            relation: The RuntimeRelationUncommitted object to create.
            on_conflict_do_nothing: If True, ignore conflicts during insertion.

        Returns:
            RuntimeRelationInternal: The created relation.
        """
        from musigree.runtime.runtime_database_manager import RuntimeDatabaseManager

        assert RuntimeDatabaseManager.runtime_database_helper is not None, (
            "runtime_database_helper must be initialized before calling initialize()"
        )

        relation_dict = relation.model_dump(exclude={"role_name"})
        role_id = RoleCache.role_name_to_role_id_lookup[relation.role_name]
        relation_dict.update(predicate=role_id)
        query = RuntimeDatabaseManager.runtime_database_helper.generate_insert_query(
            self.schema_class, relation_dict, on_conflict_do_nothing
        )
        result: Result[Any] = await self._session.execute(query)
        # result: Result = await self.execute(query)
        await self._session.flush()

        if not (instance := result.scalar_one_or_none()):
            raise DatabaseError

        relation_db = RuntimeRelationDB.model_validate(instance)
        return relation_db.to_domain()

    async def create_bulk(
        self,
        relations: list[RuntimeRelationUncommitted],
        on_conflict_do_nothing: bool = False,
    ) -> None:
        """
        Creates multiple relations in the runtime runtime_database in bulk.

        Args:
            relations: A list of RuntimeRelationUncommitted objects to create.
            on_conflict_do_nothing: If True, ignore conflicts during insertion.
        """
        from musigree.runtime.runtime_database_manager import RuntimeDatabaseManager

        assert RuntimeDatabaseManager.runtime_database_helper is not None, (
            "runtime_database_helper must be initialized before calling initialize()"
        )

        relation_dicts = []
        for relation in relations:
            relation_dict = relation.model_dump(exclude={"role_name"})
            role_id = RoleCache.role_name_to_role_id_lookup[relation.role_name]
            relation_dict.update(predicate=role_id)
            relation_dicts.append(relation_dict)
        query = RuntimeDatabaseManager.runtime_database_helper.generate_insert_bulk_query(
            self.schema_class, relation_dicts, on_conflict_do_nothing
        )
        await self._session.execute(query)

    async def delete_by_entitys(self, id_: int) -> None:
        """
        Deletes all relations associated with a specific entity.

        Args:
            id_: The ID of the entity whose relations should be deleted.
        """
        query = delete(mapped_entity(RuntimeRelationTable)).where(
            (RuntimeRelationTable.subject == id_) | (RuntimeRelationTable.object == id_)
        )
        await self._session.execute(query)
        await self._session.flush()
