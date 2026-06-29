"""
This module defines the main entry point for the Musigree data loader application.

It orchestrates the setup of various components, including logging, caching,
and database connections, and then initiates the data loading and transfer processes
using Luigi tasks.

The loader is responsible for:
    - Setting up logging for the application.
    - Initializing and managing the cache system.
    - Setting up connections to both the offline and runtime databases.
    - Defining and executing Luigi tasks for data loading and transfer.
    - Registering cleanup functions to be run when the application exits.
    - Running the loader process between specified dates.
"""

import asyncio
import datetime
import logging
import sys
from collections.abc import Coroutine
from functools import partial
from pathlib import Path
from typing import Any, cast

import asyncio_atexit  # type: ignore
import luigi
from luigi.execution_summary import LuigiRunResult
from sqlalchemy.exc import OperationalError

from musigree.config import (
    PostgresDevelopmentConfiguration,
)
from musigree.constants import (
    DISCOGS_DATA,
    ROLES_DATA,
    INSTRUMENTS_DATA,
    TEXT_SEARCH_DATA,
    TEXT_SEARCH_FILENAME,
    ALL_OFFLINE_DATABASE_TABLE_NAMES,
    ENTITY_DETAILS_DATA,
    ENTITY_DETAILS_FILENAME,
)
from musigree.library.cache.cache_manager import CacheManager
from musigree.logging_config import setup_logging, shutdown_logging
from musigree.offline.data_access_layer.offline_role_data_access import OfflineRoleDataAccess
from musigree.offline.loader.loader_master import LoaderMaster
from musigree.offline.loader.loader_role import LoaderRole
from musigree.offline.loader.loader_tasks import LoaderSetupTask
from musigree.offline.offline_database import ReleaseTable, EntityTable, RelationTable
from musigree.offline.offline_database_manager import OfflineDatabaseManager
from musigree.utils import log_banner

log = logging.getLogger(__name__)


async def load_offline_tables(data_directory: Path, date: str, is_bulk_inserts: bool) -> None:
    """
    Loads data into the offline tables.

    This method orchestrates the loading process by executing a series of stages.

    Args:
        data_directory: The directory containing the data files.
        date: The date of the data to load.
        is_bulk_inserts: Whether to use bulk inserts.
    """
    log.info("Load offline tables")
    stages = get_load_offline_table_stages(data_directory, date, is_bulk_inserts)
    for stage in stages:
        await stage()
    log.info("Load offline tables done.")


async def load_offline_table_stage(
    data_directory: Path, date: str, is_bulk_inserts: bool, stage: int
) -> None:
    """
    Loads a specific stage of the data loading process.

    Args:
        data_directory: The directory containing the data files.
        date: The date of the data to load.
        is_bulk_inserts: Whether to use bulk inserts.
        stage: The index of the stage to execute.
    """
    stages = get_load_offline_table_stages(data_directory, date, is_bulk_inserts)
    log.debug(f"Run offline stage: {stage}")
    await stages[stage]()


