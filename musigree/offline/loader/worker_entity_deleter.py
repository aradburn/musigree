"""
This module defines the `WorkerEntityDeleter` class, which is a worker process
responsible for deleting entity records and their associated relations from the
Musigree offline database.

It utilizes `multiprocessing` to enable concurrent deletion of entities,
improving the efficiency of the data loading process. The `WorkerEntityDeleter`
handles the deletion of both entity records and related data in the relation
repository.

Key functionalities include:
    - **Concurrent Deletion**: Employs `multiprocessing.Process` to perform
      deletion operations concurrently, speeding up the deletion of large
      numbers of entities.
    - **Batch Deletion**: Processes a list of entity IDs (`bulk_deletes`) in a
      single run, minimizing database interactions.
    - **Database Transactions**: Uses `offline_transaction` to ensure that each
      deletion operation is atomic, maintaining data integrity.
    - **Error Handling**: Implements error handling using `try...except` blocks
      to catch `DatabaseError` exceptions and log them.
    - **Entity and Relation Deletion**: Deletes both the entity record and
      any associated relations using `EntityRepository` and `RelationRepository`.
    - **Process Initialization**: Handles the initialization of the database
      helper in each worker process when concurrency is enabled.
    - **Logging**: Provides detailed logging of the deletion process, including
      the number of processed and deleted entities.

The `WorkerEntityDeleter` class interacts with the following components:
    - `multiprocessing.Process`: The base class for creating worker processes.
    - `OfflineDatabaseHelper`: For managing database connections and
      initialization in a concurrent environment.
    - `EntityRepository`: For database operations related to entities.
    - `RelationRepository`: For database operations related to relations.
    - `offline_transaction`: A decorator for managing database transactions.
    - `OfflineDatabaseManager`: For managing database concurrency settings.
    - `logging`: For logging operations.

The module utilizes `logging` for logging operations, `multiprocessing` for
process management, and `sqlalchemy.exc.DatabaseError` for database
related exception.
"""

import logging
import multiprocessing

from sqlalchemy.exc import DatabaseError

from musigree.offline.database.offline_database_helper import OfflineDatabaseHelper
from musigree.offline.database.entity_repository import EntityRepository
from musigree.offline.database.relation_repository import RelationRepository
from musigree.offline.database.offline_transaction import offline_transaction
from musigree.offline.offline_database_manager import OfflineDatabaseManager

log = logging.getLogger(__name__)
"""
The logger for the WorkerEntityDeleter module.
"""


class WorkerEntityDeleter(multiprocessing.Process):
    """
    A worker process for deleting entity records and their associated relations.

    This class extends `multiprocessing.Process` to perform concurrent
    deletion of entities, including both the entity record and any associated
    relations.
    """

    def __init__(
        self,
        bulk_deletes: list[int],
        processed_count: int,
    ):
        """
        Initializes the WorkerEntityDeleter.

        Args:
            bulk_deletes (list[int]): A list of entity IDs to delete.
            processed_count (int): The number of entities processed so far.
        """
        super().__init__()
        """Call the constructor of the parent class."""
        self.bulk_deletes = bulk_deletes
        """The list of entity IDs to delete."""
        self.processed_count = processed_count
        """The number of entities processed so far."""

    def run(self):
        """
        Executes the entity deletion process.

        This method performs the following steps:
            1. Initializes the database helper if concurrency is enabled.
            2. Iterates through the list of entity IDs to delete.
            3. For each ID, starts a database transaction.
            4. Deletes the associated relations using RelationRepository.
            5. Deletes the entity using EntityRepository.
            6. Increments the deletion count.
            7. Handles `DatabaseError` exceptions during the process.
            8. Logs the progress and number of entities deleted.
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
            """Iterate through the entity IDs to delete."""
            with offline_transaction():
                """Ensure that database operations are performed within a transaction."""
                entity_repository = EntityRepository()
                """Instance of EntityRepository for database operations on entities."""
                relation_repository = RelationRepository()
                """Instance of RelationRepository for database operations on relations."""
                try:
                    """Attempt to delete the entity and its relations."""
                    relation_repository.delete_by_entitys(id_)
                    """Delete the relations associated with the entity."""
                    entity_repository.delete_by_id(id_)
                    """Delete the entity itself."""

                    deleted_count += 1
                    """Increment the deletion counter."""
                except DatabaseError:
                    """Handle potential database errors."""
                    log.error("Error in WorkerEntityDeleter worker")
                    # log.exception("Error in WorkerEntityDeleter worker", exc_info=True)
                    raise

        log.info(
            f"[{proc_name}] processed: {self.processed_count}, deleted: {deleted_count}"
        )
        """Log the progress and number of deleted entities."""
