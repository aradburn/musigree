"""
This module defines the `WorkerReleaseInserter` class, which is a worker
process responsible for inserting release records into the Musigree offline
database.

It utilizes `multiprocessing` to enable concurrent insertion of releases,
improving the efficiency of the data loading process. The
`WorkerReleaseInserter` handles the insertion of a batch of release records
(`bulk_inserts`).

Key functionalities include:
    - **Concurrent Insertion**: Employs `multiprocessing.Process` to perform
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

The `WorkerReleaseInserter` class interacts with the following components:
    - `multiprocessing.Process`: The base class for creating worker processes.
    - `OfflineDatabaseHelper`: For managing database connections and
      initialization in a concurrent environment.
    - `ReleaseRepository`: For database operations related to releases.
    - `offline_transaction`: A decorator for managing database transactions.
    - `OfflineDatabaseManager`: For managing database concurrency settings.
    - `logging`: For logging operations.
    - `DatabaseError`: Used for handling the database exception.

The module utilizes `logging` for logging operations, `multiprocessing` for
process management, and `sqlalchemy.exc.DatabaseError` for database
related exception.
"""

import logging
import multiprocessing
from typing import Any

from sqlalchemy.exc import DatabaseError

from musigree.offline.database.offline_database_helper import OfflineDatabaseHelper
from musigree.offline.database.release_repository import ReleaseRepository
from musigree.offline.database.offline_transaction import offline_transaction
from musigree.offline.offline_database_manager import OfflineDatabaseManager

log = logging.getLogger(__name__)
"""
The logger for the WorkerReleaseInserter module.
"""


class WorkerReleaseInserter(multiprocessing.Process):
    """
    A worker process for inserting release records into the database.

    This class extends `multiprocessing.Process` to perform concurrent
    insertion of release records.
    """

    def __init__(
        self,
        bulk_inserts: list[dict[str, Any]],
        inserted_count: int,
    ):
        """
        Initializes the WorkerReleaseInserter.

        Args:
            bulk_inserts (list[dict[str, Any]]): A list of release records to insert.
            inserted_count (int): The number of releases already inserted.
        """
        super().__init__()
        """Call the constructor of the parent class."""
        self.bulk_inserts = bulk_inserts
        """The list of release records to insert."""
        self.inserted_count = inserted_count
        """The number of releases already inserted."""

    def run(self):
        """
        Executes the release insertion process.

        This method performs the following steps:
            1. Initializes the database helper if concurrency is enabled.
            2. Starts a database transaction.
            3. Inserts all releases in `bulk_inserts` using `ReleaseRepository`.
            4. Commits the transaction.
            5. Handles `DatabaseError` exceptions during the process.
            6. Logs the progress and number of releases inserted.
        """
        proc_name = self.name
        """Get the name of the current process."""

        if OfflineDatabaseManager.get_concurrency_count() > 1:
            """Check if concurrency is enabled."""
            OfflineDatabaseHelper.initialize()
            """Initialize the database helper."""

        with offline_transaction():
            """Ensure that database operations are performed within a transaction."""
            release_repository = ReleaseRepository()
            """Instance of ReleaseRepository for database operations on releases."""
            try:
                """Attempt to insert the releases."""
                release_repository.save_all(self.bulk_inserts)
                """Insert the releases."""
                release_repository.commit()
                """Commit the transaction."""
            except DatabaseError as e:
                """Handle potential database errors."""
                log.exception(
                    "Database Error in WorkerReleaseInserter worker", exc_info=True
                )
                raise e

        log.info(f"[{proc_name}] inserted_count: {self.inserted_count}")
        """Log the number of releases inserted."""
