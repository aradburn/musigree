"""
This module defines the `update_entities_worker` function, which is a worker function
responsible for updating or inserting entity records in the Musigree offline
database.

It is designed to be used with `concurrent.futures.ProcessPoolExecutor` to enable
concurrent updating and insertion of entities, improving the efficiency of the data
loading process. The function handles updating existing entity records with new
information, as well as inserting new entity records if they do not already
exist in the database.

Key functionalities include:
    - **Concurrent Updating/Inserting**: Designed to work with `ProcessPoolExecutor` to
      perform update and insert operations concurrently, speeding up the
      processing of large numbers of entities.
    - **Batch Processing**: Processes a list of entity data (`bulk_updates`) in
      a single run, minimizing database interactions.
    - **Database Transactions**: Uses `offline_transaction` to ensure that each
      update or insert operation is atomic, maintaining data integrity.
    - **Error Handling**: Implements error handling using `try...except` blocks
      to catch `NotFoundError` and `DatabaseError` exceptions and handle them
      appropriately.
    - **Entity Access**: Uses `EntityRepository` to access and update or insert
      entity data.
    - **Reference Resolution**: Resolves entity references (e.g., aliases,
      groups, members) within the entity data.
    - **Process Initialization**: Handles the initialization of the database
      helper in each worker process when concurrency is enabled.
    - **Change Detection**: Uses `DeepDiff` to detect changes between the
      existing entity and the new data, only updating fields that have changed.
    - **Search Content Normalization**: Normalizes entity names for full-text
      search.
    - **Logging**: Provides detailed logging of the update and insertion
      process, including the number of updated and inserted entities.

The `update_entities_worker` function interacts with the following components:
    - `OfflineDatabaseHelper`: For managing database connections and
      initialization in a concurrent environment.
    - `EntityRepository`: For database operations related to entities.
    - `Entity`: The domain object representing an entity.
    - `EntityTable`: For accessing the entity table definition.
    - `DeepDiff`: For comparing the existing entity with the new data.
    - `normalise_search_content`: A function for normalizing search content.
    - `offline_transaction`: A decorator for managing database transactions.
    - `OfflineDatabaseManager`: For managing database concurrency settings.
    - `logging`: For logging operations.
    - `NotFoundError`: Used for handling the not found exception.
    - `DatabaseError`: Used for handling the database exception.
    - `LOGGING_TRACE`: Used to check if trace logging is activated.

The module utilizes `logging` for logging operations, `sqlalchemy.exc.DatabaseError`
for database related exceptions and `pprint` for pretty print the diff between entities.
It interacts with `musigree.offline.database` for database related operations,
`musigree.library.full_text_search` for text normalization and
`musigree.offline.offline_database_manager` for managing concurrency.
"""
import asyncio
import logging
import multiprocessing
import pprint
from typing import Any

from deepdiff import DeepDiff

from musigree.exceptions import DatabaseError, NotFoundError
from musigree.library.full_text_search.text_search_utils import (
    normalise_search_content,
)
from musigree.logging_config import LOGGING_TRACE
from musigree.offline.database.entity_repository import EntityRepository
from musigree.offline.database.entity_table import EntityTable
from musigree.offline.database.offline_transaction import offline_transaction
from musigree.offline.domain.entity import Entity
from musigree.offline.offline_database_manager import OfflineDatabaseManager

log = logging.getLogger(__name__)
"""
The logger for the worker entity updater module.
"""


