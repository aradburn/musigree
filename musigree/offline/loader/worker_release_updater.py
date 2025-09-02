"""
This module defines the `update_releases_worker` function, which is a worker
function responsible for updating or inserting release records in the
Musigree offline database.

It utilizes `concurrent.futures.ProcessPoolExecutor` to enable concurrent updating and insertion of
releases, improving the efficiency of the data loading process. The
`update_releases_worker` handles updating existing release records with new
information, as well as inserting new release records if they do not already
exist in the database.

Key functionalities include:
    - **Concurrent Updating/Inserting**: Designed to work with `ProcessPoolExecutor` to
      perform update and insert operations concurrently, speeding up the
      processing of large numbers of releases.
    - **Batch Processing**: Processes a list of release data (`bulk_updates`)
      in a single run, minimizing database interactions.
    - **Database Transactions**: Uses `offline_transaction` to ensure that
      each update or insert operation is atomic, maintaining data integrity.
    - **Error Handling**: Implements error handling using `try...except` blocks
      to catch `NotFoundError` and `DatabaseError` exceptions and handle them
      appropriately.
    - **Release Access**: Uses `ReleaseRepository` to access and update or
      insert release data.
    - **Change Detection**: Uses `DeepDiff` to detect changes between the
      existing release and the new data, only updating fields that have changed.
    - **Process Initialization**: Handles the initialization of the database
      helper in each worker process when concurrency is enabled.
    - **Logging**: Provides detailed logging of the update and insertion
      process, including the number of updated and inserted releases.

The `update_releases_worker` function interacts with the following components:
    - `OfflineDatabaseHelper`: For managing database connections and
      initialization in a concurrent environment.
    - `ReleaseRepository`: For database operations related to releases.
    - `Release`: The domain object representing a release.
    - `ReleaseTable`: For accessing the release table definition.
    - `DeepDiff`: For comparing the existing release with the new data.
    - `offline_transaction`: A decorator for managing database transactions.
    - `OfflineDatabaseManager`: For managing database concurrency settings.
    - `logging`: For logging operations.
    - `NotFoundError`: Used for handling the not found exception.
    - `DatabaseError`: Used for handling the database exception.
    - `LOGGING_TRACE`: Used to check if trace logging is activated.

The module utilizes `logging` for logging operations, `sqlalchemy.exc.DatabaseError` for database
related exception and `pprint` for pretty print the diff between releases. It
interacts with `musigree.offline.database` for database related operations,
and `musigree.offline.offline_database_manager` for managing concurrency.
"""
import asyncio
import logging
import pprint
from typing import Any

from deepdiff import DeepDiff

from musigree.exceptions import DatabaseError, NotFoundError
from musigree.library.fields.entity_id import to_entity_label_internal_id
from musigree.offline.database.release_repository import ReleaseRepository
from musigree.offline.database.release_table import ReleaseTable
from musigree.offline.database.offline_transaction import offline_transaction
from musigree.offline.domain.release import Release
from musigree.logging_config import LOGGING_TRACE
from musigree.offline.offline_database_manager import OfflineDatabaseManager

log = logging.getLogger(__name__)
"""
The logger for the update_releases_worker module.
"""


