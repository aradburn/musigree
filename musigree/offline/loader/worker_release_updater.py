"""
This module defines the `WorkerReleaseUpdater` class, which is a worker
process responsible for updating or inserting release records in the
Musigree offline database.

It utilizes `multiprocessing` to enable concurrent updating and insertion of
releases, improving the efficiency of the data loading process. The
`WorkerReleaseUpdater` handles updating existing release records with new
information, as well as inserting new release records if they do not already
exist in the database.

Key functionalities include:
    - **Concurrent Updating/Inserting**: Employs `multiprocessing.Process` to
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

The `WorkerReleaseUpdater` class interacts with the following components:
    - `multiprocessing.Process`: The base class for creating worker processes.
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

The module utilizes `logging` for logging operations, `multiprocessing` for
process management, `sqlalchemy.exc.DatabaseError` for database
related exception and `pprint` for pretty print the diff between releases. It
interacts with `musigree.offline.database` for database related operations,
and `musigree.offline.offline_database_manager` for managing concurrency.
"""

import logging
import multiprocessing
import pprint
from typing import Any

from deepdiff import DeepDiff

from musigree.exceptions import DatabaseError, NotFoundError
from musigree.library.fields.entity_id import to_entity_label_internal_id
from musigree.offline.database.offline_database_helper import OfflineDatabaseHelper
from musigree.offline.database.release_repository import ReleaseRepository
from musigree.offline.database.release_table import ReleaseTable
from musigree.offline.database.offline_transaction import offline_transaction
from musigree.offline.domain.release import Release
from musigree.logging_config import LOGGING_TRACE
from musigree.offline.offline_database_manager import OfflineDatabaseManager

log = logging.getLogger(__name__)
"""
The logger for the WorkerReleaseUpdater module.
"""


class WorkerReleaseUpdater(multiprocessing.Process):
    """
    A worker process for updating or inserting release records.

    This class extends `multiprocessing.Process` to perform concurrent
    update and insert operations on release records.
    """

    def __init__(self, bulk_updates: list[dict[str, Any]], processed_count: int):
        """
        Initializes the WorkerReleaseUpdater.

        Args:
            bulk_updates (list[dict[str, Any]]): A list of release data to update or insert.
            processed_count (int): The number of releases processed so far.
        """
        super().__init__()
        """Call the constructor of the parent class."""
        self.bulk_updates = bulk_updates
        """The list of release data to update or insert."""
        self.processed_count = processed_count
        """The number of releases processed so far."""

    async def run(self):
        """
        Executes the release update/insert process.

        This method performs the following steps:
            1. Initializes the database helper if concurrency is enabled.
            2. Iterates through the list of release data.
            3. For each release data, starts a database transaction.
            4. Attempts to retrieve the existing release from the database.
            5. If the release exists, compares it with the new data using DeepDiff.
            6. Updates the release with any changed fields.
            7. If the release does not exist, creates a new release.
            8. Handles `NotFoundError` and `DatabaseError` exceptions.
            9. Logs the progress and number of releases updated and inserted.
        """
        proc_name = self.name
        """Get the name of the current process."""
        updated_count = 0
        """Counter for the number of releases updated."""
        inserted_count = 0
        """Counter for the number of releases inserted."""

        if OfflineDatabaseManager.get_concurrency_count() > 1:
            """Check if concurrency is enabled."""
            OfflineDatabaseHelper.initialize()
            """Initialize the database helper."""

        for data in self.bulk_updates:
            """Iterate over the release data."""
            async with offline_transaction():
                """Ensure that database operations are performed within a transaction."""
                release_repository = ReleaseRepository()
                """Instance of ReleaseRepository for database operations on releases."""
                updated_release = Release(**data)

                # If it has got an id, change it for an internal id
                for entry in updated_release.labels:
                    if "id" in entry:
                        id_ = entry["id"]
                        entry["id"] = to_entity_label_internal_id(id_)

                for entry in updated_release.companies:
                    if "id" in entry:
                        id_ = entry["id"]
                        entry["id"] = to_entity_label_internal_id(id_)

                """Create a new Release object from the data."""
                try:
                    """Attempt to update the release."""
                    db_release = await release_repository.get_by_id(updated_release.release_id)
                    """Retrieve the existing release from the database."""

                    differences = DeepDiff(
                        db_release,
                        updated_release,
                        exclude_paths=[
                            # "id",
                            "dirty_fields",
                            "_dirty",
                        ],
                        exclude_regex_paths=[
                            r"root.companies\[\d+\]\['id'\]",
                            r"root.labels\[\d+\]\['id'\]",
                        ],
                        # ignore_numeric_type_changes=True,
                    )
                    """Compare the release data."""
                    diff = pprint.pformat(differences)
                    """Format the diff for logging."""
                    if diff != "{}":
                        """If there are any differences."""
                        # if LOGGING_TRACE:
                        """Log the differences if trace logging is enabled."""
                        log.debug(f"release diff: {diff}")

                        # Update release
                        await release_repository.update(
                            db_release.release_id,
                            {
                                ReleaseTable.release_id.key: updated_release.release_id,
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
                                ReleaseTable.title.key: updated_release.title,
                                ReleaseTable.tracklist.key: updated_release.tracklist,
                            },
                        )
                        """Update the release fields."""

                        await release_repository.commit()
                        """Commit the transaction."""
                        updated_count += 1
                        """Increment the updated count."""
                except NotFoundError:
                    """Handle the case where the release is not found."""
                    if LOGGING_TRACE:
                        """Log if trace logging is enabled."""
                        log.debug(
                            f"New insert in WorkerReleaseUpdater: {updated_release.release_id}"
                        )
                    try:
                        """Attempt to create a new release."""
                        await release_repository.create(updated_release)
                        """Create the release."""
                        await release_repository.commit()
                        """Commit the transaction."""
                        inserted_count += 1
                        """Increment the inserted count."""
                    except DatabaseError as e:
                        """Handle database errors."""
                        log.exception("Database Error in WorkerReleaseUpdater worker")
                        raise e
                except DatabaseError as e:
                    """Handle database errors."""
                    log.exception("Database Error in WorkerReleaseUpdater")
                    raise e

        log.info(
            f"[{proc_name}] processed_count: {self.processed_count}, "
            + f"updated: {updated_count}, inserted: {inserted_count}"
        )
        """Log the number of releases processed, updated, and inserted."""
