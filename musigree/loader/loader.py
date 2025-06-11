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

import atexit
import datetime
import logging
import sys
from functools import partial
from pathlib import Path

import luigi

from musigree.config import (
    PostgresDevelopmentConfiguration,
    SqliteDevelopmentConfiguration,
)
from musigree.constants import (
    DISCOGS_DATA,
    ROLES_DATA,
    INSTRUMENTS_DATA,
    TEXT_SEARCH_DATA,
    TEXT_SEARCH_FILENAME,
)
from musigree.library.cache.cache_manager import CacheManager
from musigree.library.full_text_search.text_search_index import TextSearchIndex
from musigree.logging_config import setup_logging
from musigree.offline.data_access_layer.role_data_access import RoleDataAccess
from musigree.offline.database import ReleaseTable, EntityTable, RelationTable
from musigree.offline.loader.loader_role import LoaderRole
from musigree.offline.loader.loader_tasks import LoaderSetupTask
from musigree.offline.offline_database_manager import OfflineDatabaseManager
from musigree.runtime.data_access_layer.runtime_role_data_access import (
    RuntimeRoleDataAccess,
)
from musigree.runtime.runtime_database.runtime_database_helper import (
    RuntimeDatabaseHelper,
)
from musigree.runtime.runtime_database_manager import RuntimeDatabaseManager
from musigree.transfer.transfer_manager import TransferManager
from musigree.transfer.transfer_task import TransferTask

log = logging.getLogger(__name__)


def load_offline_tables(data_directory: Path, date: str, is_bulk_inserts: bool) -> None:
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
        stage()
    log.info("Load offline tables done.")


