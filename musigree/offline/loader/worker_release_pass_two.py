"""
This module defines the `WorkerReleasePassTwo` class, which is a worker
process responsible for processing release records in the second pass of the
data loading process in the Musigree offline system.

It utilizes `multiprocessing` to enable concurrent processing of releases,
improving the efficiency of the data loading process. The
`WorkerReleasePassTwo` handles the resolution of entity references (e.g.,
artists, labels, companies) within the release data.

Key functionalities include:
    - **Concurrent Processing**: Employs `multiprocessing.Process` to perform
      processing operations concurrently, speeding up the processing of
      large numbers of releases.
    - **Reference Resolution**: Resolves references to entities within a
      release's data, ensuring data consistency and correctness.
    - **Database Transactions**: Uses `offline_transaction` to ensure that
      each processing operation is atomic, maintaining data integrity.
    - **Error Handling**: Implements error handling using `try...except` blocks
      to catch `DatabaseError` exceptions and log them.
    - **Entity and Release Access**: Uses `EntityRepository` and
      `ReleaseRepository` to access and update entity and release data.
    - **Process Initialization**: Handles the initialization of the database
      helper in each worker process when concurrency is enabled.
    - **Logging**: Provides detailed logging of the processing, including
      the number of releases processed, any database errors encountered, and
      which releases are skipped if no changes are needed.
    - **Batch processing**: Process a list of release ids at once.
    - **Reporting**: Log every `BULK_REPORTING_SIZE` elements.

The `WorkerReleasePassTwo` class interacts with the following components:
    - `multiprocessing.Process`: The base class for creating worker processes.
    - `OfflineDatabaseHelper`: For managing database connections and
      initialization in a concurrent environment.
    - `EntityRepository`: For database operations related to entities.
    - `ReleaseRepository`: For database operations related to releases.
    - `EntityDataAccess`: For performing entity-specific data access operations,
      such as resolving references.
    - `offline_transaction`: A decorator for managing database transactions.
    - `OfflineDatabaseManager`: For managing database concurrency settings.
    - `LoaderBase`: For accessing the `BULK_REPORTING_SIZE` constant.
    - `ReleaseTable`: For accessing the release table definition.
    - `logging`: For logging operations.
    - `DatabaseError`: Used for handling the database exception.
    - `LOGGING_TRACE`: Used to check if trace logging is activated.

The module utilizes `logging` for logging operations, `multiprocessing` for
process management, and `sqlalchemy.exc.DatabaseError` for database
related exception. It interacts with `musigree.offline.database` for database
related operations and `musigree.offline.offline_database_manager` for managing
concurrency.
"""

import asyncio
import logging
import multiprocessing

from sqlalchemy.exc import DatabaseError

from musigree.logging_config import LOGGING_TRACE
from musigree.offline.database.entity_repository import EntityRepository
from musigree.offline.database.offline_database_helper import OfflineDatabaseHelper
from musigree.offline.offline_database_manager import OfflineDatabaseManager
from musigree.offline.database.offline_transaction import offline_transaction
from musigree.offline.database.release_repository import ReleaseRepository
from musigree.offline.database.release_table import ReleaseTable
from musigree.offline.data_access_layer.entity_data_access import EntityDataAccess
from musigree.offline.loader.loader_base import LoaderBase

log = logging.getLogger(__name__)


class WorkerReleasePassTwo(multiprocessing.Process):
    """
    A worker process for processing release records in the second pass.

    This class extends `multiprocessing.Process` to perform concurrent
    processing of releases, resolving references to entities.
    """

    def __init__(self, release_ids: list[int], current_total: int, total_count: int):
        """
        Initializes the WorkerReleasePassTwo.

        Args:
            release_ids (list[int]): A list of release IDs to process.
            current_total (int): The number of releases processed so far.
            total_count (int): The total number of releases to process.
        """
        super().__init__()
        """Call the constructor of the parent class."""
        self.release_ids = release_ids
        """The list of release IDs to process."""
        self.current_total = current_total
        """The number of releases processed so far."""
        self.total_count = total_count
        """The total number of releases to process."""

    def run(self):
        """
        Executes the release processing logic.

        This method performs the following steps:
            1. Initializes the database helper if concurrency is enabled.
            2. Iterates through the list of release IDs.
            3. For each ID, retrieves the release and resolves references.
            4. Updates the release with the resolved references.
            5. Handles `DatabaseError` exceptions during the process.
            6. Logs the progress of the processing.
        """
        proc_name = self.name
        """Get the name of the current process."""

        count = self.current_total
        """Counter for the number of releases processed."""
        end_count = count + len(self.release_ids)
        """The total number of releases to process."""

        if OfflineDatabaseManager.get_concurrency_count() > 1:
            """Check if concurrency is enabled."""
            OfflineDatabaseHelper.initialize()
            """Initialize the database helper."""

        for id_ in self.release_ids:
            """Iterate over the release IDs."""
            async def process_release() -> None:
                async with offline_transaction():
                    """Ensure that database operations are performed within a transaction."""
                    entity_repository = EntityRepository()
                    """Instance of EntityRepository for database operations on entities."""
                    release_repository = ReleaseRepository()
                    """Instance of ReleaseRepository for database operations on releases."""
                    try:
                        """Attempt to process the release."""
                        await self.loader_pass_two_single(
                            entity_repository=entity_repository,
                            release_repository=release_repository,
                            id_=id_,
                            annotation=proc_name,
                        )
                        """Process the release."""
                    except DatabaseError as e:
                        """Handle potential database errors."""
                        log.exception(
                            "Database Error in WorkerReleasePassTwo worker", exc_info=True
                        )
                        raise e
            
            # Run the async function
            asyncio.run(process_release())

            count += 1
            """Increment the processed counter."""
            if count % LoaderBase.BULK_REPORTING_SIZE == 0 and not count == end_count:
                """Log every BULK_REPORTING_SIZE."""
                log.debug(f"[{proc_name}] processed {count} of {self.total_count}")

        log.info(f"[{proc_name}] processed {count} of {self.total_count}")
        """Log the total number of releases processed."""

    @staticmethod
    async def loader_pass_two_single(
        *,
        entity_repository: EntityRepository,
        release_repository: ReleaseRepository,
        id_,
        annotation="",
    ) -> None:
        """
        Processes a single release record in the second pass.

        This method resolves references to entities within the given
        release's data (e.g., artists, labels, companies).

        Args:
            entity_repository (EntityRepository): The repository for entity
                operations.
            release_repository (ReleaseRepository): The repository for release
                operations.
            id_: The ID of the release to process.
            annotation (str, optional): An annotation for logging purposes.
                Defaults to "".
        """
        release = await release_repository.get_by_id(id_)
        """Retrieve the release."""
        changed = EntityDataAccess.resolve_release_references(
            entity_repository, release
        )
        """Resolve entity references."""
        if changed:
            """If any changes were made to the release."""
            if LOGGING_TRACE:
                """Log if trace logging is enabled."""
                log.debug(
                    f"Release (Pass 2) [{annotation}]\t"
                    + f"          (id:{release.release_id}): {release.title}"
                )
            await release_repository.update(
                id_,
                {
                    ReleaseTable.labels.key: release.labels,
                    ReleaseTable.companies.key: release.companies,
                },
            )
            """Update the release in the database."""
            await release_repository.commit()
            """Commit the transaction."""
        elif LOGGING_TRACE:
            """Log if trace logging is enabled."""
            log.debug(
                f"Release (Pass 2) [{annotation}]\t"
                + f"[SKIPPED] (id:{release.release_id}): {release.title}"
            )