def get_load_offline_table_stages(
    data_directory: Path, date: str, is_bulk_inserts: bool
) -> list[partial[Coroutine[Any, Any, None]]]:
    """
    Gets the list of stages for loading data into the tables.

    Args:
        data_directory: The directory containing the data files.
        date: The date of the data to load.
        is_bulk_inserts: Whether to use bulk inserts.

    Returns:
        list[partial]: A list of partial functions representing the loading stages.
    """
    from musigree.offline.loader.loader_entity import LoaderEntity
    from musigree.offline.loader.loader_relation import LoaderRelation
    from musigree.offline.loader.loader_release import LoaderRelease

    assert OfflineDatabaseManager.offline_database_helper is not None, (
        "OfflineDatabaseManager.offline_database_helper must be initialized before calling get_load_offline_table_stages()"
    )
    assert OfflineDatabaseManager.offline_database_helper.offline_async_engine is not None, (
        "OfflineDatabaseManager.offline_database_helper.offline_async_engine must be initialized before calling get_load_offline_table_stages()"
    )

    is_full = OfflineDatabaseManager.offline_database_helper.is_vacuum_full()
    is_analyze = OfflineDatabaseManager.offline_database_helper.is_vacuum_analyze()
    discogs_data_directory = data_directory / DISCOGS_DATA
    roles_directory = data_directory / ROLES_DATA
    instruments_directory = data_directory / INSTRUMENTS_DATA
    text_search_path = data_directory / TEXT_SEARCH_DATA / TEXT_SEARCH_FILENAME
    entity_details_path = data_directory / ENTITY_DETAILS_DATA / ENTITY_DETAILS_FILENAME
    stages: list[partial[Coroutine[Any, Any, None]]] = [
        partial(LoaderRole.load_roles_into_database, roles_directory, instruments_directory),
        partial(OfflineRoleDataAccess.load_all_roles_into_cache),
        partial(LoaderEntity.loader_entity_pass_one, discogs_data_directory, date, is_bulk_inserts),
        # Database cleanup
        partial(
            OfflineDatabaseManager.offline_database_helper.vacuum,
            EntityTable.__tablename__,
            is_full,
            is_analyze,
            OfflineDatabaseManager.offline_database_helper.offline_async_engine,
        ),
        partial(
            LoaderRelease.loader_release_pass_one,
            discogs_data_directory,
            date,
            is_bulk_inserts,
        ),
        partial(
            LoaderMaster.loader_master_pass_one,
            discogs_data_directory,
            date,
            is_bulk_inserts,
        ),
        partial(
            OfflineDatabaseManager.offline_database_helper.vacuum,
            ReleaseTable.__tablename__,
            is_full,
            is_analyze,
            OfflineDatabaseManager.offline_database_helper.offline_async_engine,
        ),
        # Relsolve entity ids
        partial(LoaderEntity.loader_entity_pass_two),
        # Resolve entity references within the release data
        partial(LoaderRelease.loader_release_pass_two),
        # Build the relations
        partial(LoaderRelation.loader_relation_pass_one),
        # Database cleanup
        partial(
            OfflineDatabaseManager.offline_database_helper.vacuum,
            EntityTable.__tablename__,
            is_full,
            is_analyze,
            OfflineDatabaseManager.offline_database_helper.offline_async_engine,
        ),
        partial(
            OfflineDatabaseManager.offline_database_helper.vacuum,
            ReleaseTable.__tablename__,
            is_full,
            is_analyze,
            OfflineDatabaseManager.offline_database_helper.offline_async_engine,
        ),
        partial(
            OfflineDatabaseManager.offline_database_helper.vacuum,
            RelationTable.__tablename__,
            is_full,
            is_analyze,
            OfflineDatabaseManager.offline_database_helper.offline_async_engine,
        ),
        # Update entity relation counts
        partial(LoaderEntity.loader_entity_pass_three),
        # Database cleanup
        partial(
            OfflineDatabaseManager.offline_database_helper.vacuum,
            EntityTable.__tablename__,
            is_full,
            is_analyze,
            OfflineDatabaseManager.offline_database_helper.offline_async_engine,
        ),
        partial(
            OfflineDatabaseManager.offline_database_helper.vacuum,
            ReleaseTable.__tablename__,
            is_full,
            is_analyze,
            OfflineDatabaseManager.offline_database_helper.offline_async_engine,
        ),
        partial(
            OfflineDatabaseManager.offline_database_helper.vacuum,
            RelationTable.__tablename__,
            is_full,
            is_analyze,
            OfflineDatabaseManager.offline_database_helper.offline_async_engine,
        ),
        # Create text search and entity details indexes
        partial(LoaderEntity.loader_create_text_search_index, text_search_path),
        partial(LoaderEntity.loader_create_text_search_tokens, text_search_path),
        partial(LoaderEntity.loader_create_entity_details_index, entity_details_path),
        # Process entity metadata profile embedded links
        partial(LoaderEntity.loader_entity_pass_four),
    ]
    return stages