async def update_releases_worker_async(bulk_updates: list[dict[str, Any]], processed_count: int,
                                       _total_count: int) -> None:
    """
    A worker function for updating or inserting release records.

    This function is designed to work with `ProcessPoolExecutor` to perform concurrent
    update and insert operations on release records in the Musigree offline system.

    Key functionalities include:
        - **Concurrent Processing**: Designed for use with `ProcessPoolExecutor`.
        - **Batch Processing**: Processes multiple release records in a single execution.
        - **Database Transactions**: Uses `offline_transaction` for data integrity.
        - **Error Handling**: Handles `NotFoundError` and `DatabaseError` exceptions.
        - **Change Detection**: Uses `DeepDiff` to detect and update only changed fields.
        - **Process Initialization**: Initializes database helper for concurrent processing.
        - **Logging**: Provides detailed logging of processing progress and errors.

    The function interacts with the following components:
        - `OfflineDatabaseHelper`: For database connection management.
        - `ReleaseRepository`: For database operations on releases.
        - `Release`: The domain object representing a release.
        - `ReleaseTable`: For accessing release table schema.
        - `DeepDiff`: For detecting changes between releases.
        - `offline_transaction`: For managing database transactions.

    Args:
        bulk_updates (list[dict[str, Any]]): A list of release data to update or insert.
        processed_count (int): The number of releases processed so far.
        _total_count (int): The total number of releases to process (unused).
    Raises:
        NotFoundError: When a release is not found in the database during update.
        DatabaseError: When there's an error with database operations.
    """

    updated_count = 0
    """Counter for the number of releases updated."""
    inserted_count = 0
    """Counter for the number of releases inserted."""

    async with offline_transaction():
        """Ensure that database operations are performed within a transaction."""

        release_repository = ReleaseRepository()
        """Instance of ReleaseRepository for database operations on releases."""

        for data in bulk_updates:
            """Iterate over the release data."""
            updated_release = Release(**data)

            # If it has got an id, change it for an internal id
            if updated_release.labels:
                for entry in updated_release.labels:
                    if "id" in entry:
                        id_ = entry["id"]
                        entry["id"] = to_entity_label_internal_id(id_)

            if updated_release.companies:
                for entry in updated_release.companies:
                    if "id" in entry:
                        id_ = entry["id"]
                        entry["id"] = to_entity_label_internal_id(id_)

            """Create a new Release object from the data."""
            try:
                """Attempt to update the release."""
                if LOGGING_TRACE:
                    """Log if trace logging is enabled."""
                    log.debug(f"update: {updated_release.release_id}")

                db_release = await release_repository.get_by_id(updated_release.release_id)
                """Retrieve the existing release from the database."""

                is_changed = False
                """Flag to check if any changes were made."""
                update_payload: dict[str, Any] = {}
                """Dictionary to store the update payload."""

                if db_release.title != updated_release.title:
                    """Check if the release title has changed."""
                    db_release.title = updated_release.title
                    update_payload[ReleaseTable.title.key] = db_release.title
                    """Update the release title."""
                    is_changed = True
                    """Set the changed flag."""

                # Update metadata
                differences = DeepDiff(
                    db_release,
                    updated_release,
                    exclude_paths=[
                        "dirty_fields",
                        "_dirty",
                    ],
                    ignore_numeric_type_changes=True,
                )
                """Compare the release metadata."""
                diff = pprint.pformat(differences)
                """Format the diff for logging."""
                if diff != "{}":
                    """If there are any differences."""
                    if LOGGING_TRACE:
                        """Log the differences if trace logging is enabled."""
                        log.debug(f"diff: {diff}")

                    # Update all fields that have changed
                    update_fields: dict[str, Any] = {
                        ReleaseTable.artists.key: updated_release.artists,
                        ReleaseTable.companies.key: updated_release.companies,
                        ReleaseTable.country.key: updated_release.country,
                        ReleaseTable.extra_artists.key: updated_release.extra_artists,
                        ReleaseTable.formats.key: updated_release.formats,
                        ReleaseTable.genres.key: updated_release.genres,
                        ReleaseTable.identifiers.key: updated_release.identifiers,
                        ReleaseTable.labels.key: updated_release.labels,
                        ReleaseTable.master_id.key: updated_release.master_id,
                        ReleaseTable.notes.key: updated_release.notes,
                        ReleaseTable.release_date.key: updated_release.release_date,
                        ReleaseTable.styles.key: updated_release.styles,
                        ReleaseTable.tracklist.key: updated_release.tracklist,
                    }
                    """Update payload for metadata fields."""
                    update_payload.update(update_fields)
                    """Add metadata fields to the update payload."""
                    is_changed = True
                    """Set the changed flag."""

                if is_changed:
                    """If any changes were made."""
                    await release_repository.update(updated_release.release_id, update_payload)
                    """Update the release in the database."""
                    await release_repository.commit()
                    """Commit the transaction."""
                    updated_count += 1
                    """Increment the updated counter."""

            except NotFoundError:
                """If the release is not found in the database."""
                if LOGGING_TRACE:
                    """Log if trace logging is enabled."""
                    log.debug(f"insert: {updated_release.release_id}")

                await release_repository.create(updated_release)
                """Insert the new release into the database."""
                inserted_count += 1
                """Increment the inserted counter."""

            except DatabaseError as e:
                """If there's a database error."""
                log.error(f"Database error: {e}")
                """Log the database error."""
                raise e

    log.info(
        f"worker updated {updated_count} inserted {inserted_count} releases total"
        f" processed {processed_count}"
    )
    """Log the number of updated and inserted releases."""


def update_releases_worker(bulk_updates: list[dict[str, Any]], current_total: int, total_count: int) -> None:
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

    loop.run_until_complete(update_releases_worker_async(bulk_updates, current_total, total_count))

    OfflineDatabaseManager.dispose_offline_database_async_engine(loop)
    """Close the database engine."""
