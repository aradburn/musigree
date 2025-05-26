"""
This module defines the `WorkerEntityPassThree` class, which is a worker
process responsible for processing entity records in the third pass of the
data loading process in the Musigree offline system.

It utilizes `multiprocessing` to enable concurrent processing of entities,
improving the efficiency of the data loading process. The
`WorkerEntityPassThree` handles the computation and updating of relation
counts for each entity.

Key functionalities include:
    - **Concurrent Processing**: Employs `multiprocessing.Process` to perform
      processing operations concurrently, speeding up the processing of
      large numbers of entities.
    - **Relation Count Calculation**: Computes the number of unique relations
      for each entity, grouped by role.
    - **Database Transactions**: Uses `offline_transaction` to ensure that
      each processing operation is atomic, maintaining data integrity.
    - **Error Handling**: Implements error handling using `try...except` blocks
      to catch `DatabaseError` exceptions and log them.
    - **Entity and Relation Access**: Uses `EntityRepository` and
      `RelationRepository` to access and update entity and relation data.
    - **Process Initialization**: Handles the initialization of the database
      helper in each worker process when concurrency is enabled.
    - **Logging**: Provides detailed logging of the processing, including
      the number of entities processed and any database errors encountered.
    - **Batch processing**: Process a list of ids at once.
    - **Reporting**: Log every `BULK_REPORTING_SIZE` elements.

The `WorkerEntityPassThree` class interacts with the following components:
    - `multiprocessing.Process`: The base class for creating worker processes.
    - `OfflineDatabaseHelper`: For managing database connections and
      initialization in a concurrent environment.
    - `EntityRepository`: For database operations related to entities.
    - `RelationRepository`: For database operations related to relations.
    - `offline_transaction`: A decorator for managing database transactions.
    - `OfflineDatabaseManager`: For managing database concurrency settings.
    - `LoaderBase`: For accessing the `BULK_REPORTING_SIZE` constant.
    - `EntityTable`: For accessing the entity table definition.
    - `logging`: For logging operations.

The module utilizes `logging` for logging operations, `multiprocessing` for
process management, and `sqlalchemy.exc.DatabaseError` for database
related exception. It interacts with `musigree.offline.database` for database
related operations and `musigree.offline.offline_database_manager` for managing
concurrency.
"""

import logging
import multiprocessing

from sqlalchemy.exc import DatabaseError

from musigree.offline.database.offline_database_helper import OfflineDatabaseHelper
from musigree.offline.database.entity_repository import EntityRepository
from musigree.offline.database.entity_table import EntityTable
from musigree.offline.database.relation_repository import RelationRepository
from musigree.offline.database.offline_transaction import offline_transaction
from musigree.offline.loader.loader_base import LoaderBase
from musigree.offline.offline_database_manager import OfflineDatabaseManager

log = logging.getLogger(__name__)
"""
The logger for the WorkerEntityPassThree module.
"""


class WorkerEntityPassThree(multiprocessing.Process):
    """
    A worker process for processing entity records in the third pass.

    This class extends `multiprocessing.Process` to perform concurrent
    processing of entities, calculating and updating relation counts.
    """

    def __init__(self, ids: list[int], current_total: int, total_count: int):
        """
        Initializes the WorkerEntityPassThree.

        Args:
            ids (list[int]): A list of entity IDs to process.
            current_total (int): The number of entities processed so far.
            total_count (int): The total number of entities to process.
        """
        super().__init__()
        """Call the constructor of the parent class."""
        self.ids = ids
        """The list of entity IDs to process."""
        self.current_total = current_total
        """The number of entities processed so far."""
        self.total_count = total_count
        """The total number of entities to process."""

    def run(self):
        """
        Executes the entity processing logic.

        This method performs the following steps:
            1. Initializes the database helper if concurrency is enabled.
            2. Iterates through the list of entity IDs.
            3. For each ID, starts a database transaction.
            4. Calls `loader_pass_three_single` to process the entity.
            5. Handles `DatabaseError` exceptions during the process.
            6. Logs the progress of the processing.
        """
        proc_name = self.name
        """Get the name of the current process."""

        count = self.current_total
        """Counter for the number of entities processed."""
        end_count = count + len(self.ids)
        """Counter for the number of entities processed."""

        if OfflineDatabaseManager.get_concurrency_count() > 1:
            """Check if concurrency is enabled."""
            OfflineDatabaseHelper.initialize()
            """Initialize the database helper."""

        for id_ in self.ids:
            """Iterate over the entity IDs."""
            with offline_transaction():
                """Ensure that database operations are performed within a transaction."""
                entity_repository = EntityRepository()
                """Instance of EntityRepository for database operations on entities."""
                relation_repository = RelationRepository()
                """Instance of RelationRepository for database operations on relations."""
                try:
                    """Attempt to process the entity."""
                    self.loader_pass_three_single(
                        entity_repository,
                        relation_repository,
                        id_=id_,
                    )
                    """Process the entity."""

                except DatabaseError as e:
                    """Handle potential database errors."""
                    log.exception(
                        f"Database Error for entity id: {id_} in process {proc_name}",
                        exc_info=True,
                    )
                    raise e

            count += 1
            """Increment the processed counter."""
            if count % LoaderBase.BULK_REPORTING_SIZE == 0 and not count == end_count:
                """Log every BULK_REPORTING_SIZE."""
                log.debug(f"[{proc_name}] processed {count} of {self.total_count}")

        log.info(f"[{proc_name}] processed {count} of {self.total_count}")
        """Log the total number of entities processed."""

    @staticmethod
    def loader_pass_three_single(
        entity_repository: EntityRepository,
        relation_repository: RelationRepository,
        id_: int,
    ):
        """
        Processes a single entity record in the third pass.

        This method performs the following steps:
            1. Retrieves all relations for the entity.
            2. Counts the number of unique relations for each role.
            3. Updates the entity record with the relation counts.

        Args:
            entity_repository (EntityRepository): The repository for entity operations.
            relation_repository (RelationRepository): The repository for relation operations.
            id_ (int): The ID of the entity to process.
        """
        _relation_counts = {}
        """Dictionary to store the relation counts."""

        # Get all relations for this entity, where the entity is the subject or object of the relation
        # log.debug(f"id_: {id_}")
        relations = relation_repository.find_by_entity(id_)
        # log.debug(f"relations count: {len(relations)}")

        for relation in relations:
            """Iterate over the relations."""
            # log.debug(f"relation: {relation}")
            if relation.role not in _relation_counts:
                """If the role has not been seen yet."""
                _relation_counts[relation.role] = set()
                """Create a new set for the role."""
            key = (
                relation.subject,
                relation.object,
            )
            """Create a key from the subject and the object."""
            _relation_counts.get(relation.role).add(key)
            """Add the key to the set for this role."""
        # log.debug(f"_relation_counts: {_relation_counts}")

        for role, keys in _relation_counts.items():
            """Iterate over the roles and the sets of keys."""
            _relation_counts[role] = len(keys)
            """Count the unique keys in the set."""
        # log.debug(f"_relation_counts counted: {_relation_counts}")

        try:
            """Attempt to update the relation counts."""
            # Update the relation counts for this entity
            entity_repository.update(
                id_, {EntityTable.relation_counts.key: _relation_counts}
            )
            """Update the entity."""

            entity_repository.commit()
            """Commit the transaction."""
        except DatabaseError as e:
            """Handle potential database errors."""
            log.exception(
                f"Database Error for id: {id_}",
                exc_info=True,
            )
            raise e
