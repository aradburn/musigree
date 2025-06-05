import logging
import shutil
from pathlib import Path
from typing import Type, List

# noinspection Mypy
from pg_temp import TempDB  # type: ignore
from sqlalchemy import Engine, URL, create_engine, text
from sqlalchemy.dialects.postgresql import insert, Insert
from sqlalchemy.exc import DatabaseError
from sqlalchemy.sql.dml import ReturningInsert

from musigree.config import Configuration
from musigree.offline.database.offline_database_helper import (
    OfflineDatabaseHelper,
    ConcreteTable,
)
from musigree.offline.offline_database_manager import OfflineDatabaseManager

log = logging.getLogger(__name__)


class OfflinePostgresHelper(OfflineDatabaseHelper):
    postgres_test_db: TempDB | None = None
    pg_offline_dirname: Path | None = None
    _is_test: bool = False

    @staticmethod
    def setup_database(config: Configuration) -> Engine:
        if config.PRODUCTION:
            log.info("**********************************************")
            log.info("* Using Production Postgres Offline Database *")
            log.info("**********************************************")
            log.info("")

            # Create a database engine and pool that will manage connections and execute queries
            url_object = URL.create(
                "postgresql+psycopg2",
                username=config.POSTGRES_DATABASE_USERNAME,
                password=config.POSTGRES_DATABASE_PASSWORD,
                host=config.POSTGRES_DATABASE_HOST,
                port=config.POSTGRES_DATABASE_PORT,
                database=config.POSTGRES_OFFLINE_DATABASE_NAME,
            )
            engine = create_engine(
                url_object, pool_size=40, pool_timeout=300, pool_recycle=300
            )

            # with database.connection_context():
            # database.execute_sql("SET auto_explain.log_analyze TO on;")
            # database.execute_sql("SET auto_explain.log_min_duration TO 500;")
            # database.execute_sql("CREATE EXTENSION pg_stat_statements;")

        else:
            if config.TESTING:
                log.info("Using Postgres Test Offline Database")
                assert config.POSTGRES_OFFLINE_DATA is not None, (
                    "POSTGRES_OFFLINE_DATA must be set in the configuration for testing"
                )
                pg_offline_dirname = config.POSTGRES_OFFLINE_DATA
                data_path = pg_offline_dirname / "data"
                socket_path = pg_offline_dirname / "socket"
                log.debug(f"data_path: {data_path}")
                log.debug(f"socket_path: {socket_path}")

                # pg_data_path = pathlib.Path(pg_data_dir)
                # if config['TESTING']:
                #     data_path.rmdir()
                data_path.parent.mkdir(parents=True, exist_ok=True)

                # Delete left over failed test database if present
                if data_path.is_dir():
                    shutil.rmtree(data_path)
                if socket_path.is_dir():
                    shutil.rmtree(socket_path)

                options = {
                    "work_mem": "100MB",
                    "maintenance_work_mem": "100MB",
                    "effective_cache_size": "2GB",
                    "max_connections": OfflineDatabaseManager.get_concurrency_count()
                    + 4,
                    "shared_buffers": "3GB",
                    # "log_min_duration_statement": 5000,
                    # "shared_preload_libraries": 'pg_stat_statements',
                    # "session_preload_libraries": 'auto_explain',
                    # "default_transaction_isolation": "serializable",
                    # "transaction_isolation": "serializable",
                    # "statement_timeout": "20000",
                    # "lock_timeout": "10000",
                    # "idle_in_transaction_session_timeout": "30000",
                }
                OfflinePostgresHelper.postgres_test_db = TempDB(
                    verbosity=0,
                    databases=[config.POSTGRES_OFFLINE_DATABASE_NAME],
                    initdb=config.POSTGRES_ROOT + "/bin/initdb" if config.POSTGRES_ROOT is not None else None,
                    postgres=config.POSTGRES_ROOT + "/bin/postgres" if config.POSTGRES_ROOT is not None else None,
                    psql=config.POSTGRES_ROOT + "/bin/psql" if config.POSTGRES_ROOT is not None else None,
                    createuser=config.POSTGRES_ROOT + "/bin/createuser" if config.POSTGRES_ROOT is not None else None,
                    dirname=pg_offline_dirname,
                    options=options,
                )
                OfflinePostgresHelper.pg_offline_dirname = pg_offline_dirname

                # Create a temporary test database engine and pool that will manage connections and execute queries
                url_object = URL.create(
                    "postgresql",
                    # "postgresql+psycopg2",
                    username=OfflinePostgresHelper.postgres_test_db.current_user,
                    # password=config[POSTGRES_DATABASE_PASSWORD_KEY],
                    host=OfflinePostgresHelper.postgres_test_db.pg_socket_dir,
                    # port=config[POSTGRES_DATABASE_PORT_KEY],
                    database=config.POSTGRES_OFFLINE_DATABASE_NAME,
                )
                engine = create_engine(
                    url_object,
                    pool_size=OfflineDatabaseManager.get_concurrency_count() + 4,
                    pool_timeout=30,
                    pool_recycle=30,
                    # connect_args={
                    #     "connect_timeout": 10,
                    # },
                    # isolation_level="REPEATABLE READ",
                    # isolation_level="SERIALIZABLE",
                    # execution_options={
                    #     # "isolation_level": "REPEATABLE READ",
                    #     "statement_timeout": 20000,
                    #     "lock_timeout": 10000,
                    #     "idle_in_transaction_session_timeout": 30000,
                    # },
                    # poolclass=NullPool,
                )

                OfflinePostgresHelper._is_test = True
            else:
                log.info("Using Postgres Development Offline Database")

                # Create a database engine and pool that will manage connections and execute queries
                url_object = URL.create(
                    "postgresql+psycopg2",
                    username=config.POSTGRES_DATABASE_USERNAME,
                    password=config.POSTGRES_DATABASE_PASSWORD,
                    host=config.POSTGRES_DATABASE_HOST,
                    port=config.POSTGRES_DATABASE_PORT,
                    database=config.POSTGRES_OFFLINE_DATABASE_NAME,
                )
                engine = create_engine(
                    url_object,
                    pool_size=OfflineDatabaseManager.get_concurrency_count() + 4,
                    pool_timeout=300,
                    pool_recycle=300,
                    connect_args={
                        "connect_timeout": 1000,
                    },
                    # isolation_level="REPEATABLE READ",
                    # isolation_level="SERIALIZABLE",
                    # execution_options={
                    #     # "isolation_level": "REPEATABLE READ",
                    #     "statement_timeout": 20000,
                    #     "lock_timeout": 10000,
                    #     "idle_in_transaction_session_timeout": 30000,
                    # },
                )

        return engine

    @staticmethod
    def shutdown_database() -> None:
        log.info("Shutting down Postgres offline database")

        if (
            OfflinePostgresHelper._is_test
            and OfflinePostgresHelper.postgres_test_db is not None
        ):
            log.info("Cleaning up Postgres Test Offline Database")

            OfflinePostgresHelper.postgres_test_db.cleanup()

            log.info(
                f"Delete data dir: {OfflinePostgresHelper.postgres_test_db.pg_data_dir}"
            )
            shutil.rmtree(OfflinePostgresHelper.postgres_test_db.pg_data_dir)
            log.info(
                f"Delete socket dir: {OfflinePostgresHelper.postgres_test_db.pg_socket_dir}"
            )
            shutil.rmtree(OfflinePostgresHelper.postgres_test_db.pg_socket_dir)
            if OfflinePostgresHelper.pg_offline_dirname is not None:
                log.info(f"Delete temp dir: {OfflinePostgresHelper.pg_offline_dirname}")
                shutil.rmtree(OfflinePostgresHelper.pg_offline_dirname)
            OfflinePostgresHelper.postgres_test_db = None
            OfflinePostgresHelper._is_test = False

    @staticmethod
    def check_connection(config: Configuration, engine: Engine) -> None:
        try:
            log.info("Check Postgres offline database connection...")

            with engine.connect() as connection:
                version = connection.execute(text("SELECT version();"))
                connection.commit()

            log.info(f"Database Version: {version.scalars().one_or_none()}")

            log.info("Offline Database connected OK.")
        except DatabaseError:
            log.exception("Offline Database Connection Error", exc_info=True)

    @classmethod
    def create_tables(cls, tables: List[str]) -> None:
        log.info("Create Offline Postgres tables")
        super().create_tables(tables=tables)

    @classmethod
    def drop_tables(cls, tables: List[str]) -> None:
        log.info("Drop Offline Postgres tables")
        super().drop_tables(tables=tables)

    @staticmethod
    def has_vacuum_tablename() -> bool:
        return True

    @staticmethod
    def is_vacuum_full() -> bool:
        return True

    @staticmethod
    def is_vacuum_analyze() -> bool:
        return True

    @staticmethod
    def generate_insert_query(
        schema_class: Type[ConcreteTable], values: dict, on_conflict_do_nothing=False
    ) -> ReturningInsert[tuple[ConcreteTable]]:
        if on_conflict_do_nothing:
            return (
                insert(schema_class)
                .on_conflict_do_nothing()
                .values(values)
                .returning(schema_class)
            )
        else:
            return insert(schema_class).values(values).returning(schema_class)

    @staticmethod
    def generate_insert_bulk_query(
        schema_class: Type[ConcreteTable],
        values_list: List[dict],
        on_conflict_do_nothing=False,
    ) -> Insert:
        if on_conflict_do_nothing:
            return insert(schema_class).on_conflict_do_nothing().values(values_list)
        else:
            return insert(schema_class).values(values_list)
