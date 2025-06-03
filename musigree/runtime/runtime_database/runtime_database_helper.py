"""
This module defines the `RuntimeDatabaseHelper` class and related utilities for managing the runtime database.

It provides an abstract base class for interacting with various database backends,
handling database setup, shutdown, table management, and various data access operations.

Key functionalities include:
    - Abstract methods for setting up and shutting down the database.
    - Methods for creating and dropping database tables.
    - Loading tables with initial data (e.g., roles).
    - Generating SQL insert queries.
    - Retrieving network data for entities.
    - Retrieving random entities.
    - Searching text indexes.
    - Managing database connections and sessions.
    - Caching of frequently accessed data.

The `RuntimeDatabaseHelper` class is designed to be subclassed for specific
database implementations, such as SQLite or PostgreSQL. It utilizes SQLAlchemy
for database operations and defines a set of methods that each subclass must
implement.
"""

import logging
from abc import ABC, abstractmethod
from typing import Type, List, Any

from sqlalchemy import Engine, Index, Table
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.dml import ReturningInsert, Insert

from musigree.config import Configuration
from musigree.exceptions import NotFoundError
from musigree.library.cache.cache_manager import CacheManager
from musigree.library.fields.entity_id import to_entity_external_id
from musigree.library.fields.entity_type import EntityType
from musigree.runtime.data_access_layer.entity_details_index import EntityDetailsIndex
from musigree.library.full_text_search.text_search_index import TextSearchIndex
from musigree.runtime.runtime_database.runtime_base_table import (
    RuntimeBase,
    RuntimeConcreteTable,
)
from musigree.runtime.runtime_database.runtime_entity_repository import (
    RuntimeEntityRepository,
)
from musigree.runtime.runtime_database.runtime_relation_repository import (
    RuntimeRelationRepository,
)

log = logging.getLogger(__name__)


