"""
This module defines the `update_master_worker` function, which is a worker
function responsible for updating or inserting master records in the
Musigree offline runtime_database.

It utilizes `concurrent.futures.ProcessPoolExecutor` to enable concurrent updating and insertion of
master, improving the efficiency of the data loading process. The
`update_master_worker` handles updating existing master records with new
information, as well as inserting new master records if they do not already
exist in the runtime_database.

Key functionalities include:
    - **Concurrent Updating/Inserting**: Designed to work with `ProcessPoolExecutor` to
      perform update and insert operations concurrently, speeding up the
      processing of large numbers of master.
    - **Batch Processing**: Processes a list of master data (`bulk_updates`)
      in a single run, minimizing runtime_database interactions.
    - **Database Transactions**: Uses `offline_transaction` to ensure that
      each update or insert operation is atomic, maintaining data integrity.
    - **Error Handling**: Implements error handling using `try...except` blocks
      to catch `NotFoundError` and `DatabaseError` exceptions and handle them
      appropriately.
    - **master Access**: Uses `masterRepository` to access and update or
      insert master data.
    - **Change Detection**: Uses `DeepDiff` to detect changes between the
      existing master and the new data, only updating fields that have changed.
    - **Process Initialization**: Handles the initialization of the runtime_database
      helper in each worker process when concurrency is enabled.
    - **Logging**: Provides detailed logging of the update and insertion
      process, including the number of updated and inserted master.

The `update_master_worker` function interacts with the following components:
    - `OfflineDatabaseHelper`: For managing runtime_database connections and
      initialization in a concurrent environment.
    - `masterRepository`: For runtime_database operations related to master.
    - `master`: The offline_domain object representing a master.
    - `masterTable`: For accessing the master table definition.
    - `DeepDiff`: For comparing the existing master with the new data.
    - `offline_transaction`: A decorator for managing runtime_database transactions.
    - `OfflineDatabaseManager`: For managing runtime_database concurrency settings.
    - `logging`: For logging operations.
    - `NotFoundError`: Used for handling the not found exception.
    - `DatabaseError`: Used for handling the runtime_database exception.
    - `LOGGING_TRACE`: Used to check if trace logging is activated.

The module utilizes `logging` for logging operations, `sqlalchemy.exc.DatabaseError` for runtime_database
related exception and `pprint` for pretty print the diff between master. It
interacts with `musigree.offline.runtime_database` for runtime_database related operations,
and `musigree.offline.offline_database_manager` for managing concurrency.
"""

import asyncio
import logging
import pprint
from typing import Any

from deepdiff import DeepDiff

from musigree.exceptions import DatabaseError, NotFoundError
from musigree.logging_config import LOGGING_TRACE
from musigree.offline.offline_database.master_repository import MasterRepository
from musigree.offline.offline_database.master_table import MasterTable
from musigree.offline.offline_database.offline_transaction import offline_transaction
from musigree.offline.offline_domain.master import Master
from musigree.offline.offline_database_manager import OfflineDatabaseManager

log = logging.getLogger(__name__)
"""
The logger for the update_master_worker module.
"""


