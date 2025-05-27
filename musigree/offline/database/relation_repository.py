import logging
from collections.abc import Iterator
from typing import List

from sqlalchemy import Result, select, Select, delete

from musigree.exceptions import NotFoundError, DatabaseError
from musigree.library.cache.role_cache import RoleCache
from musigree.offline.database.base_repository import BaseRepository
from musigree.offline.database.relation_table import RelationTable
from musigree.offline.domain.relation import (
    RelationUncommitted,
    RelationDB,
    RelationInternal,
)

log = logging.getLogger(__name__)


class RelationRepository(BaseRepository[RelationTable]):
    """
    Repository for managing Relation objects in the database.

    This class provides methods for interacting with the RelationTable in the
    database, including creating, retrieving, and deleting relations. It supports
    various query operations, such as finding relations by ID, key, or associated
    entity. It also includes bulk creation and deletion capabilities.

    Inherits from:
        BaseRepository[RelationTable]: Provides the basic database interaction
            functionality.

    Attributes:
        schema_class (Type[RelationTable]): The SQLAlchemy table class for relations.
    """

    schema_class = RelationTable
    """The SQLAlchemy table class for relations."""

    def _get_one_by_query(
        self, query: Select[tuple[RelationTable]]
    ) -> RelationInternal:
        """
        Executes a query that should return a single Relation.

        Args:
            query: The SQLAlchemy query to execute.

        Returns:
            RelationInternal: The retrieved relation.

        Raises:
            NotFoundError: If no relation is found matching the query.
        """
        result: Result = self.execute(query)
        # result: Result = await self.execute(query)

        if not (instance := result.scalars().one_or_none()):
            raise NotFoundError

        relation_db = RelationDB.model_validate(instance)
        return relation_db.to_domain()

    def _get_all_by_query(
        self, query: Select[tuple[RelationTable]]
    ) -> List[RelationInternal]:
        """
        Executes a query that should return multiple Relations.

        Args:
            query: The SQLAlchemy query to execute.

        Returns:
            List[RelationInternal]: A list of retrieved relations.
        """
        result: Result = self.execute(query)
        # result: Result = await self.execute(query)

        instances = result.scalars().all()
        relation_dbs = [RelationDB.model_validate(instance) for instance in instances]
        relations = [relation_db.to_domain() for relation_db in relation_dbs]
        return relations

    def all(self) -> Iterator[RelationDB]:
        """
        Retrieves all relations from the database.

        Yields:
            Iterator[RelationDB]: A iterrator yielding each relation.
        """
        query = select(RelationTable)
        with self._session.execute(
            query, execution_options={"yield_per": 1000}
        ) as results:
            for partition in results.partitions():
                # partition is an iterable that will be at most 1000 items
                for row in partition:
                    yield RelationDB.model_validate(row[0])

    def get(self, relation_id: int) -> RelationDB:
        """
        Retrieves a relation by its ID.

        Args:
            relation_id: The ID of the relation to retrieve.

        Returns:
            RelationDB: The retrieved relation.

        Raises:
            NotFoundError: If no relation is found with the given ID.
        """
        query = select(RelationTable).where(RelationTable.id == relation_id)
        result: Result = self.execute(query)
        # result: Result = await self.execute(query)

        if not (instance := result.scalars().one_or_none()):
            raise NotFoundError
        return RelationDB.model_validate(instance)

    def get_id_by_key(self, key: dict) -> int:
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
        query = select(RelationTable.id).where(
            (RelationTable.subject == key["subject"])
            & (RelationTable.predicate == key["role_id"])
            & (RelationTable.object == key["object"])
        )
        result: Result = self.execute(query)
        # result: Result = await self.execute(query)

        if not (instance := result.scalar()):
            raise NotFoundError
        return instance

    def find_by_id(self, relation_id: int) -> RelationInternal:
        """
        Retrieves a relation by its ID, with an option to lock the row for update.

        Args:
            relation_id: The ID of the relation to retrieve.

        Returns:
            RelationInternal: The retrieved relation.

        Raises:
            NotFoundError: If no relation is found with the given ID.
        """
        query = (
            select(RelationTable)
            .with_for_update(of=RelationTable, nowait=True)
            .where(RelationTable.id == relation_id)
        )
        return self._get_one_by_query(query)

    def find_by_key(self, key: dict) -> RelationInternal:
        """
        Retrieves a relation by its key components (subject, role, object).

        Args:
            key: A dictionary representing the key of the relation. It can
                contain 'role_id', 'role_name', or 'role'.

        Returns:
            RelationInternal: The retrieved relation.

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
        query = select(RelationTable).where(
            (RelationTable.subject == key["subject"])
            & (RelationTable.predicate == key["role_id"])
            & (RelationTable.object == key["object"])
        )
        return self._get_one_by_query(query)

    def find_by_entity(self, id_: int) -> List[RelationInternal]:
        """
        Retrieves all relations associated with a given entity ID.

        Args:
            id_: The ID of the entity.

        Returns:
            List[RelationInternal]: A list of relations associated with the entity.
        """
        # if roles:
        #     where_clause &= RelationTable.role.in_(roles)
        # TODO search by year
        # if year is not None:
        #     year_clause = cls.year.is_null(True)
        #     if isinstance(year, int):
        #         year_clause |= cls.year == year
        #     else:
        #         year_clause |= cls.year.between(year[0], year[1])
        #     where_clause &= year_clause
        query = (
            select(RelationTable)
            .where((RelationTable.subject == id_) | (RelationTable.object == id_))
            .order_by(
                RelationTable.predicate,
                RelationTable.subject,
                RelationTable.object,
            )
        )
        return self._get_all_by_query(query)

    def find_by_entity_and_roles(
        self, id_: int, role_ids: list[int]
    ) -> List[RelationInternal]:
        """
        Retrieves all relations associated with a given entity ID and a set of roles.

        Args:
            id_: The ID of the entity.
            role_ids: A list of role IDs.

        Returns:
            List[RelationInternal]: A list of relations associated with the entity
                and the specified roles.
        """
        if id_ is None:
            return []

        # if roles:
        #     where_clause &= RelationTable.role.in_(roles)
        # TODO search by year
        # if year is not None:
        #     year_clause = cls.year.is_null(True)
        #     if isinstance(year, int):
        #         year_clause |= cls.year == year
        #     else:
        #         year_clause |= cls.year.between(year[0], year[1])
        #     where_clause &= year_clause
        query = (
            select(RelationTable)
            .where(
                ((RelationTable.subject == id_) | (RelationTable.object == id_))
                & (RelationTable.predicate.in_(role_ids))
            )
            .order_by(
                RelationTable.predicate,
                RelationTable.subject,
                RelationTable.object,
            )
        )
        return self._get_all_by_query(query)

    def create(
        self, relation: RelationUncommitted, on_conflict_do_nothing=False
    ) -> RelationInternal:
        """
        Creates a new relation in the database.

        Args:
            relation: The RelationUncommitted object to create.
            on_conflict_do_nothing: If True, prevents the operation from failing if
                a unique constraint is violated.

        Returns:
            RelationInternal: The created relation.

        Raises:
            DatabaseError: If there is an error during the database operation.
        """
        from musigree.offline.offline_database_manager import OfflineDatabaseManager

        relation_dict = relation.model_dump(exclude={"role_name"})
        role_id = RoleCache.role_name_to_role_id_lookup[relation.role_name]
        relation_dict.update(predicate=role_id)
        query = OfflineDatabaseManager.offline_database_helper.generate_insert_query(
            self.schema_class, relation_dict, on_conflict_do_nothing
        )
        result: Result = self._session.execute(query)
        # result: Result = await self.execute(query)
        self._session.flush()
        # await self._session.flush()

        if not (instance := result.scalar_one_or_none()):
            raise DatabaseError

        relation_db = RelationDB.model_validate(instance)
        return relation_db.to_domain()

    def create_bulk(
        self, relations: List[RelationUncommitted], on_conflict_do_nothing=False
    ) -> None:
        """
        Creates multiple new relations in the database.

        Args:
            relations: A list of RelationUncommitted objects to create.
            on_conflict_do_nothing: If True, prevents the operation from failing if
                a unique constraint is violated.
        """
        from musigree.offline.offline_database_manager import OfflineDatabaseManager

        relation_dicts = []
        for relation in relations:
            relation_dict = relation.model_dump(exclude={"role_name"})
            role_id = RoleCache.role_name_to_role_id_lookup[relation.role_name]
            relation_dict.update(predicate=role_id)
            relation_dicts.append(relation_dict)
        query = (
            OfflineDatabaseManager.offline_database_helper.generate_insert_bulk_query(
                self.schema_class, relation_dicts, on_conflict_do_nothing
            )
        )
        self._session.execute(query)

    def delete_by_entitys(self, id_: int) -> None:
        """
        Deletes all relations associated with a given entity ID.

        Args:
            id_: The ID of the entity.
        """
        self.execute(
            delete(self.schema_class).where(
                (RelationTable.predicate == id_) | (RelationTable.object == id_)
            )
        )
        # await self.execute(delete(self.schema_class).where(self.schema_class.id == id_))
        # self._session.flush()
        # await self._session.flush()
