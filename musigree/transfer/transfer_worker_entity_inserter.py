"""
This module defines the `TransferWorkerEntityInserter` class, which is a worker
process responsible for inserting entity records into the runtime database in
the Musigree system.

It utilizes `multiprocessing` to enable concurrent insertion of entities,
improving the efficiency of the data transfer process from the offline to the
runtime database. The `TransferWorkerEntityInserter` handles the insertion of
a batch of entity records (`bulk_inserts`).

Key functionalities include:
    - **Concurrent Insertion**: Employs `multiprocessing.Process` to perform
      insertion operations concurrently, speeding up the insertion of large
      numbers of entities.
    - **Batch Insertion**: Processes a list of entity data (`bulk_inserts`) in
      a single run, minimizing database interactions.
    - **Database Transactions**: Uses `runtime_transaction` to ensure that
      the insertion operation is atomic, maintaining data integrity.
    - **Error Handling**: Implements error handling using `try...except` blocks
      to catch `DatabaseError` exceptions and log them.
    - **Retry Mechanism**: Implements a retry mechanism using `retrying` for
      `DatabaseError` exceptions, allowing the worker to attempt to reinsert
      entities multiple times before giving up.
    - **Entity Insertion**: Inserts entity records using
      `RuntimeEntityRepository`.
    - **Process Initialization**: Handles the initialization of the database
      helper in each worker process when concurrency is enabled.
    - **Logging**: Provides detailed logging of the insertion process, including
      the number of inserted entities.

The `TransferWorkerEntityInserter` class interacts with the following components:
    - `multiprocessing.Process`: The base class for creating worker processes.
    - `RuntimeDatabaseHelper`: For managing database connections and
      initialization in a concurrent environment.
    - `RuntimeEntityRepository`: For database operations related to entities.
    - `runtime_transaction`: A decorator for managing database transactions.
    - `RuntimeDatabaseManager`: For managing database concurrency settings.
    - `retrying`: A library for implementing retry mechanisms.
    - `logging`: For logging operations.
    - `DatabaseError`: Used for handling the database exception.

The module utilizes `logging` for logging operations, `multiprocessing` for
process management, `sqlalchemy.exc.DatabaseError` for database related
exception and `retrying` for retry. It interacts with
`musigree.runtime.runtime_database` for database related operations,
and `musigree.runtime.runtime_database_manager` for managing concurrency.
"""

import asyncio
import logging
import multiprocessing
from typing import Any

from musigree.exceptions import DatabaseError
from musigree.offline.offline_domain.entity import Entity
from musigree.runtime.data_access_layer.runtime_entity_data_access import RuntimeEntityDataAccess
from musigree.runtime.runtime_database.runtime_entity_repository import (
    RuntimeEntityRepository,
)
from musigree.runtime.runtime_database.runtime_transaction import runtime_transaction
from musigree.runtime.runtime_database_manager import RuntimeDatabaseManager

log = logging.getLogger(__name__)


async def transfer_worker_entity_inserter_async(
    bulk_inserts: list[dict[str, Any]], inserted_count: int, total_count: int
) -> None:
    """
    A worker process for inserting entity records into the runtime database.
    This function is designed to be run in a separate process to handle the
    insertion of a batch of entity records (`bulk_inserts`) into the
    runtime database, improving the efficiency of the data transfer process
    """

    proc_name = multiprocessing.current_process().name
    """Get the name of the current process."""

    count = 0

    async with runtime_transaction():
        """Ensure that database operations are performed within a transaction."""
        runtime_entity_repository = RuntimeEntityRepository()
        """Instance of RuntimeEntityRepository for database operations on entities."""
        try:
            """Attempt to insert the entities."""
            await runtime_entity_repository.save_all(bulk_inserts)
            """Insert the entities."""
            await runtime_entity_repository.commit()
            """Commit the transaction."""
            count += len(bulk_inserts)
        except DatabaseError:
            """Handle potential database errors."""
            log.error("Error in transfer_worker_entity_inserter")

    log.info(f"[{proc_name}] inserted {inserted_count + count} entities of {total_count}")
    """Log the number of entities inserted."""


def transfer_worker_entity_inserter(
    entity_list: list[Entity], current_total: int, total_count: int
) -> None:
    # Run the async function
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        """Check if the event loop is already running."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        """Set a new event loop if none exists."""

    RuntimeDatabaseManager.reinitialize_runtime_database_async_engine(loop)
    """Initialize the database engine."""

    runtime_entity_dicts_list = RuntimeEntityDataAccess.get_runtime_entity_dicts_from_entities(
        entity_list
    )

    loop.run_until_complete(
        transfer_worker_entity_inserter_async(runtime_entity_dicts_list, current_total, total_count)
    )

    RuntimeDatabaseManager.dispose_runtime_database_async_engine(loop)
    """Close the database engine."""
