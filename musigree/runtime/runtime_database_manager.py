import logging
import multiprocessing
import os
from asyncio import AbstractEventLoop

from sqlalchemy import exc
from sqlalchemy.event import listen
from sqlalchemy.ext.asyncio import async_sessionmaker, close_all_sessions

from musigree.config import Configuration
from musigree.constants import DatabaseType, ThreadingModel
from musigree.logging_config import LOGGING_TRACE
from musigree.runtime.runtime_database.runtime_database_helper import (
    RuntimeDatabaseHelper,
)

log = logging.getLogger(__name__)


class RuntimeDatabaseManager:
    runtime_database_helper: RuntimeDatabaseHelper | None = None
    _threading_model: ThreadingModel | None = None

    @staticmethod
    def get_concurrency_count() -> int:
        if RuntimeDatabaseManager._threading_model == ThreadingModel.PROCESS:
            return multiprocessing.cpu_count()
        elif RuntimeDatabaseManager._threading_model == ThreadingModel.THREAD:
            return 1
        else:
            raise NotImplementedError("THREADING_MODEL not configured")

    @classmethod
    async def setup_database(cls, config: Configuration) -> None:
        RuntimeDatabaseManager._threading_model = config.THREADING_MODEL

        # Based on configuration, use a different database.
        # noinspection PyUnreachableCode
        if config.DATABASE == DatabaseType.POSTGRES:
            from musigree.runtime.postgres.runtime_postgres_helper import RuntimePostgresHelper

            RuntimeDatabaseManager.runtime_database_helper = RuntimePostgresHelper()

        elif config.DATABASE == DatabaseType.SQLITE:
            from musigree.runtime.sqlite.runtime_sqlite_helper import RuntimeSqliteHelper

            RuntimeDatabaseManager.runtime_database_helper = RuntimeSqliteHelper()

        else:
            raise ValueError("Configuration Error: Unknown database type")

        async_engine = await RuntimeDatabaseManager.runtime_database_helper.setup_database(config)
        RuntimeDatabaseManager.runtime_database_helper.runtime_async_engine = async_engine

        def engine_on_connect(dbapi_con, connection_record):  # type: ignore
            if LOGGING_TRACE:
                log.debug(f"New engine connection: {dbapi_con}")
            connection_record.info["pid"] = os.getpid()

        def engine_on_checkout(dbapi_con, connection_record, connection_proxy):  # type: ignore
            pid = os.getpid()
            if connection_record.info["pid"] != pid:
                log.error(f"New engine checkout using wrong pid: {dbapi_con}")

                connection_record.dbapi_connection = connection_proxy.dbapi_connection = None
                raise exc.DisconnectionError(
                    "Connection record belongs to pid %s, "
                    "attempting to check out in pid %s" % (connection_record.info["pid"], pid)
                )

        if RuntimeDatabaseManager.get_concurrency_count() > 1:
            listen(async_engine.sync_engine, "connect", engine_on_connect)
            listen(async_engine.sync_engine, "checkout", engine_on_checkout)

        # a async_sessionmaker(), also in the same scope as the engine
        RuntimeDatabaseManager.runtime_database_helper.runtime_async_session_factory = (
            async_sessionmaker(
                bind=RuntimeDatabaseManager.runtime_database_helper.runtime_async_engine,
                expire_on_commit=False,
            )
        )

        # Set logging level for SqlAlchemy
        # logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARN)

        # Check database connection
        await RuntimeDatabaseManager.runtime_database_helper.check_connection(config, async_engine)

    @classmethod
    async def shutdown_database(cls) -> None:
        log.info("Shutting down database connections")

        await close_all_sessions()

        assert RuntimeDatabaseManager.runtime_database_helper is not None, (
            "RuntimeDatabaseManager.runtime_database_helper must be initialized before calling shutdown_database()"
        )

        if RuntimeDatabaseManager.runtime_database_helper.runtime_async_engine is not None:
            await RuntimeDatabaseManager.runtime_database_helper.runtime_async_engine.dispose()

        await RuntimeDatabaseManager.runtime_database_helper.shutdown_database()

    @classmethod
    def reinitialize_runtime_database_async_engine(cls, loop: AbstractEventLoop) -> None:
        """
        Initializes the database connection for a new process.

        Ensures that the parent process's database connections are not touched in
        the new connection pool.
        """
        if RuntimeDatabaseManager.get_concurrency_count() > 1:
            """Check if concurrency is enabled."""

            if (
                RuntimeDatabaseManager.runtime_database_helper is not None
                and RuntimeDatabaseManager.runtime_database_helper.runtime_async_engine is not None
            ):
                loop.run_until_complete(
                    RuntimeDatabaseManager.runtime_database_helper.runtime_async_engine.dispose(
                        close=False
                    )
                )

    @classmethod
    def dispose_runtime_database_async_engine(cls, loop: AbstractEventLoop) -> None:
        """
        Closes the database connection for a new process.

        Ensures that the parent process's database connections are not touched in
        the new connection pool.
        """
        if RuntimeDatabaseManager.get_concurrency_count() > 1:
            """Check if concurrency is enabled."""

            if (
                RuntimeDatabaseManager.runtime_database_helper is not None
                and RuntimeDatabaseManager.runtime_database_helper.runtime_async_engine is not None
            ):
                loop.run_until_complete(
                    RuntimeDatabaseManager.runtime_database_helper.runtime_async_engine.dispose(
                        close=True
                    )
                )
