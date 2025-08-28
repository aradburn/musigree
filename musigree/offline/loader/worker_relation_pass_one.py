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
from typing import List

from sqlalchemy.exc import OperationalError, IntegrityError

from musigree.exceptions import NotFoundError, DatabaseError
from musigree.library.cache.role_cache import RoleCache
from musigree.offline.data_access_layer.relation_data_access import RelationDataAccess
from musigree.offline.database.relation_release_year_repository import (
    RelationReleaseYearRepository,
)
from musigree.offline.database.relation_repository import RelationRepository
from musigree.offline.database.release_repository import ReleaseRepository
from musigree.offline.database.offline_transaction import offline_transaction
from musigree.offline.domain.relation import RelationUncommitted
from musigree.offline.domain.relation_release_year import (
    RelationReleaseYearUncommitted,
)
from musigree.offline.domain.release import Release
from musigree.offline.loader.loader_base import LoaderBase
from musigree.logging_config import LOGGING_TRACE
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

    relation_release_years: list[RelationReleaseYearUncommitted] = []
    """List to store relation-release-year mappings."""

    async with offline_transaction():
        for release_id in release_ids:
            """Iterate over the release IDs."""
            await process_release(release_id, relation_release_years)

            if len(relation_release_years) >= LoaderBase.BULK_INSERT_BATCH_SIZE:
                """If the batch size is reached."""
                await process_relation_release_years(relation_release_years)
                """Create the mappings in bulk."""
                relation_release_years = []
                """Clear the list."""

            count += 1
            """Increment the processed counter."""

            if count % LoaderBase.BULK_REPORTING_SIZE == 0 and not count == end_count:
                """Log every BULK_REPORTING_SIZE."""
                log.debug(f"[{proc_name}] processed {count} of {total_count}")

        if len(relation_release_years) > 0:
            await process_relation_release_years(relation_release_years)

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

async def to_relation_release_years(
    relation_repository: RelationRepository,
    relation: RelationUncommitted,
    release_id: int,
    year: int | None,
) -> List[RelationReleaseYearUncommitted]:
    """
    Creates relation-release-year mappings for a given relation.

    Args:
        relation_repository (RelationRepository): The repository for relation operations.
        relation (RelationUncommitted): The relation to create mappings for.
        release_id (int): The ID of the release.
        year (int | None): The year of the release.

    Returns:
        List[RelationReleaseYearUncommitted]: The list of relation-release-year mappings.

    Raises:
        OperationalError: If there's an operational error during database operations.
    """
    relation_release_years = []
    """Initialize the list of mappings."""
    try:
        """Attempt to create the mapping."""
        role_id = RoleCache.role_name_to_role_id_lookup[relation.role_name]
        """Get the role ID from the cache."""

        key = {
            "subject": relation.subject,
            "role_id": role_id,
            "object": relation.object,
        }
        """Create the key for the relation lookup."""
        relation_id = await relation_repository.get_id_by_key(key)
        """Get the relation ID."""
        relation_release_year_uncommitted = RelationReleaseYearUncommitted(
            relation_id=relation_id,
            release_id=release_id,
            year=year,
        )
        """Create the mapping."""
        relation_release_years.append(relation_release_year_uncommitted)
        """Add the mapping to the list."""
    except NotFoundError:
        """Handle the case where the relation is not found."""
        await relation_repository.rollback()
        """Rollback the transaction."""
        if LOGGING_TRACE:
            """Log if trace logging is enabled."""
            log.debug("Error cannot find relation")
    except DatabaseError:
        """Handle database errors."""
        await relation_repository.rollback()
        """Rollback the transaction."""
        log.debug("Error cannot find relation")
    except OperationalError as e:
        """Handle operational errors."""
        await relation_repository.rollback()
        """Rollback the transaction."""
        raise e
    return relation_release_years

async def create_relation_release_year_bulk(
    relation_release_year_repository: RelationReleaseYearRepository,
    relation_release_years: List[RelationReleaseYearUncommitted],
) -> None:
    """
    Creates relation-release-year mappings in bulk.

    Args:
        relation_release_year_repository (RelationReleaseYearRepository): The repository for mapping operations.
        relation_release_years (List[RelationReleaseYearUncommitted]): The list of mappings to create.

    Raises:
        OperationalError: If there's an operational error during database operations.
    """
    try:
        """Attempt to create mappings in bulk."""
        await relation_release_year_repository.create_bulk(relation_release_years)
        """Create the mappings."""
        await relation_release_year_repository.commit()
        """Commit the transaction."""
    except DatabaseError:
        """Handle database errors."""
        await relation_release_year_repository.rollback()
        """Rollback the transaction."""
        log.debug("Error cannot create RelationReleaseYear")
    except OperationalError as e:
        """Handle operational errors."""
        await relation_release_year_repository.rollback()
        """Rollback the transaction."""
        raise e

async def process_release(
    release_id: int, _relation_release_years: list[RelationReleaseYearUncommitted]
) -> None:
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

        for relation in relations:
            """Iterate over the relations."""

            # try:
            #     """Attempt to create individual relation."""
            #     await relation_repository.create(relation, on_conflict_do_nothing: bool = True)
            #     """Create the relation."""
            #     await relation_repository.commit()
            #     """Commit the transaction."""
            #     # log.debug(f"create single ok")
            # except DatabaseError as ex:
            #     """Handle database errors."""
            #     await relation_repository.rollback()
            #     """Rollback the transaction."""
            #     log.exception(ex)
            # except IntegrityError:
            #     log.debug(f"IntegrityError in relation worker process individual")
            #     """Handle integrity errors."""
            #     await relation_repository.rollback()
            #     """Rollback the transaction."""

            year = (
                release.release_date.year
                if release.release_date is not None
                and release.release_date.year is not None
                else None
            )
            """Extract the year from the release date."""
            new_relation_release_years = await to_relation_release_years(
                relation_repository=relation_repository,
                relation=relation,
                release_id=release_id,
                year=year,
            )
            """Create relation-release-year mappings."""
            _relation_release_years.extend(new_relation_release_years)
            """Add the mappings to the list."""

async def process_relation_release_years(
    _relation_release_years: list[RelationReleaseYearUncommitted],
) -> None:
    if len(_relation_release_years) > 0:
        """If there are remaining mappings to process."""

        relation_release_year_repository = RelationReleaseYearRepository()
        """Instance of RelationReleaseYearRepository for database operations."""
        await create_relation_release_year_bulk(
            relation_release_year_repository, _relation_release_years
        )
        """Create the remaining mappings in bulk."""

def process_relation_pass_one_worker(release_ids: list[int], current_total: int, total_count: int) -> None:
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

    loop.run_until_complete(process_relation_pass_one_worker_async(release_ids, current_total, total_count))
