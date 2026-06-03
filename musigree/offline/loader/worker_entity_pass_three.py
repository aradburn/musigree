"""
This module defines the `process_entity_pass_three_worker` function, which is a worker
function responsible for processing entity records in the third pass of the
data loading process in the Musigree offline system.

It is designed to be used with `concurrent.futures.ProcessPoolExecutor` to enable
concurrent processing of entities, improving the efficiency of the data loading
process. The function handles the computation and updating of relation counts
for each entity.

Key functionalities include:
    - **Concurrent Processing**: Designed to work with `ProcessPoolExecutor` to
      perform processing operations concurrently, speeding up the processing of
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

The `process_entity_pass_three_worker` function interacts with the following components:
    - `OfflineDatabaseHelper`: For managing database connections and
      initialization in a concurrent environment.
    - `EntityRepository`: For database operations related to entities.
    - `RelationRepository`: For database operations related to relations.
    - `offline_transaction`: A decorator for managing database transactions.
    - `OfflineDatabaseManager`: For managing database concurrency settings.
    - `LoaderBase`: For accessing the `BULK_REPORTING_SIZE` constant.
    - `EntityTable`: For accessing the entity table definition.
    - `logging`: For logging operations.

The module utilizes `logging` for logging operations and `sqlalchemy.exc.DatabaseError`
for database related exception. It interacts with `musigree.offline.database` for
database related operations and `musigree.offline.offline_database_manager` for
managing concurrency.
"""

import asyncio
import logging
import multiprocessing

from musigree.constants import BULK_REPORTING_SIZE
from musigree.exceptions import DatabaseError
from musigree.offline.offline_database.entity_repository import EntityRepository
from musigree.offline.offline_database.entity_table import EntityTable
from musigree.offline.offline_database.offline_transaction import offline_transaction
from musigree.offline.offline_database.relation_repository import RelationRepository
from musigree.offline.offline_database_manager import OfflineDatabaseManager

log = logging.getLogger(__name__)
"""
The logger for the worker entity pass three module.
"""


async def process_entity_pass_three_worker_async(
    ids: list[int], current_total: int, total_count: int
) -> None:
    """
    Worker function for processing entity records in the third pass.

    This function is designed to be used with ProcessPoolExecutor to perform
    concurrent processing of entities, calculating and updating relation counts.

    Args:
        ids (list[int]): A list of entity IDs to process.
        current_total (int): The number of entities processed so far.
        total_count (int): The total number of entities to process.

    Raises:
        DatabaseError: If there's an error during database operations.
    """

    proc_name = multiprocessing.current_process().name
    """Get the current process name for logging."""
    count = current_total
    """Counter for the number of entities processed."""
    end_count = count + len(ids)
    """Counter for the number of entities processed."""

    entity_repository = EntityRepository()
    """Instance of EntityRepository for database operations on entities."""
    relation_repository = RelationRepository()
    """Instance of RelationRepository for database operations on relations."""

    async with offline_transaction():
        """Ensure that database operations are performed within a transaction."""

        for id_ in ids:
            """Iterate over the entity IDs."""
            try:
                """Attempt to process the entity."""
                await worker_pass_three_single(
                    entity_repository,
                    relation_repository,
                    id_,
                )
                """Process the entity."""
                count += 1
                if count % BULK_REPORTING_SIZE == 0 and not count == end_count:
                    log.debug(f"[{proc_name}] processed {count} of {total_count}")
            except DatabaseError as e:
                """Handle potential database errors."""
                log.exception(
                    f"Database Error for entity id: {id_} in process {proc_name}",
                    exc_info=True,
                )
                raise e

    log.info(f"[{proc_name}] processed {count} of {total_count}")
    """Log the total number of entities processed."""


async def worker_pass_three_single(
    entity_repository: EntityRepository,
    relation_repository: RelationRepository,
    id_: int,
) -> None:
    """
    Processes a single entity for pass three of the loading process.

    This function calculates and updates the relation counts for a given entity.
    It queries aggregated distinct (subject, object) counts per role where the
    entity is subject or object, then updates the entity's
    relation_counts field.

    Args:
        entity_repository (EntityRepository): The repository for entity database operations.
        relation_repository (RelationRepository): The repository for relation database operations.
        id_ (int): The internal ID of the entity to process.

    Raises:
        DatabaseError: If there's an error updating the entity in the database.
    """
    _relation_count_totals = await relation_repository.find_role_counts_by_entity(id_)
    """Distinct (subject, object) counts per role (aggregated in SQL)."""

    if len(_relation_count_totals) > 0:
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


def process_entity_pass_three_worker(ids: list[int], current_total: int, total_count: int) -> None:
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

    loop.run_until_complete(process_entity_pass_three_worker_async(ids, current_total, total_count))

    OfflineDatabaseManager.dispose_offline_database_async_engine(loop)
    """Close the database engine."""
