import logging
from abc import ABC, abstractmethod
from typing import Type, List, Any

from sqlalchemy import Table
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker
from sqlalchemy.sql.ddl import DropTable
from sqlalchemy.sql.dml import Insert

from musigree.config import Configuration
from musigree.offline.database.base_table import OfflineBase, ConcreteTable
from musigree.offline.database.relation_release_year_repository import (
    RelationReleaseYearRepository,
)
from musigree.offline.database.relation_repository import RelationRepository
from musigree.offline.domain.relation import Relation

log = logging.getLogger(__name__)


class OfflineDatabaseHelper(ABC):
    """
    Abstract base class for managing offline database operations.

    This class provides a blueprint for interacting with the offline database,
    including setting up connections, creating and dropping tables, loading data,
    and managing vacuum operations. It also defines constants for graph query limitations.

    Attributes:
        offline_async_engine (Engine | None): The SQLAlchemy engine for the offline database.
        offline_async_session_factory (async_sessionmaker | None): The session factory for the offline database.
    """

    offline_async_engine: AsyncEngine | None = None
    """The SQLAlchemy engine for the offline database."""
    offline_async_session_factory: async_sessionmaker | None = None
    """The session factory for the offline database."""

    @staticmethod
    @abstractmethod
    async def setup_database(config: Configuration) -> AsyncEngine:
        """
        Abstract method to set up the database connection.

        Args:
            config: The database configuration.

        Returns:
            Engine: The SQLAlchemy engine.
        """
        pass

    @staticmethod
    @abstractmethod
    async def shutdown_database() -> None:
        """
        Abstract method to shut down the database connection.
        """
        pass

    @staticmethod
    @abstractmethod
    async def check_connection(config: Configuration, engine: AsyncEngine) -> None:
        """
        Abstract method to check the database connection.

        Args:
            config: The database configuration.
            engine: The SQLAlchemy engine.
        """
        pass

    @classmethod
    @abstractmethod
    async def create_tables(cls, tables: list[str]) -> None:
        """
        Creates tables in the database.

        Args:
            tables: A list of table names to create. If None, all tables are created.
        """
        from musigree.offline.offline_database_manager import OfflineDatabaseManager

        assert OfflineDatabaseManager.offline_database_helper is not None, (
            "OfflineDatabaseManager.offline_database_helper must be initialized before calling create_tables()"
        )
        assert (
            OfflineDatabaseManager.offline_database_helper.offline_async_engine
            is not None
        ), (
            "OfflineDatabaseManager.offline_database_helper.offline_engine must be initialized before calling create_tables()"
        )

        if tables is None:
            return

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
                OfflineBase.metadata.create_all,
                checkfirst=True,
                tables=table_definitions,
            )

    @classmethod
    @abstractmethod
    async def drop_tables(cls, tables: List[str]) -> None:
        """
        Drops tables from the database.

        Args:
            tables: A list of table names to drop. If None, all tables are dropped.
        """
        from musigree.offline.offline_database_manager import OfflineDatabaseManager

        assert OfflineDatabaseManager.offline_database_helper is not None, (
            "OfflineDatabaseManager.offline_database_helper must be initialized before calling create_tables()"
        )
        assert (
            OfflineDatabaseManager.offline_database_helper.offline_async_engine
            is not None
        ), (
            "OfflineDatabaseManager.offline_database_helper.offline_engine must be initialized before calling create_tables()"
        )

        if tables is not None:
            table_definitions: list[Table] = [
                OfflineBase.metadata.tables[table_name] for table_name in tables
            ]
            async with (
                OfflineDatabaseManager.offline_database_helper.offline_async_engine.begin() as conn
            ):
                for table in table_definitions:
                    log.debug(f"deleting table: {table.name}")
                    await conn.execute(DropTable(table, if_exists=True))
                await conn.commit()
        else:
            async with (
                OfflineDatabaseManager.offline_database_helper.offline_async_engine.begin() as conn
            ):
                await conn.run_sync(OfflineBase.metadata.drop_all, checkfirst=True)
                await conn.commit()

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
            engine: The SQLAlchemy engine connected to the database.
        """
        pass

    @staticmethod
    @abstractmethod
    def is_vacuum_full() -> bool:
        """
        Abstract method to indicate whether a full vacuum should be performed.

        Returns:
            bool: True if a full vacuum should be performed, False otherwise.
        """
        pass

    @staticmethod
    @abstractmethod
    def is_vacuum_analyze() -> bool:
        """
        Abstract method to indicate whether a vacuum analyze should be performed.

        Returns:
            bool: True if a vacuum analyze should be performed, False otherwise.
        """
        pass

    @staticmethod
    @abstractmethod
    def generate_insert_query(
        schema_class: Type[ConcreteTable],
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
        pass

    @staticmethod
    @abstractmethod
    def generate_insert_bulk_query(
        schema_class: Type[ConcreteTable],
        values: list[dict],
        on_conflict_do_nothing: bool = False,
    ) -> Insert:
        """
        Abstract method to generate a bulk insert query.

        Args:
            schema_class: The table schema class.
            values: The list of values to insert.
            on_conflict_do_nothing: Whether to do nothing on conflict.

        Returns:
            Insert[tuple[ConcreteTable]]: The bulk insert query.
        """
        pass

    # @classmethod
    # def get_relations_by_entity_id_and_entity_type(
    #     cls,
    #     entity_repository: EntityRepository,
    #     relation_repository: RelationRepository,
    #     relation_release_year_repository: RelationReleaseYearRepository,
    #     entity_id: int,
    #     entity_type: EntityType,
    # ) -> dict[str, Any]:
    #     entity = entity_repository.get_by_entity_id_and_entity_type(
    #         entity_id, entity_type
    #     )
    #     relations = relation_repository.find_by_entity(entity.id)
    #
    #     data = []
    #     for relation in relations:
    #         relation_release_years = relation_release_year_repository.get(relation.id)
    #         relation_releases = {}
    #         for relation_release_year in relation_release_years:
    #             relation_releases[relation_release_year.release_id] = (
    #                 relation_release_year.year
    #             )
    #
    #         # category = RoleType.role_definitions[relation.role]
    #         # if category is None:
    #         #     continue
    #         datum = {
    #             "role": relation.role,
    #             "releases": relation_releases,
    #         }
    #         data.append(datum)
    #     data = {"results": tuple(data)}
    #     return data

    @classmethod
    async def get_relation_by_key(
        cls,
        relation_repository: RelationRepository,
        relation_release_year_repository: RelationReleaseYearRepository,
        key: dict[str, Any],
    ) -> Relation | None:
        """
        Retrieves a relation by its key.

        Args:
            relation_repository: The relation repository.
            relation_release_year_repository: The relation release year repository.
            key: The key to search for.

        Returns:
            Relation: The found relation.
        """
        relation_internal = await relation_repository.find_by_key(key)
        relation = relation_internal.to_relation()

        if relation is not None:
            relation_release_years = await relation_release_year_repository.get(
                relation.id
            )
            relation.releases = {}
            for relation_release_year in relation_release_years:
                relation.releases[str(relation_release_year.release_id)] = (
                    relation_release_year.year
                )
        return relation
