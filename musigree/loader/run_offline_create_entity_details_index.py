import asyncio
import logging
import sys

import asyncio_atexit  # type: ignore[import-untyped]
from sqlalchemy.exc import OperationalError

from musigree.config import (
    Configuration,
    PostgresReadOnlyDevelopmentConfiguration,
)
from musigree.constants import ENTITY_DETAILS_DATA, ENTITY_DETAILS_FILENAME
from musigree.library.cache.cache_manager import CacheManager
from musigree.logging_config import setup_logging, shutdown_logging
from musigree.offline.loader.loader_entity import LoaderEntity
from musigree.offline.offline_database_manager import OfflineDatabaseManager
from musigree.utils import log_banner

log = logging.getLogger(__name__)


async def shutdown_loader() -> None:
    """
    Shuts down the loader application.

    This function is called when the application is being shut down. It
    performs cleanup tasks such as closing database connections, shutting
    down the cache, and shutting down logging.
    """
    # Logging may have been shutdown automatically before this point, so we need to reinitialize it again
    setup_logging()
    log.info("######## LOADER SHUTDOWN START ########")
    try:
        await OfflineDatabaseManager.shutdown_database()
    except OperationalError:
        pass

    await CacheManager.shutdown_cache()

    log.info("######## LOADER SHUTDOWN DONE ########")
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
        await shutdown_loader()
    except KeyboardInterrupt:
        log.warning("Offline loader shutdown interrupted (database may not be fully closed)")
    except asyncio.CancelledError:
        raise


def create_entity_details_index(offline_config: Configuration) -> None:
    """Create entity_details index asynchronously."""
    setup_logging()

    log_banner()

    log.info(f"Using {offline_config.__class__.__name__} for offline database")

    with asyncio.Runner() as runner:
        loop = runner.get_loop()
        asyncio_atexit.register(shutdown_loader, loop=loop)

        try:
            # Setup Cache
            try:
                runner.run(CacheManager.setup_and_clear_cache(offline_config))
            except RuntimeError as exc:
                log.error("%s", exc)
                sys.exit(1)

            runner.run(OfflineDatabaseManager.setup_database(offline_config))

            assert OfflineDatabaseManager.offline_database_helper is not None, (
                "offline_database_helper must be initialized"
            )

            entity_details_path = (
                offline_config.DATA_DIR / ENTITY_DETAILS_DATA / ENTITY_DETAILS_FILENAME
            )
            runner.run(LoaderEntity().loader_create_entity_details_index(entity_details_path))
        finally:
            asyncio_atexit.unregister(shutdown_loader, loop=loop)
            try:
                runner.run(_finalize_offline_loader_before_loop_close())
            except KeyboardInterrupt:
                log.warning(
                    "Offline loader finalize interrupted; proceeding with event loop shutdown"
                )


if __name__ == "__main__":
    _config = PostgresReadOnlyDevelopmentConfiguration()
    create_entity_details_index(_config)
