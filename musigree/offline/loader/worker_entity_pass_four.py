"""
This module defines the `process_entity_pass_four_worker` function, which is a worker
function responsible for processing entity records in the fourth pass of the
data loading process in the Musigree offline system.

It is designed to be used with `concurrent.futures.ProcessPoolExecutor` to enable
concurrent processing of entities, improving the efficiency of the data loading
process. The function handles the computation and updating of profile data
for each entity. Profiles can have embedded links to other entities, this class
processes all embedded profile links to add either missing entity_id or entity_name
        There maybe multiple links
        [a12345] -> [a12345=Artist Name]
        [a=Artist Name] -> [a12345=Artist Name]
        [l7890] -> [l7890=Label Name]
        [l=Label Name] -> [l7890=Label Name]
        [l7890=Label Name]
        e.g. "Classic Techno label from Detroit, USA.\r\n[b]Label owner:[/b] [a=Carl Craig].\r\n" ->
             "Classic Techno label from Detroit, USA.\r\n[b]Label owner:[/b] [a871=Carl Craig].\r\n"

Key functionalities include:
    - **Concurrent Processing**: Designed to work with `ProcessPoolExecutor` to
      perform processing operations concurrently, speeding up the processing of
      large numbers of entities.
    - **Profile link updating**: Computes the entity_id or entity_name of embedded links.
    - **Database Transactions**: Uses `offline_transaction` to ensure that
      each processing operation is atomic, maintaining data integrity.
    - **Error Handling**: Implements error handling using `try...except` blocks
      to catch `DatabaseError` exceptions and log them.
    - **Entity and Relation Access**: Uses `EntityRepository` and
      `RelationRepository` to access and update entity and relation data.
    - **Process Initialization**: Handles the initialization of the runtime_database
      helper in each worker process when concurrency is enabled.
    - **Logging**: Provides detailed logging of the processing, including
      the number of entities processed and any runtime_database errors encountered.
    - **Batch processing**: Process a list of ids at once.
    - **Reporting**: Log every `BULK_REPORTING_SIZE` elements.

The `process_entity_pass_four_worker` function interacts with the following components:
    - `OfflineDatabaseHelper`: For managing runtime_database connections and
      initialization in a concurrent environment.
    - `EntityRepository`: For runtime_database operations related to entities.
    - `RelationRepository`: For runtime_database operations related to relations.
    - `offline_transaction`: A decorator for managing runtime_database transactions.
    - `OfflineDatabaseManager`: For managing runtime_database concurrency settings.
    - `LoaderBase`: For accessing the `BULK_REPORTING_SIZE` constant.
    - `EntityTable`: For accessing the entity table definition.
    - `logging`: For logging operations.

The module utilizes `logging` for logging operations and `sqlalchemy.exc.DatabaseError`
for runtime_database related exception. It interacts with `musigree.offline.runtime_database` for
runtime_database related operations and `musigree.offline.offline_database_manager` for
managing concurrency.
"""

import asyncio
import logging
import multiprocessing

from musigree.constants import BULK_REPORTING_SIZE
from musigree.exceptions import DatabaseError
from musigree.offline.data_access_layer.offline_entity_data_access import OfflineEntityDataAccess
from musigree.offline.offline_database import EntityTable
from musigree.offline.offline_database.entity_repository import EntityRepository
from musigree.offline.offline_database.offline_transaction import offline_transaction
from musigree.offline.offline_database_manager import OfflineDatabaseManager

log = logging.getLogger(__name__)
"""
The logger for the worker entity pass four module.
"""


async def process_entity_pass_four_worker_async(
    ids: list[int], current_total: int, total_count: int
) -> None:
    """
    Worker function for processing entity records in the fourth pass.

    This function is designed to be used with ProcessPoolExecutor to perform
    concurrent processing of entities, calculating and updating relation counts.

    Args:
        ids (list[int]): A list of entity IDs to process.
        current_total (int): The number of entities processed so far.
        total_count (int): The total number of entities to process.

    Raises:
        DatabaseError: If there's an error during runtime_database operations.
    """

    proc_name = multiprocessing.current_process().name
    """Get the current process name for logging."""
    count = current_total
    """Counter for the number of entities processed."""
    end_count = count + len(ids)
    """Counter for the number of entities processed."""

    entity_repository = EntityRepository()
    """Instance of EntityRepository for offline_database operations on entities."""

    async with offline_transaction():
        """Ensure that offline_database operations are performed within a transaction."""

        for id_ in ids:
            """Iterate over the entity IDs."""
            try:
                """Attempt to process the entity."""
                await worker_pass_four_single(
                    entity_repository,
                    id_,
                )
                """Process the entity."""
                count += 1
                if count % BULK_REPORTING_SIZE == 0 and not count == end_count:
                    log.debug(f"[{proc_name}] processed {count} of {total_count}")
            except DatabaseError as e:
                """Handle potential runtime_database errors."""
                log.exception(
                    f"Database Error for entity id: {id_} in process {proc_name}",
                    exc_info=True,
                )
                raise e

    log.info(f"[{proc_name}] processed {count} of {total_count}")
    """Log the total number of entities processed."""


async def worker_pass_four_single(
    entity_repository: EntityRepository,
    id_: int,
) -> None:
    """
    Processes a single entity for pass four of the loading process.

    This function calculates and updates the embedded links in a profile field for a given entity.

    Args:
        entity_repository (EntityRepository): The repository for entity runtime_database operations.
        id_ (int): The internal ID of the entity to process.

    Raises:
        DatabaseError: If there's an error updating the entity in the runtime_database.
    """
    entity = await entity_repository.get_by_id(id_)
    metadata = entity.entity_metadata
    if metadata is not None:
        profile = entity.entity_metadata.get("profile", None)
        if profile:
            updated_profile = await OfflineEntityDataAccess.process_profile_links(
                entity_repository, profile
            )
            if profile != updated_profile:
                """If any changes were made to the entity."""
                log.debug(f"Entity (Pass 4)\n{profile} ->\n{updated_profile}")
                entity.entity_metadata["profile"] = updated_profile
                try:
                    await entity_repository.update(
                        entity.id,
                        {EntityTable.entity_metadata.key: entity.entity_metadata},
                    )
                    """Update the entity in the database."""
                    await entity_repository.commit()
                    """Commit the transaction."""
                except DatabaseError:
                    """Handle potential database errors."""
                    log.warning(f"Database Error for id: {entity.id}")
                    await entity_repository.rollback()
                    # raise e


def process_entity_pass_four_worker(ids: list[int], current_total: int, total_count: int) -> None:
    # Run the async function
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        """Check if the event loop is already running."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        """Set a new event loop if none exists."""

    OfflineDatabaseManager.reinitialize_offline_database_async_engine(loop)
    """Initialize the runtime_database engine."""

    loop.run_until_complete(process_entity_pass_four_worker_async(ids, current_total, total_count))

    OfflineDatabaseManager.dispose_offline_database_async_engine(loop)
    """Close the runtime_database engine."""
