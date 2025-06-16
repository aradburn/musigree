"""
This module defines the `WorkerEntityPassTwo` class, which is a worker
process responsible for processing entity records in the second pass of the
data loading process in the Musigree offline system.

It utilizes `multiprocessing` to enable concurrent processing of entities,
improving the efficiency of the data loading process. The `WorkerEntityPassTwo`
handles the resolution of entity references (e.g., aliases, groups, members)
within the entity data.

Key functionalities include:
    - **Concurrent Processing**: Employs `multiprocessing.Process` to perform
      processing operations concurrently, speeding up the processing of
      large numbers of entities.
    - **Reference Resolution**: Resolves references to other entities within
      an entity's data, ensuring data consistency and correctness.
    - **Database Transactions**: Uses `offline_transaction` to ensure that
      each processing operation is atomic, maintaining data integrity.
    - **Error Handling**: Implements error handling using `try...except` blocks
      to catch `NotFoundError` and `DatabaseError` exceptions and handle
      them appropriately.
    - **Retry Mechanism**: Implements a retry mechanism for `NotFoundError`
      exceptions, allowing the worker to attempt to reprocess an entity
      multiple times before giving up.
    - **Entity Access**: Uses `EntityRepository` to access and update
      entity data.
    - **Process Initialization**: Handles the initialization of the database
      helper in each worker process when concurrency is enabled.
    - **Logging**: Provides detailed logging of the processing, including
      the number of entities processed, any database errors encountered, and
      any entities that could not be found or updated.
    - **Batch processing**: Process a list of ids at once.
    - **Reporting**: Log every `BULK_REPORTING_SIZE` elements.

The `WorkerEntityPassTwo` class interacts with the following components:
    - `multiprocessing.Process`: The base class for creating worker processes.
    - `OfflineDatabaseHelper`: For managing database connections and
      initialization in a concurrent environment.
    - `EntityRepository`: For database operations related to entities.
    - `EntityDataAccess`: For performing entity-specific data access operations,
      such as resolving references.
    - `offline_transaction`: A decorator for managing database transactions.
    - `OfflineDatabaseManager`: For managing database concurrency settings.
    - `LoaderBase`: For accessing the `BULK_REPORTING_SIZE` constant.
    - `EntityTable`: For accessing the entity table definition.
    - `Entity`: The domain object representing an entity.
    - `logging`: For logging operations.
    - `NotFoundError`: Used for handling the not found exception.
    - `DatabaseError`: Used for handling the database exception.

The module utilizes `logging` for logging operations, `multiprocessing` for
process management, and `sqlalchemy.exc.DatabaseError` for database
related exception. It interacts with `musigree.offline.database` for database
related operations and `musigree.offline.offline_database_manager` for managing
concurrency.
"""

import asyncio
import logging
import multiprocessing

from musigree.exceptions import NotFoundError, DatabaseError
from musigree.offline.data_access_layer.entity_data_access import EntityDataAccess
from musigree.offline.database.offline_database_helper import OfflineDatabaseHelper
from musigree.offline.database.entity_repository import EntityRepository
from musigree.offline.database.entity_table import EntityTable
from musigree.offline.database.offline_transaction import offline_transaction
from musigree.offline.domain.entity import Entity
from musigree.offline.loader.loader_base import LoaderBase
from musigree.logging_config import LOGGING_TRACE
from musigree.offline.offline_database_manager import OfflineDatabaseManager

log = logging.getLogger(__name__)
"""
The logger for the WorkerEntityPassTwo module.
"""


