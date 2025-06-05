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

import logging
import multiprocessing
from typing import Any

from retrying import retry  # type: ignore
from sqlalchemy.exc import DatabaseError

from musigree.runtime.runtime_database.runtime_database_helper import (
    RuntimeDatabaseHelper,
)
from musigree.runtime.runtime_database.runtime_entity_repository import (
    RuntimeEntityRepository,
)
from musigree.runtime.runtime_database.runtime_transaction import runtime_transaction
from musigree.runtime.runtime_database_manager import RuntimeDatabaseManager

log = logging.getLogger(__name__)
"""
The logger for the TransferWorkerEntityInserter module.
"""


class TransferWorkerEntityInserter(multiprocessing.Process):
    """
    A worker process for inserting entity records into the runtime database.

    This class extends `multiprocessing.Process` to perform concurrent
    insertion of entity records.
    """

    def __init__(
        self,
        bulk_inserts: list[dict[str, Any]],
        inserted_count: int,
    ):
        """
        Initializes the TransferWorkerEntityInserter.

        Args:
            bulk_inserts (list[dict[str, Any]]): A list of entity records to insert.
            inserted_count (int): The number of entities already inserted.
        """
        super().__init__()
        """Call the constructor of the parent class."""
        self.bulk_inserts = bulk_inserts
        """The list of entity records to insert."""
        self.inserted_count = inserted_count
        """The number of entities already inserted."""

    def run(self):
        """
        Executes the entity insertion process.

        This method performs the following steps:
            1. Initializes the database helper if concurrency is enabled.
            2. Inserts all entities in `bulk_inserts` using the `save_all`
            method.
            3. Logs the progress and number of entities inserted.
        """
        proc_name = self.name
        """Get the name of the current process."""

        if RuntimeDatabaseManager.get_concurrency_count() > 1:
            """Check if concurrency is enabled."""
            RuntimeDatabaseHelper.initialize()
            """Initialize the database helper."""

        self.save_all(self.bulk_inserts)
        """Save all the entities."""

        log.info(f"[{proc_name}] inserted_count: {self.inserted_count}")
        """Log the number of entities inserted."""

    @staticmethod
    def retry_if_db_error(exception):
        """
        Determines if the operation should be retried based on the exception type.

        Args:
            exception (Exception): The exception that was raised.

        Returns:
            bool: True if the exception is a DatabaseError, False otherwise.
        """
        return isinstance(exception, DatabaseError)

    @staticmethod
    @retry(
        stop_max_attempt_number=3,
        wait_fixed=60000,
        retry_on_exception=retry_if_db_error,
    )
    def save_all(bulk_inserts: list[dict[str, Any]]) -> None:
        """
        Saves a batch of entities to the runtime database.

        This method attempts to insert a batch of entities into the runtime
        database. If a `DatabaseError` occurs, it retries the operation up
        to 3 times, waiting for 60 seconds between retries.

        Args:
            bulk_inserts: A list of dictionaries, where each dictionary
                represents an entity to be inserted.

        Raises:
            DatabaseError: If there is a database error during the insertion,
            and all retry attempts have failed.
        """
        with runtime_transaction():
            """Ensure that database operations are performed within a transaction."""
            runtime_entity_repository = RuntimeEntityRepository()
            """Instance of RuntimeEntityRepository for database operations on runtime entities."""
            try:
                """Attempt to insert the releases."""
                runtime_entity_repository.save_all(bulk_inserts)
                """Insert the entities."""
                runtime_entity_repository.commit()
                """Commit the transaction."""
            except DatabaseError:
                """Handle potential database errors."""
                log.error("Error in TransferWorkerEntityInserter worker")
                # log.exception("Error in TransferWorkerEntityInserter worker", exc_info=True)
                raise
