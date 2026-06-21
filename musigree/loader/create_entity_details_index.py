import asyncio
import atexit
import logging
import sys

from musigree.config import (
    Configuration,
    PostgresReadOnlyDevelopmentConfiguration,
)
from musigree.constants import ENTITY_DETAILS_DATA, ENTITY_DETAILS_FILENAME
from musigree.library.cache.cache_manager import CacheManager
from musigree.logging_config import setup_logging
from musigree.offline.loader.loader_entity import LoaderEntity
from musigree.offline.offline_database_manager import OfflineDatabaseManager
from musigree.utils import log_banner

log = logging.getLogger(__name__)


async def create_entity_details_index(config: Configuration) -> None:
    """Create entity_details index asynchronously."""
    setup_logging()

    log_banner()

    log.info(f"Using {config.__class__.__name__} for offline database")

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

    # Note reverse order (last in first out), logging is the last to be shutdown
    # atexit.register(shutdown_logging)
    atexit.register(CacheManager.shutdown_cache)
    atexit.register(OfflineDatabaseManager.shutdown_database)

    entity_details_path = config.DATA_DIR / ENTITY_DETAILS_DATA / ENTITY_DETAILS_FILENAME
    await LoaderEntity().loader_create_entity_details_index(entity_details_path)


if __name__ == "__main__":
    _config = PostgresReadOnlyDevelopmentConfiguration()
    asyncio.run(create_entity_details_index(_config))
