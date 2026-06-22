import logging
from typing import Coroutine, Any

import asyncio_atexit  # type: ignore
from sqlalchemy.exc import OperationalError

from musigree.config import (
    Configuration,
)
from musigree.constants import ENTITY_DETAILS_DATA, ENTITY_DETAILS_FILENAME
from musigree.library.cache.cache_manager import CacheManager
from musigree.logging_config import setup_logging, shutdown_logging
from musigree.offline.data_access_layer.offline_role_data_access import OfflineRoleDataAccess
from musigree.offline.offline_database_manager import OfflineDatabaseManager
from musigree.runtime.runtime_database_manager import RuntimeDatabaseManager
from musigree.transfer.transfer_manager import TransferManager
from musigree.utils import log_banner

log = logging.getLogger(__name__)


async def shutdown_process_runner() -> None:
    """
    Shuts down the application.

    This function is called when the application is being shut down. It
    performs cleanup tasks such as closing database connections, shutting
    down the cache, and shutting down logging.
    """
    # Logging may have been shutdown automatically before this point, so we need to reinitialize it again
    setup_logging()
    log.info("######## RUNTIME LOADER SHUTDOWN START ########")
    try:
        if OfflineDatabaseManager.offline_database_helper is not None:
            await OfflineDatabaseManager.shutdown_database()
    except OperationalError:
        pass

    try:
        if RuntimeDatabaseManager.runtime_database_helper is not None:
            await RuntimeDatabaseManager.shutdown_database()
    except OperationalError:
        pass

    await CacheManager.shutdown_cache()

    shutdown_logging()
    log.info("######## RUNTIME LOADER SHUTDOWN DONE ########")


async def run_runtime_loading_process(
    offline_config: Configuration,
    runtime_config: Configuration,
    process: Coroutine[Any, Any, None],
    table_names: list[str] | None = None,
) -> None:
    """Create loader asynchronously."""

    setup_logging()

    log_banner()

    log.info(f"Using {offline_config.__class__.__name__} for offline database")
    log.info(f"Using {runtime_config.__class__.__name__} for runtime database")

    # Setup Cache
    await CacheManager.setup_and_clear_cache(offline_config)

    await OfflineDatabaseManager.setup_database(offline_config)
    await RuntimeDatabaseManager.setup_database(runtime_config)

    assert OfflineDatabaseManager.offline_database_helper is not None, (
        "offline_database_helper must be initialized"
    )
    assert RuntimeDatabaseManager.runtime_database_helper is not None, (
        "runtime_database_helper must be initialized before calling initialize()"
    )

    if table_names:
        await RuntimeDatabaseManager.runtime_database_helper.create_tables(table_names)

    asyncio_atexit.register(shutdown_process_runner)

    await OfflineRoleDataAccess.load_all_roles_into_cache()

    entity_details_path = runtime_config.DATA_DIR / ENTITY_DETAILS_DATA / ENTITY_DETAILS_FILENAME
    await TransferManager.transfer_load_entity_details_index(entity_details_path)

    # Run the process
    # Note: this is used to run a single part of the runtime loading process,
    # usually the whole process is ran by run_runtime_loader()
    await process