class WorkerEntityPassTwo(multiprocessing.Process):
    """
    A worker process for processing entity records in the second pass.

    This class extends `multiprocessing.Process` to perform concurrent
    processing of entities, resolving references to other entities.
    """

    def __init__(self, ids: list[int], current_total: int, total_count: int):
        """
        Initializes the WorkerEntityPassTwo.

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
            3. For each ID, attempts to process the entity, retrying on `NotFoundError`.
            4. Calls `worker_pass_two_single` to resolve references.
            5. Handles `NotFoundError` and `DatabaseError` exceptions.
            6. Logs the progress of the processing.
            7. Raises an exception if an entity could not be updated after
            multiple attempts.
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
            max_attempts = 10
            """Maximum number of attempts to process an entity."""
            error = True
            """Flag indicating if an error occurred."""
            while error and max_attempts != 0:
                """Retry loop."""
                error = False
                """Reset the error flag."""
                
                async def process_entity():
                    nonlocal error, max_attempts
                    entity = None  # Initialize entity variable
                    async with offline_transaction():
                        """Ensure that database operations are performed within a transaction."""
                        entity_repository = EntityRepository()
                        """Instance of EntityRepository for database operations on entities."""
                        try:
                            """Attempt to process the entity."""
                            entity = await entity_repository.get_by_id(id_)
                            """Retrieve the entity."""
                            await self.worker_pass_two_single(
                                entity_repository, entity, proc_name
                            )
                            """Process the entity."""
                        except NotFoundError:
                            """Handle the case where the entity is not found."""
                            if entity:
                                log.warning(
                                    f"Database NotFoundError: {entity.entity_id}-{entity.entity_type} in process: {proc_name}"
                                )
                            else:
                                log.warning(
                                    f"Database NotFoundError: entity with id {id_} in process: {proc_name}"
                                )
                            await entity_repository.rollback()
                            """Rollback the transaction."""
                            max_attempts -= 1
                            """Decrement the number of attempts."""
                            error = True
                            """Set the error flag."""
                        except DatabaseError as e:
                            """Handle potential database errors."""
                            if entity:
                                log.exception(
                                    f"Database Error for entity_id: {entity.entity_id}-{entity.entity_type} "
                                    + f"in process: {proc_name}",
                                    exc_info=True,
                                )
                            else:
                                log.exception(
                                    f"Database Error for entity with id {id_} in process: {proc_name}",
                                    exc_info=True,
                                )
                            raise e
                
                # Run the async function
                asyncio.run(process_entity())

            if error:
                """If the entity could not be processed after multiple attempts."""
                log.debug(
                    f"Error in updating references for entity_id: {id_}"
                )
                raise Exception(
                    f"Error in updating references for entity_id: {id_}"
                )

            count += 1
            """Increment the processed counter."""
            if count % LoaderBase.BULK_REPORTING_SIZE == 0 and not count == end_count:
                """Log every BULK_REPORTING_SIZE."""
                log.debug(f"[{proc_name}] processed {count} of {self.total_count}")

        log.info(f"[{proc_name}] processed {count} of {self.total_count}")
        """Log the total number of entities processed."""

    # PUBLIC METHODS

    @staticmethod
    async def worker_pass_two_single(
        entity_repository: EntityRepository, entity: Entity, proc_name: str
    ):
        """
        Processes a single entity record in the second pass.

        This method resolves references to other entities within the given entity's data
        (e.g., aliases, groups, members).

        Args:
            entity_repository (EntityRepository): The repository for entity operations.
            entity (Entity): The entity to process.
            proc_name (str): An annotation for logging purposes.
        """
        if LOGGING_TRACE:
            log.debug(f"id: {entity.entity_id}-{entity.entity_type}")

        changed = EntityDataAccess.resolve_entity_references(entity_repository, entity)
        """Resolve entity references."""
        if changed:
            """If any changes were made to the entity."""
            if LOGGING_TRACE:
                log.debug(
                    f"Entity (Pass 2) [{proc_name}]\t"
                    + f"          (id: {entity.entity_id}-{entity.entity_type}): {entity.entity_name}"
                )
            await entity_repository.update(
                entity.id,
                {EntityTable.entities.key: entity.entities},
            )
            """Update the entity in the database."""
            await entity_repository.commit()
            """Commit the transaction."""
