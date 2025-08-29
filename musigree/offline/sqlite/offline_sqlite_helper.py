import logging
from typing import Type

from sqlalchemy import text, StaticPool
from sqlalchemy.dialects.sqlite import insert, Insert
from sqlalchemy.exc import DatabaseError
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from musigree.config import Configuration
from musigree.offline.database.offline_database_helper import (
    OfflineDatabaseHelper,
    ConcreteTable,
)

log = logging.getLogger(__name__)


class OfflineSqliteHelper(OfflineDatabaseHelper):
    @staticmethod
    async def setup_database(config: Configuration) -> AsyncEngine:
        log.info("Using Sqlite Offline Database")

        assert config.SQLITE_OFFLINE_DATABASE_NAME is not None, (
            "Configuration Error: SQLITE_OFFLINE_DATABASE_NAME is not set"
        )

        target_path = config.SQLITE_OFFLINE_DATABASE_NAME
        target_parent = target_path.parent
        target_parent.mkdir(parents=True, exist_ok=True)
        log.info(f"Sqlite Database: {target_path}")

        engine = create_async_engine(
            f"sqlite+aiosqlite:///{target_path}",
            connect_args={
                # "check_same_thread": True,
                "check_same_thread": False,
            },
            # poolclass=NullPool,
            poolclass=StaticPool,
        )
        return engine

    @staticmethod
    async def shutdown_database() -> None:
        log.info("Shutting down Sqlite offline database")

    @staticmethod
    async def check_connection(config: Configuration, engine: AsyncEngine) -> None:
        try:
            log.info("Check Sqlite offline database connection...")

            async with engine.connect() as connection:
                version = await connection.execute(
                    text("SELECT sqlite_version() AS version;")
                )
                log.info(f"Database Version: {version.scalars().one_or_none()}")

            # Reset Sqlite if already exists
            async with engine.connect() as connection:
                await connection.execute(text("pragma writable_schema=1;"))
                await connection.execute(text("DELETE FROM sqlite_master;"))
                await connection.execute(text("pragma writable_schema=0;"))

            async with engine.connect() as connection:
                await connection.execute(text("VACUUM;"))

            async with engine.connect() as connection:
                await connection.execute(text("pragma integrity_check;"))

                # Setup Sqlite
                await connection.execute(text("pragma journal_mode=MEMORY;"))
                await connection.execute(text("pragma journal_size_limit = 6144000;"))
                await connection.execute(text("pragma synchronous=OFF;"))
                await connection.execute(text("pragma cache_size=-10000;"))
                await connection.execute(text("pragma temp_store=MEMORY;"))
                await connection.execute(text("pragma foreign_keys=ON;"))

                # Setup Sqlite
                # await connection.execute(text("pragma journal_mode=WAL;"))
                # await connection.execute(text("pragma journal_size_limit = 6144000;"))
                # await connection.execute(text("pragma synchronous=NORMAL;"))
                # await connection.execute(text("pragma cache_size=-10000;"))
                # await connection.execute(text("pragma temp_store=MEMORY;"))
                # await connection.execute(text("pragma foreign_keys=ON;"))

                await connection.commit()
                log.info("Offline Database connected OK.")
        except DatabaseError:
            log.exception("Offline Database Connection Error", exc_info=True)

    @classmethod
    async def create_tables(cls, tables: list[str]) -> None:
        log.info("Create Offline Sqlite tables")
        await super().create_tables(tables=tables)

    @classmethod
    async def drop_tables(cls, tables: list[str]) -> None:
        log.info("Drop Offline Sqlite tables")
        await super().drop_tables(tables=tables)

    @classmethod
    async def vacuum(
        cls, table_name: str, is_full: bool, is_analyze: bool, engine: AsyncEngine
    ) -> None:
        """
        Performs a VACUUM operation on the database.

        Args:
            table_name: The name of the table to vacuum. Not used in SQLite.
            is_full: If True, performs a `VACUUM FULL` operation.
            is_analyze: If True, performs a `VACUUM ANALYZE` operation.
            engine: The SQLAlchemy engine connected to the database.
        """
        log.debug(f"VACUUM {table_name}")

        query = "VACUUM"
        if is_full:
            query += " FULL"
        if is_analyze:
            query += " ANALYZE"
        query += ";"

        # try:
        #     loop = asyncio.get_running_loop()
        # except RuntimeError:
        #     """Check if the event loop is already running."""
        #     loop = asyncio.new_event_loop()
        #     asyncio.set_event_loop(loop)
        #     """Set a new event loop if none exists."""
        #
        # if OfflineDatabaseManager.get_concurrency_count() > 1:
        #     """Check if concurrency is enabled."""
        #     cls.initialize(loop)
        #     """Initialize the database helper."""

        async with engine.connect() as connection:
            await connection.execute(text(query))

    @staticmethod
    def is_vacuum_full() -> bool:
        return False

    @staticmethod
    def is_vacuum_analyze() -> bool:
        return False

    @staticmethod
    def generate_insert_query(
        schema_class: Type[ConcreteTable],
        values: dict,
        on_conflict_do_nothing: bool = False,
    ) -> Insert:
        if on_conflict_do_nothing:
            return insert(schema_class).on_conflict_do_nothing().values(values)
        else:
            return insert(schema_class).values(values)

    @staticmethod
    def generate_insert_bulk_query(
        schema_class: Type[ConcreteTable],
        values_list: list[dict],
        on_conflict_do_nothing: bool = False,
    ) -> Insert:
        if on_conflict_do_nothing:
            return insert(schema_class).on_conflict_do_nothing().values(values_list)
        else:
            return insert(schema_class).values(values_list)
