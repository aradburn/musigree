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
import atexit
import datetime
import logging
import sys
from collections.abc import Coroutine
from functools import partial
from pathlib import Path
from typing import Any

import luigi
from sqlalchemy.exc import OperationalError

from musigree.config import (
    SqliteDevelopmentConfiguration,
)
from musigree.constants import (
    TEXT_SEARCH_DATA,
    TEXT_SEARCH_FILENAME,
    ALL_OFFLINE_DATABASE_TABLE_NAMES,
    ALL_RUNTIME_DATABASE_TABLE_NAMES,
    ENTITY_DETAILS_DATA,
    ENTITY_DETAILS_FILENAME,
)
from musigree.library.cache.cache_manager import CacheManager
from musigree.logging_config import setup_logging, shutdown_logging
from musigree.offline.data_access_layer.role_data_access import RoleDataAccess
from musigree.offline.offline_database_manager import OfflineDatabaseManager
from musigree.runtime.data_access_layer.runtime_role_data_access import (
    RuntimeRoleDataAccess,
)
from musigree.runtime.runtime_database_manager import RuntimeDatabaseManager
from musigree.transfer.transfer_manager import TransferManager
from musigree.utils import log_banner

log = logging.getLogger(__name__)


async def load_runtime_tables(data_directory: Path, date: str | None) -> None:
    """
    Loads data into the runtime tables.

    This method orchestrates the runtime loading process by executing a series of stages.

    Args:
        data_directory: The directory containing the data files.
        date: The date of the data to load. Used to mark the date as done in the metadata of the data laoding process
    """
    log.info("Load runtime tables")
    stages = get_load_runtime_table_stages(data_directory, date)
    for stage in stages:
        await stage()
    log.info("Load runtime tables done.")


async def load_runtime_table_stage(data_directory: Path, date: str | None, stage: int) -> None:
    """
    Loads a specific stage of the runtime data loading process.

    Args:
        data_directory: The directory containing the data files.
        date: The date of the data to load.
        stage: The index of the stage to execute.
    """
    stages = get_load_runtime_table_stages(data_directory, date)
    log.debug(f"Run runtime stage: {stage}")
    await stages[stage]()


def get_load_runtime_table_stages(
    data_directory: Path, _date: str | None
) -> list[partial[Coroutine[Any, Any, None]]]:
    """
    Gets the list of stages for loading data into the tables.

    Args:
        data_directory: The directory containing the data files.
        _date: The date of the data to load.

    Returns:
        list[partial]: A list of partial functions representing the loading stages.
    """
    assert RuntimeDatabaseManager.runtime_database_helper is not None, (
        "RuntimeDatabaseManager.runtime_database_helper must be initialized before calling get_load_runtime_table_stages()"
    )
    assert RuntimeDatabaseManager.runtime_database_helper.runtime_async_engine is not None, (
        "RuntimeDatabaseManager.runtime_database_helper.runtime_async_engine must be initialized before calling get_load_runtime_table_stages()"
    )

    text_search_path = data_directory / TEXT_SEARCH_DATA / TEXT_SEARCH_FILENAME
    entity_details_path = data_directory / ENTITY_DETAILS_DATA / ENTITY_DETAILS_FILENAME
    stages: list[partial[Coroutine[Any, Any, None]]] = [
        # Load roles into the runtime database
        partial(TransferManager.transfer_role),
        # Load role cache in memory
        partial(RuntimeRoleDataAccess.load_all_roles_into_cache),
        # Load text search index for entities
        partial(TransferManager.transfer_load_text_search_index, text_search_path),
        # Load entities details into memory
        partial(TransferManager.transfer_load_entity_details_index, entity_details_path),
        # Load entities details (countries, genres and styles) into the runtime database
        partial(TransferManager.transfer_entity_details),
        # Load entities into the runtime database
        partial(TransferManager.transfer_entity),
        # Load relations into the runtime database
        partial(TransferManager.transfer_relation),
    ]
    return stages


