import logging
from abc import ABC, abstractmethod
from typing import Type, List, Any

from sqlalchemy import Engine, Table
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.dml import ReturningInsert, Insert

from musigree.config import Configuration
from musigree.offline.database.base_table import Base, ConcreteTable
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
        offline_engine (Engine | None): The SQLAlchemy engine for the offline database.
        offline_session_factory (sessionmaker | None): The session factory for the offline database.
    """

    offline_engine: Engine | None = None
    """The SQLAlchemy engine for the offline database."""
    offline_session_factory: sessionmaker | None = None
    """The session factory for the offline database."""

    @staticmethod
    @abstractmethod
    def setup_database(config: Configuration) -> Engine:
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
    def shutdown_database() -> None:
        """
        Abstract method to shut down the database connection.
        """
        pass

    @classmethod
    def initialize(cls) -> None:
        """
        Initializes the database connection for a new process.

        Ensures that the parent process's database connections are not touched in
        the new connection pool.
        """
        from musigree.offline.offline_database_manager import OfflineDatabaseManager

        OfflineDatabaseManager.offline_database_helper.offline_engine.dispose(
            close=False
        )

    @staticmethod
    @abstractmethod
    def check_connection(config: Configuration, engine: Engine) -> None:
        """
        Abstract method to check the database connection.

        Args:
            config: The database configuration.
            engine: The SQLAlchemy engine.
        """
        pass

    @classmethod
    @abstractmethod
    def create_tables(cls, tables: List[str] = None) -> None:
        """
        Creates tables in the database.

        Args:
            tables: A list of table names to create. If None, all tables are created.
        """
        from musigree.offline.offline_database_manager import OfflineDatabaseManager

        # for table in ALL_OFFLINE_DATABASE_TABLES:
        #     log.debug(f"table definition for: {table.__tablename__}")
        for table in Base.metadata.tables:
            log.debug(f"table in metadata: {table}")
        table_definitions: List[Table] = [
            Base.metadata.tables[table_name] for table_name in tables
        ]
        for table in table_definitions:
            log.debug(f"creating table: {table.name}")

        Base.metadata.create_all(
            OfflineDatabaseManager.offline_database_helper.offline_engine,
            checkfirst=True,
            tables=table_definitions,
        )

    @classmethod
    @abstractmethod
    def drop_tables(cls, tables: List[str] = None) -> None:
        """
        Drops tables from the database.

        Args:
            tables: A list of table names to drop. If None, all tables are dropped.
        """
        from musigree.offline.offline_database_manager import OfflineDatabaseManager

        if tables is not None:
            table_definitions: List[Table] = [
                Base.metadata.tables[table_name] for table_name in tables
            ]
            for table in table_definitions:
                log.debug(f"deleting table: {table.name}")
                table.drop(
                    OfflineDatabaseManager.offline_database_helper.offline_engine,
                    checkfirst=True,
                )
        else:
            Base.metadata.drop_all(
                OfflineDatabaseManager.offline_database_helper.offline_engine,
                checkfirst=True,
            )

    @staticmethod
    @abstractmethod
    def has_vacuum_tablename() -> bool:
        """
        Abstract method to indicate whether vacuum should be performed on a table.

        Returns:
            bool: True if vacuum should be performed on a table, False otherwise.
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
        schema_class: Type[ConcreteTable], values: dict, on_conflict_do_nothing=False
    ) -> ReturningInsert[tuple[ConcreteTable]]:
        """
        Abstract method to generate an insert query.

        Args:
            schema_class: The table schema class.
            values: The values to insert.
            on_conflict_do_nothing: Whether to do nothing on conflict.

        Returns:
            ReturningInsert[tuple[ConcreteTable]]: The insert query.
        """
        pass

    @staticmethod
    @abstractmethod
    def generate_insert_bulk_query(
        schema_class: Type[ConcreteTable],
        values: List[dict],
        on_conflict_do_nothing=False,
    ) -> Insert[tuple[ConcreteTable]]:
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
    def get_relation_by_key(
        cls,
        relation_repository: RelationRepository,
        relation_release_year_repository: RelationReleaseYearRepository,
        key: dict[str, Any],
    ) -> Relation:
        """
        Retrieves a relation by its key.

        Args:
            relation_repository: The relation repository.
            relation_release_year_repository: The relation release year repository.
            key: The key to search for.

        Returns:
            Relation: The found relation.
        """
        relation_internal = relation_repository.find_by_key(key)
        relation = relation_internal.to_relation()

        relation_release_years = relation_release_year_repository.get(relation.id)
        relation.releases = {}
        for relation_release_year in relation_release_years:
            relation.releases[str(relation_release_year.release_id)] = (
                relation_release_year.year
            )
        return relation