async def shutdown_offline_loader() -> None:
    """
    Shuts down the offline loader application.

    This function is called when the application is being shut down. It
    performs cleanup tasks such as closing database connections, shutting
    down the cache, and shutting down logging.
    """
    # Logging may have been shutdown automatically before this point, so we need to reinitialize it again
    setup_logging()
    log.info("######## OFFLINE LOADER SHUTDOWN START ########")
    try:
        if OfflineDatabaseManager.offline_database_helper is not None:
            await OfflineDatabaseManager.shutdown_database()
    except OperationalError:
        pass

    await CacheManager.clear_cache()
    await CacheManager.shutdown_cache()

    log.info("######## OFFLINE LOADER SHUTDOWN DONE ########")
    shutdown_logging()


async def _finalize_offline_loader_before_loop_close() -> None:
    """
    Cancel loader tasks and release resources while the event loop is still usable.

    Runner.close() runs asyncio_atexit during loop.close(); a second SIGINT during
    engine.dispose() then corrupts shutdown. Running cleanup here (with unregister)
    avoids that path and drains pending tasks first.
    """
    loop = asyncio.get_running_loop()
    current = asyncio.current_task()
    pending = [t for t in asyncio.all_tasks(loop) if t is not current and not t.done()]
    for task in pending:
        task.cancel()
    if pending:
        await asyncio.gather(*pending, return_exceptions=True)
    try:
        await shutdown_offline_loader()
    except KeyboardInterrupt:
        log.warning("Offline loader shutdown interrupted (database may not be fully closed)")
    except asyncio.CancelledError:
        raise


def offline_loader_main() -> None:
    """
    The main function for the Musigree offline data loader application.

    This function orchestrates the setup of the application environment, including:
        1. Configuring logging.
        2. Displaying application information in the log.
        3. Setting up the cache system.
        4. Establishing connections to the offline and runtime databases.
        5. Registering functions for graceful shutdown.
        6. Defining and executing the Luigi tasks for data loading and transfer.
    """
    setup_logging()

    console_handler = logging.getHandlerByName("console_handler")
    if console_handler is not None:
        console_handler.setLevel(logging.DEBUG)

    log_banner()

    offline_config = PostgresDevelopmentConfiguration()
    log.info(f"Using {offline_config.__class__.__name__} for offline database")

    with asyncio.Runner() as runner:
        # Register shutdown
        loop = runner.get_loop()
        asyncio_atexit.register(shutdown_offline_loader, loop=loop)

        try:
            # Setup Cache
            try:
                runner.run(CacheManager.setup_and_clear_cache(offline_config))
            except RuntimeError as exc:
                log.error("%s", exc)
                sys.exit(1)

            runner.run(OfflineDatabaseManager.setup_database(offline_config))

            assert OfflineDatabaseManager.offline_database_helper is not None, (
                "offline_database_helper must be initialized before calling initialize()"
            )
            runner.run(
                OfflineDatabaseManager.offline_database_helper.create_tables(
                    ALL_OFFLINE_DATABASE_TABLE_NAMES
                )
            )
            # Load roles, may be empty if no roles in offline_database yet
            runner.run(OfflineRoleDataAccess.load_all_roles_into_cache())

            # Get the current date
            now_date = datetime.datetime.now()

            # Run the loader process between these dates
            start_date = datetime.date(2026, 3, 1)
            end_date = datetime.date(now_date.year, now_date.month, 1)

            offline_data_directory: str = str(offline_config.DATA_DIR)
            tasks = [
                LoaderSetupTask(
                    data_directory=offline_data_directory, start_date=start_date, end_date=end_date
                ),
            ]
            luigi_run_result = cast(
                LuigiRunResult,
                luigi.build(
                    tasks,
                    detailed_summary=True,
                    local_scheduler=True,
                    log_level="WARNING",
                ),
            )
            log.info(luigi_run_result.summary_text)
        finally:
            asyncio_atexit.unregister(shutdown_offline_loader, loop=loop)
            try:
                runner.run(_finalize_offline_loader_before_loop_close())
            except KeyboardInterrupt:
                log.warning(
                    "Offline loader finalize interrupted; proceeding with event loop shutdown"
                )


if __name__ == "__main__":
    offline_loader_main()
