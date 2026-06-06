"""
This module defines the `RuntimeSqliteHelper` class, which provides
functionality for managing a SQLite runtime database in the Musigree system.

It extends the `RuntimeDatabaseHelper` abstract base class to provide
SQLite-specific implementations of runtime_database setup, shutdown, connection
checking, table creation/deletion, and query generation.

Key functionalities include:
    - **Database Setup**: `setup_database` creates a SQLite runtime_database engine,
      handling the creation of the runtime_database file if it does not exist.
    - **Database Shutdown**: `shutdown_database` provides a placeholder for
      shutting down the runtime_database, as SQLite does not require explicit
      shutdown.
    - **Connection Checking**: `check_connection` checks the runtime_database
      connection and performs SQLite-specific setup, such as enabling WAL
      journaling and setting cache size.
    - **Table Management**: `create_tables` and `drop_tables` implement
      table creation and deletion using the SQLAlchemy metadata.
    - **Query Generation**: `generate_insert_query` and
      `generate_insert_bulk_query` provide SQLite-specific implementations
      for generating insert queries, including support for "on conflict do
      nothing" behavior.
    - **Vacuum Support**: Indicates that SQLite does not support table-specific
      vacuuming or full/analyze vacuum options.
    - **File Management**: Creates the parent folder of the SQLite runtime_database file
    if it does not exist.
    - **Pool Management**: Use `NullPool` to manage the connection pool.
    - **Journal management**: Use `WAL` journaling.

The `RuntimeSqliteHelper` class interacts with the following components:
    - `sqlalchemy.Engine`: For creating and managing runtime_database connections.
    - `sqlalchemy.create_engine`: For creating SQLite engines.
    - `sqlalchemy.text`: For executing raw SQL queries.
    - `sqlalchemy.dialects.sqlite.insert`: For generating SQLite-specific
      insert queries.
    - `sqlalchemy.NullPool`: To manage the connection pool.
    - `pathlib.Path`: For managing file paths.
    - `musigree.config.Configuration`: For accessing application
      configuration settings.
    - `musigree.runtime.runtime_database.runtime_database_helper.RuntimeDatabaseHelper`:
      The base class for runtime_database helper classes.
    - `musigree.runtime.runtime_database.runtime_base_table.RuntimeConcreteTable`:
        For type hinting for table classes.
    - `logging`: For logging operations.

The module utilizes `logging` for logging operations, `pathlib` for file path
operations, `sqlalchemy` for runtime_database operations, and `typing` for type
hinting. It interacts with `musigree` library for specific configuration and
runtime operation.
"""

import logging
import os
import sys
from sqlite3 import OperationalError
from typing import Type

from sqlalchemy import text, StaticPool, URL, Pool, AsyncAdaptedQueuePool, exc
from sqlalchemy.dialects.sqlite import insert, Insert
from sqlalchemy.exc import DatabaseError
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlalchemy.sql.dml import ReturningInsert

from musigree.config import Configuration
from musigree.constants import SQLITE_DRIVER_NAME
from musigree.logging_config import LOGGING_TRACE
from musigree.runtime.runtime_database.runtime_database_helper import (
    RuntimeDatabaseHelper,
    RuntimeConcreteTable,
)
from musigree.runtime.runtime_database_manager import RuntimeDatabaseManager

log = logging.getLogger(__name__)
"""
The logger for the RuntimeSqliteHelper module.
"""


