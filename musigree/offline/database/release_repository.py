import logging
from typing import Any, Sequence, AsyncGenerator

from sqlalchemy import select, Result, update, delete

from musigree.exceptions import NotFoundError
from musigree.offline.database.base_repository import BaseRepository
from musigree.offline.database.release_table import ReleaseTable
from musigree.offline.domain.release import Release

log = logging.getLogger(__name__)


class ReleaseRepository(BaseRepository[ReleaseTable]):
    """
    Repository for managing Release objects in the database.

    This class provides async methods for interacting with the ReleaseTable in the
    database, including creating, retrieving, and managing releases.

    Inherits from:
        BaseRepository[ReleaseTable]: Provides the basic async database interaction
            functionality.

    Attributes:
        schema_class (Type[ReleaseTable]): The SQLAlchemy table class for releases.
    """

    schema_class = ReleaseTable
    """The SQLAlchemy table class for releases."""

    async def all(self) -> AsyncGenerator[Release, None]:
        """
        Retrieves all releases from the database.

        Yields:
            AsyncGenerator[Release]: An async iterator yielding each release.
        """
        query = select(ReleaseTable)
        result = await self._session.stream(
            query, execution_options={"yield_per": 1000}
        )
        async for row in result:
            yield Release.model_validate(row[0])

    async def get_by_id(self, release_id: int) -> Release:
        """
        Retrieves a release by its ID.

        Args:
            release_id: The ID of the release to retrieve.

        Returns:
            Release: The retrieved release.

        Raises:
            NotFoundError: If no release is found with the given ID.
        """
        instance = await self._get("release_id", release_id)
        if not instance:
            raise NotFoundError
        return Release.model_validate(instance)

    async def get_by_master_id(self, master_id: int) -> list[Release]:
        """
        Retrieves all releases associated with a given master ID.

        Args:
            master_id: The master ID of the releases.

        Returns:
            List[Release]: A list of releases associated with the master ID.
        """
        query = select(ReleaseTable).where(ReleaseTable.master_id == master_id)
        result: Result = await self._session.execute(query)

        instances = result.scalars().all()
        return [Release.model_validate(instance) for instance in instances]

    async def create(self, release: Release) -> Release:
        """
        Creates a new release in the database.

        Args:
            release: The Release object to create.

        Returns:
            Release: The created release.
        """
        instance: ReleaseTable = await self._save(release.model_dump())
        return Release.model_validate(instance)

    async def get_ids(self) -> Sequence[int]:
        """
        Retrieves all release IDs from the database.

        Returns:
            Sequence[int]: A sequence of all release IDs.
        """
        query = select(ReleaseTable.release_id)
        result: Result = await self._session.execute(query)
        return result.scalars().all()

    async def update(
        self,
        release_id: int,
        payload: dict[str, Any],
    ) -> None:
        """
        Updates an existing release in the database.

        Args:
            release_id: The ID of the release to update.
            payload: A dictionary containing the fields to update and their new values.

        Returns:
            ReleaseTable: The updated release table row.

        Raises:
            DatabaseError: If there is an error updating the release.
        """
        query = (
            update(self.schema_class)
            .where(ReleaseTable.release_id == release_id)
            .values(payload)
        )
        await self._session.execute(query)
        await self._session.flush()

    async def delete_by_id(self, release_id: int) -> None:
        """
        Deletes a release by its ID.

        Args:
            release_id: The ID of the release to delete.
        """
        await self.execute(
            delete(self.schema_class).where(ReleaseTable.release_id == release_id)
        )
        await self._session.flush()
