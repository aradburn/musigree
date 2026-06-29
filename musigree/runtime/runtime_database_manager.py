import logging
import multiprocessing
from asyncio import AbstractEventLoop

from sqlalchemy.event import listen
from sqlalchemy.ext.asyncio import async_sessionmaker, close_all_sessions

from musigree.config import Configuration
from musigree.constants import DatabaseType, ThreadingModel
from musigree.runtime.runtime_database.runtime_database_helper import (
    RuntimeDatabaseHelper,
)

log = logging.getLogger(__name__)


class RuntimeDatabaseManager:
    runtime_database_helper: RuntimeDatabaseHelper | None = None
    threading_model: ThreadingModel | None = None

    @staticmethod
    def get_concurrency_count() -> int:
        if RuntimeDatabaseManager.threading_model == ThreadingModel.PROCESS:
            return multiprocessing.cpu_count()
        elif RuntimeDatabaseManager.threading_model == ThreadingModel.THREAD:
            return 1
        else:
            raise NotImplementedError("THREADING_MODEL not configured")

    @classmethod
    async def setup_database(cls, config: Configuration) -> None:
        RuntimeDatabaseManager.threading_model = config.THREADING_MODEL

        # Based on configuration, use a different runtime_database.
        # noinspection PyUnreachableCode
        if config.DATABASE == DatabaseType.POSTGRES:
            from musigree.runtime.postgres.runtime_postgres_helper import RuntimePostgresHelper

            RuntimeDatabaseManager.runtime_database_helper = RuntimePostgresHelper()

        elif config.DATABASE == DatabaseType.SQLITE:
            from musigree.runtime.sqlite.runtime_sqlite_helper import RuntimeSqliteHelper

            RuntimeDatabaseManager.runtime_database_helper = RuntimeSqliteHelper()

        else:
            raise ValueError("Configuration Error: Unknown database type")

        if RuntimeDatabaseManager.runtime_database_helper is None:
            raise ValueError("Configuration Error: Cannot set database helper")

        async_engine = await RuntimeDatabaseManager.runtime_database_helper.setup_database(config)
        RuntimeDatabaseManager.runtime_database_helper.runtime_async_engine = async_engine

        if config.IS_READ_ONLY:
            listen(
                async_engine.sync_engine,
                "connect",
                RuntimeDatabaseManager.runtime_database_helper.engine_on_connect_read_only,
            )
        else:
            listen(
                async_engine.sync_engine,
                "connect",
                RuntimeDatabaseManager.runtime_database_helper.engine_on_connect,
            )
        listen(
            async_engine.sync_engine,
            "checkout",
            RuntimeDatabaseManager.runtime_database_helper.engine_on_checkout,
        )

        # a async_sessionmaker(), also in the same scope as the engine
        RuntimeDatabaseManager.runtime_database_helper.runtime_async_session_factory = (
            async_sessionmaker(
                bind=RuntimeDatabaseManager.runtime_database_helper.runtime_async_engine,
                expire_on_commit=False,
            )
        )

        # Logging level for SqlAlchemy set in logging_config
        # logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
        # logging.getLogger("sqlalchemy.engine").setLevel(logging.WARN)

        # Check runtime_database connection
        await RuntimeDatabaseManager.runtime_database_helper.check_connection(config, async_engine)

    @classmethod
    async def shutdown_database(cls) -> None:
        log.info("Shutting down runtime_database connections")

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
        Initializes the runtime_database connection for a new process.

        Ensures that the parent process's runtime_database connections are not touched in
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
        Closes the runtime_database connection for a new process.

        Ensures that the parent process's runtime_database connections are not touched in
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