def shutdown_loader() -> None:
    """
    Shuts down the loader application.

    This function is called when the application is being shut down. It
    performs cleanup tasks such as closing database connections, shutting
    down the cache, and shutting down logging.
    """
    # Logging may have been shutdown automatically before this point, so we need to reinitialize it again
    setup_logging()
    log.info("######## RUNTIME LOADER SHUTDOWN START ########")
    with asyncio.Runner() as runner:
        try:
            runner.run(OfflineDatabaseManager.shutdown_database())
        except OperationalError:
            pass

        try:
            runner.run(RuntimeDatabaseManager.shutdown_database())
        except OperationalError:
            pass

        runner.run(CacheManager.shutdown_cache())

    shutdown_logging()
    log.info("######## RUNTIME LOADER SHUTDOWN DONE ########")


def runtime_loader_main() -> None:
    """
    The main function for the Musigree data loader application.

    This function orchestrates the setup of the application environment, including:
        1. Configuring logging.
        2. Displaying application information in the log.
        3. Setting up the cache system.
        4. Establishing connections to the offline and runtime databases.
        5. Registering functions for graceful shutdown.
        6. Defining and executing the Luigi tasks for data loading and transfer.
    """
    from musigree.transfer.transfer_task import RuntimeLoaderSetupTask

    setup_logging()

    log_banner()

    # log.info(f"DATABASE_HOST: {os.getenv('MUSIGREE_DATABASE_HOST')}")
    # log.info(f"DATABASE_NAME: {os.getenv('MUSIGREE_DATABASE_NAME')}")
    offline_config = SqliteDevelopmentConfiguration()
    runtime_config = SqliteDevelopmentConfiguration()
    log.info(f"Using {offline_config.__class__.__name__} for offline database")
    log.info(f"Using {runtime_config.__class__.__name__} for runtime database")

    # Note reverse order (last in first out), logging is the last to be shutdown
    atexit.register(shutdown_loader)

    with asyncio.Runner() as runner:
        # Setup Cache
        runner.run(CacheManager.setup_cache(offline_config))
        cache = CacheManager.get_cache()
        if cache is None:
            log.error("Cache not set")
            sys.exit()

        log.debug("Clearing cache")
        runner.run(CacheManager.clear())
        runner.run(OfflineDatabaseManager.setup_database(offline_config))
        runner.run(RuntimeDatabaseManager.setup_database(runtime_config))
        runner.close()

    assert OfflineDatabaseManager.offline_database_helper is not None, (
        "offline_database_helper must be initialized before calling initialize()"
    )
    assert RuntimeDatabaseManager.runtime_database_helper is not None, (
        "runtime_database_helper must be initialized before calling initialize()"
    )
    with asyncio.Runner() as runner:
        runner.run(
            OfflineDatabaseManager.offline_database_helper.create_tables(
                ALL_OFFLINE_DATABASE_TABLE_NAMES
            )
        )
        runner.run(
            RuntimeDatabaseManager.runtime_database_helper.drop_tables(
                ALL_RUNTIME_DATABASE_TABLE_NAMES
            )
        )
        runner.run(
            RuntimeDatabaseManager.runtime_database_helper.create_tables(
                ALL_RUNTIME_DATABASE_TABLE_NAMES
            )
        )
        # Load roles, may be empty if no roles in database yet
        runner.run(RoleDataAccess.load_all_roles_into_cache())
        runner.close()

    # Run the loader process between these dates
    start_date = datetime.date(2025, 8, 1)
    # start_date = datetime.date(2023, 10, 1)
    end_date = datetime.date(2025, 8, 1)
    # end_date = datetime.datetime.now()
    runtime_data_directory: str = str(runtime_config.DATA_DIR)
    tasks = [
        RuntimeLoaderSetupTask(
            data_directory=runtime_data_directory, start_date=start_date, end_date=end_date
        ),
    ]
    luigi_run_result = luigi.build(
        tasks,
        detailed_summary=True,
        local_scheduler=True,
        log_level="WARNING",
    )
    log.info(luigi_run_result.summary_text)


if __name__ == "__main__":
    runtime_loader_main()