async def update_entities_worker_async(bulk_updates: list[dict[str, Any]], processed_count: int, total_count: int) -> None:
    """
    Worker function for updating or inserting entity records.

    This function is designed to be used with ProcessPoolExecutor to perform
    concurrent update and insert operations on entity records.

    Args:
        bulk_updates (list[dict[str, Any]]): A list of entity data to update or insert.
        processed_count (int): The number of entities processed so far.
        total_count (int): The total number of entities to process.
    Raises:
        NotFoundError: If an entity is not found during the update process.
        DatabaseError: If there's an error during database operations.
    """

    proc_name = multiprocessing.current_process().name
    """Get the name of the current process."""

    updated_count = 0
    """Counter for the number of entities updated."""
    inserted_count = 0
    """Counter for the number of entities inserted."""

    async with offline_transaction():
        for data in bulk_updates:
            """Iterate over the entity data."""

            """Ensure that database operations are performed within a transaction."""
            entity_repository = EntityRepository()
            """Instance of EntityRepository for database operations on entities."""
            updated_entity = Entity(**data)
            """Create a new Entity object from the data."""
            try:
                """Attempt to update the entity."""
                if LOGGING_TRACE:
                    """Log if trace logging is enabled."""
                    log.debug(
                        f"update: {updated_entity.entity_id}-{updated_entity.entity_type}"
                    )

                db_entity = (
                    await entity_repository.get_by_entity_id_and_entity_type(
                        updated_entity.entity_id, updated_entity.entity_type
                    )
                )
                """Retrieve the existing entity from the database."""

                is_changed = False
                """Flag to check if any changes were made."""
                update_payload: dict[str, Any] = {}
                """Dictionary to store the update payload."""

                if db_entity.entity_name != updated_entity.entity_name:
                    """Check if the entity name has changed."""
                    # Update name
                    db_entity.entity_name = updated_entity.entity_name
                    update_payload[EntityTable.entity_name.key] = (
                        db_entity.entity_name
                    )
                    """Update the entity name."""

                    # Update search_content
                    db_entity.search_content = normalise_search_content(
                        updated_entity.entity_name
                    )
                    update_payload[EntityTable.search_content.key] = (
                        db_entity.search_content
                    )
                    """Update the search content."""
                    is_changed = True
                    """Set the changed flag."""

                # Update metadata
                differences = DeepDiff(
                    db_entity,
                    updated_entity,
                    include_paths=[
                        "entity_metadata",
                    ],
                    ignore_numeric_type_changes=True,
                )
                """Compare the entity metadata."""
                diff = pprint.pformat(differences)
                """Format the diff for logging."""
                if diff != "{}":
                    """If there are any differences."""
                    if LOGGING_TRACE:
                        """Log the differences if trace logging is enabled."""
                        log.debug(f"diff: {diff}")
                    # log.debug(f"db_entity     : {db_entity}")
                    # log.debug(f"updated_entity: {updated_entity}")

                    db_entity.entity_metadata = updated_entity.entity_metadata
                    """Update the entity metadata."""

                    update_payload[EntityTable.entity_metadata.key] = (
                        db_entity.entity_metadata
                    )
                    """Add the metadata to the update payload."""
                    is_changed = True
                    """Set the changed flag."""

                if is_changed:
                    """If any changes were made, update the entity."""
                    await entity_repository.update(db_entity.id, update_payload)
                    """Update the entity."""
                    await entity_repository.commit()
                    """Commit the transaction."""
                    updated_count += 1
                    """Increment the updated count."""
            except NotFoundError:
                """Handle the case where the entity is not found."""
                # log.debug(
                #     f"New insert in update_entities_worker: {updated_entity.entity_id}-{updated_entity.entity_type}"
                # )
                try:
                    """Attempt to create a new entity."""
                    await entity_repository.create(updated_entity)
                    """Create the entity."""
                    await entity_repository.commit()
                    """Commit the transaction."""
                    inserted_count += 1
                    """Increment the inserted count."""
                except DatabaseError as e:
                    """Handle database errors."""
                    log.exception("Error in update_entities_worker")
                    raise e
            except DatabaseError as e:
                """Handle database errors."""
                log.exception("Error in update_entities_worker")
                raise e

    log.info(
        f"[{proc_name}] processed_count: {processed_count}, "
        + f"updated: {updated_count}, inserted: {inserted_count}"
    )
    """Log the number of entities processed, updated, and inserted."""

def update_entities_worker(bulk_updates: list[dict[str, Any]], current_total: int, total_count: int) -> None:
    # Run the async function
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        """Check if the event loop is already running."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        """Set a new event loop if none exists."""

    if OfflineDatabaseManager.get_concurrency_count() > 1:
        """Check if concurrency is enabled."""
        OfflineDatabaseManager.reinitialize_offline_database_async_engine(loop)
        """Initialize the database engine."""

    loop.run_until_complete(update_entities_worker_async(bulk_updates, current_total, total_count))

