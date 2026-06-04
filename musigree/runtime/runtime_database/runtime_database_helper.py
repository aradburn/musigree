"""
This module defines the `RuntimeDatabaseHelper` class and related utilities for managing the runtime runtime_database.

It provides an abstract base class for interacting with various runtime_database backends,
handling runtime_database setup, shutdown, table management, and various data access operations.

Key functionalities include:
    - Abstract methods for setting up and shutting down the runtime_database.
    - Methods for creating and dropping runtime_database tables.
    - Loading tables with initial data (e.g., roles).
    - Generating SQL insert queries.
    - Retrieving network data for entities.
    - Managing runtime_database connections and sessions.
    - Caching of frequently accessed data.

The `RuntimeDatabaseHelper` class is designed to be subclassed for specific
runtime_database implementations, such as SQLite or PostgreSQL. It utilizes SQLAlchemy
for runtime_database operations and defines a set of methods that each subclass must
implement.
"""

import logging
from abc import ABC, abstractmethod
from typing import Type, Any

from sqlalchemy import Table
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker
from sqlalchemy.sql.dml import ReturningInsert, Insert

from musigree.config import Configuration
from musigree.exceptions import NotFoundError
from musigree.library.fields.entity_type import EntityType
from musigree.library.full_text_search.text_search_index import TextSearchIndex
from musigree.runtime.data_access_layer.entity_details_index import EntityDetailsIndex
from musigree.runtime.data_access_layer.relation_grapher import (
    RelationGrapher,
)
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
    Abstract base class for managing the runtime runtime_database.

    This class provides an interface for interacting with the runtime runtime_database,
    including methods for setting up and shutting down the runtime_database, creating
    and dropping tables, loading initial data, and performing various data
    access operations.

    Subclasses should implement the abstract methods to provide runtime_database-specific
    functionality.

    Attributes:
        runtime_async_engine (Engine | None): The SQLAlchemy engine for the runtime runtime_database.
        runtime_async_session_factory (async_sessionmaker | None): The SQLAlchemy session factory
            for creating runtime_database sessions.
        text_search_index (TextSearchIndex | None): An index for text-based searches.
        entity_details_index (EntityDetailsIndex | None): An index for entity details.
        entity_count_cached (int): A cached count of entities.
        MAX_NODES (int): The maximum number of nodes in a network.
        MAX_NODES_MOBILE (int): The maximum number of nodes in a mobile network.
        MAX_DEGREE (int): The maximum degree of a node in a network.
        MAX_DEGREE_MOBILE (int): The maximum degree of a node in a mobile network.
        LINK_RATIO (int): A ratio for link calculations.
    """

    runtime_async_engine: AsyncEngine | None = None
    """The SQLAlchemy engine for the runtime runtime_database."""
    runtime_async_session_factory: async_sessionmaker | None = None
    """The SQLAlchemy session factory for creating runtime_database sessions."""

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
    async def setup_database(config: Configuration) -> AsyncEngine:
        """
        Sets up the runtime_database connection and returns the engine.

        Args:
            config: The application configuration.

        Returns:
            AsyncEngine: The SQLAlchemy async engine.
        """
        pass

    @staticmethod
    @abstractmethod
    async def shutdown_database() -> None:
        """Shuts down the runtime_database connection."""
        pass

    @staticmethod
    @abstractmethod
    async def check_connection(config: Configuration, engine: AsyncEngine) -> None:
        """
        Checks the runtime_database connection.

        Args:
            config: The application configuration.
            engine: The SQLAlchemy async engine.
        """
        pass

    @classmethod
    @abstractmethod
    async def create_tables(cls, tables: list[str]) -> None:
        """
        Creates runtime_database tables.

        Args:
            tables: An optional list of table names to create. If None, all tables
                defined in `RuntimeBase.metadata` will be created.
        """
        from musigree.runtime.runtime_database_manager import RuntimeDatabaseManager
        from musigree.runtime.runtime_database import ALL_RUNTIME_DATABASE_TABLES

        for table_class in ALL_RUNTIME_DATABASE_TABLES:
            log.debug(f"table definition for: {table_class.__tablename__}")
        for table_name in RuntimeBase.metadata.tables:
            log.debug(f"table in metadata: {table_name}")
        table_definitions: list[Table] = [
            RuntimeBase.metadata.tables[table_name] for table_name in tables
        ]
        for table in table_definitions:
            log.debug(f"creating table: {table.name}")

        assert RuntimeDatabaseManager.runtime_database_helper is not None, (
            "runtime_database_helper must be initialized before calling create_tables()"
        )
        assert RuntimeDatabaseManager.runtime_database_helper.runtime_async_engine is not None, (
            "runtime_async_engine must be initialized before calling create_tables()"
        )
        # noinspection PyTypeChecker
        async with (
            RuntimeDatabaseManager.runtime_database_helper.runtime_async_engine.begin() as conn
        ):
            # noinspection PyTypeChecker
            await conn.run_sync(
                RuntimeBase.metadata.create_all,
                checkfirst=True,
                tables=table_definitions,
            )

    @classmethod
    @abstractmethod
    async def drop_tables(cls, tables: list[str]) -> None:
        """
        Drops runtime_database tables.

        Args:
            tables: An optional list of table names to drop. If None, all tables
                defined in `RuntimeBase.metadata` will be dropped.
        """
        from musigree.runtime.runtime_database_manager import RuntimeDatabaseManager

        assert RuntimeDatabaseManager.runtime_database_helper is not None, (
            "runtime_database_helper must be initialized before calling drop_tables()"
        )
        assert RuntimeDatabaseManager.runtime_database_helper.runtime_async_engine is not None, (
            "runtime_async_engine must be initialized before calling drop_tables()"
        )

        if tables is not None:
            # noinspection PyTypeChecker
            table_definitions: list[Table] = [
                RuntimeBase.metadata.tables[table_name] for table_name in tables
            ]
            for table in table_definitions:
                log.debug(f"deleting table: {table.name}")
                # noinspection PyTypeChecker
                async with (
                    RuntimeDatabaseManager.runtime_database_helper.runtime_async_engine.begin() as conn
                ):
                    # noinspection PyTypeChecker
                    await conn.run_sync(
                        table.drop,
                        checkfirst=True,
                    )
        else:
            # noinspection PyTypeChecker
            async with (
                RuntimeDatabaseManager.runtime_database_helper.runtime_async_engine.begin() as conn
            ):
                # noinspection PyTypeChecker
                await conn.run_sync(
                    RuntimeBase.metadata.drop_all,
                    checkfirst=True,
                )

    @staticmethod
    @abstractmethod
    async def vacuum(table_name: str, is_full: bool, is_analyze: bool, engine: AsyncEngine) -> None:
        """
        Abstract method to initate a vacuum on a table.
        Args:
            table_name: The name of the table to vacuum.
            is_full: If True, performs a full vacuum.
            is_analyze: If True, performs an analyze operation.
            engine: The SQLAlchemy async engine connected to the runtime_database.
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
        on_conflict_do_nothing: bool = False,
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
        values: list[dict],
        on_conflict_do_nothing: bool = False,
    ) -> Insert:
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
    async def get_network(
        entity_repository: RuntimeEntityRepository,
        relation_repository: RuntimeRelationRepository,
        entity_id: int,
        entity_type: EntityType,
        on_mobile: bool,
        roles: list[str],
    ) -> dict[str, Any] | None:
        """
        Retrieves a network of entities and relations.

        Args:
            entity_repository: The entity repository.
            relation_repository: The relation repository.
            entity_id: The ID of the entity.
            entity_type: The type of the entity.
            on_mobile: Whether the request is from a mobile device.
            roles: A list of role names to filter by.

        Returns:
            dict: The network data.
        """

        try:
            entity = await entity_repository.get_by_entity_id_and_entity_type(
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
        data = await relation_grapher.get_relation_graph(entity_repository, relation_repository)
        return data

    @staticmethod
    async def get_random_entity(
        entity_repository: RuntimeEntityRepository,
    ) -> tuple[int, EntityType]:
        """
        Retrieves a random entity.

        Args:
            entity_repository: The entity repository.

        Returns:
            tuple[int, EntityType]: A tuple containing the entity ID and type.
        """
        from musigree.runtime.runtime_database_manager import RuntimeDatabaseManager

        assert RuntimeDatabaseManager.runtime_database_helper is not None, (
            "runtime_database_helper must be initialized before calling initialize()"
        )

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
            entity = None

            if RuntimeDatabaseManager.runtime_database_helper.entity_count_cached == 0:
                RuntimeDatabaseManager.runtime_database_helper.entity_count_cached = (
                    await entity_repository.count()
                )

            try:
                entity = await entity_repository.get_random_entity(
                    RuntimeDatabaseManager.runtime_database_helper.entity_count_cached
                )
            except NotFoundError:
                log.debug("random not found")
                counter += 1
                continue

            if entity is None:
                continue
            if entity.entity_type == EntityType.LABEL:
                continue

            relation_counts = entity.relation_counts
            entities = entity.entities
            counter += 1
            if entity.entity_type == EntityType.LABEL:
                continue
            if (
                relation_counts is not None
                and (
                    "Member Of" in relation_counts
                    or "Alias" in relation_counts
                    or ("members" in entities and len(list(entities.get("members", []))) > 0)
                    or ("groups" in entities and len(entities["groups"]) > 0)
                )
                and entity.entity_type == EntityType.ARTIST
            ):
                break

            if counter >= 1000:
                entity = None
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
    async def get_relations_by_entity_id_and_entity_type(
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
        entity = await entity_repository.get_by_entity_id_and_entity_type(entity_id, entity_type)
        relation_internals = await relation_repository.find_by_entity(entity.id)

        role_dict: dict[str, dict[str, int | None]] = {}
        for relation_internal in relation_internals:
            releases_dict: dict[str, int | None] = role_dict.get(relation_internal.role) or {}
            releases_dict.update({str(relation_internal.release_id): relation_internal.year})
            role_dict.update({relation_internal.role: releases_dict})

        data = []
        for role in role_dict.keys():
            datum = {
                "role": role,
                "releases": role_dict[role],
            }
            data.append(datum)
        result = {"results": tuple(data)}
        return result
