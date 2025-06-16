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
import asyncio

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
        Executes the third pass of the loading process for the assigned entity IDs.

        This method processes each entity ID in the worker's assigned list,
        calculating and updating relation counts for each entity. It handles
        database transactions and provides progress logging.

        The method:
        1. Initializes database connections if concurrency is enabled
        2. Processes each entity ID within a database transaction
        3. Calculates relation counts for the entity
        4. Updates the entity record with the counts
        5. Provides periodic progress logging

        Raises:
            DatabaseError: If there's an error during database operations.
        """
        proc_name = multiprocessing.current_process().name
        """Get the current process name for logging."""
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
            async def process_entity():
                async with offline_transaction():
                    """Ensure that database operations are performed within a transaction."""
                    entity_repository = EntityRepository()
                    """Instance of EntityRepository for database operations on entities."""
                    relation_repository = RelationRepository()
                    """Instance of RelationRepository for database operations on relations."""
                    try:
                        """Attempt to process the entity."""
                        await self.loader_pass_three_single(
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
            
            # Run the async function
            asyncio.run(process_entity())

            count += 1
            """Increment the processed counter."""
            if count % LoaderBase.BULK_REPORTING_SIZE == 0 and not count == end_count:
                """Log every BULK_REPORTING_SIZE."""
                log.debug(f"[{proc_name}] processed {count} of {self.total_count}")

        log.info(f"[{proc_name}] processed {count} of {self.total_count}")
        """Log the total number of entities processed."""

    @staticmethod
    async def loader_pass_three_single(
        entity_repository: EntityRepository,
        relation_repository: RelationRepository,
        id_: int,
    ):
        """
        Processes a single entity for pass three of the loading process.

        This method calculates and updates the relation counts for a given entity.
        It retrieves all relations where the entity is either the subject or object,
        counts the unique relations for each role, and updates the entity's
        relation_counts field.

        Args:
            entity_repository (EntityRepository): The repository for entity database operations.
            relation_repository (RelationRepository): The repository for relation database operations.
            id_ (int): The internal ID of the entity to process.

        Raises:
            DatabaseError: If there's an error updating the entity in the database.
        """
        _relation_counts: dict[str, set[tuple[int, int]]] = {}
        """A dictionary to store relation counts by role."""
        _relation_count_totals: dict[str, int] = {}
        """A dictionary to store the total counts for each role."""

        # Get all relations for this entity, where the entity is the subject or object of the relation
        # log.debug(f"id_: {id_}")
        relations = await relation_repository.find_by_entity(id_)
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
            set_entry = _relation_counts.get(relation.role)
            if set_entry is not None:
                set_entry.add(key)
            """Add the key to the set for this role."""
        # log.debug(f"_relation_counts: {_relation_counts}")

        for role, keys in _relation_counts.items():
            """Iterate over the roles and the sets of keys."""
            _relation_count_totals[role] = len(keys)
            """Count the unique keys in the set."""
        # log.debug(f"_relation_counts counted: {_relation_counts}")

        try:
            """Attempt to update the relation counts."""
            # Update the relation counts for this entity
            await entity_repository.update(
                id_, {EntityTable.relation_counts.key: _relation_count_totals}
            )
            """Update the entity."""

            await entity_repository.commit()
            """Commit the transaction."""
        except DatabaseError as e:
            """Handle potential database errors."""
            log.exception(
                f"Database Error for id: {id_}",
                exc_info=True,
            )
            raise e
