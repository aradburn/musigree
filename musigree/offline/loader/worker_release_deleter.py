"""
This module defines the `delete_releases_worker` function, which is a worker function
responsible for deleting release records from the Musigree offline database.

It is designed to be used with `concurrent.futures.ProcessPoolExecutor` to enable
concurrent deletion of releases, improving the efficiency of the data loading process.
The function handles the deletion of a batch of release records (`bulk_deletes`).

Key functionalities include:
    - **Concurrent Deletion**: Designed to work with `ProcessPoolExecutor` to perform
      deletion operations concurrently, speeding up the deletion of large
      numbers of releases.
    - **Batch Deletion**: Processes a list of release IDs (`bulk_deletes`) in
      a single run, minimizing database interactions.
    - **Database Transactions**: Uses `offline_transaction` to ensure that
      each deletion operation is atomic, maintaining data integrity.
    - **Error Handling**: Implements error handling using `try...except` blocks
      to catch `DatabaseError` exceptions and log them.
    - **Release Deletion**: Deletes release records using `ReleaseRepository`.
    - **Process Initialization**: Handles the initialization of the database
      helper in each worker process when concurrency is enabled.
    - **Logging**: Provides detailed logging of the deletion process, including
      the number of processed and deleted releases.

The `delete_releases_worker` function interacts with the following components:
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

from musigree.exceptions import DatabaseError
from musigree.offline.database.offline_database_helper import OfflineDatabaseHelper
from musigree.offline.database.offline_transaction import offline_transaction
from musigree.offline.database.release_repository import ReleaseRepository
from musigree.offline.offline_database_manager import OfflineDatabaseManager

log = logging.getLogger(__name__)
"""
The logger for the worker release deleter module.
"""


def delete_releases_worker(bulk_deletes: list[int], processed_count: int) -> None:
    """
    Worker function for deleting release records from the database.

    This function is designed to be used with ProcessPoolExecutor to perform
    concurrent deletion of release records.

    Args:
        bulk_deletes (list[int]): A list of release IDs to delete.
        processed_count (int): The number of releases processed so far.

    Raises:
        DatabaseError: If there's an error during database operations.
    """

    async def delete_releases(_bulk_deletes: list[int]) -> None:
        """Async function to handle release deletion."""

        proc_name = multiprocessing.current_process().name
        """Get the name of the current process."""
        deleted_count = 0
        """Counter for the number of releases deleted."""

        async with offline_transaction():
            for _id in _bulk_deletes:
                """Iterate through the release IDs to delete."""

                """Ensure that database operations are performed within a transaction."""
                release_repository = ReleaseRepository()
                """Instance of ReleaseRepository for database operations on releases."""
                try:
                    """Attempt to delete the release."""
                    await release_repository.delete_by_id(_id)
                    """Delete the release."""
                    deleted_count += 1
                    """Increment the deletion counter."""
                except DatabaseError:
                    """Handle potential database errors."""
                    log.error("Error in delete_releases_worker")
                    # log.exception("Error in delete_releases_worker", exc_info=True)
                    raise

        log.info(
            f"[{proc_name}] processed: {processed_count}, deleted: {deleted_count}"
        )
        """Log the progress and number of deleted releases."""

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

    loop.run_until_complete(delete_releases(bulk_deletes))
