"""
Unit tests for the RelationRepository class.

This module tests the RelationRepository class which manages Relation objects
in the offline_database, including CRUD operations and specialized queries.
"""

from unittest.mock import AsyncMock, Mock, patch, PropertyMock

import pytest
from sqlalchemy import Result, select

from musigree.config import SqliteTestConfiguration
from musigree.exceptions import NotFoundError
from musigree.offline.offline_database.relation_repository import RelationRepository
from musigree.offline.offline_database.relation_table import RelationTable
from musigree.offline.offline_domain.relation import (
    RelationUncommitted,
    RelationDB,
    RelationInternal,
)


class TestRelationRepository:
    """Test class for RelationRepository."""

    @pytest.fixture(autouse=True)
    def setup_config(self) -> None:
        """Set up test configuration."""
        self.config = SqliteTestConfiguration()

    @pytest.fixture
    def mock_relation_internal(self) -> RelationInternal:
        """Create a mock internal relation for testing."""
        return RelationInternal(
            id=1,
            subject=100,
            role="performer",
            object=200,
            release_id=0,
            year=0,
        )

    @pytest.fixture
    def mock_relation_uncommitted(self) -> RelationUncommitted:
        """Create a mock uncommitted relation for testing."""
        return RelationUncommitted(
            subject=100,
            object=200,
            role_name="performer",
            release_id=0,
            year=0,
        )

    @pytest.fixture
    def mock_relation_table(self) -> RelationTable:
        """Create a mock relation table record."""
        table_mock = Mock(spec=RelationTable)
        table_mock.id = 1
        table_mock.subject = 100
        table_mock.predicate = 1
        table_mock.object = 200
        return table_mock

    @pytest.fixture
    def relation_repository(self) -> RelationRepository:
        """Create a RelationRepository instance for testing."""
        return RelationRepository()

    @pytest.mark.asyncio
    async def test_get_one_by_query_success(
        self,
        relation_repository: RelationRepository,
        mock_relation_table: RelationTable,
        mock_relation_internal: RelationInternal,
    ) -> None:
        """Test successful _get_one_by_query execution."""
        # Arrange
        query = select(RelationTable).where(RelationTable.id == 1)

        mock_session = AsyncMock()
        with patch.object(
            RelationRepository, "_session", new_callable=PropertyMock
        ) as mock_session_prop:
            mock_session_prop.return_value = mock_session
            mock_result = Mock(spec=Result)
            mock_result.scalars.return_value.one_or_none.return_value = mock_relation_table
            mock_session.execute.return_value = mock_result

            with patch.object(RelationDB, "model_validate") as mock_validate:
                mock_relation_instance = Mock()
                mock_relation_instance.to_domain.return_value = mock_relation_internal
                mock_validate.return_value = mock_relation_instance

                # Act
                result = await relation_repository._get_one_by_query(query)

                # Assert
                assert result == mock_relation_internal
                mock_session.execute.assert_called_once_with(query)
                mock_validate.assert_called_once_with(mock_relation_table)

    @pytest.mark.asyncio
    async def test_get_one_by_query_not_found(
        self, relation_repository: RelationRepository
    ) -> None:
        """Test _get_one_by_query when no relation is found."""
        # Arrange
        query = select(RelationTable).where(RelationTable.id == 999)

        mock_session = AsyncMock()
        with patch.object(
            RelationRepository, "_session", new_callable=PropertyMock
        ) as mock_session_prop:
            mock_session_prop.return_value = mock_session
            mock_result = Mock(spec=Result)
            mock_result.scalars.return_value.one_or_none.return_value = None
            mock_session.execute.return_value = mock_result

            # Act & Assert
            with pytest.raises(NotFoundError):
                await relation_repository._get_one_by_query(query)

    @pytest.mark.asyncio
    async def test_get_all_by_query_success(
        self,
        relation_repository: RelationRepository,
        mock_relation_table: RelationTable,
        mock_relation_internal: RelationInternal,
    ) -> None:
        """Test successful _get_all_by_query execution."""
        # Arrange
        query = select(RelationTable).where(RelationTable.subject == 100)

        mock_session = AsyncMock()
        with patch.object(
            RelationRepository, "_session", new_callable=PropertyMock
        ) as mock_session_prop:
            mock_session_prop.return_value = mock_session
            mock_result = Mock(spec=Result)
            mock_result.scalars.return_value.all.return_value = [mock_relation_table]
            mock_session.execute.return_value = mock_result

            with patch.object(RelationDB, "model_validate") as mock_validate:
                mock_relation_instance = Mock()
                mock_relation_instance.to_domain.return_value = mock_relation_internal
                mock_validate.return_value = mock_relation_instance

                # Act
                result = await relation_repository._get_all_by_query(query)

                # Assert
                assert result == [mock_relation_internal]
                mock_session.execute.assert_called_once_with(query)
                mock_validate.assert_called_once_with(mock_relation_table)

    @pytest.mark.asyncio
    async def test_get_all_by_query_empty_result(
        self, relation_repository: RelationRepository
    ) -> None:
        """Test _get_all_by_query when no relations are found."""
        # Arrange
        query = select(RelationTable).where(RelationTable.subject == 999)

        mock_session = AsyncMock()
        with patch.object(
            RelationRepository, "_session", new_callable=PropertyMock
        ) as mock_session_prop:
            mock_session_prop.return_value = mock_session
            mock_result = Mock(spec=Result)
            mock_result.scalars.return_value.all.return_value = []
            mock_session.execute.return_value = mock_result

            # Act
            result = await relation_repository._get_all_by_query(query)

            # Assert
            assert result == []

    @pytest.mark.asyncio
    async def test_find_by_key_success(
        self,
        relation_repository: RelationRepository,
        mock_relation_internal: RelationInternal,
    ) -> None:
        """Test successful find_by_key execution."""
        # Arrange
        key = {"subject": 100, "role_id": 1, "object": 200}

        with patch.object(relation_repository, "_get_all_by_query") as mock_get_all:
            mock_get_all.return_value = [mock_relation_internal]

            # Act
            result = await relation_repository.find_by_key(key)

            # Assert
            assert result == [mock_relation_internal]
            mock_get_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_by_entity_success(
        self,
        relation_repository: RelationRepository,
        mock_relation_internal: RelationInternal,
    ) -> None:
        """Test successful find_by_entity execution."""
        # Arrange
        entity_id = 100

        with patch.object(relation_repository, "_get_all_by_query") as mock_get_all:
            mock_get_all.return_value = [mock_relation_internal]

            # Act
            result = await relation_repository.find_by_entity(entity_id)

            # Assert
            assert result == [mock_relation_internal]
            mock_get_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_by_entity_and_roles_success(
        self,
        relation_repository: RelationRepository,
        mock_relation_internal: RelationInternal,
    ) -> None:
        """Test successful find_by_entity_and_roles execution."""
        # Arrange
        entity_id = 100
        role_ids = [1, 2]

        with patch.object(relation_repository, "_get_all_by_query") as mock_get_all:
            mock_get_all.return_value = [mock_relation_internal]

            # Act
            result = await relation_repository.find_by_entity_and_roles(entity_id, role_ids)

            # Assert
            assert result == [mock_relation_internal]
            mock_get_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_by_entity_and_roles_empty_roles(
        self, relation_repository: RelationRepository
    ) -> None:
        """Test find_by_entity_and_roles with empty role list."""
        # Arrange
        entity_id = 100
        role_ids: list[int] = []

        # Act
        result = await relation_repository.find_by_entity_and_roles(entity_id, role_ids)

        # Assert
        assert result == []

    @pytest.mark.asyncio
    async def test_create_success(
        self,
        relation_repository: RelationRepository,
        mock_relation_uncommitted: RelationUncommitted,
    ) -> None:
        """Test successful create execution."""
        # Arrange
        mock_session = AsyncMock()
        mock_database_helper = Mock()
        mock_query = Mock()
        mock_database_helper.generate_insert_query.return_value = mock_query

        with patch.object(
            RelationRepository, "_session", new_callable=PropertyMock
        ) as mock_session_prop:
            mock_session_prop.return_value = mock_session
            with patch(
                "musigree.offline.offline_database_manager.OfflineDatabaseManager"
            ) as mock_manager:
                mock_manager.offline_database_helper = mock_database_helper

                with patch(
                    "musigree.offline.offline_database.relation_repository.RoleCache"
                ) as mock_role_cache:
                    mock_role_cache.role_name_to_role_id_lookup = {"performer": 1}

                    # Act
                    await relation_repository.create(mock_relation_uncommitted)

                    # Assert
                    mock_session.execute.assert_called_once_with(mock_query)
                    mock_session.flush.assert_called_once()
                    mock_database_helper.generate_insert_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_bulk_success(
        self,
        relation_repository: RelationRepository,
        mock_relation_uncommitted: RelationUncommitted,
    ) -> None:
        """Test successful create_bulk execution."""
        # Arrange
        relations = [mock_relation_uncommitted]
        mock_session = AsyncMock()
        mock_database_helper = Mock()
        mock_query = Mock()
        mock_database_helper.generate_insert_bulk_query.return_value = mock_query

        with patch.object(
            RelationRepository, "_session", new_callable=PropertyMock
        ) as mock_session_prop:
            mock_session_prop.return_value = mock_session
            with patch(
                "musigree.offline.offline_database_manager.OfflineDatabaseManager"
            ) as mock_manager:
                mock_manager.offline_database_helper = mock_database_helper

                with patch(
                    "musigree.offline.offline_database.relation_repository.RoleCache"
                ) as mock_role_cache:
                    mock_role_cache.role_name_to_role_id_lookup = {"performer": 1}

                    # Act
                    await relation_repository.create_bulk(relations)

                    # Assert
                    mock_session.execute.assert_called_once_with(mock_query)
                    mock_database_helper.generate_insert_bulk_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_by_entitys_success(self, relation_repository: RelationRepository) -> None:
        """Test successful delete_by_entitys execution."""
        # Arrange
        entity_id = 100
        mock_session = AsyncMock()

        with patch.object(
            RelationRepository, "_session", new_callable=PropertyMock
        ) as mock_session_prop:
            mock_session_prop.return_value = mock_session
            # Act
            await relation_repository.delete_by_entitys(entity_id)

            # Assert
            mock_session.execute.assert_called_once()
            mock_session.flush.assert_called_once()

    def test_schema_class_is_set(self, relation_repository: RelationRepository) -> None:
        """Test that schema_class is properly set."""
        assert relation_repository.schema_class == RelationTable

    def test_repository_initialization_success(self) -> None:
        """Test successful repository initialization."""
        repo = RelationRepository()
        assert repo.schema_class == RelationTable

    @pytest.mark.asyncio
    async def test_find_by_key_not_found(self, relation_repository: RelationRepository) -> None:
        """Test find_by_key when relation is not found."""
        # Arrange
        key = {"subject": 999, "role_name": "performer", "object": 888}

        with patch.object(relation_repository, "_get_all_by_query") as mock_get_all:
            mock_get_all.return_value = []

            with patch(
                "musigree.offline.offline_database.relation_repository.RoleCache"
            ) as mock_role_cache:
                mock_role_cache.role_name_to_role_id_lookup = {"performer": 1}

                # Act
                result = await relation_repository.find_by_key(key)

                # Assert
                assert result == []

    @pytest.mark.asyncio
    async def test_create_database_helper_not_initialized(
        self,
        relation_repository: RelationRepository,
        mock_relation_uncommitted: RelationUncommitted,
    ) -> None:
        """Test create when offline_database helper is not initialized."""
        # Arrange
        with patch(
            "musigree.offline.offline_database_manager.OfflineDatabaseManager"
        ) as mock_manager:
            mock_manager.offline_database_helper = None

            # Act & Assert
            with pytest.raises(AssertionError):
                await relation_repository.create(mock_relation_uncommitted)

    @pytest.mark.asyncio
    async def test_create_bulk_database_helper_not_initialized(
        self,
        relation_repository: RelationRepository,
        mock_relation_uncommitted: RelationUncommitted,
    ) -> None:
        """Test create_bulk when offline_database helper is not initialized."""
        # Arrange
        relations = [mock_relation_uncommitted]

        with patch(
            "musigree.offline.offline_database_manager.OfflineDatabaseManager"
        ) as mock_manager:
            mock_manager.offline_database_helper = None

            # Act & Assert
            with pytest.raises(AssertionError):
                await relation_repository.create_bulk(relations)
