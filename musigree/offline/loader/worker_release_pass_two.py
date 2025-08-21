"""
This module defines the `process_release_pass_two_worker` function, which is a worker
function responsible for processing release records in the second pass of the
data loading process in the Musigree offline system.

It is designed to be used with `concurrent.futures.ProcessPoolExecutor` to enable
concurrent processing of releases, improving the efficiency of the data loading
process. The function handles the resolution of entity references (e.g., artists,
labels, companies) within the release data.

Key functionalities include:
    - **Concurrent Processing**: Designed to work with `ProcessPoolExecutor` to
      perform processing operations concurrently, speeding up the processing of
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

The `process_release_pass_two_worker` function interacts with the following components:
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

The module utilizes `logging` for logging operations and `sqlalchemy.exc.DatabaseError`
for database related exception. It interacts with `musigree.offline.database` for
database related operations and `musigree.offline.offline_database_manager` for
managing concurrency.
"""

import asyncio
import logging
import multiprocessing

from musigree.exceptions import DatabaseError
from musigree.offline.database.entity_repository import EntityRepository
from musigree.offline.database.offline_database_helper import OfflineDatabaseHelper
from musigree.offline.offline_database_manager import OfflineDatabaseManager
from musigree.offline.database.offline_transaction import offline_transaction
from musigree.offline.database.release_repository import ReleaseRepository
from musigree.offline.database.release_table import ReleaseTable
from musigree.offline.data_access_layer.entity_data_access import EntityDataAccess
from musigree.offline.loader.loader_base import LoaderBase

log = logging.getLogger(__name__)
"""
The logger for the worker release pass two module.
"""


def process_release_pass_two_worker(
    release_ids: list[int], current_total: int, total_count: int
) -> None:
    """
    Worker function for processing release records in the second pass.

    This function is designed to be used with ProcessPoolExecutor to perform
    concurrent processing of releases, resolving references to entities.

    Args:
        release_ids (list[int]): A list of release IDs to process.
        current_total (int): The number of releases processed so far.
        total_count (int): The total number of releases to process.

    Raises:
        DatabaseError: If there's an error during database operations.
    """

    async def process_releases(_release_ids: list[int]) -> None:
        proc_name = multiprocessing.current_process().name
        """Get the name of the current process."""

        count = current_total
        """Counter for the number of releases processed."""
        end_count = count + len(release_ids)
        """The total number of releases to process."""

        async with offline_transaction():
            for _id in _release_ids:
                """Iterate over the release IDs."""
                await process_release(_id)

                count += 1
                """Increment the processed counter."""
                if (
                    count % LoaderBase.BULK_REPORTING_SIZE == 0
                    and not count == end_count
                ):
                    """Log every BULK_REPORTING_SIZE."""
                    log.debug(f"[{proc_name}] processed {count} of {total_count}")

        log.info(f"[{proc_name}] processed {count} of {total_count}")
        """Log the total number of releases processed."""

    async def process_release(release_id: int) -> None:
        """Ensure that database operations are performed within a transaction."""
        entity_repository = EntityRepository()
        """Instance of EntityRepository for database operations on entities."""
        release_repository = ReleaseRepository()
        """Instance of ReleaseRepository for database operations on releases."""
        try:
            """Attempt to process the release."""
            await worker_pass_two_single(
                entity_repository=entity_repository,
                release_repository=release_repository,
                id_=release_id,
            )
            """Process the release."""
        except DatabaseError as e:
            """Handle potential database errors."""
            log.exception(
                "Database Error in process_release_pass_two_worker", exc_info=True
            )
            raise e

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
        OfflineDatabaseHelper.initialize(loop)
        """Initialize the database helper."""

    loop.run_until_complete(process_releases(release_ids))


async def worker_pass_two_single(
    *,
    entity_repository: EntityRepository,
    release_repository: ReleaseRepository,
    id_: int,
) -> None:
    """
    Processes a single release record in the second pass.

    This function resolves references to entities within the given
    release's data (e.g., artists, labels, companies).

    Args:
        entity_repository (EntityRepository): The repository for entity
            operations.
        release_repository (ReleaseRepository): The repository for release
            operations.
        id_: The ID of the release to process.

    Raises:
        DatabaseError: If there's an error during database operations.
    """
    release = await release_repository.get_by_id(id_)
    """Retrieve the release."""
    changed = await EntityDataAccess.resolve_release_references(
        entity_repository, release
    )
    """Resolve entity references."""

    if changed:
        """If any changes were made to the release."""

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