class RuntimeSqliteHelper(RuntimeDatabaseHelper):
    """
    Provides functionality for managing a SQLite runtime runtime_database.

    This class extends `RuntimeDatabaseHelper` to provide SQLite-specific
    implementations for runtime_database operations.
    """

    @staticmethod
    async def setup_database(config: Configuration) -> AsyncEngine:
        """
        Sets up the SQLite runtime_database connection and returns the engine.

        This method creates a SQLite runtime_database file if it does not exist and
        returns the SQLAlchemy engine.

        Args:
            config (Configuration): The application configuration.

        Returns:
            AsyncEngine: The SQLAlchemy async engine.
        """
        log.info("Using Sqlite Runtime Database")

        assert config.SQLITE_RUNTIME_DATABASE_NAME is not None, (
            "Configuration Error: SQLITE_RUNTIME_DATABASE_NAME is not set"
        )

        # The path to the SQLite runtime_database file.
        target_path = config.SQLITE_RUNTIME_DATABASE_NAME
        log.info(f"Sqlite runtime_database path: {target_path}")

        # target_parent = target_path.parent
        """Get the parent folder of the runtime_database file."""
        # target_parent.mkdir(parents=True, exist_ok=True)
        """Create the parent folder if it does not exist."""

        if config.IS_READ_ONLY:
            query = {
                "mode": "ro",
                "immutable": "1",
            }
        else:
            query = {}

        target_url = URL.create(SQLITE_DRIVER_NAME, database=str(target_path), query=query)

        log.info(f"Sqlite Database URL: {target_url}")

        poolclass: type[Pool]
        engine: AsyncEngine
        if config.IS_READ_ONLY:
            poolclass = AsyncAdaptedQueuePool
            engine = create_async_engine(
                target_url,
                connect_args={
                    "check_same_thread": False,
                    "timeout": 60,
                },
                poolclass=poolclass,
                pool_size=4,
                max_overflow=0,
            )
        else:
            # During loading we have a single thread, so we can use a static pool
            poolclass = StaticPool
            engine = create_async_engine(
                target_url,
                connect_args={
                    "check_same_thread": False,
                    "timeout": 600,
                },
                poolclass=poolclass,
            )

        """Create the engine."""
        return engine

    @staticmethod
    async def shutdown_database() -> None:
        """
        Shuts down the SQLite runtime_database connection.

        This method is a placeholder as SQLite does not require explicit
        shutdown.
        """
        log.info("Shutting down Sqlite Runtime Database")

    @staticmethod
    def engine_on_connect(dbapi_con, connection_record):  # type: ignore
        try:
            """Attempt to connect to the runtime_database."""
            log.info("Check Sqlite runtime runtime_database connection...")

            # Setup Sqlite for development
            dbapi_con.execute("pragma journal_mode=MEMORY;")
            dbapi_con.execute("pragma journal_size_limit=6144000;")
            dbapi_con.execute("pragma locking_mode=EXCLUSIVE;")

            # Common for dev and prod
            dbapi_con.execute("pragma mmap_size=24000000000;")
            dbapi_con.execute("pragma synchronous=OFF;")
            dbapi_con.execute("pragma cache_size=-32768;")
            dbapi_con.execute("pragma temp_store=MEMORY;")
            dbapi_con.execute("pragma foreign_keys=OFF;")

            # dbapi_con.commit()
            """Commit the operation."""

            log.info("Runtime Database connected OK.")
        except (DatabaseError, OperationalError):
            """Handle runtime_database errors."""
            log.error("Runtime Database Connection Error")
            sys.exit("Runtime Database Connection Error")

        if RuntimeDatabaseManager.get_concurrency_count() > 1:
            if LOGGING_TRACE:
                log.debug(f"New engine connection: {dbapi_con}")
            connection_record.info["pid"] = os.getpid()

    @staticmethod
    def engine_on_connect_read_only(dbapi_con, connection_record):  # type: ignore
        try:
            """Attempt to connect to the runtime_database."""
            log.info("Check Sqlite runtime runtime_database connection...")

            # Setup Sqlite read only
            dbapi_con.execute("pragma query_only=ON;")
            dbapi_con.execute("pragma journal_mode=OFF;")
            dbapi_con.execute("pragma locking_mode=NORMAL;")

            # Common for dev and prod
            dbapi_con.execute("pragma mmap_size=24000000000;")
            dbapi_con.execute("pragma synchronous=OFF;")
            dbapi_con.execute("pragma cache_size=-32768;")
            dbapi_con.execute("pragma temp_store=MEMORY;")
            dbapi_con.execute("pragma foreign_keys=OFF;")

            dbapi_con.commit()
            """Commit the operation."""

            log.info("Runtime Database connected OK.")
        except (DatabaseError, OperationalError):
            """Handle runtime_database errors."""
            log.error("Runtime Database Connection Error")
            sys.exit("Runtime Database Connection Error")

        if RuntimeDatabaseManager.get_concurrency_count() > 1:
            if LOGGING_TRACE:
                log.debug(f"New engine connection: {dbapi_con}")
            connection_record.info["pid"] = os.getpid()

    @staticmethod
    def engine_on_checkout(dbapi_con, connection_record, connection_proxy):  # type: ignore
        if RuntimeDatabaseManager.get_concurrency_count() > 1:
            pid = os.getpid()
            if connection_record.info["pid"] != pid:
                log.error(f"New engine checkout using wrong pid: {dbapi_con}")

                connection_record.dbapi_connection = connection_proxy.dbapi_connection = None
                raise exc.DisconnectionError(
                    "Connection record belongs to pid %s, "
                    "attempting to check out in pid %s" % (connection_record.info["pid"], pid)
                )

    @staticmethod
    async def check_connection(config: Configuration, engine: AsyncEngine) -> None:
        """
        Checks the SQLite runtime_database connection and performs setup.

        This method checks the runtime_database connection, retrieves the SQLite
        version, and performs SQLite-specific setup, such as enabling WAL
        journaling, setting cache size, and enabling foreign keys.

        Args:
            config (Configuration): The application configuration.
            engine (Engine): The SQLAlchemy engine.
        """
        try:
            """Attempt to connect to the runtime_database."""
            log.info("Check Sqlite runtime runtime_database connection...")

            async with engine.connect() as connection:
                """Open a connection."""
                version = await connection.execute(text("SELECT sqlite_version() AS version;"))
                """Get the sqlite version."""
                log.info(f"Database Version: {version.scalars().one_or_none()}")
                """Log the version."""

                await connection.commit()
                """Commit the operation."""

            log.info("Runtime Database connected OK.")
        except (DatabaseError, OperationalError):
            """Handle runtime_database errors."""
            log.error("Runtime Database Connection Error")
            sys.exit("Runtime Database Connection Error")

    @classmethod
    async def create_tables(cls, tables: list[str]) -> None:
        """
        Creates tables in the SQLite runtime_database.

        This method creates runtime_database tables using the SQLAlchemy metadata.

        Args:
            tables (list[str], optional): An optional list of table names to
                create. If None, all tables defined in
                `RuntimeBase.metadata` will be created. Defaults to None.
        """
        log.info("Create runtime Sqlite tables")
        await super().create_tables(tables=tables)
        """Create the table."""

    @classmethod
    async def drop_tables(cls, tables: list[str]) -> None:
        """
        Drops tables from the SQLite runtime_database.

        This method drops runtime_database tables using the SQLAlchemy metadata.

        Args:
            tables (List[str], optional): An optional list of table names to
                drop. If None, all tables defined in
                `RuntimeBase.metadata` will be dropped. Defaults to None.
        """
        log.info("Drop runtime Sqlite tables")
        await super().drop_tables(tables=tables)
        """Drop the table."""

    @staticmethod
    async def vacuum(table_name: str, is_full: bool, is_analyze: bool, engine: AsyncEngine) -> None:
        """
        Performs a VACUUM operation on the runtime_database.

        Args:
            table_name: The name of the table to vacuum. Not used in SQLite.
            is_full: If True, performs a `VACUUM FULL` operation.
            is_analyze: If True, performs a `VACUUM ANALYZE` operation.
            engine: The SQLAlchemy engine connected to the runtime_database.
        """
        log.debug(f"VACUUM {table_name}")

        query = "VACUUM"
        if is_full:
            query += " FULL"
        if is_analyze:
            query += " ANALYZE"
        query += ";"

        async with engine.connect() as connection:
            await connection.execute(text(query))

    @staticmethod
    def is_vacuum_full() -> bool:
        """
        Indicates whether SQLite supports full vacuum operations.

        Returns:
            bool: False, as this is not supported.
        """
        return False

    @staticmethod
    def is_vacuum_analyze() -> bool:
        """
        Indicates whether SQLite supports analyze operations after a vacuum.

        Returns:
            bool: False, as this is not supported.
        """
        return False

    @staticmethod
    def generate_insert_query(
        schema_class: Type[RuntimeConcreteTable],
        values: dict,
        on_conflict_do_nothing: bool = False,
    ) -> ReturningInsert[tuple[RuntimeConcreteTable]]:
        """
        Generates an SQL insert query for SQLite.

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
            """If `on_conflict_do_nothing` is enabled."""
            return (
                insert(schema_class).on_conflict_do_nothing().values(values).returning(schema_class)
            )
        else:
            """If `on_conflict_do_nothing` is disabled."""
            return insert(schema_class).values(values).returning(schema_class)

    @staticmethod
    def generate_insert_bulk_query(
        schema_class: Type[RuntimeConcreteTable],
        values_list: list[dict],
        on_conflict_do_nothing: bool = False,
    ) -> Insert:
        """
        Generates an SQL bulk insert query for SQLite.

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
            """If `on_conflict_do_nothing` is enabled."""
            return insert(schema_class).on_conflict_do_nothing().values(values_list)
        else:
            """If `on_conflict_do_nothing` is disabled."""
            return insert(schema_class).values(values_list)
