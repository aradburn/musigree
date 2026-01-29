import logging
from typing import Any, Sequence, AsyncGenerator

from sqlalchemy import select, Result, update, delete

from musigree.constants import BULK_YIELD_SIZE
from musigree.exceptions import NotFoundError
from musigree.offline.offline_database.base_repository import BaseRepository
from musigree.offline.offline_database.master_table import MasterTable
from musigree.offline.offline_domain.master import Master

log = logging.getLogger(__name__)


class MasterRepository(BaseRepository[MasterTable]):
    """
    Repository for managing master objects in the runtime_database.

    This class provides async methods for interacting with the MasterTable in the
    runtime_database, including creating, retrieving, and managing masters.

    Inherits from:
        BaseRepository[MasterTable]: Provides the basic async runtime_database interaction
            functionality.

    Attributes:
        schema_class (Type[MasterTable]): The SQLAlchemy table class for masters.
    """

    schema_class = MasterTable
    """The SQLAlchemy table class for masters."""

    async def all(self) -> AsyncGenerator[list[Master], None]:
        """
        Retrieves all masters from the runtime_database.

        Yields:
            AsyncGenerator[master]: An async iterator yielding each master.
        """
        query = select(MasterTable)
        result = await self._session.stream(query, execution_options={"yield_per": BULK_YIELD_SIZE})
        async for partition in result.partitions():
            # partition is an iterable that will be at most 1000 items
            masters: list[Master] = []
            for row in partition:
                masters.append(Master.model_validate(row[0]))
            yield masters

    async def get_by_id(self, master_id: int) -> Master:
        """
        Retrieves a master by its ID.

        Args:
            master_id: The ID of the master to retrieve.

        Returns:
            master: The retrieved master.

        Raises:
            NotFoundError: If no master is found with the given ID.
        """
        instance = await self._get("master_id", master_id)
        if not instance:
            raise NotFoundError
        return Master.model_validate(instance)

    async def create(self, master: Master) -> Master:
        """
        Creates a new master in the runtime_database.

        Args:
            master: The master object to create.

        Returns:
            master: The created master.
        """
        instance: MasterTable = await self._save(master.model_dump())
        return master.model_validate(instance)

    async def get_ids(self) -> Sequence[int]:
        """
        Retrieves all master IDs from the runtime_database.

        Returns:
            Sequence[int]: A sequence of all master IDs.
        """
        query = select(MasterTable.master_id)
        result: Result = await self._session.execute(query)
        return result.scalars().all()

    async def update(
        self,
        master_id: int,
        payload: dict[str, Any],
    ) -> None:
        """
        Updates an existing master in the runtime_database.

        Args:
            master_id: The ID of the master to update.
            payload: A dictionary containing the fields to update and their new values.

        Returns:
            MasterTable: The updated master table row.

        Raises:
            DatabaseError: If there is an error updating the master.
        """
        query = update(self.schema_class).where(MasterTable.master_id == master_id).values(payload)
        await self._session.execute(query)
        await self._session.flush()

    async def delete_by_id(self, master_id: int) -> None:
        """
        Deletes a master by its ID.

        Args:
            master_id: The ID of the master to delete.
        """
        await self.execute(delete(self.schema_class).where(MasterTable.master_id == master_id))
        await self._session.flush()
