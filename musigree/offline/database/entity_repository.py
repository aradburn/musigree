import logging
from collections.abc import Iterator, Sequence
from typing import Any, List

from sqlalchemy import Result, select, update, Select, delete, func

from musigree import utils
from musigree.exceptions import NotFoundError, DatabaseError, UnprocessableError
from musigree.library.fields.entity_type import EntityType
from musigree.offline.database.base_repository import BaseRepository
from musigree.offline.database.entity_table import EntityTable
from musigree.offline.domain.entity import Entity

log = logging.getLogger(__name__)


class EntityRepository(BaseRepository[EntityTable]):
    """
    Repository for managing Entity objects in the database.

    This class provides methods for interacting with the EntityTable in the
    database, including creating, retrieving, updating, and deleting entities.
    It also supports various query operations, such as finding entities by ID,
    type, name, or search content.

    Inherits from:
        BaseRepository[EntityTable]: Provides the basic database interaction
            functionality.

    Attributes:
        schema_class (Type[EntityTable]): The SQLAlchemy table class for entities.
    """

    schema_class = EntityTable
    """
      The SQLAlchemy table class for entities.
    """

    def _get_one_by_query(self, query: Select[tuple[EntityTable]]) -> Entity:
        """
        Executes a query that should return a single Entity.

        Args:
            query: The SQLAlchemy query to execute.

        Returns:
            Entity: The retrieved entity.

        Raises:
            NotFoundError: If no entity is found matching the query.
        """
        result: Result = self.execute(query)
        # result: Result = await self.execute(query)

        if not (instance := result.scalars().one_or_none()):
            raise NotFoundError

        entity_db = Entity.model_validate(instance)
        return entity_db.to_domain()

    def _get_all_by_query(self, query: Select[tuple[EntityTable]]) -> List[Entity]:
        """
        Executes a query that should return multiple Entities.

        Args:
            query: The SQLAlchemy query to execute.

        Returns:
            List[Entity]: A list of retrieved entities.
        """
        result: Result = self.execute(query)

        instances = result.scalars().all()
        entity_dbs = [Entity.model_validate(instance) for instance in instances]
        entities = [entity_db.to_domain() for entity_db in entity_dbs]
        return entities

    def count_by_type(self, entity_type: EntityType) -> int:
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
        result: Result = self.execute(query)
        # result: Result = await self.execute(func.count(self.schema_class.id))
        value = result.scalar()

        if not isinstance(value, int):
            raise UnprocessableError(
                message=(
                    "For some reason count function returned not an integer."
                    f"Value: {value}"
                ),
            )

        return value

    def all(self) -> Iterator[Entity]:
        """
        Retrieves all entities from the database.

        Yields:
            Iterator[Entity]: An iterrator yielding each entity.
        """
        query = select(EntityTable)
        with self._session.execute(
            query, execution_options={"yield_per": 1000}
        ) as results:
            for partition in results.partitions():
                # partition is an iterable that will be at most 1000 items
                for row in partition:
                    yield Entity.model_validate(row[0])

    def all_ids_and_names(self) -> Iterator[tuple[int, str]]:
        """
        Retrieves all entity IDs and names from the database.

        Yields:
            Iterator[tuple[int, str]]: An iterrator yielding tuples of
                (entity ID, entity name).
        """
        query = select(EntityTable.id, EntityTable.entity_name)
        with self._session.execute(
            query, execution_options={"yield_per": 1000}
        ) as results:
            for partition in results.partitions():
                # partition is an iterable that will be at most 1000 items
                for row in partition:
                    yield row[0], row[1]

    def get_by_id(self, id_: int) -> Entity:
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
        return self._get_one_by_query(query)

    def get_by_entity_id_and_entity_type(
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
        return self._get_one_by_query(query)

    def get_ids(self) -> Sequence[int]:
        """
        Retrieves all entity IDs from the database.

        Returns:
            Sequence[int]: A sequence of all entity IDs.
        """
        return self._session.scalars(select(EntityTable.id)).all()

    def get_ids_by_type(self, entity_type: EntityType) -> Sequence[int]:
        """
        Retrieves all entity IDs of a specific type.

        Args:
            entity_type: The type of entities to retrieve.

        Returns:
            Sequence[int]: A sequence of entity IDs of the specified type.
        """
        return self._session.scalars(
            select(EntityTable.id).where(EntityTable.entity_type == entity_type)
        ).all()

    def get_entity_ids_by_type(self, entity_type: EntityType) -> Sequence[int]:
        """
        Retrieves all external entity IDs of a specific type.

        Args:
            entity_type: The type of entities to retrieve.

        Returns:
            Sequence[int]: A sequence of external entity IDs of the specified type.
        """
        return self._session.scalars(
            select(EntityTable.entity_id).where(EntityTable.entity_type == entity_type)
        ).all()

    def get_entity_id_by_entity_type_and_entity_name(
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
        return self._session.execute(
            select(EntityTable.entity_id).where(
                (EntityTable.entity_name == entity_name)
                & (EntityTable.entity_type == entity_type)
            )
        ).scalar_one_or_none()

    def get_id_by_entity_type_and_entity_name(
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
        return self._session.execute(
            select(EntityTable.id).where(
                (EntityTable.entity_name == entity_name)
                & (EntityTable.entity_type == entity_type)
            )
        ).scalar_one_or_none()

    def get_id_by_entity_type_and_entity_id(
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
        return self._session.execute(
            select(EntityTable.id).where(
                (EntityTable.entity_id == entity_id)
                & (EntityTable.entity_type == entity_type)
            )
        ).scalar_one_or_none()

    def get_batched_ids(self, num_in_batch: int) -> Iterator[List[int]]:
        """
        Retrieves all entity IDs in batches.

        Args:
            num_in_batch: The number of IDs in each batch.

        Returns:
            List[List[int]]: A list of batches, where each batch is a list of entity IDs.
        """
        return utils.batched(self.get_ids(), num_in_batch)

    def find_by_search_content(self, search_string: str) -> List[Entity]:
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
        return self._get_all_by_query(query)

    def create(self, entity: Entity) -> Entity:
        """
        Creates a new entity in the database.

        Args:
            entity: The entity to create.

        Returns:
            Entity: The created entity.
        """
        instance: EntityTable = self._save(entity.model_dump())
        # instance: EntityTable = await self._save(schema.model_dump())
        return Entity.model_validate(instance)

    def get_by_type_and_name(self, entity_type: EntityType, entity_name: str) -> Entity:
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
        return self._get_one_by_query(query)

    def update(
        self,
        id_: int,
        payload: dict[str, Any],
    ) -> Entity:
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
        query = (
            update(self.schema_class)
            .where(EntityTable.id == id_)
            .values(payload)
            .returning(self.schema_class)
        )
        result: Result = self._session.execute(query)
        # result: Result = await self.execute(query)
        self._session.flush()
        # await self._session.flush()

        if not (instance := result.scalar_one_or_none()):
            raise DatabaseError

        entity_db = Entity.model_validate(instance)
        return entity_db.to_domain()

    def delete_by_id(self, id_: int) -> None:
        """
        Deletes an entity by its ID.

        Args:
            id_: The ID of the entity to delete.
        """
        self.execute(delete(self.schema_class).where(EntityTable.id == id_))
        # await self.execute(delete(self.schema_class).where(self.schema_class.id == id_))
        # self._session.flush()
        # await self._session.flush()

    def search_multi(self, entity_keys) -> List[Entity]:
        """
        Searches for multiple entities by their entity keys (entity ID and type).

        Args:
            entity_keys: A list of tuples, where each tuple contains an entity ID and
                its type.

        Returns:
            List[Entity]: A list of found entities.
        """
        artist_ids: List[int] = []
        label_ids: List[int] = []
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
        return self._get_all_by_query(query)
