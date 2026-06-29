import logging
import re
from collections.abc import Sequence, AsyncGenerator
from typing import Any

from sqlalchemy import Result, select, tuple_, update, Select, delete, func

from musigree.constants import BULK_YIELD_SIZE
from musigree.exceptions import NotFoundError, DatabaseError
from musigree.library.fields.entity_type import EntityType
from musigree.offline.offline_database.base_repository import BaseRepository
from musigree.offline.offline_database.entity_table import EntityTable
from musigree.offline.offline_domain.entity import Entity

log = logging.getLogger(__name__)


class EntityRepository(BaseRepository[EntityTable]):
    """
    Repository for managing Entity objects in the runtime_database.

    This class provides async methods for interacting with the EntityTable in the
    runtime_database, including creating, retrieving, updating, and deleting entities.
    It also supports various query operations, such as finding entities by ID,
    type, name, or search content.

    Inherits from:
        BaseRepository[EntityTable]: Provides the basic async runtime_database interaction
            functionality.

    Attributes:
        schema_class (Type[EntityTable]): The SQLAlchemy table class for entities.
    """

    schema_class = EntityTable
    """
      The SQLAlchemy table class for entities.
    """

    async def _get_one_by_query(self, query: Select[tuple[EntityTable]]) -> Entity:
        """
        Executes a query that should return a single Entity.

        Args:
            query: The SQLAlchemy query to execute.

        Returns:
            Entity: The retrieved entity.

        Raises:
            NotFoundError: If no entity is found matching the query.
        """
        result = await self.execute(query)

        if not (instance := result.scalars().one_or_none()):
            raise NotFoundError

        entity_db = Entity.model_validate(instance)
        return entity_db.to_domain()

    async def _get_all_by_query(self, query: Select[tuple[EntityTable]]) -> list[Entity]:
        """
        Executes a query that should return multiple Entities.

        Args:
            query: The SQLAlchemy query to execute.

        Returns:
            List[Entity]: A list of retrieved entities.
        """
        result = await self.execute(query)
        instances = result.scalars().all()
        entity_dbs = [Entity.model_validate(instance) for instance in instances]
        entities = [entity_db.to_domain() for entity_db in entity_dbs]
        return entities

    async def count_by_type(self, entity_type: EntityType) -> int:
        """
        Counts the number of entities of a given type.

        Args:
            entity_type: The type of entity to count.

        Returns:
            int: The number of entities of the specified type.

        Raises:
            UnprocessableError: If the count function returns a non-integer value.
        """
        query = (
            select(func.count())
            .select_from(self.schema_class)
            .where(EntityTable.entity_type == entity_type)
        )
        result = await self.execute(query)
        value = result.scalar()

        if not isinstance(value, int):
            raise DatabaseError(
                message=f"Count function returned non integer value: {value}",
            )

        return value

    async def all(self) -> AsyncGenerator[list[Entity], None]:
        """
        Retrieves all entities from the runtime_database.

        Yields:
            AsyncGenerator[Entity]: An async iterator yielding each entity.
        """
        query = select(EntityTable)
        result = await self._session.stream(query, execution_options={"yield_per": BULK_YIELD_SIZE})
        async for partition in result.partitions():
            # partition is an iterable that will be at most 1000 items
            entities: list[Entity] = []
            for row in partition:
                entities.append(Entity.model_validate(row[0]))
            yield entities

    async def all_ids_and_names(self) -> AsyncGenerator[list[tuple[int, str]], None]:
        """
        Retrieves all entity IDs and names from the runtime_database.

        Yields:
            AsyncGenerator[tuple[int, str]]: An async iterator yielding tuples of
                (entity ID, entity name).
        """
        query = select(EntityTable.id, EntityTable.entity_name, EntityTable.entity_metadata)
        result = await self._session.stream(query, execution_options={"yield_per": BULK_YIELD_SIZE})
        async for partition in result.partitions():
            # partition is an iterable that will be at most BULK_YIELD_SIZE items
            tuples: list[tuple[int, str]] = []
            for row in partition:
                tuples.append((row[0], row[1]))
                entity_metadata: dict[str, Any] = row[2]
                if entity_metadata is not None:
                    if "name_variations" in entity_metadata:
                        name_variation_list: list[str] | None = entity_metadata["name_variations"]
                        if name_variation_list:
                            for name_variation in name_variation_list:
                                tuples.append((row[0], name_variation))
                                if name_variation == "NULL":
                                    log.debug(f"name_variation: {row[0]}: {name_variation}")
                    if "real_name" in entity_metadata:
                        real_name: str | None = entity_metadata["real_name"]
                        if real_name is not None:
                            split_real_names = re.split(r",|&|and|/|&amp;", real_name)
                            for split_name in split_real_names:
                                tuples.append((row[0], split_name.strip()))
                                if split_name == "NULL":
                                    log.debug(f"split_name is NULL: {row[0]}: {split_name}")
            yield tuples

    async def get_by_id(self, id_: int) -> Entity:
        """
        Retrieves an entity by its ID.

        Args:
            id_: The ID of the entity to retrieve.

        Returns:
            Entity: The retrieved entity.

        Raises:
            NotFoundError: If no entity is found with the given ID.
        """
        query = select(EntityTable).where(EntityTable.id == id_)
        return await self._get_one_by_query(query)

    async def get_by_entity_id_and_entity_type(
        self, entity_id: int, entity_type: EntityType
    ) -> Entity:
        """
        Retrieves an entity by its external entity ID and type.

        Args:
            entity_id: The external ID of the entity.
            entity_type: The type of the entity.

        Returns:
            Entity: The retrieved entity.

        Raises:
            NotFoundError: If no entity is found with the given external ID and type.
        """
        query = select(EntityTable).where(
            (EntityTable.entity_id == entity_id) & (EntityTable.entity_type == entity_type)
        )
        return await self._get_one_by_query(query)

    async def get_ids(self) -> Sequence[int]:
        """
        Retrieves all entity IDs from the runtime_database.

        Returns:
            Sequence[int]: A sequence of all entity IDs.
        """
        query = select(EntityTable.id)
        result = await self._session.execute(query)
        return result.scalars().all()

    async def get_ids_by_type(self, entity_type: EntityType) -> Sequence[int]:
        """
        Retrieves all entity IDs of a specific type.

        Args:
            entity_type: The type of entities to retrieve.

        Returns:
            Sequence[int]: A sequence of entity IDs of the specified type.
        """
        query = select(EntityTable.id).where(EntityTable.entity_type == entity_type)
        result = await self._session.execute(query)
        return result.scalars().all()

    async def get_entity_ids_by_type(self, entity_type: EntityType) -> Sequence[int]:
        """
        Retrieves all external entity IDs of a specific type.

        Args:
            entity_type: The type of entities to retrieve.

        Returns:
            Sequence[int]: A sequence of external entity IDs of the specified type.
        """
        query = select(EntityTable.entity_id).where(EntityTable.entity_type == entity_type)
        result = await self._session.execute(query)
        return result.scalars().all()

    async def get_entity_id_by_entity_type_and_entity_name(
        self, entity_type: EntityType, entity_name: str
    ) -> int | None:
        """
        Retrieves an external entity ID by its type and name.

        Args:
            entity_type: The type of the entity.
            entity_name: The name of the entity.

        Returns:
            int | None: The external entity ID, or None if no matching entity is found.
        """
        query = select(EntityTable.entity_id).where(
            (EntityTable.entity_name == entity_name) & (EntityTable.entity_type == entity_type)
        )
        result = await self._session.execute(query)
        # Note: There can be more than one row here, we just pick the first
        one = result.scalar()
        return one

    async def get_id_by_entity_type_and_entity_name(
        self, entity_type: EntityType, entity_name: str
    ) -> int | None:
        """
        Retrieves an entity ID by its type and name.

        Args:
            entity_type: The type of the entity.
            entity_name: The name of the entity.

        Returns:
            int | None: The entity ID, or None if no matching entity is found.
        """
        query = select(EntityTable.id).where(
            (EntityTable.entity_name == entity_name) & (EntityTable.entity_type == entity_type)
        )
        result = await self._session.execute(query)
        # Note: There can be more than one row here, we just pick the first
        one = result.scalar()
        return one

    async def get_id_by_entity_type_and_entity_id(
        self, entity_type: EntityType, entity_id: int
    ) -> int | None:
        """
        Retrieves an entity ID by its type and external entity ID.

        Args:
            entity_type: The type of the entity.
            entity_id: The external ID of the entity.

        Returns:
            int | None: The entity ID, or None if no matching entity is found.
        """
        query = select(EntityTable.id).where(
            (EntityTable.entity_id == entity_id) & (EntityTable.entity_type == entity_type)
        )
        result = await self._session.execute(query)
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
            select(EntityTable.entity_name).where(EntityTable.id == id_)
        )
        return result.scalar_one_or_none()

    async def create(self, entity: Entity) -> Entity:
        """
        Creates a new entity in the runtime_database.

        Args:
            entity: The entity to create.

        Returns:
            Entity: The created entity.
        """
        instance: EntityTable = await self._save(entity.model_dump())
        return Entity.model_validate(instance)

    async def get_by_type_and_name(self, entity_type: EntityType, entity_name: str) -> Entity:
        """
        Retrieves an entity by its type and name.

        Args:
            entity_type: The type of the entity.
            entity_name: The name of the entity.

        Returns:
            Entity: The retrieved entity.

        Raises:
            NotFoundError: If no entity is found with the given type and name.
        """
        query = (
            select(EntityTable)
            .where(
                (EntityTable.entity_type == entity_type) & (EntityTable.entity_name == entity_name)
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
            id_: The ID of the entity to update.
            payload: A dictionary containing the fields to update and their new values.

        Returns:
            Entity: The updated entity.

        Raises:
            DatabaseError: If there is an error updating the entity.
        """
        query = update(self.schema_class).where(EntityTable.id == id_).values(payload)
        _result: Result = await self._session.execute(query)
        await self._session.flush()

    async def delete_by_id(self, id_: int) -> None:
        """
        Deletes an entity by its ID.

        Args:
            id_: The ID of the entity to delete.
        """
        query = delete(self.schema_class).where(EntityTable.id == id_)
        await self.execute(query)
        await self._session.flush()

    async def search_multi(self, entity_keys: list[tuple[int, EntityType]]) -> list[Entity]:
        """
        Searches for multiple entities by their entity keys (entity ID and type).

        Args:
            entity_keys: A list of tuples, where each tuple contains an entity ID and
                its type.

        Returns:
            List[Entity]: A list of found entities.
        """
        if not entity_keys:
            return []
        composite_keys = [(entity_id, entity_type.value) for entity_id, entity_type in entity_keys]
        query = select(EntityTable).where(
            tuple_(EntityTable.entity_id, EntityTable.entity_type).in_(composite_keys)
        )
        return await self._get_all_by_query(query)
