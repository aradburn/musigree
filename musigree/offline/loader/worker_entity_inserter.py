"""
This module defines the `WorkerEntityInserter` class, which is a worker process
responsible for inserting entity records into the Musigree offline database.

It utilizes `multiprocessing` to enable concurrent insertion of entities,
improving the efficiency of the data loading process. The `WorkerEntityInserter`
handles the insertion of a batch of entity records (`bulk_inserts`).

Key functionalities include:
    - **Concurrent Insertion**: Employs `multiprocessing.Process` to perform
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

The `WorkerEntityInserter` class interacts with the following components:
    - `multiprocessing.Process`: The base class for creating worker processes.
    - `OfflineDatabaseHelper`: For managing database connections and
      initialization in a concurrent environment.
    - `EntityRepository`: For database operations related to entities.
    - `offline_transaction`: A decorator for managing database transactions.
    - `OfflineDatabaseManager`: For managing database concurrency settings.
    - `logging`: For logging operations.

The module utilizes `logging` for logging operations, `multiprocessing` for
process management, and `sqlalchemy.exc.DatabaseError` for database
related exception.
"""

import logging
import multiprocessing
from typing import Any

from sqlalchemy.exc import DatabaseError

from musigree.offline.database.offline_database_helper import OfflineDatabaseHelper
from musigree.offline.database.entity_repository import EntityRepository
from musigree.offline.database.offline_transaction import offline_transaction
from musigree.offline.offline_database_manager import OfflineDatabaseManager

log = logging.getLogger(__name__)
"""
The logger for the WorkerEntityInserter module.
"""


class WorkerEntityInserter(multiprocessing.Process):
    """
    A worker process for inserting entity records into the database.

    This class extends `multiprocessing.Process` to perform concurrent
    insertion of entity records.
    """

    def __init__(
        self,
        bulk_inserts: list[dict[str, Any]],
        inserted_count: int,
    ):
        """
        Initializes the WorkerEntityInserter.

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
            2. Starts a database transaction.
            3. Inserts all entities in `bulk_inserts` using `EntityRepository`.
            4. Commits the transaction.
            5. Handles `DatabaseError` exceptions during the process.
            6. Logs the progress and number of entities inserted.
        """
        proc_name = self.name
        """Get the name of the current process."""

        if OfflineDatabaseManager.get_concurrency_count() > 1:
            """Check if concurrency is enabled."""
            OfflineDatabaseHelper.initialize()
            """Initialize the database helper."""

        with offline_transaction():
            """Ensure that database operations are performed within a transaction."""
            entity_repository = EntityRepository()
            """Instance of EntityRepository for database operations on entities."""
            try:
                """Attempt to insert the entities."""
                entity_repository.save_all(self.bulk_inserts)
                """Insert the entities."""
                entity_repository.commit()
                """Commit the transaction."""
            except DatabaseError:
                """Handle potential database errors."""
                log.error("Error in WorkerEntityInserter worker")
                # log.exception("Error in WorkerEntityInserter worker", exc_info=True)
                raise
        log.info(f"[{proc_name}] inserted_count: {self.inserted_count}")
        """Log the number of entities inserted."""
