import logging
from collections.abc import Sequence, AsyncGenerator
from typing import Any

from sqlalchemy import Result, select, update, Select, delete, func

from musigree.exceptions import NotFoundError, UnprocessableError
from musigree.library.fields.entity_type import EntityType
from musigree.offline.database.base_repository import BaseRepository
from musigree.offline.database.entity_table import EntityTable
from musigree.offline.domain.entity import Entity

log = logging.getLogger(__name__)


class EntityRepository(BaseRepository[EntityTable]):
    """
    Repository for managing Entity objects in the database.

    This class provides async methods for interacting with the EntityTable in the
    database, including creating, retrieving, updating, and deleting entities.
    It also supports various query operations, such as finding entities by ID,
    type, name, or search content.

    Inherits from:
        BaseRepository[EntityTable]: Provides the basic async database interaction
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

    async def _get_all_by_query(
        self, query: Select[tuple[EntityTable]]
    ) -> list[Entity]:
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
            raise UnprocessableError(
                message=(
                    "For some reason count function returned not an integer."
                    f"Value: {value}"
                ),
            )

        return value

    async def all(self) -> AsyncGenerator[Entity, None]:
        """
        Retrieves all entities from the database.

        Yields:
            AsyncGenerator[Entity]: An async iterator yielding each entity.
        """
        query = select(EntityTable)
        result = await self._session.stream(
            query, execution_options={"yield_per": 1000}
        )
        async for row in result:
            yield Entity.model_validate(row[0])
            # for partition in results.partitions():
            #     partition is an iterable that will be at most 1000 items
            # for row in partition:
            #     yield Entity.model_validate(row[0])

    async def all_ids_and_names(self) -> AsyncGenerator[tuple[int, str], None]:
        """
        Retrieves all entity IDs and names from the database.

        Yields:
            AsyncGenerator[tuple[int, str]]: An async iterator yielding tuples of
                (entity ID, entity name).
        """
        query = select(EntityTable.id, EntityTable.entity_name)
        result = await self._session.stream(
            query, execution_options={"yield_per": 1000}
        )
        async for row in result:
            yield row[0], row[1]

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
            (EntityTable.entity_id == entity_id)
            & (EntityTable.entity_type == entity_type)
        )
        return await self._get_one_by_query(query)

    async def get_ids(self) -> Sequence[int]:
        """
        Retrieves all entity IDs from the database.

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
        return result.scalar_one_or_none()

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
        return result.scalar_one_or_none()

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

    # async def get_batched_ids(self, num_in_batch: int) -> Iterator[list[int]]:
    #     """
    #     Retrieves all entity IDs in batches.
    #
    #     Args:
    #         num_in_batch: The number of IDs in each batch.
    #
    #     Returns:
    #         List[List[int]]: A list of batches, where each batch is a list of entity IDs.
    #     """
    #     ids = await self.get_ids()
    #     return utils.batched(iter(ids), num_in_batch)

    async def find_by_search_content(self, search_string: str) -> list[Entity]:
        """
        Finds entities whose search content matches the given string.

        Args:
            search_string: The string to search for in the search content.

        Returns:
            List[Entity]: A list of entities matching the search string.
        """
        query = select(EntityTable).where(
            EntityTable.search_content.match(search_string)
        )
        return await self._get_all_by_query(query)

    async def create(self, entity: Entity) -> Entity:
        """
        Creates a new entity in the database.

        Args:
            entity: The entity to create.

        Returns:
            Entity: The created entity.
        """
        instance: EntityTable = await self._save(entity.model_dump())
        return Entity.model_validate(instance)

    async def get_by_type_and_name(
        self, entity_type: EntityType, entity_name: str
    ) -> Entity:
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
                (EntityTable.entity_type == entity_type)
                & (EntityTable.entity_name == entity_name)
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
        Updates an existing entity in the database.

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

    async def search_multi(
        self, entity_keys: list[tuple[int, EntityType]]
    ) -> list[Entity]:
        """
        Searches for multiple entities by their entity keys (entity ID and type).

        Args:
            entity_keys: A list of tuples, where each tuple contains an entity ID and
                its type.

        Returns:
            List[Entity]: A list of found entities.
        """
        artist_ids: list[int] = []
        label_ids: list[int] = []
        for entity_id, entity_type in entity_keys:
            if entity_type == EntityType.ARTIST:
                artist_ids.append(entity_id)
            elif entity_type == EntityType.LABEL:
                label_ids.append(entity_id)
        if artist_ids and label_ids:
            where_clause = (
                (EntityTable.entity_type == EntityType.ARTIST)
                & (EntityTable.entity_id.in_(artist_ids))
            ) | (
                (EntityTable.entity_type == EntityType.LABEL)
                & (EntityTable.entity_id.in_(label_ids))
            )
        elif artist_ids:
            where_clause = (EntityTable.entity_type == EntityType.ARTIST) & (
                EntityTable.entity_id.in_(artist_ids)
            )
        else:
            where_clause = (EntityTable.entity_type == EntityType.LABEL) & (
                EntityTable.entity_id.in_(label_ids)
            )
        query = select(EntityTable).where(where_clause)
        return await self._get_all_by_query(query)
