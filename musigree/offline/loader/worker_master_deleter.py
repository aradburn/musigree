"""
This module defines the `delete_masters_worker` function, which is a worker function
responsible for deleting master records from the Musigree offline runtime_database.

It is designed to be used with `concurrent.futures.ProcessPoolExecutor` to enable
concurrent deletion of masters, improving the efficiency of the data loading process.
The function handles the deletion of a batch of master records (`bulk_deletes`).

Key functionalities include:
    - **Concurrent Deletion**: Designed to work with `ProcessPoolExecutor` to perform
      deletion operations concurrently, speeding up the deletion of large
      numbers of masters.
    - **Batch Deletion**: Processes a list of master IDs (`bulk_deletes`) in
      a single run, minimizing runtime_database interactions.
    - **Database Transactions**: Uses `offline_transaction` to ensure that
      each deletion operation is atomic, maintaining data integrity.
    - **Error Handling**: Implements error handling using `try...except` blocks
      to catch `DatabaseError` exceptions and log them.
    - **master Deletion**: Deletes master records using `masterRepository`.
    - **Process Initialization**: Handles the initialization of the runtime_database
      helper in each worker process when concurrency is enabled.
    - **Logging**: Provides detailed logging of the deletion process, including
      the number of processed and deleted masters.

The `delete_masters_worker` function interacts with the following components:
    - `OfflineDatabaseHelper`: For managing runtime_database connections and
      initialization in a concurrent environment.
    - `MasterRepository`: For runtime_database operations related to masters.
    - `offline_transaction`: A decorator for managing runtime_database transactions.
    - `OfflineDatabaseManager`: For managing runtime_database concurrency settings.
    - `logging`: For logging operations.
    - `DatabaseError`: Used for handling the runtime_database exception.

The module utilizes `logging` for logging operations and `sqlalchemy.exc.DatabaseError`
for runtime_database related exceptions.
"""

import asyncio
import logging
import multiprocessing

from musigree.exceptions import DatabaseError
from musigree.offline.offline_database.master_repository import MasterRepository
from musigree.offline.offline_database.offline_transaction import offline_transaction
from musigree.offline.offline_database_manager import OfflineDatabaseManager

log = logging.getLogger(__name__)
"""
The logger for the worker master deleter module.
"""


async def delete_masters_worker_async(
    bulk_deletes: list[int], processed_count: int, _total_count: int
) -> None:
    """
    Worker function for deleting master records from the runtime_database.

    This function is designed to be used with ProcessPoolExecutor to perform
    concurrent deletion of master records.

    Args:
        bulk_deletes (list[int]): A list of master IDs to delete.
        processed_count (int): The number of masters processed so far.
        _total_count (int): The total number of masters to process.
    Raises:
        DatabaseError: If there's an error during runtime_database operations.
    """

    proc_name = multiprocessing.current_process().name
    """Get the name of the current process."""
    deleted_count = 0
    """Counter for the number of masters deleted."""

    async with offline_transaction():
        master_repository = MasterRepository()
        """Instance of masterRepository for runtime_database operations on masters."""

        for master_id in bulk_deletes:
            """Iterate through the master IDs to delete."""

            """Ensure that runtime_database operations are performed within a transaction."""
            try:
                """Attempt to delete the master."""
                await master_repository.delete_by_id(master_id)
                """Delete the master."""
                deleted_count += 1
                """Increment the deletion counter."""
            except DatabaseError:
                """Handle potential runtime_database errors."""
                log.error("Error in delete_masters_worker")
                # log.exception("Error in delete_masters_worker", exc_info=True)
                raise

    log.info(f"[{proc_name}] processed: {processed_count}, deleted: {deleted_count}")
    """Log the progress and number of deleted masters."""


def delete_masters_worker(bulk_deletes: list[int], current_total: int, total_count: int) -> None:
    # Run the async function
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        """Check if the event loop is already running."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        """Set a new event loop if none exists."""

    OfflineDatabaseManager.reinitialize_offline_database_async_engine(loop)
    """Initialize the runtime_database engine."""

    loop.run_until_complete(delete_masters_worker_async(bulk_deletes, current_total, total_count))

    OfflineDatabaseManager.dispose_offline_database_async_engine(loop)
    """Close the runtime_database engine."""
