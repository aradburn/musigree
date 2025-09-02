"""
This module defines the `process_relation_pass_one_worker` function, which is a worker
function responsible for processing relations in the first pass of the data loading
process in the Musigree offline system.

It is designed to be used with `concurrent.futures.ProcessPoolExecutor` to enable
concurrent processing of relations, improving the efficiency of the data loading
process. The function handles the creation of relation records and relation-release-year
mappings from release data.

Key functionalities include:
    - **Concurrent Processing**: Designed to work with `ProcessPoolExecutor` to
      perform processing operations concurrently, speeding up the processing of
      large numbers of releases.
    - **Relation Creation**: Creates relation records from release data, handling
      duplicate entries gracefully.
    - **Relation-Release-Year Mapping**: Creates mappings between relations,
      releases, and years for temporal analysis.
    - **Database Transactions**: Uses `offline_transaction` to ensure that
      each processing operation is atomic, maintaining data integrity.
    - **Error Handling**: Implements comprehensive error handling for database
      operations, including retry logic for individual records.
    - **Batch Processing**: Processes records in batches to optimize database
      performance.
    - **Process Initialization**: Handles the initialization of the database
      helper in each worker process when concurrency is enabled.
    - **Logging**: Provides detailed logging of the processing progress.

The `process_relation_pass_one_worker` function interacts with the following components:
    - `OfflineDatabaseHelper`: For managing database connections and
      initialization in a concurrent environment.
    - `RelationRepository`: For database operations related to relations.
    - `RelationReleaseYearRepository`: For database operations related to
      relation-release-year mappings.
    - `ReleaseRepository`: For database operations related to releases.
    - `RelationDataAccess`: For extracting relation data from releases.
    - `RoleCache`: For role name to ID lookups.
    - `offline_transaction`: A decorator for managing database transactions.
    - `OfflineDatabaseManager`: For managing database concurrency settings.
    - `LoaderBase`: For accessing batch size constants.
    - `logging`: For logging operations.

The module utilizes `logging` for logging operations and handles various database
exceptions including `DatabaseError`, `IntegrityError`, and `OperationalError`.
"""
import asyncio
import logging
import multiprocessing

from sqlalchemy.exc import OperationalError, IntegrityError

from musigree.exceptions import NotFoundError, DatabaseError
from musigree.offline.data_access_layer.relation_data_access import RelationDataAccess
from musigree.offline.database.relation_repository import RelationRepository
from musigree.offline.database.release_repository import ReleaseRepository
from musigree.offline.database.offline_transaction import offline_transaction
from musigree.offline.domain.relation import RelationUncommitted
from musigree.offline.domain.release import Release
from musigree.offline.loader.loader_base import LoaderBase
from musigree.offline.offline_database_manager import OfflineDatabaseManager

log = logging.getLogger(__name__)
"""
The logger for the worker relation pass one module.
"""


async def process_relation_pass_one_worker_async(release_ids: list[int], current_total: int, total_count: int) -> None:
    """
    Worker function for processing relations in the first pass.

    This function is designed to be used with ProcessPoolExecutor to perform
    concurrent processing of relations from release data.

    Args:
        release_ids (list[int]): A list of release IDs to process.
        current_total (int): The number of releases processed so far.
        total_count (int): The total number of releases to process.

    Raises:
        DatabaseError: If there's an error during database operations.
        OperationalError: If there's an operational error during database operations.
    """

    proc_name = multiprocessing.current_process().name
    """Get the name of the current process."""

    count = current_total
    """Counter for the number of releases processed."""
    end_count = count + len(release_ids)
    """The total number of releases to process."""

    async with offline_transaction():
        for release_id in release_ids:
            """Iterate over the release IDs."""
            await process_release(release_id)

            count += 1
            """Increment the processed counter."""

            if count % LoaderBase.BULK_REPORTING_SIZE == 0 and not count == end_count:
                """Log every BULK_REPORTING_SIZE."""
                log.debug(f"[{proc_name}] processed {count} of {total_count}")

    log.info(f"[{proc_name}] processed {count} of {total_count}")
    """Log the total number of releases processed."""


async def create_relation_bulk(
    relation_repository: RelationRepository,
    relations: list[RelationUncommitted],
) -> None:
    """
    Creates relations in bulk with error handling and retry logic.

    Args:
        relation_repository (RelationRepository): The repository for relation operations.
        relations (list[RelationUncommitted]): The list of relations to create.

    Raises:
        OperationalError: If there's an operational error during database operations.
    """
    # save, do nothing if already exists
    try:
        """Attempt to create relations in bulk."""
        await relation_repository.create_bulk(
            relations, on_conflict_do_nothing=True
        )
        """Create the relations."""
        await relation_repository.commit()
        """Commit the transaction."""
        # log.debug(f"create_bulk ok")
    except DatabaseError:
        """Handle database errors."""
        await relation_repository.rollback()
        """Rollback the transaction."""
    except IntegrityError:
        """Handle integrity errors."""
        await relation_repository.rollback()
        # log.debug(f"IntegrityError in relation worker process")
        """Rollback the transaction."""
        for relation in relations:
            """Try to create relations one by one."""
            try:
                """Attempt to create individual relation."""
                await relation_repository.create(
                    relation, on_conflict_do_nothing=True
                )
                """Create the relation."""
                await relation_repository.commit()
                """Commit the transaction."""
                # log.debug(f"create single ok")
            except DatabaseError as ex:
                """Handle database errors."""
                await relation_repository.rollback()
                """Rollback the transaction."""
                log.exception(ex)
            except IntegrityError:
                log.debug("IntegrityError in relation worker process individual")
                """Handle integrity errors."""
                await relation_repository.rollback()
                """Rollback the transaction."""
    except OperationalError as e:
        """Handle operational errors."""
        await relation_repository.rollback()
        """Rollback the transaction."""
        log.debug("OperationalError in worker process")
        raise e


async def process_release(release_id: int) -> None:
    """Async function to handle relation processing."""
    """Ensure that database operations are performed within a transaction."""
    release_repository = ReleaseRepository()
    """Instance of ReleaseRepository for database operations on releases."""
    relation_repository = RelationRepository()
    """Instance of RelationRepository for database operations on relations."""

    release: Release | None = None
    """Initialize release variable."""
    relations: list[RelationUncommitted] = []
    try:
        """Attempt to process the release."""
        release = await release_repository.get_by_id(release_id)
        """Retrieve the release."""
        relations = RelationDataAccess.from_release(release)
        """Extract relations from the release."""
    except NotFoundError:
        """Handle the case where the release is not found."""
        log.debug(
            f"process_relation_pass_one_worker release_id not found: {release_id}"
        )
    except DatabaseError:
        """Handle database errors."""
        log.error("Error in process_relation_pass_one_worker")
        raise

    if len(relations) > 0 and release is not None:
        """If relations were found and release is valid."""
        await create_relation_bulk(
            relation_repository,
            relations,
        )
        """Create the relations in bulk."""


def process_relation_pass_one_worker(release_ids: list[int], current_total: int, total_count: int) -> None:
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

    loop.run_until_complete(process_relation_pass_one_worker_async(release_ids, current_total, total_count))

    OfflineDatabaseManager.dispose_offline_database_async_engine(loop)
    """Close the database engine."""
