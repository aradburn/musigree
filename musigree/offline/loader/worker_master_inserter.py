"""
This module defines the `insert_master_worker` function, which is a worker function
responsible for inserting master records into the Musigree offline runtime_database.

It is designed to be used with `concurrent.futures.ProcessPoolExecutor` to enable
concurrent insertion of master, improving the efficiency of the data loading process.
The function handles the insertion of a batch of master records (`bulk_inserts`).

Key functionalities include:
    - **Concurrent Insertion**: Designed to work with `ProcessPoolExecutor` to perform
      insertion operations concurrently, speeding up the insertion of large
      numbers of master.
    - **Batch Insertion**: Processes a list of master data (`bulk_inserts`) in
      a single run, minimizing runtime_database interactions.
    - **Database Transactions**: Uses `offline_transaction` to ensure that
      the insertion operation is atomic, maintaining data integrity.
    - **Error Handling**: Implements error handling using `try...except` blocks
      to catch `DatabaseError` exceptions and log them.
    - **master Insertion**: Inserts master records using `masterRepository`.
    - **Process Initialization**: Handles the initialization of the runtime_database
      helper in each worker process when concurrency is enabled.
    - **Logging**: Provides detailed logging of the insertion process, including
      the number of inserted master.

The `insert_master_worker` function interacts with the following components:
    - `OfflineDatabaseHelper`: For managing runtime_database connections and
      initialization in a concurrent environment.
    - `MasterRepository`: For runtime_database operations related to master.
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
from typing import Any

from musigree.exceptions import DatabaseError
from musigree.offline.offline_database.master_repository import MasterRepository
from musigree.offline.offline_database.offline_transaction import offline_transaction
from musigree.offline.offline_database_manager import OfflineDatabaseManager

log = logging.getLogger(__name__)
"""
The logger for the worker master inserter module.
"""


async def insert_master_worker_async(
    bulk_inserts: list[dict[str, Any]], inserted_count: int, _total_count: int
) -> None:
    """
    Worker function for inserting master records into the runtime_database.

    This function is designed to be used with ProcessPoolExecutor to perform
    concurrent insertion of master records.

    Args:
        bulk_inserts (list[dict[str, Any]]): A list of master records to insert.
        inserted_count (int): The number of master already inserted.
        _total_count (int): The total number of master to be inserted.
    Raises:
        DatabaseError: If there's an error during runtime_database operations.
    """

    proc_name = multiprocessing.current_process().name
    """Get the name of the current process."""

    count = 0

    async with offline_transaction():
        """Ensure that runtime_database operations are performed within a transaction."""
        master_repository = MasterRepository()
        """Instance of masterRepository for runtime_database operations on master."""
        try:
            """Attempt to insert the master."""
            await master_repository.save_all(bulk_inserts)
            """Insert the master."""
            await master_repository.commit()
            """Commit the transaction."""
            count += len(bulk_inserts)
        except DatabaseError:
            """Handle potential runtime_database errors."""
            log.error("Error in insert_master_worker")
            # log.exception("Error in insert_master_worker", exc_info=True)
            # raise

    log.info(f"[{proc_name}] inserted_count: {inserted_count + count}")
    """Log the number of master inserted."""


def insert_master_worker(
    bulk_inserts: list[dict[str, Any]], current_total: int, total_count: int
) -> None:
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

    loop.run_until_complete(insert_master_worker_async(bulk_inserts, current_total, total_count))

    OfflineDatabaseManager.dispose_offline_database_async_engine(loop)
    """Close the runtime_database engine."""
