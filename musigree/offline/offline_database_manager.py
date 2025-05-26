import logging
import multiprocessing
import os

from sqlalchemy import exc
from sqlalchemy.event import listen
from sqlalchemy.orm import sessionmaker, close_all_sessions

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
            return multiprocessing.cpu_count()
        elif OfflineDatabaseManager._threading_model == ThreadingModel.THREAD:
            return 1
        else:
            raise NotImplementedError("THREADING_MODEL not configured")

    @classmethod
    def setup_database(cls, config) -> None:
        OfflineDatabaseManager._threading_model = config.THREADING_MODEL

        # Based on configuration, use a different database.
        if config.DATABASE == DatabaseType.POSTGRES:
            from musigree.offline.postgres.postgres_helper import (
                OfflinePostgresHelper,
            )

            OfflineDatabaseManager.offline_database_helper = OfflinePostgresHelper()

        elif config.DATABASE == DatabaseType.SQLITE:
            from musigree.offline.sqlite.sqlite_helper import OfflineSqliteHelper

            OfflineDatabaseManager.offline_database_helper = OfflineSqliteHelper()

        else:
            raise ValueError("Configuration Error: Unknown database type")

        engine = OfflineDatabaseManager.offline_database_helper.setup_database(config)
        OfflineDatabaseManager.offline_database_helper.offline_engine = engine
        print(
            f"engine: {OfflineDatabaseManager.offline_database_helper.offline_engine}"
        )

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

        if OfflineDatabaseManager.get_concurrency_count() > 1:
            listen(engine, "connect", engine_on_connect)
            listen(engine, "checkout", engine_on_checkout)

        # a sessionmaker(), also in the same scope as the engine
        OfflineDatabaseManager.offline_database_helper.offline_session_factory = (
            sessionmaker(
                bind=OfflineDatabaseManager.offline_database_helper.offline_engine
            )
        )

        # Set logging level for SqlAlchemy
        # logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARN)

        # Check database connection
        OfflineDatabaseManager.offline_database_helper.check_connection(config, engine)

        # TODO remove - was Create tables
        # OfflineDatabaseManager.offline_database_helper.create_tables(
        #     ALL_OFFLINE_DATABASE_TABLE_NAMES
        # )
        #
        # LoaderRole.load_roles_into_database()

    @classmethod
    def shutdown_database(cls) -> None:
        log.info("Shutting down offline database connections")

        close_all_sessions()
        OfflineDatabaseManager.offline_database_helper.offline_engine.dispose()

        OfflineDatabaseManager.offline_database_helper.shutdown_database()
