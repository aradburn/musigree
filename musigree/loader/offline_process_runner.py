import asyncio
import logging
import sys
from typing import Coroutine, Any

import asyncio_atexit  # type: ignore
from sqlalchemy.exc import OperationalError

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
    log.info("######## OFFLINE LOADER SHUTDOWN START ########")
    try:
        if OfflineDatabaseManager.offline_database_helper is not None:
            await OfflineDatabaseManager.shutdown_database()
    except OperationalError:
        pass

    await CacheManager.shutdown_cache()

    shutdown_logging()
    log.info("######## OFFLINE LOADER SHUTDOWN DONE ########")


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
        await shutdown_process_runner()
    except KeyboardInterrupt:
        log.warning("Offline loader shutdown interrupted (database may not be fully closed)")
    except asyncio.CancelledError:
        raise


def run_offline_loading_process(
    offline_config: Configuration,
    process: Coroutine[Any, Any, None],
    table_names: list[str] | None = None,
) -> None:
    """Create loader asynchronously."""

    setup_logging()

    log_banner()

    log.info(f"Using {offline_config.__class__.__name__}")

    with asyncio.Runner() as runner:
        loop = runner.get_loop()
        asyncio_atexit.register(shutdown_process_runner, loop=loop)
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

            if table_names:
                runner.run(
                    OfflineDatabaseManager.offline_database_helper.create_tables(table_names)
                )

            runner.run(OfflineRoleDataAccess.load_all_roles_into_cache())

            # Run the process
            # Note: this is used to run a single part of the offline loading process,
            # usually the whole process is ran by run_offline_loader()
            runner.run(process)

        finally:
            asyncio_atexit.unregister(shutdown_process_runner, loop=loop)
            try:
                runner.run(_finalize_offline_loader_before_loop_close())
            except KeyboardInterrupt:
                log.warning(
                    "Offline loader finalize interrupted; proceeding with event loop shutdown"
                )
