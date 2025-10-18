import asyncio
import atexit
import logging
import sys

from musigree.config import (
    PostgresDevelopmentConfiguration,
    SqliteDevelopmentConfiguration,
)
from musigree.constants import (
    TEXT_SEARCH_DATA,
    TEXT_SEARCH_FILENAME,
    ALL_RUNTIME_DATABASE_TABLE_NAMES,
)
from musigree.library.cache.cache_manager import CacheManager
from musigree.logging_config import setup_logging, shutdown_logging
from musigree.offline.loader.loader_entity import LoaderEntity
from musigree.offline.offline_database_manager import OfflineDatabaseManager
from musigree.runtime.runtime_database_manager import RuntimeDatabaseManager
from musigree.transfer.transfer_manager import TransferManager
from musigree.utils import log_banner

log = logging.getLogger(__name__)


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
        runner.run(OfflineDatabaseManager.shutdown_database())
        runner.run(RuntimeDatabaseManager.shutdown_database())

    CacheManager.shutdown_cache()
    log.info("######## RUNTIME LOADER SHUTDOWN DONE ########")
    shutdown_logging()


def create_text_search_index() -> None:
    """Create text search index asynchronously."""
    setup_logging()

    log_banner()

    offline_config = PostgresDevelopmentConfiguration()
    runtime_config = SqliteDevelopmentConfiguration()
    log.info(f"Using {offline_config.__class__.__name__} for offline database")
    log.info(f"Using {runtime_config.__class__.__name__} for runtime database")

    atexit.register(shutdown_loader)

    # Setup Cache
    CacheManager.setup_cache(offline_config)
    cache = CacheManager.get_cache()
    print(f"cache: {cache}")
    if cache is None:
        log.error("Cache not set")
        sys.exit()
    else:
        log.debug("Clearing cache")
        CacheManager.clear()

    with asyncio.Runner() as runner:
        runner.run(OfflineDatabaseManager.setup_database(offline_config))
        runner.run(RuntimeDatabaseManager.setup_database(runtime_config))
        runner.close()

    text_search_path = offline_config.DATA_DIR / TEXT_SEARCH_DATA / TEXT_SEARCH_FILENAME

    assert OfflineDatabaseManager.offline_database_helper is not None, (
        "offline_database_helper must be initialized before calling initialize()"
    )
    assert RuntimeDatabaseManager.runtime_database_helper is not None, (
        "runtime_database_helper must be initialized before calling initialize()"
    )

    with asyncio.Runner() as runner:
        runner.run(
            RuntimeDatabaseManager.runtime_database_helper.create_tables(
                ALL_RUNTIME_DATABASE_TABLE_NAMES
            )
        )
        # Copy text search index into runtime database
        runner.run(LoaderEntity().loader_create_text_search_index(text_search_path))
        runner.run(TransferManager().transfer_load_text_search_index(text_search_path))
        runner.close()


if __name__ == "__main__":
    create_text_search_index()
