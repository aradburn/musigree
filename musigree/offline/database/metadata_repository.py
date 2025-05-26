import logging
from typing import Any

from sqlalchemy import Result, select, update, Select

from musigree.exceptions import NotFoundError, DatabaseError
from musigree.offline.database.base_repository import BaseRepository
from musigree.offline.database.metadata_table import MetadataTable
from musigree.offline.domain.metadata import Metadata, MetadataUncommitted

log = logging.getLogger(__name__)


class MetadataRepository(BaseRepository[MetadataTable]):
    """
    Repository for managing Metadata objects in the database.

    This class provides methods for interacting with the MetadataTable in the
    database, including creating, retrieving, and updating metadata entries.

    Inherits from:
        BaseRepository[MetadataTable]: Provides the basic database interaction
            functionality.

    Attributes:
        schema_class (Type[MetadataTable]): The SQLAlchemy table class for metadata.
    """

    schema_class = MetadataTable
    """
    The SQLAlchemy table class for metadata.
    """

    def _get_one_by_query(self, query: Select[tuple[MetadataTable]]) -> Metadata:
        """
        Executes a query that should return a single Metadata object.

        Args:
            query: The SQLAlchemy query to execute.

        Returns:
            Metadata: The retrieved metadata object.

        Raises:
            NotFoundError: If no metadata is found matching the query.
        """
        result: Result = self.execute(query)
        # result: Result = await self.execute(query)

        if not (instance := result.scalars().one_or_none()):
            raise NotFoundError

        metadata_db = Metadata.model_validate(instance)
        return metadata_db.to_domain()

    def get(self, metadata_id: int) -> Metadata:
        """
        Retrieves a Metadata object by its ID.

        Args:
            metadata_id: The ID of the metadata to retrieve.

        Returns:
            Metadata: The retrieved metadata object.

        Raises:
             NotFoundError: If no metadata is found matching the ID.
        """
        query = select(MetadataTable).where(MetadataTable.metadata_id == metadata_id)
        return self._get_one_by_query(query)

    def get_by_key(self, metadata_key: str) -> Metadata:
        """
        Retrieves a Metadata object by its key.

        Args:
            metadata_key: The key of the metadata to retrieve.

        Returns:
            Metadata: The retrieved metadata object.

        Raises:
             NotFoundError: If no metadata is found matching the key.
        """
        query = select(MetadataTable).where(MetadataTable.metadata_key == metadata_key)
        return self._get_one_by_query(query)

    def create(self, metadata: MetadataUncommitted) -> Metadata:
        """
        Creates a new Metadata object in the database.

        Args:
            metadata: The MetadataUncommitted object to create.

        Returns:
            Metadata: The created metadata object.
        """
        instance: MetadataTable = self._save(metadata.model_dump())
        # instance: MetadataTable = await self._save(metadata.model_dump())
        return Metadata.model_validate(instance)

    def update(
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
        result: Result = self._session.execute(query)
        # result: Result = await self.execute(query)
        self._session.flush()
        # await self._session.flush()

        if not (instance := result.scalar_one_or_none()):
            raise DatabaseError

        metadata_db = Metadata.model_validate(instance)
        return metadata_db.to_domain()
