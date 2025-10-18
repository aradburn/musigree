"""
This module defines the `process_entity_pass_two_worker` function, which is a worker function
responsible for processing entity records in the second pass of the
data loading process in the Musigree offline system.

It is designed to be used with `concurrent.futures.ProcessPoolExecutor` to enable
concurrent processing of entities, improving the efficiency of the data loading process.
The function handles the resolution of entity references (e.g., aliases, groups, members)
within the entity data.

Key functionalities include:
    - **Concurrent Processing**: Designed to work with `ProcessPoolExecutor` to perform
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

The `process_entity_pass_two_worker` function interacts with the following components:
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

The module utilizes `logging` for logging operations and `sqlalchemy.exc.DatabaseError`
for database related exceptions. It interacts with `musigree.offline.database` for database
related operations and `musigree.offline.offline_database_manager` for managing
concurrency.
"""

import asyncio
import logging
import multiprocessing

from musigree.constants import BULK_REPORTING_SIZE
from musigree.exceptions import NotFoundError, DatabaseError
from musigree.logging_config import LOGGING_TRACE
from musigree.offline.data_access_layer.entity_data_access import EntityDataAccess
from musigree.offline.database.entity_repository import EntityRepository
from musigree.offline.database.entity_table import EntityTable
from musigree.offline.database.offline_transaction import offline_transaction
from musigree.offline.domain.entity import Entity
from musigree.offline.offline_database_manager import OfflineDatabaseManager

log = logging.getLogger(__name__)
"""
The logger for the worker entity pass two module.
"""


async def process_entity_pass_two_worker_async(
    ids: list[int], current_total: int, total_count: int
) -> None:
    """
    Worker function for processing entity records in the second pass.

    This function is designed to be used with ProcessPoolExecutor to perform
    concurrent processing of entities, resolving references to other entities.

    Args:
        ids (list[int]): A list of entity IDs to process.
        current_total (int): The number of entities processed so far.
        total_count (int): The total number of entities to process.

    Raises:
        NotFoundError: If an entity is not found during processing.
        DatabaseError: If there's an error during database operations.
        Exception: If an entity could not be updated after multiple attempts.
    """

    proc_name = multiprocessing.current_process().name
    """Get the name of the current process."""

    count = current_total
    """Counter for the number of entities processed."""
    end_count = count + len(ids)

    async with offline_transaction():
        """Ensure that database operations are performed within a transaction."""
        entity_repository = EntityRepository()
        """Instance of EntityRepository for database operations on entities."""

        for entity_id in ids:
            # log.debug(f"[{proc_name}] processing entity id: {_id}")
            """Iterate over the entity IDs."""
            try:
                """Attempt to process the entity."""
                entity = await entity_repository.get_by_id(entity_id)
                """Retrieve the entity."""
                await worker_pass_two_single(entity_repository, entity, proc_name)
                """Process the entity."""
                count += 1
                # """Increment the entity counter."""
                if count % BULK_REPORTING_SIZE == 0 and not count == end_count:
                    """Log the progress."""
            except NotFoundError:
                """Handle the case where the entity is not found."""
                log.warning(
                    f"Database NotFoundError: entity with id {entity_id} in process: {proc_name}"
                )
                await entity_repository.rollback()
                """Rollback the transaction."""

                log.debug(f"[{proc_name}] processed {count} of {total_count}")

    log.info(f"[{proc_name}] processed {count} of {total_count}")


async def worker_pass_two_single(
    entity_repository: EntityRepository, entity: Entity, proc_name: str
) -> None:
    """
    Processes a single entity in the second pass.

    This function resolves references to other entities within an entity's
    data. It accesses entity metadata and resolves any entity references
    found within the metadata.

    Args:
        entity_repository (EntityRepository): The repository for entity operations.
        entity (Entity): The entity to process.
        proc_name (str): The name of the current process.

    Raises:
        DatabaseError: If there's an error during database operations.
    """
    if LOGGING_TRACE:
        log.debug(f"id: {entity.entity_id}-{entity.entity_type}")

    changed = await EntityDataAccess.resolve_entity_references(entity_repository, entity)
    """Resolve entity references."""
    if changed:
        """If any changes were made to the entity."""
        if LOGGING_TRACE:
            log.debug(
                f"Entity (Pass 2) [{proc_name}]\t"
                + f"          (id: {entity.entity_id}-{entity.entity_type}): {entity.entity_name}"
            )
        try:
            await entity_repository.update(
                entity.id,
                {EntityTable.entities.key: entity.entities},
            )
            """Update the entity in the database."""
            await entity_repository.commit()
            """Commit the transaction."""
        except DatabaseError as e:
            """Handle potential database errors."""
            log.exception(
                f"Database Error for id: {entity.id}",
                exc_info=True,
            )
            raise e


def process_entity_pass_two_worker(ids: list[int], current_total: int, total_count: int) -> None:
    # Run the async function
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        """Check if the event loop is already running."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        """Set a new event loop if none exists."""

    OfflineDatabaseManager.reinitialize_offline_database_async_engine(loop)
    """Initialize the database engine."""

    loop.run_until_complete(process_entity_pass_two_worker_async(ids, current_total, total_count))

    OfflineDatabaseManager.dispose_offline_database_async_engine(loop)
    """Close the database engine."""
