import atexit
import logging
import sys
from typing import Coroutine, Any

from musigree.config import (
    Configuration,
)
from musigree.library.cache.cache_manager import CacheManager
from musigree.logging_config import setup_logging
from musigree.offline.data_access_layer.role_data_access import RoleDataAccess
from musigree.offline.offline_database_manager import OfflineDatabaseManager
from musigree.utils import log_banner

log = logging.getLogger(__name__)


async def run_offline_loading_process(
    _config: Configuration, process: Coroutine[Any, Any, None]
) -> None:
    """Create entity_details index asynchronously."""
    setup_logging()

    log_banner()

    log.info("Using PostgresDevelopmentConfiguration")

    # Setup Cache
    CacheManager.setup_cache(_config)
    cache = CacheManager.get_cache()
    if cache is None:
        log.error("Cache not set")
        sys.exit()
    else:
        log.debug("Clearing cache")
        CacheManager.clear()

    await OfflineDatabaseManager.setup_database(_config)

    # Note reverse order (last in first out), logging is the last to be shutdown
    # atexit.register(shutdown_logging)
    atexit.register(CacheManager.shutdown_cache)
    atexit.register(OfflineDatabaseManager.shutdown_database)

    await RoleDataAccess.load_all_roles_into_cache()
    await process
