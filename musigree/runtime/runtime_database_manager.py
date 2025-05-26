import logging
import multiprocessing
import os

from sqlalchemy import exc
from sqlalchemy.event import listen
from sqlalchemy.orm import sessionmaker, close_all_sessions

from musigree.config import Configuration
from musigree.constants import DatabaseType, ThreadingModel
from musigree.logging_config import LOGGING_TRACE
from musigree.runtime.runtime_database.runtime_database_helper import (
    RuntimeDatabaseHelper,
)

log = logging.getLogger(__name__)


class RuntimeDatabaseManager:
    runtime_database_helper: RuntimeDatabaseHelper
    _threading_model: ThreadingModel

    @staticmethod
    def get_concurrency_count() -> int:
        if RuntimeDatabaseManager._threading_model == ThreadingModel.PROCESS:
            return multiprocessing.cpu_count()
        elif RuntimeDatabaseManager._threading_model == ThreadingModel.THREAD:
            return 1
        else:
            raise NotImplementedError("THREADING_MODEL not configured")

    @classmethod
    def setup_database(cls, config: Configuration) -> None:
        RuntimeDatabaseManager._threading_model = config.THREADING_MODEL

        # Based on configuration, use a different database.
        if config.DATABASE == DatabaseType.POSTGRES:
            from musigree.runtime.postgres.postgres_helper import (
                RuntimePostgresHelper,
            )

            RuntimeDatabaseManager.runtime_database_helper = RuntimePostgresHelper()

        elif config.DATABASE == DatabaseType.SQLITE:
            from musigree.runtime.sqlite.sqlite_helper import RuntimeSqliteHelper

            RuntimeDatabaseManager.runtime_database_helper = RuntimeSqliteHelper()

        else:
            raise ValueError("Configuration Error: Unknown database type")

        engine = RuntimeDatabaseManager.runtime_database_helper.setup_database(config)
        RuntimeDatabaseHelper.runtime_engine = engine

        def engine_on_connect(dbapi_con, connection_record):
            if LOGGING_TRACE:
                log.debug(f"New engine connection: {dbapi_con}")
            connection_record.info["pid"] = os.getpid()

        def engine_on_checkout(dbapi_con, connection_record, connection_proxy):
            pid = os.getpid()
            if connection_record.info["pid"] != pid:
                log.error(f"New engine checkout using wrong pid: {dbapi_con}")

                connection_record.dbapi_connection = (
                    connection_proxy.dbapi_connection
                ) = None
                raise exc.DisconnectionError(
                    "Connection record belongs to pid %s, "
                    "attempting to check out in pid %s"
                    % (connection_record.info["pid"], pid)
                )

        if RuntimeDatabaseManager.get_concurrency_count() > 1:
            listen(engine, "connect", engine_on_connect)
            listen(engine, "checkout", engine_on_checkout)

        # a sessionmaker(), also in the same scope as the engine
        RuntimeDatabaseHelper.runtime_session_factory = sessionmaker(bind=engine)

        # Set logging level for SqlAlchemy
        # logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARN)

        # Check database connection
        RuntimeDatabaseManager.runtime_database_helper.check_connection(config, engine)

    @classmethod
    def shutdown_database(cls):
        log.info("Shutting down database connections")

        close_all_sessions()
        RuntimeDatabaseManager.runtime_database_helper.runtime_engine.dispose()

        RuntimeDatabaseManager.runtime_database_helper.shutdown_database()