async def update_master_worker_async(
    bulk_updates: list[dict[str, Any]], processed_count: int, _total_count: int
) -> None:
    """
    A worker function for updating or inserting master records.

    This function is designed to work with `ProcessPoolExecutor` to perform concurrent
    update and insert operations on master records in the Musigree offline system.

    Key functionalities include:
        - **Concurrent Processing**: Designed for use with `ProcessPoolExecutor`.
        - **Batch Processing**: Processes multiple master records in a single execution.
        - **Database Transactions**: Uses `offline_transaction` for data integrity.
        - **Error Handling**: Handles `NotFoundError` and `DatabaseError` exceptions.
        - **Change Detection**: Uses `DeepDiff` to detect and update only changed fields.
        - **Process Initialization**: Initializes runtime_database helper for concurrent processing.
        - **Logging**: Provides detailed logging of processing progress and errors.

    The function interacts with the following components:
        - `OfflineDatabaseHelper`: For runtime_database connection management.
        - `MasterRepository`: For runtime_database operations on master.
        - `master`: The offline_domain object representing a master.
        - `masterTable`: For accessing master table schema.
        - `DeepDiff`: For detecting changes between master.
        - `offline_transaction`: For managing runtime_database transactions.

    Args:
        bulk_updates (list[dict[str, Any]]): A list of master data to update or insert.
        processed_count (int): The number of master processed so far.
        _total_count (int): The total number of master to process (unused).
    Raises:
        NotFoundError: When a master is not found in the runtime_database during update.
        DatabaseError: When there's an error with runtime_database operations.
    """

    updated_count = 0
    """Counter for the number of master updated."""
    inserted_count = 0
    """Counter for the number of master inserted."""

    async with offline_transaction():
        """Ensure that runtime_database operations are performed within a transaction."""

        master_repository = MasterRepository()
        """Instance of masterRepository for runtime_database operations on master."""

        for data in bulk_updates:
            """Iterate over the master data."""
            updated_master = Master(**data)

            """Create a new master object from the data."""
            try:
                """Attempt to update the master."""
                if LOGGING_TRACE:
                    """Log if trace logging is enabled."""
                    log.debug(f"update: {updated_master.master_id}")

                db_master = await master_repository.get_by_id(updated_master.master_id)
                """Retrieve the existing master from the runtime_database."""

                is_changed = False
                """Flag to check if any changes were made."""
                update_payload: dict[str, Any] = {}
                """Dictionary to store the update payload."""

                if db_master.title != updated_master.title:
                    """Check if the master title has changed."""
                    db_master.title = updated_master.title
                    update_payload[MasterTable.title.key] = db_master.title
                    """Update the master title."""
                    is_changed = True
                    """Set the changed flag."""

                # Update metadata
                differences = DeepDiff(
                    db_master,
                    updated_master,
                    exclude_paths=[
                        "dirty_fields",
                        "_dirty",
                    ],
                    ignore_numeric_type_changes=True,
                )
                """Compare the master metadata."""
                diff = pprint.pformat(differences)
                """Format the diff for logging."""
                if diff != "{}":
                    """If there are any differences."""
                    if LOGGING_TRACE:
                        """Log the differences if trace logging is enabled."""
                        log.debug(f"diff: {diff}")

                    # Update all fields that have changed
                    update_fields: dict[str, Any] = {
                        MasterTable.title.key: updated_master.title,
                        MasterTable.year.key: updated_master.year,
                        MasterTable.main_release.key: updated_master.main_release,
                        MasterTable.data_quality.key: updated_master.data_quality,
                        MasterTable.artists.key: updated_master.artists,
                        MasterTable.genres.key: updated_master.genres,
                        MasterTable.styles.key: updated_master.styles,
                        MasterTable.videos.key: updated_master.videos,
                    }

                    """Update payload for metadata fields."""
                    update_payload.update(update_fields)
                    """Add metadata fields to the update payload."""
                    is_changed = True
                    """Set the changed flag."""

                if is_changed:
                    """If any changes were made."""
                    await master_repository.update(updated_master.master_id, update_payload)
                    """Update the master in the runtime_database."""
                    await master_repository.commit()
                    """Commit the transaction."""
                    updated_count += 1
                    """Increment the updated counter."""

            except NotFoundError:
                """If the master is not found in the runtime_database."""
                if LOGGING_TRACE:
                    """Log if trace logging is enabled."""
                    log.debug(f"insert: {updated_master.master_id}")

                await master_repository.create(updated_master)
                """Insert the new master into the runtime_database."""
                inserted_count += 1
                """Increment the inserted counter."""

            except DatabaseError as e:
                """If there's a runtime_database error."""
                log.error(f"Database error: {e}")
                """Log the runtime_database error."""
                raise e

    log.info(
        f"worker updated {updated_count} inserted {inserted_count} master total processed {processed_count}"
    )
    """Log the number of updated and inserted master."""


def update_master_worker(
    bulk_updates: list[dict[str, Any]], current_total: int, total_count: int
) -> None:
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

    loop.run_until_complete(update_master_worker_async(bulk_updates, current_total, total_count))

    OfflineDatabaseManager.dispose_offline_database_async_engine(loop)
    """Close the runtime_database engine."""