def load_offline_table_stage(
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
    log.debug(f"Run stage: {stage}")
    stages[stage]()


def get_load_offline_table_stages(
    data_directory: Path, date: str, is_bulk_inserts: bool
) -> list[partial]:
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
    assert OfflineDatabaseManager.offline_database_helper.offline_engine is not None, (
        "OfflineDatabaseManager.offline_database_helper.offline_engine must be initialized before calling get_load_offline_table_stages()"
    )

    is_full = OfflineDatabaseManager.offline_database_helper.is_vacuum_full()
    is_analyze = OfflineDatabaseManager.offline_database_helper.is_vacuum_analyze()
    discogs_data_directory = data_directory / DISCOGS_DATA
    text_search_path = data_directory / TEXT_SEARCH_DATA / TEXT_SEARCH_FILENAME
    stages = [
        partial(RoleDataAccess.load_all_roles),
        partial(
            LoaderEntity().loader_entity_pass_one,
            discogs_data_directory,
            date,
            is_bulk_inserts,
        ),
        partial(
            OfflineDatabaseManager.offline_database_helper.vacuum,
            EntityTable.__tablename__,
            is_full,
            is_analyze,
            OfflineDatabaseManager.offline_database_helper.offline_engine,
        ),
        partial(
            LoaderRelease().loader_release_pass_one,
            discogs_data_directory,
            date,
            is_bulk_inserts,
        ),
        partial(
            OfflineDatabaseManager.offline_database_helper.vacuum,
            ReleaseTable.__tablename__,
            is_full,
            is_analyze,
            OfflineDatabaseManager.offline_database_helper.offline_engine,
        ),
        partial(LoaderEntity().loader_entity_pass_two),
        partial(LoaderRelease().loader_release_pass_two),
        partial(LoaderRelation().loader_relation_pass_one, date),
        # partial(LoaderRelation().loader_relation_pass_two, date),
        partial(
            OfflineDatabaseManager.offline_database_helper.vacuum,
            EntityTable.__tablename__,
            is_full,
            is_analyze,
            OfflineDatabaseManager.offline_database_helper.offline_engine,
        ),
        partial(
            OfflineDatabaseManager.offline_database_helper.vacuum,
            ReleaseTable.__tablename__,
            is_full,
            is_analyze,
            OfflineDatabaseManager.offline_database_helper.offline_engine,
        ),
        partial(
            OfflineDatabaseManager.offline_database_helper.vacuum,
            RelationTable.__tablename__,
            is_full,
            is_analyze,
            OfflineDatabaseManager.offline_database_helper.offline_engine,
        ),
        partial(LoaderEntity().loader_entity_pass_three),
        partial(
            OfflineDatabaseManager.offline_database_helper.vacuum,
            EntityTable.__tablename__,
            is_full,
            is_analyze,
            OfflineDatabaseManager.offline_database_helper.offline_engine,
        ),
        partial(
            OfflineDatabaseManager.offline_database_helper.vacuum,
            ReleaseTable.__tablename__,
            is_full,
            is_analyze,
            OfflineDatabaseManager.offline_database_helper.offline_engine,
        ),
        partial(
            OfflineDatabaseManager.offline_database_helper.vacuum,
            RelationTable.__tablename__,
            is_full,
            is_analyze,
            OfflineDatabaseManager.offline_database_helper.offline_engine,
        ),
        partial(
            LoaderEntity().loader_create_text_search_index,
            text_search_path,
        ),
    ]
    return stages


def load_runtime_tables(data_directory: Path) -> None:
    """Loads runtime tables with initial data."""
    log.info("Load tables")
    RuntimeRoleDataAccess.load_all_roles()

    text_search_path = data_directory / TEXT_SEARCH_DATA / TEXT_SEARCH_FILENAME
    RuntimeDatabaseHelper.text_search_index = (
        TextSearchIndex.load_text_search_index_from_file(text_search_path)
    )
    log.info("Load tables done.")


def load_offline_test_tables(
    data_directory: Path, date: str, is_bulk_inserts: bool
) -> None:
    """
    Loads test data into the offline tables.

    This method is used for loading test data into the offline database.
    It is typically called during the setup phase of tests.
    """

    assert OfflineDatabaseManager.offline_database_helper is not None, (
        "OfflineDatabaseManager.offline_database_helper must be initialized before calling load_offline_test_tables()"
    )

    roles_directory = data_directory / ROLES_DATA
    instruments_directory = data_directory / INSTRUMENTS_DATA
    LoaderRole.load_roles_into_database(roles_directory, instruments_directory)
    load_offline_tables(data_directory, date, is_bulk_inserts=is_bulk_inserts)

    # text_search_path = data_directory / TEXT_SEARCH_DATA / TEXT_SEARCH_FILENAME
    # OfflineDatabaseManager.offline_database_helper.text_search_index = (
    #     TextSearchIndex.load_text_search_index_from_file(text_search_path)
    # )


def load_runtime_test_tables(data_directory: Path) -> None:
    TransferManager.transfer_all(data_directory)
    load_runtime_tables(data_directory)


def loader_main() -> None:
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
    setup_logging()
    log.info("")
    log.info("")
    log.info("######  #   # #   ####   ####   ####   ####    ##   #####  #    # ")
    log.info("#     # # #      #    # #    # #    # #    #  #  #  #    # #    # ")
    log.info("#     # #  ####  #      #    # #      #    # #    # #    # ###### ")
    log.info("#     # #      # #      #    # #  ### #####  ###### #####  #    # ")
    log.info("#     # # #    # #    # #    # #    # #   #  #    # #      #    # ")
    log.info("######  #  ####   ####   ####   ####  #    # #    # #      #    # ")
    log.info("")
    log.info("")
    log.info("Using PostgresDevelopmentConfiguration")
    # log.info(f"DATABASE_HOST: {os.getenv('MUSIGREE_DATABASE_HOST')}")
    # log.info(f"DATABASE_NAME: {os.getenv('MUSIGREE_DATABASE_NAME')}")
    offline_config = PostgresDevelopmentConfiguration()
    runtime_config = SqliteDevelopmentConfiguration()

    # Setup Cache
    CacheManager.setup_cache(offline_config)
    cache = CacheManager.get_cache()
    if cache is None:
        log.error("Cache not set")
        sys.exit()
    else:
        log.debug("Clearing cache")
        CacheManager.clear()

    OfflineDatabaseManager.setup_database(offline_config)
    RuntimeDatabaseManager.setup_database(runtime_config)

    # Note reverse order (last in first out), logging is the last to be shutdown
    # atexit.register(shutdown_logging)
    atexit.register(CacheManager.shutdown_cache)
    atexit.register(OfflineDatabaseManager.shutdown_database)
    atexit.register(RuntimeDatabaseManager.shutdown_database)

    # Run the loader process between these dates
    start_date = datetime.date(2024, 11, 1)
    # start_date = datetime.date(2023, 10, 1)
    end_date = datetime.date(2024, 11, 1)
    # end_date = datetime.datetime.now()
    data_directory: str = str(offline_config.DATA_DIR)
    tasks = [
        LoaderSetupTask(
            data_directory=data_directory, start_date=start_date, end_date=end_date
        ),
        TransferTask(data_directory=data_directory),
    ]
    luigi_run_result = luigi.build(
        tasks,
        detailed_summary=True,
        local_scheduler=True,
        log_level="WARNING",
    )
    log.info(luigi_run_result.summary_text)


if __name__ == "__main__":
    loader_main()
