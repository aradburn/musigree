"""
This module defines the `RuntimeEntityRepository` class, which is responsible for
managing `RuntimeEntity` objects in the runtime runtime_database.

It provides async methods for performing various operations on entities, such as
creating, retrieving, updating, and deleting entities. It also supports
searching for entities based on different criteria.

Key functionalities include:
    - Retrieving entities by ID, entity ID and type, type and name.
    - Retrieving multiple entities by a list of entity keys.
    - Counting entities by type.
    - Iterating through all entities or a subset based on a type.
    - Creating new entities and updating existing ones.
    - Deleting entities by ID.
    - Searching for entities based on various criteria.

The `RuntimeEntityRepository` interacts with the `RuntimeEntityTable` in the
runtime_database to persist and retrieve entity data. It utilizes SQLAlchemy for runtime_database
operations and inherits common functionality from `RuntimeBaseRepository`.
"""

import logging
import random
from collections.abc import Sequence
from typing import Any, AsyncGenerator

from sqlalchemy import Result, select, tuple_, update, Select, delete, func, null

from musigree.constants import BULK_YIELD_SIZE
from musigree.exceptions import NotFoundError, DatabaseError
from musigree.library.fields.entity_type import EntityType
from musigree.runtime.runtime_database import RuntimeEntityTable
from musigree.runtime.runtime_database.runtime_base_repository import (
    RuntimeBaseRepository,
)
from musigree.runtime.runtime_domain.runtime_entity import RuntimeEntity, RuntimeEntityDB

log = logging.getLogger(__name__)


