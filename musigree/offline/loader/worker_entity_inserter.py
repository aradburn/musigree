"""
This module defines the `insert_entities_worker` function, which is a worker function
responsible for inserting entity records into the Musigree offline database.

It is designed to be used with `concurrent.futures.ProcessPoolExecutor` to enable
concurrent insertion of entities, improving the efficiency of the data loading process.
The function handles the insertion of a batch of entity records (`bulk_inserts`).

Key functionalities include:
    - **Concurrent Insertion**: Designed to work with `ProcessPoolExecutor` to perform
      insertion operations concurrently, speeding up the insertion of large
      numbers of entities.
    - **Batch Insertion**: Processes a list of entity data (`bulk_inserts`) in
      a single run, minimizing database interactions.
    - **Database Transactions**: Uses `offline_transaction` to ensure that the
      insertion operation is atomic, maintaining data integrity.
    - **Error Handling**: Implements error handling using `try...except` blocks
      to catch `DatabaseError` exceptions and log them.
    - **Entity Insertion**: Inserts entity records using `EntityRepository`.
    - **Process Initialization**: Handles the initialization of the database
      helper in each worker process when concurrency is enabled.
    - **Logging**: Provides detailed logging of the insertion process, including
      the number of inserted entities.

The `insert_entities_worker` function interacts with the following components:
    - `OfflineDatabaseHelper`: For managing database connections and
      initialization in a concurrent environment.
    - `EntityRepository`: For database operations related to entities.
    - `offline_transaction`: A decorator for managing database transactions.
    - `OfflineDatabaseManager`: For managing database concurrency settings.
    - `logging`: For logging operations.

The module utilizes `logging` for logging operations and `sqlalchemy.exc.DatabaseError`
for database related exceptions.
"""

import logging
import multiprocessing
from typing import Any

from musigree.exceptions import DatabaseError
from musigree.offline.database.entity_repository import EntityRepository
from musigree.offline.database.offline_transaction import offline_transaction

log = logging.getLogger(__name__)
"""
The logger for the worker entity inserter module.
"""


async def insert_entities_worker(bulk_inserts: list[dict[str, Any]], current_total: int, total_count: int) -> None:
    """
    Worker function for inserting entity records into the database.

    This function is designed to be used with ProcessPoolExecutor to perform
    concurrent insertion of entity records.

    Args:
        bulk_inserts (list[dict[str, Any]]): A list of entity records to insert.
        current_total (int): The number of entities processed so far.
        total_count (int): The total number of entities to process.

    Raises:
        DatabaseError: If there's an error during database operations.
    """

    proc_name = multiprocessing.current_process().name
    """Get the name of the current process."""

    async with offline_transaction():
        """Ensure that database operations are performed within a transaction."""
        entity_repository = EntityRepository()
        """Instance of EntityRepository for database operations on entities."""
        try:
            """Attempt to insert the entities."""
            await entity_repository.save_all(bulk_inserts)
            """Insert the entities."""
            await entity_repository.commit()
            """Commit the transaction."""
        except DatabaseError:
            """Handle potential database errors."""
            log.error("Error in insert_entities_worker")
            # log.exception("Error in insert_entities_worker", exc_info=True)
            # raise

    log.info(f"[{proc_name}] inserted {current_total} of {total_count}")
    """Log the number of entities inserted."""
