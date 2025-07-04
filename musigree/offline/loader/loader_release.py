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
import asyncio
import logging
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

from musigree.offline.database.offline_transaction import offline_transaction
from musigree.offline.database.release_repository import ReleaseRepository
from musigree.offline.database.release_table import ReleaseTable
from musigree.offline.loader.loader_base import LoaderBase
from musigree.offline.loader.parser_release import ParserRelease
from musigree.offline.loader.worker_release_deleter import delete_releases_worker
from musigree.offline.loader.worker_release_inserter import insert_releases_worker
from musigree.offline.loader.worker_release_pass_two import process_release_pass_two_worker
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
        cls, discogs_data_directory: Path, date: str, is_bulk_inserts=False
    ) -> int:
        """
        Performs the first pass of loading release data.

        This method loads release data from the specified directory and date,
        parsing and inserting the data into the database. It uses the
        `loader_pass_one_manager` method to handle the loading process.

        Args:
            discogs_data_directory (Path): The directory containing the Discogs data files.
            date (str): The date of the data to load.
            is_bulk_inserts (bool): Whether to use bulk inserts for better performance.

        Returns:
            int: The number of releases loaded.
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
        return releases_loaded

    @classmethod
    async def insert_bulk(cls, bulk_inserts: list[dict[str, Any]], inserted_count: int, executor: ProcessPoolExecutor, concurrency_count: int) -> None:
        """
        Performs a bulk insert operation for releases.

        This method is called to insert a batch of release records into the
        database using the `insert_releases_worker` function.

        Args:
            bulk_inserts (list[dict[str, Any]]): The list of release records to insert.
            inserted_count (int): The number of records processed so far.
            executor (ProcessPoolExecutor): The executor to submit the work to.
            concurrency_count (int): The number of concurrent operations allowed.
        """
        loop = asyncio.get_running_loop()
        loop.set_debug(True)
        if concurrency_count > 1:
            future = loop.run_in_executor(executor, insert_releases_worker, bulk_inserts, inserted_count)
        else:
            future = loop.run_in_executor(None, insert_releases_worker, bulk_inserts, inserted_count)
        return await future

    @classmethod
    async def update_bulk(cls,
                          bulk_updates: list[dict[str, Any]],
                          processed_count: int,
                          executor: ProcessPoolExecutor,
                          concurrency_count: int) -> None:
        """
        Performs a bulk update operation for releases.

        This method is called to update a batch of release records in the
        database using the `update_releases_worker` function.

        Args:
            bulk_updates (list[dict[str, Any]]): The list of release records to update.
            processed_count (int): The number of records processed so far.
            executor (ProcessPoolExecutor): The executor to submit the work to.
            concurrency_count (int): The number of concurrent operations allowed.
        """
        loop = asyncio.get_running_loop()
        if concurrency_count > 1:
            future = loop.run_in_executor(executor, update_releases_worker, bulk_updates, processed_count)
        else:
            future = loop.run_in_executor(None, update_releases_worker, bulk_updates, processed_count)
        return await future

    @classmethod
    async def delete_bulk(cls, bulk_deletes: list[int], processed_count: int, executor: ProcessPoolExecutor,
                          concurrency_count: int) -> None:
        """
        Performs a bulk delete operation for releases.

        This method is called to delete a batch of release records from the
        database using the `delete_releases_worker` function.

        Args:
            bulk_deletes (list[int]): The list of release IDs to delete.
            processed_count (int): The number of records processed so far.
            executor (ProcessPoolExecutor): The executor to submit the work to.
            concurrency_count (int): The number of concurrent operations allowed.
        """
        loop = asyncio.get_running_loop()
        if concurrency_count > 1:
            future = loop.run_in_executor(executor, delete_releases_worker, bulk_deletes, processed_count)
        else:
            future = loop.run_in_executor(None, delete_releases_worker, bulk_deletes, processed_count)
        return await future

    @classmethod
    async def get_set_of_ids(cls, entity_type):
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
    async def loader_release_pass_two(cls):
        """
        Performs the second pass of loading release data.

        This method performs post-processing operations on the loaded release
        data, such as resolving references and updating related tables. It
        processes releases in batches using the `process_release_pass_two_worker` function.
        """
        log.debug("loader release pass two")
        number_in_batch = int(LoaderBase.BULK_INSERT_BATCH_SIZE)
        """Determine the number of releases to process in each batch."""

        async with offline_transaction():
            """Ensure that database operations are performed within a transaction."""
            release_repository = ReleaseRepository()
            """Instance of ReleaseRepository for database operations on releases."""
            total_count = await release_repository.count()
            """Total number of releases in the database."""
            batched_release_ids = await release_repository.get_batched_ids(number_in_batch)
        """Get the release ids in batches."""

        current_total = 0
        """Counter for the total number of releases processed."""
        concurrency_count = OfflineDatabaseManager.get_concurrency_count()

        if concurrency_count > 1:
            # Multi-threaded execution
            # Use ProcessPoolExecutor to run the worker function concurrently
            with ProcessPoolExecutor(max_workers=concurrency_count) as executor:
                async with asyncio.TaskGroup() as task_group:
                    for ids in batched_release_ids:
                        """Iterate over the batches of release IDs."""
                        future = cls.run_worker_function(process_release_pass_two_worker,
                                                         ids, current_total, total_count,
                                                         executor, concurrency_count)
                        task_group.create_task(future)
                        current_total += number_in_batch
        else:
            # Single-threaded execution
            for ids in batched_release_ids:
                """Iterate over the batches of release IDs."""
                with ProcessPoolExecutor(max_workers=concurrency_count) as executor:
                    async with asyncio.TaskGroup() as task_group:
                        future = cls.run_worker_function(process_release_pass_two_worker,
                                                         ids, current_total, total_count,
                                                         executor, concurrency_count)
                        task_group.create_task(future)
                        current_total += number_in_batch
