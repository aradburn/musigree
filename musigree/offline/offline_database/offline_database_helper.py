import logging
from abc import ABC, abstractmethod
from collections.abc import Sequence

from sqlalchemy import Table
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker
from sqlalchemy.sql.ddl import DropTable
from sqlalchemy.sql.dml import Insert

from musigree.config import Configuration
from musigree.offline.offline_database.base_table import ConcreteTable, OfflineBase

log = logging.getLogger(__name__)


def _create_all_tables(
    connection: Connection,
    tables: Sequence[Table] | None = None,
    *,
    checkfirst: bool = True,
) -> None:
    """Create offline tables using a sync Connection from AsyncConnection.run_sync.

    MetaData.create_all accepts Engine | Connection | MockConnection, which does
    not match run_sync's Connection-first callable type. This adapter narrows
    the bind so the call is type-safe.
    """
    OfflineBase.metadata.create_all(
        bind=connection,
        tables=tables,
        checkfirst=checkfirst,
    )


class OfflineDatabaseHelper(ABC):
    """
    Abstract base class for managing offline runtime_database operations.

    This class provides a blueprint for interacting with the offline runtime_database,
    including setting up connections, creating and dropping tables, loading data,
    and managing vacuum operations. It also defines constants for graph query limitations.

    Attributes:
        offline_async_engine (Engine | None): The SQLAlchemy engine for the offline runtime_database.
        offline_async_session_factory (async_sessionmaker | None): The session factory for the offline runtime_database.
    """

    offline_async_engine: AsyncEngine | None = None
    """The SQLAlchemy engine for the offline runtime_database."""
    offline_async_session_factory: async_sessionmaker | None = None
    """The session factory for the offline runtime_database."""

    @staticmethod
    @abstractmethod
    async def setup_database(config: Configuration) -> AsyncEngine:
        """
        Abstract method to set up the runtime_database connection.

        Args:
            config: The runtime_database configuration.

        Returns:
            Engine: The SQLAlchemy engine.
        """

    @staticmethod
    @abstractmethod
    async def shutdown_database() -> None:
        """
        Abstract method to shut down the runtime_database connection.
        """

    @staticmethod
    @abstractmethod
    async def check_connection(config: Configuration, engine: AsyncEngine) -> None:
        """
        Abstract method to check the runtime_database connection.

        Args:
            config: The runtime_database configuration.
            engine: The SQLAlchemy engine.
        """

    @classmethod
    @abstractmethod
    async def create_tables(cls, tables: list[str]) -> None:
        """
        Creates tables in the offline_database.

        Args:
            tables: A list of table names to create.
        """
        from musigree.offline.offline_database_manager import OfflineDatabaseManager

        assert OfflineDatabaseManager.offline_database_helper is not None, (
            "OfflineDatabaseManager.offline_database_helper must be initialized before calling create_tables()"
        )
        assert OfflineDatabaseManager.offline_database_helper.offline_async_engine is not None, (
            "OfflineDatabaseManager.offline_database_helper.offline_async_engine must be initialized before calling create_tables()"
        )

        for table in OfflineBase.metadata.tables:
            log.debug(f"table in metadata: {table}")

        table_definitions: list[Table] = [
            OfflineBase.metadata.tables[table_name] for table_name in tables
        ]
        for table_def in table_definitions:
            log.debug(f"creating table: {table_def.name}")

        async with (
            OfflineDatabaseManager.offline_database_helper.offline_async_engine.begin() as conn
        ):
            await conn.run_sync(
                _create_all_tables,
                tables=table_definitions,
                checkfirst=True,
            )

    @classmethod
    @abstractmethod
    async def drop_tables(cls, tables: list[str]) -> None:
        """
        Drops tables from the offline_database.

        Args:
            tables: A list of table names to drop.
        """
        from musigree.offline.offline_database_manager import OfflineDatabaseManager

        assert OfflineDatabaseManager.offline_database_helper is not None, (
            "OfflineDatabaseManager.offline_database_helper must be initialized "
            "before calling drop_tables()"
        )
        assert OfflineDatabaseManager.offline_database_helper.offline_async_engine is not None, (
            "OfflineDatabaseManager.offline_database_helper.offline_async_engine "
            "must be initialized before calling drop_tables()"
        )

        table_definitions: list[Table] = [
            OfflineBase.metadata.tables[table_name] for table_name in tables
        ]
        async with (
            OfflineDatabaseManager.offline_database_helper.offline_async_engine.begin() as conn
        ):
            for table in table_definitions:
                log.debug(f"deleting table: {table.name}")
                await conn.execute(DropTable(table, if_exists=True))

    @classmethod
    @abstractmethod
    async def vacuum(
        cls, table_name: str, is_full: bool, is_analyze: bool, engine: AsyncEngine
    ) -> None:
        """
        Abstract method to initate a vacuum on a table.
        Args:
            table_name: The name of the table to vacuum.
            is_full: If True, performs a full vacuum.
            is_analyze: If True, performs an analyze operation.
            engine: The SQLAlchemy engine connected to the runtime_database.
        """

    @staticmethod
    @abstractmethod
    def is_vacuum_full() -> bool:
        """
        Abstract method to indicate whether a full vacuum should be performed.

        Returns:
            bool: True if a full vacuum should be performed, False otherwise.
        """

    @staticmethod
    @abstractmethod
    def is_vacuum_analyze() -> bool:
        """
        Abstract method to indicate whether a vacuum analyze should be performed.

        Returns:
            bool: True if a vacuum analyze should be performed, False otherwise.
        """

    @staticmethod
    @abstractmethod
    def generate_insert_query(
        schema_class: type[ConcreteTable],
        values: dict,
        on_conflict_do_nothing: bool = False,
    ) -> Insert:
        """
        Abstract method to generate an insert query.

        Args:
            schema_class: The table schema class.
            values: The values to insert.
            on_conflict_do_nothing: Whether to do nothing on conflict.

        Returns:
            Insert: The insert query.
        """

    @staticmethod
    @abstractmethod
    def generate_insert_bulk_query(
        schema_class: type[ConcreteTable],
        values_list: list[dict],
        on_conflict_do_nothing: bool = False,
    ) -> Insert:
        """
        Abstract method to generate a bulk insert query.

        Args:
            schema_class: The table schema class.
            values_list: The list of values to insert.
            on_conflict_do_nothing: Whether to do nothing on conflict.

        Returns:
            Insert[tuple[ConcreteTable]]: The bulk insert query.
        """
