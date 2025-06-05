import logging
from typing import Type

from sqlalchemy import Engine, create_engine, text, StaticPool
from sqlalchemy.dialects.sqlite import insert, Insert
from sqlalchemy.exc import DatabaseError
from sqlalchemy.sql.dml import ReturningInsert

from musigree.config import Configuration
from musigree.offline.database.offline_database_helper import (
    OfflineDatabaseHelper,
    ConcreteTable,
)

log = logging.getLogger(__name__)


class OfflineSqliteHelper(OfflineDatabaseHelper):

    @staticmethod
    def setup_database(config: Configuration) -> Engine:
        log.info("Using Sqlite Offline Database")
        # if config[TESTING_KEY]:
        #     engine = create_engine(
        #         "sqlite://",
        #         connect_args={
        #             "check_same_thread": False,
        #         },
        #         poolclass=StaticPool,
        #     )
        # else:

        assert config.SQLITE_OFFLINE_DATABASE_NAME is not None, (
            "Configuration Error: SQLITE_OFFLINE_DATABASE_NAME is not set"
        )

        target_path = config.SQLITE_OFFLINE_DATABASE_NAME
        target_parent = target_path.parent
        target_parent.mkdir(parents=True, exist_ok=True)
        log.info(f"Sqlite Database: {target_path}")

        engine = create_engine(
            f"sqlite:///{target_path}",
            connect_args={
                "check_same_thread": False,
            },
            poolclass=StaticPool,
        )
        return engine

    @staticmethod
    def shutdown_database() -> None:
        log.info("Shutting down Sqlite offline database")

    @staticmethod
    def check_connection(config: Configuration, engine: Engine) -> None:
        try:
            log.info("Check Sqlite offline database connection...")

            with engine.connect() as connection:
                version = connection.execute(
                    text("SELECT sqlite_version() AS version;")
                )
                log.info(f"Database Version: {version.scalars().one_or_none()}")

            # Reset Sqlite if already exists
            with engine.connect() as connection:
                connection.execute(text("pragma writable_schema=1;"))
                connection.execute(text("DELETE FROM sqlite_master;"))
                connection.execute(text("pragma writable_schema=0;"))

            with engine.connect() as connection:
                connection.execute(text("VACUUM;"))

            with engine.connect() as connection:
                connection.execute(text("pragma integrity_check;"))

                # Setup Sqlite
                # connection.execute(text("pragma journal_mode=MEMORY;"))
                # connection.execute(text("pragma synchronous=OFF;"))
                # connection.execute(text("pragma cache_size=-10000;"))
                # connection.execute(text("pragma temp_store=MEMORY;"))
                # connection.execute(text("pragma foreign_keys=ON;"))

                # Setup Sqlite
                connection.execute(text("pragma journal_mode=WAL;"))
                connection.execute(text("pragma journal_size_limit = 6144000;"))
                connection.execute(text("pragma synchronous=NORMAL;"))
                connection.execute(text("pragma cache_size=-10000;"))
                connection.execute(text("pragma temp_store=MEMORY;"))
                connection.execute(text("pragma foreign_keys=ON;"))

                connection.commit()
                log.info("Offline Database connected OK.")
        except DatabaseError:
            log.exception("Offline Database Connection Error", exc_info=True)

    @classmethod
    def create_tables(cls, tables: list[str]) -> None:
        log.info("Create Offline Sqlite tables")
        super().create_tables(tables=tables)

    @classmethod
    def drop_tables(cls, tables: list[str]) -> None:
        log.info("Drop Offline Sqlite tables")
        super().drop_tables(tables=tables)

    @staticmethod
    def has_vacuum_tablename() -> bool:
        return False

    @staticmethod
    def is_vacuum_full() -> bool:
        return False

    @staticmethod
    def is_vacuum_analyze() -> bool:
        return False

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
        values_list: list[dict],
        on_conflict_do_nothing=False,
    ) -> Insert:
        if on_conflict_do_nothing:
            return insert(schema_class).on_conflict_do_nothing().values(values_list)
        else:
            return insert(schema_class).values(values_list)
