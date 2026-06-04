"""
This module defines the `RuntimePostgresHelper` class, which provides
functionality for managing a PostgreSQL runtime database in the Musigree
system.

It extends the `RuntimeDatabaseHelper` abstract base class to provide
PostgreSQL-specific implementations of database setup, shutdown, connection
checking, table creation/deletion, and query generation.

Key functionalities include:
    - **Database Setup**: `setup_database` creates a PostgreSQL database engine,
      handling connections to both production, development, and test databases.
      For test environments, it uses `pg_temp` to create temporary test databases.
    - **Database Shutdown**: `shutdown_database` handles the shutdown of the
      PostgreSQL runtime_database. For test databases, it performs cleanup, including
      removing temporary runtime_database files.
    - **Connection Checking**: `check_connection` checks the runtime_database
      connection, retrieves the PostgreSQL version, and logs the result.
    - **Table Management**: `create_tables` and `drop_tables` implement
      table creation and deletion using the SQLAlchemy metadata.
    - **Query Generation**: `generate_insert_query` and
      `generate_insert_bulk_query` provide PostgreSQL-specific implementations
      for generating insert queries, including support for "on conflict do
      nothing" behavior.
    - **Vacuum Support**: Indicates that PostgreSQL supports table-specific
      vacuuming and full/analyze vacuum options.
    - **Test Database Management**: Utilizes `pg_temp` to create and manage
      temporary test databases, including setup and cleanup.
    - **Configuration Handling**: Dynamically configures the runtime_database connection
      based on the `PRODUCTION` and `TESTING` flags in the application
      configuration.
    - **Pool Management**: Use different pool, `SingletonThreadPool` or classic
    pool to manage the connection pool.
    - **Connection Management**: Set the `connect_timeout`.

The `RuntimePostgresHelper` class interacts with the following components:
    - `sqlalchemy.Engine`: For creating and managing runtime_database connections.
    - `sqlalchemy.create_engine`: For creating PostgreSQL engines.
    - `sqlalchemy.text`: For executing raw SQL queries.
    - `sqlalchemy.dialects.postgresql.insert`: For generating PostgreSQL-specific
      insert queries.
    - `sqlalchemy.SingletonThreadPool`: To manage the connection pool.
    - `pg_temp.TempDB`: For managing temporary PostgreSQL test databases.
    - `pathlib.Path`: For managing file paths.
    - `shutil`: For file system operations (removing temporary directories).
    - `os`: For file system operations.
    - `musigree.config.Configuration`: For accessing application
      configuration settings.
    - `musigree.runtime.runtime_database.runtime_database_helper.RuntimeDatabaseHelper`:
      The base class for runtime_database helper classes.
    - `musigree.runtime.runtime_database.runtime_base_table.RuntimeConcreteTable`:
        For type hinting for table classes.
    - `musigree.runtime.runtime_database_manager.RuntimeDatabaseManager`:
        For accessing the number of concurrency.
    - `logging`: For logging operations.

The module utilizes `logging` for logging operations, `pathlib` for file path
operations, `sqlalchemy` for runtime_database operations, `typing` for type hinting,
`shutil` for file deletion, `os` for os operation and `pg_temp` to manage the
test runtime_database. It interacts with `musigree` library for specific configuration
and runtime operation.
"""

import logging
import shutil
from pathlib import Path
from typing import Type

# noinspection Mypy
from pg_temp import TempDB  # type: ignore
from sqlalchemy import URL, text, SingletonThreadPool, AsyncAdaptedQueuePool
from sqlalchemy.dialects.postgresql import insert, Insert
from sqlalchemy.exc import DatabaseError
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlalchemy.sql.dml import ReturningInsert

from musigree.config import Configuration
from musigree.constants import POSTGRESQL_DRIVER_NAME
from musigree.runtime.runtime_database.runtime_base_table import RuntimeConcreteTable
from musigree.runtime.runtime_database.runtime_database_helper import (
    RuntimeDatabaseHelper,
)
from musigree.runtime.runtime_database_manager import RuntimeDatabaseManager

log = logging.getLogger(__name__)
"""
The logger for the RuntimePostgresHelper module.
"""


