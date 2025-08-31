import logging
from typing import AsyncGenerator

from sqlalchemy import Result, select, Select, delete

from musigree.exceptions import NotFoundError, DatabaseError
from musigree.library.cache.role_cache import RoleCache
from musigree.runtime.runtime_database import RuntimeRelationTable
from musigree.runtime.runtime_database.runtime_base_repository import (
    RuntimeBaseRepository,
)
from musigree.runtime.runtime_domain.relation import (
    RuntimeRelationDB,
    RuntimeRelationInternal,
    RuntimeRelationUncommitted,
)

log = logging.getLogger(__name__)


class RuntimeRelationRepository(RuntimeBaseRepository[RuntimeRelationTable]):
    """
    Repository for managing RuntimeRelation objects in the runtime database.

    This class provides async methods for interacting with the RuntimeRelationTable
    in the runtime database, including creating, retrieving, and deleting
    relations. It supports various query operations, such as finding relations
    by ID, key, or associated entity. It also includes bulk creation and
    deletion capabilities.

    Inherits from:
        RuntimeBaseRepository[RuntimeRelationTable]: Provides the basic runtime
            database interaction functionality.

    Attributes:
        schema_class (Type[RuntimeRelationTable]): The SQLAlchemy table class
            for runtime relations.
    """

    schema_class = RuntimeRelationTable
    """The SQLAlchemy table class for runtime relations."""

    async def _get_one_by_query(
        self, query: Select[tuple[RuntimeRelationTable]]
    ) -> RuntimeRelationInternal:
        """
        Executes a query that should return a single RuntimeRelation.

        Args:
            query: The SQLAlchemy query to execute.

        Returns:
            RuntimeRelationInternal: The retrieved relation.

        Raises:
            NotFoundError: If no relation is found matching the query.
        """
        result: Result = await self._session.execute(query)

        if not (instance := result.scalars().one_or_none()):
            raise NotFoundError

        relation_db = RuntimeRelationDB.model_validate(instance)
        return relation_db.to_domain()

    async def _get_all_by_query(
        self, query: Select[tuple[RuntimeRelationTable]]
    ) -> list[RuntimeRelationInternal]:
        """
        Executes a query that should return multiple RuntimeRelations.

        Args:
            query: The SQLAlchemy query to execute.

        Returns:
            List[RuntimeRelationInternal]: A list of retrieved relations.
        """
        result: Result = await self._session.execute(query)

        instances = result.scalars().all()
        relation_dbs = [
            RuntimeRelationDB.model_validate(instance) for instance in instances
        ]
        relations = [relation_db.to_domain() for relation_db in relation_dbs]
        return relations

    async def all(self) -> AsyncGenerator[RuntimeRelationInternal, None]:
        """
        Retrieves all relations from the runtime database.

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
        query = select(RuntimeRelationTable).where(
            RuntimeRelationTable.id == relation_id
        )
        result: Result = await self._session.execute(query)

        if not (instance := result.scalars().one_or_none()):
            raise NotFoundError
        return RuntimeRelationDB.model_validate(instance)

    async def get_id_by_key(self, key: dict) -> int:
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
        result: Result = await self._session.execute(query)

        if not (instance := result.scalar()):
            raise NotFoundError
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
            select(RuntimeRelationTable)
            .with_for_update(of=RuntimeRelationTable, nowait=True)
            .where(RuntimeRelationTable.id == relation_id)
        )
        return await self._get_one_by_query(query)

    async def find_by_key(self, key: dict) -> list[RuntimeRelationInternal]:
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
        query = select(RuntimeRelationTable).where(
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
        query = select(RuntimeRelationTable).where(
            (RuntimeRelationTable.subject == id_) | (RuntimeRelationTable.object == id_)
        )
        return await self._get_all_by_query(query)

    async def find_by_entity_and_roles(
        self, id_: int, role_ids: list[int]
    ) -> list[RuntimeRelationInternal]:
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
            select(RuntimeRelationTable)
            .where(
                (
                    (RuntimeRelationTable.subject == id_)
                    | (RuntimeRelationTable.object == id_)
                )
                & (RuntimeRelationTable.predicate.in_(role_ids))
            )
            .order_by(
                RuntimeRelationTable.predicate,
                RuntimeRelationTable.subject,
                RuntimeRelationTable.object,
            )
        )
        return await self._get_all_by_query(query)

    async def create(
        self, relation: RuntimeRelationUncommitted, on_conflict_do_nothing: bool = False
    ) -> RuntimeRelationInternal:
        """
        Creates a new relation in the runtime database.

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
        result: Result = await self._session.execute(query)
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
        Creates multiple relations in the runtime database in bulk.

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
        query = (
            RuntimeDatabaseManager.runtime_database_helper.generate_insert_bulk_query(
                self.schema_class, relation_dicts, on_conflict_do_nothing
            )
        )
        await self._session.execute(query)

    async def delete_by_entitys(self, id_: int) -> None:
        """
        Deletes all relations associated with a specific entity.

        Args:
            id_: The ID of the entity whose relations should be deleted.
        """
        query = delete(RuntimeRelationTable).where(
            (RuntimeRelationTable.subject == id_) | (RuntimeRelationTable.object == id_)
        )
        await self._session.execute(query)
        await self._session.flush()
