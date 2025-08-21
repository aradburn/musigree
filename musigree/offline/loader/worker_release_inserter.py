"""
This module defines the `insert_releases_worker` function, which is a worker function
responsible for inserting release records into the Musigree offline database.

It is designed to be used with `concurrent.futures.ProcessPoolExecutor` to enable
concurrent insertion of releases, improving the efficiency of the data loading process.
The function handles the insertion of a batch of release records (`bulk_inserts`).

Key functionalities include:
    - **Concurrent Insertion**: Designed to work with `ProcessPoolExecutor` to perform
      insertion operations concurrently, speeding up the insertion of large
      numbers of releases.
    - **Batch Insertion**: Processes a list of release data (`bulk_inserts`) in
      a single run, minimizing database interactions.
    - **Database Transactions**: Uses `offline_transaction` to ensure that
      the insertion operation is atomic, maintaining data integrity.
    - **Error Handling**: Implements error handling using `try...except` blocks
      to catch `DatabaseError` exceptions and log them.
    - **Release Insertion**: Inserts release records using `ReleaseRepository`.
    - **Process Initialization**: Handles the initialization of the database
      helper in each worker process when concurrency is enabled.
    - **Logging**: Provides detailed logging of the insertion process, including
      the number of inserted releases.

The `insert_releases_worker` function interacts with the following components:
    - `OfflineDatabaseHelper`: For managing database connections and
      initialization in a concurrent environment.
    - `ReleaseRepository`: For database operations related to releases.
    - `offline_transaction`: A decorator for managing database transactions.
    - `OfflineDatabaseManager`: For managing database concurrency settings.
    - `logging`: For logging operations.
    - `DatabaseError`: Used for handling the database exception.

The module utilizes `logging` for logging operations and `sqlalchemy.exc.DatabaseError`
for database related exceptions.
"""

import asyncio
import logging
import multiprocessing
from typing import Any

from musigree.exceptions import DatabaseError
from musigree.offline.database.offline_database_helper import OfflineDatabaseHelper
from musigree.offline.database.release_repository import ReleaseRepository
from musigree.offline.database.offline_transaction import offline_transaction
from musigree.offline.offline_database_manager import OfflineDatabaseManager

log = logging.getLogger(__name__)
"""
The logger for the worker release inserter module.
"""


def insert_releases_worker(
    bulk_inserts: list[dict[str, Any]],
    inserted_count: int,
) -> None:
    """
    Worker function for inserting release records into the database.

    This function is designed to be used with ProcessPoolExecutor to perform
    concurrent insertion of release records.

    Args:
        bulk_inserts (list[dict[str, Any]]): A list of release records to insert.
        inserted_count (int): The number of releases already inserted.

    Raises:
        DatabaseError: If there's an error during database operations.
    """

    async def insert_releases(_bulk_inserts: list[dict[str, Any]]) -> None:
        """Async function to handle release insertion."""

        proc_name = multiprocessing.current_process().name
        """Get the name of the current process."""

        async with offline_transaction():
            """Ensure that database operations are performed within a transaction."""
            release_repository = ReleaseRepository()
            """Instance of ReleaseRepository for database operations on releases."""
            try:
                """Attempt to insert the releases."""
                await release_repository.save_all(_bulk_inserts)
                """Insert the releases."""
                await release_repository.commit()
                """Commit the transaction."""
            except DatabaseError:
                """Handle potential database errors."""
                log.error("Error in insert_releases_worker")
                # log.exception("Error in insert_releases_worker", exc_info=True)
                # raise

        log.info(f"[{proc_name}] inserted_count: {inserted_count}")
        """Log the number of releases inserted."""

    # Run the async function
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        """Check if the event loop is already running."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        """Set a new event loop if none exists."""

    if OfflineDatabaseManager.get_concurrency_count() > 1:
        """Check if concurrency is enabled."""
        OfflineDatabaseHelper.initialize(loop)
        """Initialize the database helper."""

    loop.run_until_complete(insert_releases(bulk_inserts))