class RuntimePostgresHelper(RuntimeDatabaseHelper):
    """
    Provides functionality for managing a PostgreSQL runtime database.

    This class extends `RuntimeDatabaseHelper` to provide PostgreSQL-specific
    implementations for runtime_database operations. It handles connections to
    production, development, and test databases, using `pg_temp` for test
    environments.
    """

    postgres_test_db: TempDB | None = None
    """Instance of the test runtime_database."""
    pg_runtime_dirname: Path | None = None
    """Directory used for storing temp runtime_database files."""
    _is_test: bool = False
    """Flag to indicate if it is a test runtime_database."""

    @staticmethod
    async def setup_database(config: Configuration) -> AsyncEngine:
        """
        Sets up the PostgreSQL runtime_database connection and returns the engine.

        This method creates a PostgreSQL runtime_database engine, handling connections
        to production, development, and test databases based on the application
        configuration. For test databases, it utilizes `pg_temp` to create and
        manage temporary test databases.

        Args:
            config (Configuration): The application configuration.

        Returns:
            Engine: The SQLAlchemy engine.
        """
        if config.PRODUCTION:
            """Handle production configuration."""
            log.info("**********************************************")
            log.info("* Using Production Postgres Runtime Database *")
            log.info("**********************************************")
            log.info("")

            host = config.POSTGRES_DATABASE_HOST
            """Get the host."""
            port = config.POSTGRES_DATABASE_PORT
            """Get the port."""
            name = config.POSTGRES_RUNTIME_DATABASE_NAME
            """Get the runtime_database name."""

            log.info(f"DATABASE_HOST: {host}")
            log.info(f"DATABASE_PORT: {port}")
            log.info(f"DATABASE_NAME: {name}")

            # Create a runtime_database engine and pool that will manage connections and execute queries
            url_object = URL.create(
                POSTGRESQL_DRIVER_NAME,
                username=config.POSTGRES_DATABASE_USERNAME,
                password=config.POSTGRES_DATABASE_PASSWORD,
                host=host,
                port=port,
                database=name,
            )
            """Create the url to connect to the runtime_database."""
            engine = create_async_engine(
                url_object, pool_size=40, pool_timeout=300, pool_recycle=300
            )
            """Create the engine."""

        else:
            """Handle development and testing configuration."""
            if config.TESTING:
                """Handle the testing configuration."""
                log.info("Using Test Postgres Runtime Database")
                assert config.POSTGRES_RUNTIME_DATA is not None, (
                    "POSTGRES_RUNTIME_DATA must be set in the configuration for testing"
                )
                pg_runtime_dirname = config.POSTGRES_RUNTIME_DATA
                """Get the path to the data folder."""
                data_path = pg_runtime_dirname / "data"
                """Create the path to the data folder."""
                socket_path = pg_runtime_dirname / "socket"
                """Create the path to the socket folder."""
                log.debug(f"data_path: {data_path}")
                log.debug(f"socket_path: {socket_path}")

                data_path.parent.mkdir(parents=True, exist_ok=True)
                """Create the parent folder if needed."""

                # Delete left over failed test runtime_database if present
                if data_path.is_dir():
                    """If the data folder already exists."""
                    shutil.rmtree(data_path)
                    """Remove it."""
                if socket_path.is_dir():
                    """If the socket folder already exists."""
                    shutil.rmtree(socket_path)
                    """Remove it."""

                options = {
                    "work_mem": "100MB",
                    "maintenance_work_mem": "100MB",
                    "effective_cache_size": "2GB",
                    "max_connections": RuntimeDatabaseManager.get_concurrency_count() + 4,
                    "shared_buffers": "3GB",
                }
                """The option for the db."""
                RuntimePostgresHelper.postgres_test_db = TempDB(
                    verbosity=0,
                    databases=[config.POSTGRES_RUNTIME_DATABASE_NAME],
                    initdb=config.POSTGRES_ROOT + "/bin/initdb"
                    if config.POSTGRES_ROOT is not None
                    else None,
                    postgres=config.POSTGRES_ROOT + "/bin/postgres"
                    if config.POSTGRES_ROOT is not None
                    else None,
                    psql=config.POSTGRES_ROOT + "/bin/psql"
                    if config.POSTGRES_ROOT is not None
                    else None,
                    createuser=config.POSTGRES_ROOT + "/bin/createuser"
                    if config.POSTGRES_ROOT is not None
                    else None,
                    dirname=pg_runtime_dirname,
                    options=options,
                )
                """Create the temp db."""
                RuntimePostgresHelper.pg_runtime_dirname = pg_runtime_dirname
                """Set the runtime dir name."""

                if RuntimePostgresHelper.postgres_test_db is None:
                    raise ValueError("Configuration Error: Cannot set test database")

                # Create a temporary test runtime_database engine and pool that will manage connections and execute queries
                url_object = URL.create(
                    POSTGRESQL_DRIVER_NAME,
                    username=RuntimePostgresHelper.postgres_test_db.current_user,
                    host=RuntimePostgresHelper.postgres_test_db.pg_socket_dir,
                    database=config.POSTGRES_RUNTIME_DATABASE_NAME,
                )
                """Create the url to connect to the db."""
                engine = create_async_engine(
                    url_object,
                    poolclass=AsyncAdaptedQueuePool,
                    pool_size=RuntimeDatabaseManager.get_concurrency_count(),
                    pool_timeout=30,
                    pool_recycle=30,
                )
                """Create the engine."""

                RuntimePostgresHelper._is_test = True
                """Set the test mode."""
            else:
                """Handle the development configuration."""
                log.info("Using Development Postgres Runtime Database")

                # Create a runtime_database engine and pool that will manage connections and execute queries
                url_object = URL.create(
                    POSTGRESQL_DRIVER_NAME,
                    username=config.POSTGRES_DATABASE_USERNAME,
                    password=config.POSTGRES_DATABASE_PASSWORD,
                    host=config.POSTGRES_DATABASE_HOST,
                    port=config.POSTGRES_DATABASE_PORT,
                    database=config.POSTGRES_RUNTIME_DATABASE_NAME,
                )
                """Create the url to connect to the db."""
                engine = create_async_engine(
                    url_object,
                    poolclass=SingletonThreadPool,
                    connect_args={"connect_timeout": 1000},
                )
                """Create the engine."""

        return engine

    @staticmethod
    async def shutdown_database() -> None:
        """
        Shuts down the PostgreSQL runtime_database connection.

        This method handles the shutdown of the PostgreSQL runtime_database. For test
        databases, it performs cleanup operations, including removing the temporary
        runtime_database files and directories.
        """
        log.info("Shutting down Postgres runtime runtime_database")

        if RuntimePostgresHelper._is_test and RuntimePostgresHelper.postgres_test_db is not None:
            """If it is a test runtime_database."""
            log.info("Cleaning up Postgres Test Database")
            RuntimePostgresHelper.postgres_test_db.cleanup()
            """Clean up the temp runtime_database."""

            log.info(f"Delete data dir: {RuntimePostgresHelper.postgres_test_db.pg_data_dir}")
            shutil.rmtree(RuntimePostgresHelper.postgres_test_db.pg_data_dir)
            """Remove the data dir."""
            log.info(f"Delete socket dir: {RuntimePostgresHelper.postgres_test_db.pg_socket_dir}")
            shutil.rmtree(RuntimePostgresHelper.postgres_test_db.pg_socket_dir)
            """Remove the socket dir."""
            if RuntimePostgresHelper.pg_runtime_dirname is not None:
                """Remove the runtime folder."""
                log.info(f"Delete temp dir: {RuntimePostgresHelper.pg_runtime_dirname}")
                shutil.rmtree(RuntimePostgresHelper.pg_runtime_dirname)
            RuntimePostgresHelper.postgres_test_db = None
            """Remove the temp db reference."""
            RuntimePostgresHelper._is_test = False
            """Reset the test flag."""

    @staticmethod
    async def check_connection(config: Configuration, engine: AsyncEngine) -> None:
        """
        Checks the PostgreSQL runtime_database connection and performs setup.

        This method checks the runtime_database connection, retrieves the PostgreSQL
        version, and logs the result.

        Args:
            config (Configuration): The application configuration.
            engine (AsyncEngine): The SQLAlchemy async engine.
        """
        try:
            """Try to connect to the runtime_database."""
            log.info("Check Postgres runtime runtime_database connection...")

            async with engine.connect() as connection:
                """Open a connection."""
                version = await connection.execute(text("SELECT version();"))
                """Get the version."""
                await connection.commit()
                """Commit the operation."""

            log.info(f"Database Version: {version.scalars().one_or_none()}")
            """Log the version."""

            log.info("Runtime Database connected OK.")
        except DatabaseError:
            """Handle the potential exception."""
            log.exception("Runtime Database Connection Error", exc_info=True)

    @classmethod
    async def create_tables(cls, tables: list[str]) -> None:
        """
        Creates tables in the PostgreSQL runtime_database.

        This method creates runtime_database tables using the SQLAlchemy metadata.

        Args:
            tables (List[str], optional): An optional list of table names to
                create. If None, all tables defined in
                `RuntimeBase.metadata` will be created. Defaults to None.
        """
        log.info("Create runtime Postgres tables")
        await super().create_tables(tables=tables)
        """Create the tables."""

    @classmethod
    async def drop_tables(cls, tables: list[str]) -> None:
        """
        Drops tables from the PostgreSQL runtime_database.

        This method drops runtime_database tables using the SQLAlchemy metadata.

        Args:
            tables (List[str], optional): An optional list of table names to
                drop. If None, all tables defined in
                `RuntimeBase.metadata` will be dropped. Defaults to None.
        """
        log.info("Drop runtime Postgres tables")
        await super().drop_tables(tables=tables)
        """Drop the tables."""

    @staticmethod
    async def vacuum(table_name: str, is_full: bool, is_analyze: bool, engine: AsyncEngine) -> None:
        """
        Initate a vacuum on a table.
        Args:
            table_name: The name of the table to vacuum.
            is_full: If True, performs a full vacuum.
            is_analyze: If True, performs an analyze operation.
            engine: The SQLAlchemy async engine connected to the runtime_database.
        """
        log.debug(f"VACUUM {table_name}")

        query = "VACUUM"
        if is_full:
            query += " FULL"
        if is_analyze:
            query += " ANALYZE"
        query += " " + table_name
        query += ";"

        async with engine.execution_options(isolation_level="AUTOCOMMIT").connect() as connection:
            await connection.execute(text(query))
            await connection.commit()

    @staticmethod
    def is_vacuum_full() -> bool:
        """
        Indicates whether PostgreSQL supports full vacuum operations.

        Returns:
            bool: True, as this is supported.
        """
        return True

    @staticmethod
    def is_vacuum_analyze() -> bool:
        """
        Indicates whether PostgreSQL supports analyze operations after a vacuum.

        Returns:
            bool: True, as this is supported.
        """
        return True

    @staticmethod
    def generate_insert_query(
        schema_class: Type[RuntimeConcreteTable],
        values: dict,
        on_conflict_do_nothing: bool = False,
    ) -> ReturningInsert[tuple[RuntimeConcreteTable]]:
        """
        Generates an SQL insert query for PostgreSQL.

        This method generates an insert query for a single record, including
        the option to do nothing on conflict.

        Args:
            schema_class (Type[RuntimeConcreteTable]): The schema class for
                the table.
            values (dict): A dictionary of values to insert.
            on_conflict_do_nothing (bool, optional): Whether to do nothing
                on conflict. Defaults to False.

        Returns:
            ReturningInsert[tuple[RuntimeConcreteTable]]: The insert query.
        """
        if on_conflict_do_nothing:
            """If the `on_conflict_do_nothing` flag is enable."""
            return (
                insert(schema_class).on_conflict_do_nothing().values(values).returning(schema_class)
            )
        else:
            """If the `on_conflict_do_nothing` flag is disable."""
            return insert(schema_class).values(values).returning(schema_class)

    @staticmethod
    def generate_insert_bulk_query(
        schema_class: Type[RuntimeConcreteTable],
        values_list: list[dict],
        on_conflict_do_nothing: bool = False,
    ) -> Insert:
        """
        Generates an SQL bulk insert query for PostgreSQL.

        This method generates an insert query for multiple records, including
        the option to do nothing on conflict.

        Args:
            schema_class (Type[RuntimeConcreteTable]): The schema class for
                the table.
            values_list (List[dict]): A list of dictionaries, each containing
                values to insert.
            on_conflict_do_nothing (bool, optional): Whether to do nothing
                on conflict. Defaults to False.

        Returns:
            Insert[tuple[RuntimeConcreteTable]]: The bulk insert query.
        """
        if on_conflict_do_nothing:
            """If the `on_conflict_do_nothing` flag is enable."""
            return insert(schema_class).on_conflict_do_nothing().values(values_list)
        else:
            return insert(schema_class).values(values_list)