class RuntimeEntityRepository(RuntimeBaseRepository[RuntimeEntityTable]):
    """
    Repository for managing `RuntimeEntity` objects in the runtime runtime_database.

    This class provides async methods for interacting with the `RuntimeEntityTable`
    in the runtime runtime_database, including creating, retrieving, updating, and
    deleting entities. It supports various query operations, such as finding
    entities by ID, entity ID and type, or a list of entity keys.

    Inherits from:
        RuntimeBaseRepository[RuntimeEntityTable]: Provides the basic runtime
            runtime_database interaction functionality.

    Attributes:
        schema_class (Type[RuntimeEntityTable]): The SQLAlchemy table class
            for runtime entities.
    """

    schema_class = RuntimeEntityTable
    """The SQLAlchemy table class for runtime entities."""

    async def _get_one_by_query(self, query: Select[tuple[RuntimeEntityTable]]) -> RuntimeEntity:
        """
        Executes a query that should return a single `RuntimeEntity`.

        Args:
            query: The SQLAlchemy query to execute.

        Returns:
            RuntimeEntity: The retrieved entity.

        Raises:
            NotFoundError: If no entity is found matching the query.
        """
        result: Result = await self.execute(query)

        if not (instance := result.scalars().one_or_none()):
            raise NotFoundError

        entity_db = RuntimeEntityDB.model_validate(instance)
        return entity_db.to_domain()

    async def _get_all_by_query(
        self, query: Select[tuple[RuntimeEntityTable]]
    ) -> list[RuntimeEntity]:
        """
        Executes a query that should return multiple `RuntimeEntity` objects.

        Args:
            query: The SQLAlchemy query to execute.

        Returns:
            List[RuntimeEntity]: A list of retrieved entities.
        """
        result: Result = await self.execute(query)
        instances = result.scalars().all()
        entity_dbs = [RuntimeEntityDB.model_validate(instance) for instance in instances]
        entities = [entity_db.to_domain() for entity_db in entity_dbs]
        return entities

    async def count_by_type(self, entity_type: EntityType) -> int:
        """
        Counts the number of entities of a specific type.

        Args:
            entity_type: The type of entity to count.

        Returns:
            int: The number of entities of the specified type.

        Raises:
            UnprocessableError: If the runtime_database query returns a non-integer value.
        """
        query = (
            select(func.count())
            .select_from(self.schema_class)
            .where(RuntimeEntityTable.entity_type == entity_type)
        )
        result: Result = await self.execute(query)
        value = result.scalar()

        if not isinstance(value, int):
            raise DatabaseError(
                message=f"For some reason count function returned not an integer.Value: {value}",
            )

        return value

    async def all(self) -> AsyncGenerator[RuntimeEntity, None]:
        """
        Retrieves all entities from the runtime runtime_database.

        Yields:
            AsyncGenerator[RuntimeEntity]: An async iterator yielding each entity.
        """
        query = select(RuntimeEntityTable)
        result = await self._session.stream(query, execution_options={"yield_per": BULK_YIELD_SIZE})
        async for row in result:
            yield RuntimeEntityDB.model_validate(row[0]).to_domain()

    async def all_ids_and_names(self) -> AsyncGenerator[tuple[int, str], None]:
        """
        Retrieves all entity IDs and names from the runtime runtime_database.

        Yields:
            AsyncGenerator[tuple[int, str]]: An async iterator yielding each
            entity's ID and name as a tuple.
        """
        query = select(RuntimeEntityTable.id, RuntimeEntityTable.entity_name)
        result = await self._session.stream(query, execution_options={"yield_per": BULK_YIELD_SIZE})
        async for row in result:
            yield row[0], row[1]

    async def get_by_id(self, id_: int) -> RuntimeEntity:
        """
        Retrieves an entity by its internal ID.

        Args:
            id_: The internal ID of the entity to retrieve.

        Returns:
            RuntimeEntity: The retrieved entity.

        Raises:
            NotFoundError: If no entity is found with the given ID.
        """
        query = select(RuntimeEntityTable).where(RuntimeEntityTable.id == id_)
        return await self._get_one_by_query(query)

    async def get_by_entity_id_and_entity_type(
        self, entity_id: int, entity_type: EntityType
    ) -> RuntimeEntity:
        """
        Retrieves an entity by its external entity ID and entity type.

        Args:
            entity_id: The external ID of the entity.
            entity_type: The type of the entity.

        Returns:
            RuntimeEntity: The retrieved entity.

        Raises:
            NotFoundError: If no entity is found with the given ID and type.
        """
        query = select(RuntimeEntityTable).where(
            (RuntimeEntityTable.entity_id == entity_id)
            & (RuntimeEntityTable.entity_type == entity_type)
        )
        return await self._get_one_by_query(query)

    async def get_ids(self) -> Sequence[int]:
        """
        Retrieves all internal entity IDs.

        Returns:
            list[int]: A list of internal entity IDs.
        """
        result = await self._session.scalars(select(RuntimeEntityTable.id))
        return result.all()

    async def get_ids_by_type(self, entity_type: EntityType) -> Sequence[int]:
        """
        Retrieves all internal entity IDs of a specific entity type.

        Args:
            entity_type: The type of entity.

        Returns:
            list[int]: A list of internal entity IDs of the specified type.
        """
        result = await self._session.scalars(
            select(RuntimeEntityTable.id).where(RuntimeEntityTable.entity_type == entity_type)
        )
        return result.all()

    async def get_entity_ids_by_type(self, entity_type: EntityType) -> Sequence[int]:
        """
        Retrieves all external entity IDs of a specific entity type.

        Args:
            entity_type: The type of entity.

        Returns:
            list[int]: A list of external entity IDs of the specified type.
        """
        result = await self._session.scalars(
            select(RuntimeEntityTable.entity_id).where(
                RuntimeEntityTable.entity_type == entity_type
            )
        )
        return result.all()

    async def get_entity_id_by_entity_type_and_entity_name(
        self, entity_type: EntityType, entity_name: str
    ) -> int | None:
        """
        Retrieves an external entity ID by entity type and entity name.

        Args:
            entity_type: The type of the entity.
            entity_name: The name of the entity.

        Returns:
            int | None: The external entity ID, or None if not found.
        """
        result = await self._session.execute(
            select(RuntimeEntityTable.entity_id).where(
                (RuntimeEntityTable.entity_name == entity_name)
                & (RuntimeEntityTable.entity_type == entity_type)
            )
        )
        return result.scalar_one_or_none()

    async def get_id_by_entity_type_and_entity_name(
        self, entity_type: EntityType, entity_name: str
    ) -> int | None:
        """
        Retrieves an internal entity ID by entity type and entity name.

        Args:
            entity_type: The type of the entity.
            entity_name: The name of the entity.

        Returns:
            int | None: The internal entity ID, or None if not found.
        """
        result = await self._session.execute(
            select(RuntimeEntityTable.id).where(
                (RuntimeEntityTable.entity_name == entity_name)
                & (RuntimeEntityTable.entity_type == entity_type)
            )
        )
        return result.scalar_one_or_none()

    async def get_id_by_entity_type_and_entity_id(
        self, entity_type: EntityType, entity_id: int
    ) -> int | None:
        """
        Retrieves an internal entity ID by entity type and external entity ID.

        Args:
            entity_type: The type of the entity.
            entity_id: The external entity ID.

        Returns:
            int | None: The internal entity ID, or None if not found.
        """
        result = await self._session.execute(
            select(RuntimeEntityTable.id).where(
                (RuntimeEntityTable.entity_id == entity_id)
                & (RuntimeEntityTable.entity_type == entity_type)
            )
        )
        return result.scalar_one_or_none()

    async def get_entity_name_by_id(self, id_: int) -> str | None:
        """
        Retrieves an entity name by its id.

        Args:
            id_: The id of the entity.

        Returns:
            str | None: The entity name, or None if not found.
        """
        result = await self._session.execute(
            select(RuntimeEntityTable.entity_name).where(RuntimeEntityTable.id == id_)
        )
        return result.scalar_one_or_none()

    async def create(self, entity: RuntimeEntity) -> RuntimeEntity:
        """
        Creates a new entity in the runtime runtime_database.

        Args:
            entity: The `RuntimeEntity` object to create.

        Returns:
            RuntimeEntity: The created entity.
        """
        entity_uncommitted = entity.to_db()
        instance: RuntimeEntityTable = await self._save(entity_uncommitted.model_dump())
        entity_db = RuntimeEntityDB.model_validate(instance)
        return entity_db.to_domain()

    async def get_by_type_and_name(
        self, entity_type: EntityType, entity_name: str
    ) -> RuntimeEntity:
        """
        Retrieves an entity by its type and name.

        Args:
            entity_type: The type of the entity.
            entity_name: The name of the entity.

        Returns:
            RuntimeEntity: The retrieved entity.

        Raises:
            NotFoundError: If no entity is found with the given type and name.
        """
        query = (
            select(RuntimeEntityTable)
            .where(
                (RuntimeEntityTable.entity_type == entity_type)
                & (RuntimeEntityTable.entity_name == entity_name)
            )
            .limit(1)
        )
        return await self._get_one_by_query(query)

    async def update(
        self,
        id_: int,
        payload: dict[str, Any],
    ) -> None:
        """
        Updates an existing entity in the runtime_database.

        Args:
            id_: The internal ID of the entity to update.
            payload: A dictionary containing the data to update.

        Returns:
            RuntimeEntityTable: The updated entity.

        Raises:
            DatabaseError: If there is an error during the update operation.
        """
        query = update(self.schema_class).where(RuntimeEntityTable.id == id_).values(payload)
        _result: Result = await self._session.execute(query)
        await self._session.flush()

    async def delete_by_id(self, id_: int) -> None:
        """
        Deletes an entity by its internal ID.

        Args:
            id_: The internal ID of the entity to delete.
        """
        await self.execute(delete(self.schema_class).where(RuntimeEntityTable.id == id_))
        await self._session.flush()

    async def search_multi(self, entity_keys: list[tuple[int, EntityType]]) -> list[RuntimeEntity]:
        """
        Retrieves multiple entities based on a list of entity keys.

        Args:
            entity_keys: A list of tuples, where each tuple contains an
                external entity ID and an entity type.

        Returns:
            List[RuntimeEntity]: A list of retrieved entities.
        """
        if not entity_keys:
            return []
        composite_keys = [(entity_id, entity_type.value) for entity_id, entity_type in entity_keys]
        # Select every column required by RuntimeEntityDB except the (potentially
        # large) entity_metadata, which is returned as NULL to avoid loading it.
        query = select(
            RuntimeEntityTable.id,
            RuntimeEntityTable.entity_id,
            RuntimeEntityTable.entity_type,
            RuntimeEntityTable.entity_name,
            RuntimeEntityTable.relation_counts,
            null().label(RuntimeEntityTable.entity_metadata.key),
            RuntimeEntityTable.aliases,
            RuntimeEntityTable.groups,
            RuntimeEntityTable.members,
            RuntimeEntityTable.parent_label,
            RuntimeEntityTable.countries,
            RuntimeEntityTable.genres,
            RuntimeEntityTable.styles,
        ).where(
            tuple_(RuntimeEntityTable.entity_id, RuntimeEntityTable.entity_type).in_(composite_keys)
        )
        result: Result = await self.execute(query)
        # mappings() yields a dict per row; scalars() would return only the first
        # column (entity_id) and break model_validate.
        rows = result.mappings().all()
        entity_dbs = [RuntimeEntityDB.model_validate(dict(row)) for row in rows]
        entities = [entity_db.to_domain() for entity_db in entity_dbs]
        return entities

    async def get_random_entity(self, max_row: int) -> RuntimeEntity | None:
        """
        Retrieves a random entity id.

        Returns:
            int | None: The entity id or None if none found.
        """
        random_row = random.randint(0, max_row)
        query = (
            select(RuntimeEntityTable)
            .where(RuntimeEntityTable.id >= random_row)
            .order_by(RuntimeEntityTable.id)
            .limit(1)
        )
        result: Result = await self.execute(query)
        instance = result.scalar_one_or_none()
        if instance is None:
            return None
        entity_db = RuntimeEntityDB.model_validate(instance)
        return entity_db.to_domain()
