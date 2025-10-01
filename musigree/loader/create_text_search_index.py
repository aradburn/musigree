import asyncio
import atexit
import logging
import sys

from musigree.config import (
    PostgresDevelopmentConfiguration,
    Configuration,
)
from musigree.constants import TEXT_SEARCH_DATA, TEXT_SEARCH_FILENAME
from musigree.library.cache.cache_manager import CacheManager
from musigree.logging_config import setup_logging
from musigree.offline.loader.loader_entity import LoaderEntity
from musigree.offline.offline_database_manager import OfflineDatabaseManager

log = logging.getLogger(__name__)


async def create_text_search_index(_config: Configuration) -> None:
    """Create text search index asynchronously."""
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

    # Setup Cache
    CacheManager.setup_cache(_config)
    cache = CacheManager.get_cache()
    print(f"cache: {cache}")
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

    text_search_path = _config.DATA_DIR / TEXT_SEARCH_DATA / TEXT_SEARCH_FILENAME
    await LoaderEntity().loader_create_text_search_index(text_search_path)


if __name__ == "__main__":
    _config = PostgresDevelopmentConfiguration()
    asyncio.run(create_text_search_index(_config))
