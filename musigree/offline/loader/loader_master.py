"""
This module defines the `LoaderMaster` class, responsible for loading,
managing, and processing master data in the Musigree offline system.

It handles the complex process of loading master data from XML files,
storing it in the runtime_database, and performing various operations on the
master data.


"""

import logging
from pathlib import Path
from typing import Any, Callable

from musigree.library.fields.entity_type import EntityType
from musigree.offline.offline_database.master_repository import MasterRepository
from musigree.offline.offline_database.master_table import MasterTable
from musigree.offline.offline_database.offline_transaction import offline_transaction
from musigree.offline.loader.loader_base import LoaderBase
from musigree.offline.loader.parser_master import ParserMaster
from musigree.offline.loader.worker_master_deleter import delete_masters_worker
from musigree.offline.loader.worker_master_inserter import insert_master_worker
from musigree.offline.loader.worker_master_updater import update_master_worker

log = logging.getLogger(__name__)
"""
The logger for the LoaderMaster module.
"""


class LoaderMaster(LoaderBase):
    """
    Manages loading, handling, and processing master data in the Musigree offline system.

    This class handles the first pass of loading master data.

    Inherits from:
        LoaderBase: Provides common loader functionalities.
    """

    # CLASS VARIABLES

    # PUBLIC METHODS

    @classmethod
    # @timeit
    async def loader_master_pass_one(
        cls, discogs_data_directory: Path, date: str, is_bulk_inserts: bool = False
    ) -> None:
        """
        Performs the first pass of loading release data.

        This method loads release data from the specified directory and date,
        parsing and inserting the data into the runtime_database. It uses the
        `loader_pass_one_manager` method to handle the loading process.

        Args:
            discogs_data_directory (Path): The directory containing the Discogs data files.
            date (str): The date of the data to load.
            is_bulk_inserts (bool): Whether to use bulk inserts for better performance.
        """
        log.debug(f"loader release pass one - date: {date}")

        master_repository = MasterRepository()
        """Instance of MasterRepository for runtime_database operations on master data records."""
        master_parser = ParserMaster()
        """Instance of ParserMaster for parsing master data."""
        masters_loaded = await cls.loader_pass_one_manager(
            repository=master_repository,
            parser=master_parser,
            discogs_data_directory=discogs_data_directory,
            date=date,
            xml_tag="master",
            id_attr=MasterTable.master_id.name,
            skip_without=["title"],
            is_bulk_inserts=is_bulk_inserts,
        )
        log.info(f"Releases loaded: {masters_loaded}")

    @staticmethod
    def get_insert_worker_function() -> Callable[[list[dict[str, Any]], int, int], None]:
        return insert_master_worker

    @staticmethod
    def get_update_worker_function() -> Callable[[list[dict[str, Any]], int, int], None]:
        return update_master_worker

    @staticmethod
    def get_delete_worker_function() -> Callable[[list[int], int, int], None]:
        return delete_masters_worker

    @classmethod
    async def get_set_of_ids(cls, entity_type: EntityType | None) -> set[int]:
        """
        Retrieves a set of release IDs from the runtime_database.

        This method is called to get a set of all release IDs.

        Args:
            entity_type: Ignored, not used.
        Returns:
            set[int]: The set of release IDs.
        """
        async with offline_transaction():
            master_repository = MasterRepository()
            """Instance of MasterRepository for runtime_database operations on master data records."""
            ids = await master_repository.get_ids()
        set_of_ids = set(ids)
        return set_of_ids
