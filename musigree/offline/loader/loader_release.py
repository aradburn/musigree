"""
This module defines the `LoaderRelease` class, responsible for loading,
managing, and processing release data in the Musigree offline system.

It handles the complex process of loading release data from XML files,
storing it in the database, and performing various operations on the
release data, such as creating an entity details index.

Key functionalities include:
    - **`loader_release_pass_one`**: The first pass of loading release data. It
      reads release data from XML files, preprocesses it, and performs bulk
      insert or update operations in the database.
    - **`loader_release_pass_two`**: The second pass of loading release data. It
      performs post-processing operations on the loaded release data, such as
      resolving references and updating related tables.
    - **`loader_release_vacuum`**: Performs database cleanup on the release
      table using the `VACUUM` command, which helps to defragment and optimize
      the database.
    - **`loader_create_entity_details_index`**: Creates an `EntityDetailsIndex`
      by extracting details (countries, genres, styles) from release data.
    - **`loader_init_entity_details_index_from_database`**: Initializes an
      `EntityDetailsIndex` by iterating through all releases in the database.
    - **`save_entity_details_index_to_file`**: Saves an `EntityDetailsIndex` to
      a file using pickle serialization.
    - **`insert_bulk`, `update_bulk`, `delete_bulk`, `get_set_of_ids`**:
      Methods for bulk database operations. These are implemented using
      worker functions (`insert_releases_worker`, `update_releases_worker`,
      `delete_releases_worker`).
    - **Concurrency Management**: The class uses ProcessPoolExecutor to improve
      performance when processing a large number of releases.
    - **Database Transactions**: It utilizes database transactions (`offline_transaction`)
      to ensure data consistency.
    - **Batching**: It processes releases in batches to manage memory usage.
    - **Timing**: It uses the `timeit` decorator to measure the execution
      time of key methods.
    - **Skipping data**: It can skip data that does not contain certain required fields.

The `LoaderRelease` class interacts with the following components:
    - `ReleaseRepository`: For database operations related to releases.
    - `ReleaseDataAccess`: For operations related to release data extraction.
    - `ParserRelease`: For parsing release data from XML elements.
    - `EntityDetailsIndex`: For managing the entity details index.
    - `insert_releases_worker`, `update_releases_worker`, `delete_releases_worker`:
      Worker functions for handling bulk database operations.
    - `process_release_pass_two_worker`: A worker function for handling the second pass
      of release data loading.
    - `LoaderBase`: The base class that provides common loader functionalities.
    - `OfflineDatabaseManager`: For managing database concurrency settings.
    - `offline_transaction`: A decorator for managing database transactions.
    - `timeit`: A decorator for timing method execution.
    - `Path`: for filesystem interaction.

The module utilizes `logging` for logging operations, `pickle` for serialization,
`SortedSet` for managing sorted sets of IDs, `Path` for file system operations,
and `concurrent.futures.ProcessPoolExecutor` for concurrent processing.
"""

import logging
from pathlib import Path
from typing import Any, Callable

from musigree import utils
from musigree.constants import BULK_INSERT_BATCH_SIZE
from musigree.library.fields.entity_type import EntityType
from musigree.offline.database.offline_transaction import offline_transaction
from musigree.offline.database.release_repository import ReleaseRepository
from musigree.offline.database.release_table import ReleaseTable
from musigree.offline.loader.loader_base import LoaderBase
from musigree.offline.loader.parser_release import ParserRelease
from musigree.offline.loader.worker_release_deleter import delete_releases_worker
from musigree.offline.loader.worker_release_inserter import insert_releases_worker
from musigree.offline.loader.worker_release_pass_two import (
    process_release_pass_two_worker,
)
from musigree.offline.loader.worker_release_updater import update_releases_worker
from musigree.offline.offline_database_manager import OfflineDatabaseManager

log = logging.getLogger(__name__)
"""
The logger for the LoaderRelease module.
"""


class LoaderRelease(LoaderBase):
    """
    Manages loading, handling, and processing release data in the Musigree offline system.

    This class handles the first and second passes of loading release data, database
    cleanup tasks, and creating the entity details index.

    Inherits from:
        LoaderBase: Provides common loader functionalities.
    """

    # CLASS VARIABLES

    _artists_mapping: dict[str, Any] = {}
    """
    A mapping for artists, not currently used
    """

    _companies_mapping: dict[str, Any] = {}
    """
    A mapping for companies, not currently used
    """

    _tracks_mapping: dict[str, Any] = {}
    """
    A mapping for tracks, not currently used
    """

    # PUBLIC METHODS

    @classmethod
    # @timeit
    async def loader_release_pass_one(
        cls, discogs_data_directory: Path, date: str, is_bulk_inserts: bool = False
    ) -> None:
        """
        Performs the first pass of loading release data.

        This method loads release data from the specified directory and date,
        parsing and inserting the data into the database. It uses the
        `loader_pass_one_manager` method to handle the loading process.

        Args:
            discogs_data_directory (Path): The directory containing the Discogs data files.
            date (str): The date of the data to load.
            is_bulk_inserts (bool): Whether to use bulk inserts for better performance.
        """
        log.debug(f"loader release pass one - date: {date}")

        release_repository = ReleaseRepository()
        """Instance of ReleaseRepository for database operations on releases."""
        release_parser = ParserRelease()
        """Instance of ParserRelease for parsing release data."""
        releases_loaded = await cls.loader_pass_one_manager(
            repository=release_repository,
            parser=release_parser,
            discogs_data_directory=discogs_data_directory,
            date=date,
            xml_tag="release",
            id_attr=ReleaseTable.release_id.name,
            skip_without=["title"],
            is_bulk_inserts=is_bulk_inserts,
        )
        log.info(f"Releases loaded: {releases_loaded}")

    @staticmethod
    def get_insert_worker_function() -> Callable[[list[dict[str, Any]], int, int], None]:
        return insert_releases_worker

    @staticmethod
    def get_update_worker_function() -> Callable[[list[dict[str, Any]], int, int], None]:
        return update_releases_worker

    @staticmethod
    def get_delete_worker_function() -> Callable[[list[int], int, int], None]:
        return delete_releases_worker

    @classmethod
    async def get_set_of_ids(cls, entity_type: EntityType | None) -> set[int]:
        """
        Retrieves a set of release IDs from the database.

        This method is called to get a set of all release IDs.

        Args:
            entity_type: Ignored, not used.
        Returns:
            set[int]: The set of release IDs.
        """
        async with offline_transaction():
            release_repository = ReleaseRepository()
            """Instance of ReleaseRepository for database operations on releases."""
            ids = await release_repository.get_ids()
        set_of_ids = set(ids)
        return set_of_ids

    @classmethod
    # @timeit
    async def loader_release_pass_two(cls) -> None:
        """
        Performs the second pass of loading release data.

        This method performs post-processing operations on the loaded release
        data, such as resolving references and updating related tables. It
        processes releases in batches using the `process_release_pass_two_worker` function.
        """
        log.debug("loader release pass two")

        async with offline_transaction():
            """Ensure that database operations are performed within a transaction."""
            release_repository = ReleaseRepository()
            """Instance of ReleaseRepository for database operations on releases."""
            total_count = await release_repository.count()
            """Total number of releases in the database."""
            release_ids = await release_repository.get_ids()

        batched_release_ids = utils.batched(release_ids, BULK_INSERT_BATCH_SIZE)

        worker_coroutines = utils.worker_generator(process_release_pass_two_worker, batched_release_ids, total_count)

        await utils.queue_worker_functions(OfflineDatabaseManager.get_concurrency_count(), worker_coroutines)
