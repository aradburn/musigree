import logging
import sys
from typing import Coroutine, Any

import asyncio_atexit  # type: ignore

from musigree.config import (
    Configuration,
)
from musigree.library.cache.cache_manager import CacheManager
from musigree.logging_config import setup_logging, shutdown_logging
from musigree.offline.data_access_layer.offline_role_data_access import OfflineRoleDataAccess
from musigree.offline.offline_database_manager import OfflineDatabaseManager
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
    log.info("######## LOADER SHUTDOWN BEGIN ########")
    await OfflineDatabaseManager.shutdown_database()
    await CacheManager.shutdown_cache()
    log.info("######## LOADER SHUTDOWN END ########")
    shutdown_logging()


async def run_offline_loading_process(
    config: Configuration, process: Coroutine[Any, Any, None]
) -> None:
    """Create loader asynchronously."""
    setup_logging()

    log_banner()

    log.info(f"Using {config.__class__.__name__}")

    # Setup Cache
    await CacheManager.setup_cache(config)
    cache = CacheManager.get_cache()
    if cache is None:
        log.error("Cache not set")
        sys.exit()
    else:
        log.debug("Clearing cache")
        await CacheManager.clear()

    await OfflineDatabaseManager.setup_database(config)

    asyncio_atexit.register(shutdown_process_runner)

    await OfflineRoleDataAccess.load_all_roles_into_cache()
    await process