class RuntimeDatabaseHelper(ABC):
    """
    Abstract base class for managing the runtime database.

    This class provides an interface for interacting with the runtime database,
    including methods for setting up and shutting down the database, creating
    and dropping tables, loading initial data, and performing various data
    access operations.

    Subclasses should implement the abstract methods to provide database-specific
    functionality.

    Attributes:
        runtime_engine (Engine | None): The SQLAlchemy engine for the runtime database.
        runtime_session_factory (sessionmaker | None): The SQLAlchemy session factory
            for creating database sessions.
        idx_entity_one_id (Index | None): An index for entity one ID.
        idx_entity_two_id (Index | None): An index for entity two ID.
        text_search_index (TextSearchIndex | None): An index for text-based searches.
        entity_details_index (EntityDetailsIndex | None): An index for entity details.
        entity_count_cached (int): A cached count of entities.
        MAX_NODES (int): The maximum number of nodes in a network.
        MAX_NODES_MOBILE (int): The maximum number of nodes in a mobile network.
        MAX_DEGREE (int): The maximum degree of a node in a network.
        MAX_DEGREE_MOBILE (int): The maximum degree of a node in a mobile network.
        LINK_RATIO (int): A ratio for link calculations.
    """

    runtime_engine: Engine
    """The SQLAlchemy engine for the runtime database."""
    runtime_session_factory: sessionmaker
    """The SQLAlchemy session factory for creating database sessions."""

    idx_entity_one_id: Index
    """An index for entity one ID."""
    idx_entity_two_id: Index
    """An index for entity two ID."""

    text_search_index: TextSearchIndex
    """An index for text-based searches."""
    entity_details_index: EntityDetailsIndex
    """An index for entity details."""

    entity_count_cached = 0
    """A cached count of entities."""

    MAX_NODES = 400
    """The maximum number of nodes in a network."""
    MAX_NODES_MOBILE = 25
    """The maximum number of nodes in a mobile network."""

    MAX_DEGREE = 5
    """The maximum degree of a node in a network."""
    # was 12
    MAX_DEGREE_MOBILE = 3
    """The maximum degree of a node in a mobile network."""

    LINK_RATIO = 10
    """A ratio for link calculations."""
    # was 3

    @staticmethod
    @abstractmethod
    def setup_database(config: Configuration) -> Engine:
        """
        Sets up the database connection and returns the engine.

        Args:
            config: The application configuration.

        Returns:
            Engine: The SQLAlchemy engine.
        """
        pass

    @staticmethod
    @abstractmethod
    def shutdown_database() -> None:
        """Shuts down the database connection."""
        pass

    @classmethod
    def initialize(cls) -> None:
        """
        Initializes the database connection.

        Ensures that the parent process's database connections are not touched
        in the new connection pool.
        """
        from musigree.runtime.runtime_database_manager import RuntimeDatabaseManager

        RuntimeDatabaseManager.runtime_database_helper.runtime_engine.dispose(
            close=False
        )

    @staticmethod
    @abstractmethod
    def check_connection(config: Configuration, engine: Engine) -> None:
        """
        Checks the database connection.

        Args:
            config: The application configuration.
            engine: The SQLAlchemy engine.
        """
        pass

    @classmethod
    @abstractmethod
    def create_tables(cls, tables: List[str]) -> None:
        """
        Creates database tables.

        Args:
            tables: An optional list of table names to create. If None, all tables
                defined in `RuntimeBase.metadata` will be created.
        """
        from musigree.runtime.runtime_database_manager import RuntimeDatabaseManager
        from musigree.runtime.runtime_database import ALL_RUNTIME_DATABASE_TABLES

        for table in ALL_RUNTIME_DATABASE_TABLES:
            log.debug(f"table definition for: {table.__tablename__}")
        for table in RuntimeBase.metadata.tables:
            log.debug(f"table in metadata: {table}")
        table_definitions: List[Table] = [
            RuntimeBase.metadata.tables[table_name] for table_name in tables
        ]
        for table in table_definitions:
            log.debug(f"creating table: {table.name}")
        RuntimeBase.metadata.create_all(
            RuntimeDatabaseManager.runtime_database_helper.runtime_engine,
            checkfirst=True,
            tables=table_definitions,
        )

    @classmethod
    @abstractmethod
    def drop_tables(cls, tables: List[str]) -> None:
        """
        Drops database tables.

        Args:
            tables: An optional list of table names to drop. If None, all tables
                defined in `RuntimeBase.metadata` will be dropped.
        """
        from musigree.runtime.runtime_database_manager import RuntimeDatabaseManager

        if tables is not None:
            table_definitions: List[Table] = [
                RuntimeBase.metadata.tables[table_name] for table_name in tables
            ]
            for table in table_definitions:
                log.debug(f"deleting table: {table.name}")
                table.drop(
                    RuntimeDatabaseManager.runtime_database_helper.runtime_engine,
                    checkfirst=True,
                )
        else:
            RuntimeBase.metadata.drop_all(
                RuntimeDatabaseManager.runtime_database_helper.runtime_engine,
                checkfirst=True,
            )

    @staticmethod
    @abstractmethod
    def has_vacuum_tablename() -> bool:
        """
        Indicates whether the database supports vacuuming a specific table.
        """
        pass

    @staticmethod
    @abstractmethod
    def is_vacuum_full() -> bool:
        """
        Indicates whether a full vacuum operation is supported.
        """
        pass

    @staticmethod
    @abstractmethod
    def is_vacuum_analyze() -> bool:
        """
        Indicates whether the analyze operation is supported after a vacuum.
        """
        pass

    @staticmethod
    @abstractmethod
    def generate_insert_query(
        schema_class: Type[RuntimeConcreteTable],
        values: dict,
        on_conflict_do_nothing=False,
    ) -> ReturningInsert[tuple[RuntimeConcreteTable]]:
        """
        Generates an SQL insert query.

        Args:
            schema_class: The schema class for the table.
            values: A dictionary of values to insert.
            on_conflict_do_nothing: Whether to do nothing on conflict.

        Returns:
            ReturningInsert[tuple[RuntimeConcreteTable]]: The insert query.
        """
        pass

    @staticmethod
    @abstractmethod
    def generate_insert_bulk_query(
        schema_class: Type[RuntimeConcreteTable],
        values: List[dict],
        on_conflict_do_nothing=False,
    ) -> Insert[tuple[RuntimeConcreteTable]]:
        """
        Generates an SQL insert bulk query.

        Args:
            schema_class: The schema class for the table.
            values: A list of dictionaries, each containing values to insert.
            on_conflict_do_nothing: Whether to do nothing on conflict.

        Returns:
            Insert[tuple[RuntimeConcreteTable]]: The bulk insert query.
        """
        pass

    @staticmethod
    def get_network(
        entity_repository: RuntimeEntityRepository,
        relation_repository: RuntimeRelationRepository,
        entity_id: int,
        entity_type: EntityType,
        on_mobile,
        roles: List[str],
    ):
        """
        Retrieves network data for an entity.

        Args:
            entity_repository: The entity repository.
            relation_repository: The relation repository.
            entity_id: The ID of the entity.
            entity_type: The type of the entity.
            on_mobile: Whether the request is from a mobile device.
            roles: An optional list of roles to filter by.

        Returns:
            Any: The network data.
        """
        from musigree.runtime.data_access_layer.relation_grapher import (
            RelationGrapher,
        )

        cache = CacheManager.get_cache()

        assert entity_type in (EntityType.ARTIST, EntityType.LABEL)
        template = "musigree:/api/{entity_type}/network/{entity_id}"
        if on_mobile:
            template += "/mobile"

        cache_key = RelationGrapher.make_cache_key(
            template,
            entity_id,
            entity_type,
            roles=roles,
        )
        # cache_key = cache_key.format(entity_type, entity_id)
        if cache_key is not None and len(cache_key) < 200:
            log.debug(f"  get cache_key: {cache_key}")
            data = cache.get(cache_key)
            if data is not None:
                return data

        try:
            entity = entity_repository.get_by_entity_id_and_entity_type(
                entity_id, entity_type
            )
        except NotFoundError:
            return None
        if entity is None:
            return None
        if not on_mobile:
            max_nodes = RuntimeDatabaseHelper.MAX_NODES
            degree = RuntimeDatabaseHelper.MAX_DEGREE
        else:
            max_nodes = RuntimeDatabaseHelper.MAX_NODES_MOBILE
            degree = RuntimeDatabaseHelper.MAX_DEGREE_MOBILE
        relation_grapher = RelationGrapher(
            center_entity=entity,
            degree=degree,
            link_ratio=RuntimeDatabaseHelper.LINK_RATIO,
            max_nodes=max_nodes,
            role_names=roles,
        )
        data = relation_grapher.get_relation_graph(
            entity_repository, relation_repository
        )
        if cache_key is not None and len(cache_key) < 200:
            cache.set(cache_key, data)
        return data

    @staticmethod
    def get_random_entity(
        entity_repository: RuntimeEntityRepository,
    ) -> tuple[int, EntityType]:
        """
        Retrieves a random entity.

        Args:
            entity_repository: The entity repository.

        Returns:
            tuple[int, EntityType]: A tuple containing the entity ID and type.
        """
        # structural_roles = [
        #     "Alias",
        #     "Member Of",
        #     "Sublabel Of",
        # ]
        # if role_names and any(_ not in structural_roles for _ in role_names):
        #     relation = relation_repository.get_random(role_names=role_names)
        #     entity_choice = random.randint(1, 2)
        #     if entity_choice == 1:
        #         entity_type = relation.entity_one_type
        #         entity_id = relation.entity_one_id
        #     else:
        #         entity_type = relation.entity_two_type
        #         entity_id = relation.entity_two_id
        #     log.debug("random link")
        # else:
        counter = 0

        while True:
            random_id = RuntimeDatabaseHelper.search_get_random_id()
            entity_id, entity_type = to_entity_external_id(random_id)
            if entity_type == EntityType.LABEL:
                log.debug("random skip label")
                entity = None
                continue
            try:
                entity = entity_repository.get_by_id(random_id)
            except NotFoundError:
                log.debug("random not found")
                counter += 1
                entity = None
                continue

            # if DatabaseHelper.entity_count_cached == 0:
            #     DatabaseHelper.entity_count_cached = entity_repository.count()
            # random_id = random.randint(1, DatabaseHelper.entity_count_cached)
            # try:
            #     entity = entity_repository.get_random_by_id(random_id)
            #     # entity = entity_repository.get_by_id(random_id)
            # except NotFoundError:
            #     counter += 1
            #     entity = None
            #     continue

            relation_counts = entity.relation_counts
            entities = entity.entities
            # log.debug(f"relation_counts: {relation_counts}")
            counter += 1
            if entity.entity_type == EntityType.LABEL:
                log.debug("random skip label")
                continue
            if (
                relation_counts is not None
                and (
                    "Member Of" in relation_counts
                    or "Alias" in relation_counts
                    or (
                        "members" in entities
                        and len(list(entities.get("members", []))) > 0
                    )
                    or ("groups" in entities and len(entities["groups"]) > 0)
                )
                and entity.entity_type == EntityType.ARTIST
            ):
                log.debug(f"random node: {entity} counter: {counter}")
                break
            else:
                log.debug(f"random fail: {entity} counter: {counter}")

            if counter >= 1000:
                log.debug("random count expired")
                break

        if entity:
            entity_id, entity_type = entity.entity_id, entity.entity_type
        else:
            entity_id = 0
            entity_type = EntityType.ARTIST

        assert entity_type in (EntityType.ARTIST, EntityType.LABEL)
        return entity_id, entity_type

    @classmethod
    def get_relations_by_entity_id_and_entity_type(
        cls,
        entity_repository: RuntimeEntityRepository,
        relation_repository: RuntimeRelationRepository,
        # relation_release_year_repository: RuntimeRelationReleaseYearRepository,
        entity_id: int,
        entity_type: EntityType,
    ) -> dict[str, Any]:
        """
        Retrieves relations for an entity.

        Args:
            entity_repository: The entity repository.
            relation_repository: The relation repository.
            entity_id: The ID of the entity.
            entity_type: The type of the entity.

        Returns:
            dict[str, Any]: The relations data.
        """
        # TODO Add info on releases back in one day
        entity = entity_repository.get_by_entity_id_and_entity_type(
            entity_id, entity_type
        )
        relations = relation_repository.find_by_entity(entity.id)

        data = []
        for relation in relations:
            # relation_release_years = relation_release_year_repository.get(relation.id)
            relation_releases = {}
            # for relation_release_year in relation_release_years:
            #     relation_releases[relation_release_year.release_id] = (
            #         relation_release_year.year
            #     )

            # category = RoleType.role_definitions[relation.role]
            # if category is None:
            #     continue
            datum = {
                "role": relation.role,
                "releases": relation_releases,
            }
            data.append(datum)
        data = {"results": tuple(data)}
        return data

    @classmethod
    def search_text_index(cls, search_text):
        return RuntimeDatabaseHelper.text_search_index.search(search_text)

    @classmethod
    def search_get_random_id(cls):
        return RuntimeDatabaseHelper.text_search_index.get_random_id()
