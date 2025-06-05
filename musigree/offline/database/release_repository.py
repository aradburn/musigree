import logging
from collections.abc import Iterator, Sequence
from typing import Any, List

from sqlalchemy import Result, select, update, Select, delete

from musigree import utils
from musigree.exceptions import NotFoundError, DatabaseError
from musigree.offline.database.base_repository import BaseRepository
from musigree.offline.database.release_table import ReleaseTable
from musigree.offline.domain.release import Release

log = logging.getLogger(__name__)


class ReleaseRepository(BaseRepository[ReleaseTable]):
    """
    Repository for managing Release objects in the database.

    This class provides methods for interacting with the ReleaseTable in the
    database, including creating, retrieving, updating, and deleting releases.
    It supports various query operations, such as retrieving a release by its ID,
    getting all releases, and batching release IDs.

    Inherits from:
        BaseRepository[ReleaseTable]: Provides the basic database interaction
            functionality.

    Attributes:
        schema_class (Type[ReleaseTable]): The SQLAlchemy table class for releases.
    """

    schema_class = ReleaseTable
    """The SQLAlchemy table class for releases."""

    def _get_one_by_query(self, query: Select[tuple[ReleaseTable]]) -> Release:
        """
        Executes a query that should return a single Release.

        Args:
            query: The SQLAlchemy query to execute.

        Returns:
            Release: The retrieved release.

        Raises:
            NotFoundError: If no release is found matching the query.
        """
        result: Result = self.execute(query)
        # result: Result = await self.execute(query)

        if not (instance := result.scalars().one_or_none()):
            raise NotFoundError

        release_db = Release.model_validate(instance)
        return release_db.to_domain()

    def _get_all_by_query(self, query: Select[tuple[ReleaseTable]]) -> list[Release]:
        """
        Executes a query that should return multiple Releases.

        Args:
            query: The SQLAlchemy query to execute.

        Returns:
            List[Release]: A list of retrieved releases.
        """
        result: Result = self.execute(query)

        instances = result.scalars().all()
        release_dbs = [Release.model_validate(instance) for instance in instances]
        releases = [release_db.to_domain() for release_db in release_dbs]
        return releases

    def all(self) -> Iterator[Release]:
        """
        Retrieves all releases from the database.

        Yields:
            Iterator[Release]: An iterator yielding each release.
        """
        query = select(ReleaseTable)
        with self._session.execute(
            query, execution_options={"yield_per": 1000}
        ) as results:
            for partition in results.partitions():
                # partition is an iterable that will be at most 1000 items
                for row in partition:
                    yield Release.model_validate(row[0])

    def get(self, release_id: int) -> Release:
        """
        Retrieves a release by its ID.

        Args:
            release_id: The ID of the release to retrieve.

        Returns:
            Release: The retrieved release.

        Raises:
            NotFoundError: If no release is found with the given ID.
        """
        query = select(ReleaseTable).where(ReleaseTable.release_id == release_id)

        result: Result = self.execute(query)
        # result: Result = await self.execute(query)

        if not (instance := result.scalars().one_or_none()):
            raise NotFoundError

        return Release.model_validate(instance)

    def create(self, release: Release) -> Release:
        """
        Creates a new release in the database.

        Args:
            release: The Release object to create.

        Returns:
            Release: The created release.
        """
        instance: ReleaseTable = self._save(release.model_dump())
        # instance: ReleaseTable = await self._save(schema.model_dump())
        return Release.model_validate(instance)

    def get_ids(self) -> Sequence[int]:
        """
        Retrieves all release IDs from the database.

        Returns:
            Sequence[int]: A sequence of all release IDs.
        """
        return self._session.scalars(select(ReleaseTable.release_id)).all()

    def get_batched_ids(self, num_in_batch: int) -> Iterator[List[int]]:
        """
        Retrieves all release IDs in batches.

        Args:
            num_in_batch: The number of IDs in each batch.

        Returns:
            List[List[int]]: A list of batches, where each batch is a list of release IDs.
        """
        return utils.batched(self.get_ids(), num_in_batch)

    def update(
        self,
        release_id: int,
        payload: dict[str, Any],
    ) -> ReleaseTable:
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
            .returning(self.schema_class)
        )
        result: Result = self._session.execute(query)
        # result: Result = await self.execute(query)
        self._session.flush()
        # await self._session.flush()

        if not (schema := result.scalar_one_or_none()):
            raise DatabaseError

        return schema

    def delete_by_id(self, release_id: int) -> None:
        """
        Deletes a release by its ID.

        Args:
            release_id: The ID of the release to delete.
        """
        self.execute(
            delete(self.schema_class).where(ReleaseTable.release_id == release_id)
        )
        # await self.execute(delete(self.schema_class).where(self.schema_class.id == id_))
        # self._session.flush()
        # await self._session.flush()
