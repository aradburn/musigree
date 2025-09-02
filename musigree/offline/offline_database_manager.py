import logging
import multiprocessing
import os
from asyncio import AbstractEventLoop

from sqlalchemy import exc
from sqlalchemy.event import listen
from sqlalchemy.ext.asyncio import async_sessionmaker

from musigree.config import Configuration
from musigree.constants import DatabaseType, ThreadingModel
from musigree.logging_config import LOGGING_TRACE
from musigree.offline.database.offline_database_helper import OfflineDatabaseHelper

log = logging.getLogger(__name__)


class OfflineDatabaseManager:
    offline_database_helper: OfflineDatabaseHelper | None = None
    _threading_model: ThreadingModel | None = None

    @staticmethod
    def get_concurrency_count() -> int:
        if OfflineDatabaseManager._threading_model == ThreadingModel.PROCESS:
            return multiprocessing.cpu_count() * 2
        elif OfflineDatabaseManager._threading_model == ThreadingModel.THREAD:
            return 1
        else:
            raise NotImplementedError("THREADING_MODEL not configured")

    @classmethod
    async def setup_database(cls, config: Configuration) -> None:
        OfflineDatabaseManager._threading_model = config.THREADING_MODEL

        # Based on configuration, use a different database.
        # noinspection PyUnreachableCode
        if config.DATABASE == DatabaseType.POSTGRES:
            from musigree.offline.postgres.offline_postgres_helper import (
                OfflinePostgresHelper,
            )

            OfflineDatabaseManager.offline_database_helper = OfflinePostgresHelper()

        elif config.DATABASE == DatabaseType.SQLITE:
            from musigree.offline.sqlite.offline_sqlite_helper import (
                OfflineSqliteHelper,
            )

            OfflineDatabaseManager.offline_database_helper = OfflineSqliteHelper()

        else:
            raise ValueError("Configuration Error: Unknown database type")

        async_engine = (
            await OfflineDatabaseManager.offline_database_helper.setup_database(config)
        )
        OfflineDatabaseManager.offline_database_helper.offline_async_engine = (
            async_engine
        )
        log.debug(
            f"engine: {OfflineDatabaseManager.offline_database_helper.offline_async_engine}"
        )

        def engine_on_connect(dbapi_con, connection_record) -> None:  # type: ignore
            if LOGGING_TRACE:
                log.debug(f"Connect engine connection: {dbapi_con}")
            connection_record.info["pid"] = os.getpid()

        def engine_on_checkout(dbapi_con, connection_record, connection_proxy) -> None:  # type: ignore
            pid = os.getpid()
            # log.debug(f"Checkout engine connection: {dbapi_con}")

            if connection_record.info["pid"] != pid:
                log.error(f"Checkout engine connection using wrong pid: {dbapi_con}")

                connection_record.dbapi_connection = (
                    connection_proxy.dbapi_connection
                ) = None
                raise exc.DisconnectionError(
                    "Connection record belongs to pid %s, "
                    "attempting to check out in pid %s"
                    % (connection_record.info["pid"], pid)
                )

        def engine_on_checkin(dbapi_con, connection_record) -> None:  # type: ignore
            log.debug(f"Checkin engine connection: {dbapi_con}")
            connection_record.info["pid"] = os.getpid()

        def engine_on_close(dbapi_con, connection_record) -> None:  # type: ignore
            log.debug(f"Close engine connection: {dbapi_con}")
            connection_record.info["pid"] = os.getpid()

        if OfflineDatabaseManager.get_concurrency_count() > 1:
            listen(async_engine.sync_engine, "connect", engine_on_connect)
            listen(async_engine.sync_engine, "checkout", engine_on_checkout)
            # listen(async_engine.sync_engine, "checkin", engine_on_checkin)
            # listen(async_engine.sync_engine, "close", engine_on_close)

        # a async_sessionmaker(), also in the same scope as the engine
        OfflineDatabaseManager.offline_database_helper.offline_async_session_factory = async_sessionmaker(
            bind=OfflineDatabaseManager.offline_database_helper.offline_async_engine,
            expire_on_commit=False,
        )

        # Set logging level for SqlAlchemy
        # logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARN)
        # logging.getLogger("sqlalchemy.dialects.postgresql").setLevel(logging.DEBUG)
        # logging.getLogger("sqlalchemy.pool").setLevel(logging.DEBUG)
        # logging.getLogger("asyncio").setLevel(logging.DEBUG)

        # Check database connection
        await OfflineDatabaseManager.offline_database_helper.check_connection(
            config, async_engine
        )

    @classmethod
    async def shutdown_database(cls) -> None:
        log.info("Shutting down offline database connections")

        # close_all_sessions()

        assert OfflineDatabaseManager.offline_database_helper is not None, (
            "OfflineDatabaseManager.offline_database_helper must be initialized before calling shutdown_database()"
        )

        if (
            OfflineDatabaseManager.offline_database_helper.offline_async_engine
            is not None
        ):
            await OfflineDatabaseManager.offline_database_helper.offline_async_engine.dispose()

        await OfflineDatabaseManager.offline_database_helper.shutdown_database()

    @classmethod
    def reinitialize_offline_database_async_engine(cls, loop: AbstractEventLoop) -> None:
        """
        Initializes the database connection for a new process.

        Ensures that the parent process's database connections are not touched in
        the new connection pool.
        """
        if OfflineDatabaseManager.get_concurrency_count() > 1:
            """Check if concurrency is enabled."""

            if (OfflineDatabaseManager.offline_database_helper is not None and
                OfflineDatabaseManager.offline_database_helper.offline_async_engine is not None):
                loop.run_until_complete(
                    OfflineDatabaseManager.offline_database_helper.offline_async_engine.dispose(
                        close=False
                    )
                )

    @classmethod
    def dispose_offline_database_async_engine(cls, loop: AbstractEventLoop) -> None:
        """
        Closes the database connection for a new process.

        Ensures that the parent process's database connections are not touched in
        the new connection pool.
        """
        if OfflineDatabaseManager.get_concurrency_count() > 1:
            """Check if concurrency is enabled."""

            if (OfflineDatabaseManager.offline_database_helper is not None and
                OfflineDatabaseManager.offline_database_helper.offline_async_engine is not None):
                loop.run_until_complete(
                    OfflineDatabaseManager.offline_database_helper.offline_async_engine.dispose(
                        close=True
                    )
                )
