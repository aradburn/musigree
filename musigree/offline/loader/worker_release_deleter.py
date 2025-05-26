"""
This module defines the `WorkerReleaseDeleter` class, which is a worker
process responsible for deleting release records from the Musigree offline
database.

It utilizes `multiprocessing` to enable concurrent deletion of releases,
improving the efficiency of the data loading process. The `WorkerReleaseDeleter`
handles the deletion of a batch of release records (`bulk_deletes`).

Key functionalities include:
    - **Concurrent Deletion**: Employs `multiprocessing.Process` to perform
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

The `WorkerReleaseDeleter` class interacts with the following components:
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

from sqlalchemy.exc import DatabaseError

from musigree.offline.database.offline_database_helper import OfflineDatabaseHelper
from musigree.offline.database.release_repository import ReleaseRepository
from musigree.offline.database.offline_transaction import offline_transaction
from musigree.offline.offline_database_manager import OfflineDatabaseManager

log = logging.getLogger(__name__)
"""
The logger for the WorkerReleaseDeleter module.
"""


class WorkerReleaseDeleter(multiprocessing.Process):
    """
    A worker process for deleting release records from the database.

    This class extends `multiprocessing.Process` to perform concurrent
    deletion of release records.
    """

    def __init__(self, bulk_deletes: list[int], processed_count: int):
        """
        Initializes the WorkerReleaseDeleter.

        Args:
            bulk_deletes (list[int]): A list of release IDs to delete.
            processed_count (int): The number of releases processed so far.
        """
        super().__init__()
        """Call the constructor of the parent class."""
        self.bulk_deletes = bulk_deletes
        """The list of release IDs to delete."""
        self.processed_count = processed_count
        """The number of releases processed so far."""

    def run(self):
        """
        Executes the release deletion process.

        This method performs the following steps:
            1. Initializes the database helper if concurrency is enabled.
            2. Iterates through the list of release IDs to delete.
            3. For each ID, starts a database transaction.
            4. Deletes the release using `ReleaseRepository`.
            5. Handles `DatabaseError` exceptions during the process.
            6. Logs the progress and number of releases deleted.
        """
        proc_name = self.name
        """Get the name of the current process."""
        deleted_count = 0
        """Initialize the deletion counter."""

        if OfflineDatabaseManager.get_concurrency_count() > 1:
            """Check if concurrency is enabled."""
            OfflineDatabaseHelper.initialize()
            """Initialize the database helper."""

        for id_ in self.bulk_deletes:
            """Iterate through the release IDs to delete."""
            with offline_transaction():
                """Ensure that database operations are performed within a transaction."""
                release_repository = ReleaseRepository()
                """Instance of ReleaseRepository for database operations on releases."""
                try:
                    """Attempt to delete the release."""
                    release_repository.delete_by_id(id_)
                    """Delete the release."""
                    deleted_count += 1
                    """Increment the deletion counter."""
                except DatabaseError as e:
                    """Handle potential database errors."""
                    log.exception(
                        "Database Error in WorkerReleaseDeleter worker", exc_info=True
                    )
                    raise e

        log.info(
            f"[{proc_name}] processed: {self.processed_count}, deleted: {deleted_count}"
        )
        """Log the progress and number of deleted releases."""
