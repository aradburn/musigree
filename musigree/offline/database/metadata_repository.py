import logging
from typing import Any, AsyncGenerator

from sqlalchemy import Result, select, update

from musigree.exceptions import NotFoundError, DatabaseError
from musigree.offline.database.base_repository import BaseRepository
from musigree.offline.database.metadata_table import MetadataTable
from musigree.offline.domain.metadata import Metadata, MetadataUncommitted

log = logging.getLogger(__name__)


class MetadataRepository(BaseRepository[MetadataTable]):
    """
    Repository for managing Metadata objects in the database.

    This class provides async methods for interacting with the MetadataTable in the
    database, including creating, retrieving, and managing metadata.

    Inherits from:
        BaseRepository[MetadataTable]: Provides the basic async database interaction
            functionality.

    Attributes:
        schema_class (Type[MetadataTable]): The SQLAlchemy table class for metadata.
    """

    schema_class = MetadataTable
    """
    The SQLAlchemy table class for metadata.
    """

    async def all(self) -> AsyncGenerator[Metadata, None]:
        """
        Retrieves all metadata from the database.

        Yields:
            AsyncGenerator[Metadata]: An async iterator yielding each metadata.
        """
        async for instance in self._all():
            yield Metadata.model_validate(instance)

    async def get_by_id(self, metadata_id: int) -> Metadata:
        """
        Retrieves metadata by its ID.

        Args:
            metadata_id: The ID of the metadata to retrieve.

        Returns:
            Metadata: The retrieved metadata.

        Raises:
            NotFoundError: If no metadata is found with the given ID.
        """
        instance = await self._get("metadata_id", metadata_id)
        if not instance:
            raise NotFoundError
        return Metadata.model_validate(instance)

    async def get_by_key(self, key: str) -> Metadata:
        """
        Retrieves metadata by its key.

        Args:
            key: The key of the metadata to retrieve.

        Returns:
            Metadata: The retrieved metadata.

        Raises:
            NotFoundError: If no metadata is found with the given key.
        """
        query = select(MetadataTable).where(MetadataTable.metadata_key == key)
        result: Result = await self._session.execute(query)

        if not (instance := result.scalars().one_or_none()):
            raise NotFoundError
        return Metadata.model_validate(instance)

    async def create(self, metadata: MetadataUncommitted) -> Metadata:
        """
        Creates a new Metadata object in the database.

        Args:
            metadata: The MetadataUncommitted object to create.

        Returns:
            Metadata: The created metadata object.
        """
        instance: MetadataTable = await self._save(metadata.model_dump())
        return Metadata.model_validate(instance)

    async def update_by_key(self, key: str, value: str) -> Metadata:
        """
        Updates metadata by its key.

        Args:
            key: The key of the metadata to update.
            value: The new value for the metadata.

        Returns:
            Metadata: The updated metadata.

        Raises:
            NotFoundError: If no metadata is found with the given key.
        """
        instance = await self._update("metadata_key", key, {"metadata_value": value})
        return Metadata.model_validate(instance)

    async def update(
        self,
        payload: dict[str, Any],
    ) -> Metadata:
        """
        Updates an existing Metadata object in the database.

        Args:
            payload: A dictionary containing the fields to update and their new values.

        Returns:
            Metadata: The updated metadata object.

        Raises:
            DatabaseError: If there is an error updating the metadata.
        """
        query = update(self.schema_class).values(payload).returning(self.schema_class)
        result: Result = await self._session.execute(query)

        if not (instance := result.scalar_one_or_none()):
            raise DatabaseError

        metadata_db = Metadata.model_validate(instance)
        return metadata_db.to_domain()
