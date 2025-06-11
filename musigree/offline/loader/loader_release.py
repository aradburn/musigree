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
      worker classes (`WorkerReleaseInserter`, `WorkerReleaseUpdater`,
      `WorkerReleaseDeleter`).
    - **Concurrency Management**: The class uses worker processes to improve
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
    - `WorkerReleaseInserter`, `WorkerReleaseUpdater`, `WorkerReleaseDeleter`:
      Worker classes for handling bulk database operations.
    - `WorkerReleasePassTwo`: A worker class for handling the second pass
      of release data loading.
    - `LoaderBase`: The base class that provides common loader functionalities.
    - `OfflineDatabaseManager`: For managing database concurrency settings.
    - `offline_transaction`: A decorator for managing database transactions.
    - `timeit`: A decorator for timing method execution.
    - `Path`: for filesystem interaction.

The module utilizes `logging` for logging operations, `pickle` for serialization,
`SortedSet` for managing sorted sets of IDs, and `Path` for file system operations.
"""

import logging
from pathlib import Path
from typing import Any

from sortedcontainers import SortedSet

from musigree.offline.database.release_repository import ReleaseRepository
from musigree.offline.database.release_table import ReleaseTable
from musigree.offline.database.offline_transaction import offline_transaction
from musigree.offline.loader.loader_base import LoaderBase
from musigree.offline.loader.parser_release import ParserRelease
from musigree.offline.loader.worker_release_deleter import WorkerReleaseDeleter
from musigree.offline.loader.worker_release_inserter import WorkerReleaseInserter
from musigree.offline.loader.worker_release_pass_two import WorkerReleasePassTwo
from musigree.offline.loader.worker_release_updater import WorkerReleaseUpdater
from musigree.offline.offline_database_manager import OfflineDatabaseManager
from musigree.utils import timeit

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
    @timeit
    def loader_release_pass_one(
        cls, discogs_data_directory: Path, date: str, is_bulk_inserts=False
    ) -> int:
        """
        Performs the first pass of loading release data.

        This method reads release data from XML files, parses it using
        `ParserRelease`, and performs bulk insert or update operations
        in the database. It manages the process of skipping records without
        required fields.

        Args:
            discogs_data_directory (Path): The directory containing the XML files.
            date (str): The date of the data dump being processed.
            is_bulk_inserts (bool): Whether to perform bulk inserts or updates.

        Returns:
            int: The number of releases loaded.
        """
        log.debug(f"loader release pass one - date: {date}")
        with offline_transaction():
            """Ensure that database operations are performed within a transaction."""
            release_repository = ReleaseRepository()
            """Instance of ReleaseRepository for database operations on releases."""
            release_parser = ParserRelease()
            """Instance of ParserRelease for parsing release data."""
            releases_loaded = cls.loader_pass_one_manager(
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
    def insert_bulk(cls, bulk_inserts: list[dict[str, Any]], inserted_count: int):
        """
        Performs a bulk insert operation for releases.

        This method is called to insert a batch of release records into the
        database using the `WorkerReleaseInserter` worker class.

        Args:
            bulk_inserts (list[dict[str, Any]]): The list of release records to insert.
            inserted_count (int): The number of records processed so far.

        Returns:
            WorkerReleaseInserter: The worker instance handling the insert operation.
        """
        worker = WorkerReleaseInserter(
            bulk_inserts=bulk_inserts,
            inserted_count=inserted_count,
        )
        return worker

    @classmethod
    def update_bulk(cls, bulk_updates: list[dict[str, Any]], processed_count: int):
        """
        Performs a bulk update operation for releases.

        This method is called to update a batch of release records in the
        database using the `WorkerReleaseUpdater` worker class.

        Args:
            bulk_updates (list[dict[str, Any]]): The list of release records to update.
            processed_count (int): The number of records processed so far.

        Returns:
            WorkerReleaseUpdater: The worker instance handling the update operation.
        """
        worker = WorkerReleaseUpdater(
            bulk_updates=bulk_updates,
            processed_count=processed_count,
        )
        return worker

    @classmethod
    def delete_bulk(cls, bulk_deletes: list[int], processed_count: int):
        """
        Performs a bulk delete operation for releases.

        This method is called to delete a batch of release records from the
        database using the `WorkerReleaseDeleter` worker class.

        Args:
            bulk_deletes (list[int]): The list of release IDs to delete.
            processed_count (int): The number of records processed so far.

        Returns:
            WorkerReleaseDeleter: The worker instance handling the delete operation.
        """
        worker = WorkerReleaseDeleter(
            bulk_deletes=bulk_deletes,
            processed_count=processed_count,
        )
        return worker

    @classmethod
    def get_set_of_ids(cls, entity_type):
        """
        Retrieves a set of release IDs from the database.

        This method is called to get a set of all release IDs.

        Args:
            entity_type: Ignored, not used.
        Returns:
            SortedSet: The set of release IDs.
        """
        with offline_transaction():
            release_repository = ReleaseRepository()
            """Instance of ReleaseRepository for database operations on releases."""
            ids = release_repository.get_ids()
        set_of_ids = SortedSet(ids)
        return set_of_ids

    @classmethod
    @timeit
    def loader_release_pass_two(cls):
        """
        Performs the second pass of loading release data.

        This method performs post-processing operations on the loaded release
        data, such as resolving references and updating related tables. It
        processes releases in batches using the `WorkerReleasePassTwo` worker class.
        """
        log.debug("loader release pass two")
        number_in_batch = int(LoaderBase.BULK_INSERT_BATCH_SIZE)
        """Determine the number of releases to process in each batch."""

        with offline_transaction():
            """Ensure that database operations are performed within a transaction."""
            release_repository = ReleaseRepository()
            """Instance of ReleaseRepository for database operations on releases."""
            total_count = release_repository.count()
            """Total number of releases in the database."""
            batched_release_ids = release_repository.get_batched_ids(number_in_batch)
        """Get the release ids in batches."""

        current_total = 0
        """Counter for the total number of releases processed."""

        workers = []
        """List of worker processes."""
        for release_ids in batched_release_ids:
            """Iterate over the batches of release IDs."""
            worker = WorkerReleasePassTwo(release_ids, current_total, total_count)
            """Create a new worker for the batch."""
            worker.start()
            """Start the worker process."""
            workers.append(worker)
            """Add the worker to the list."""
            current_total += number_in_batch
            """Update the counter."""

            if len(workers) > OfflineDatabaseManager.get_concurrency_count():
                """If the number of workers exceeds the concurrency limit."""
                worker = workers.pop(0)
                """Remove the first worker from the list."""
                cls.loader_wait_for_worker(worker)
            """Wait for the worker to finish."""

        while len(workers) > 0:
            """Wait for any remaining workers to finish."""
            worker = workers.pop(0)
            """Remove the first worker from the list."""
            cls.loader_wait_for_worker(worker)
        """Wait for the worker to finish."""
