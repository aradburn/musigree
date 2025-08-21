"""
Unit tests for the MetadataRepository class.

This module tests the MetadataRepository class which manages Metadata objects
in the offline database.
"""

from typing import AsyncGenerator

import pytest
from unittest.mock import AsyncMock, Mock, patch, PropertyMock
from datetime import datetime

from musigree.config import SqliteTestConfiguration
from musigree.exceptions import NotFoundError, DatabaseError
from musigree.offline.database.metadata_repository import MetadataRepository
from musigree.offline.database.metadata_table import MetadataTable
from musigree.offline.domain.metadata import Metadata, MetadataUncommitted


class TestMetadataRepository:
    """Test class for MetadataRepository."""

    @pytest.fixture(autouse=True)
    def setup_config(self) -> None:
        """Set up test configuration."""
        self.config = SqliteTestConfiguration()

    @pytest.fixture
    def mock_metadata(self) -> Metadata:
        """Create a mock metadata for testing."""
        return Metadata(
            metadata_id=1,
            metadata_key="test_key",
            metadata_value="test_value",
            metadata_timestamp=datetime(2023, 1, 1, 12, 0, 0),
        )

    @pytest.fixture
    def mock_metadata_uncommitted(self) -> MetadataUncommitted:
        """Create a mock uncommitted metadata for testing."""
        return MetadataUncommitted(
            metadata_key="new_key",
            metadata_value="new_value",
            metadata_timestamp=datetime(2023, 1, 2, 12, 0, 0),
        )

    @pytest.fixture
    def mock_metadata_table(self) -> MetadataTable:
        """Create a mock metadata table record."""
        table_mock = Mock(spec=MetadataTable)
        table_mock.metadata_id = 1
        table_mock.metadata_key = "test_key"
        table_mock.metadata_value = "test_value"
        table_mock.metadata_timestamp = datetime(2023, 1, 1, 12, 0, 0)
        return table_mock

    @pytest.fixture
    def metadata_repository(self) -> MetadataRepository:
        """Create a MetadataRepository instance for testing."""
        return MetadataRepository()

    @pytest.mark.asyncio
    async def test_all_success(
        self,
        metadata_repository: MetadataRepository,
        mock_metadata_table: MetadataTable,
        mock_metadata: Metadata,
    ) -> None:
        """Test successful all() method execution."""
        # Arrange
        with patch.object(metadata_repository, "_all") as mock_all:

            async def mock_async_iterator() -> AsyncGenerator[MetadataTable, None]:
                yield mock_metadata_table

            mock_all.return_value = mock_async_iterator()

            with patch.object(Metadata, "model_validate") as mock_validate:
                mock_validate.return_value = mock_metadata

                # Act
                results = []
                async for metadata in metadata_repository.all():
                    results.append(metadata)

                # Assert
                assert len(results) == 1
                assert results[0] == mock_metadata
                mock_validate.assert_called_once_with(mock_metadata_table)

    @pytest.mark.asyncio
    async def test_get_by_id_success(
        self,
        metadata_repository: MetadataRepository,
        mock_metadata_table: MetadataTable,
        mock_metadata: Metadata,
    ) -> None:
        """Test successful get_by_id execution."""
        # Arrange
        metadata_id = 1

        with patch.object(metadata_repository, "_get") as mock_get:
            mock_get.return_value = mock_metadata_table

            with patch.object(Metadata, "model_validate") as mock_validate:
                mock_validate.return_value = mock_metadata

                # Act
                result = await metadata_repository.get_by_id(metadata_id)

                # Assert
                assert result == mock_metadata
                mock_get.assert_called_once_with("metadata_id", metadata_id)
                mock_validate.assert_called_once_with(mock_metadata_table)

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(
        self, metadata_repository: MetadataRepository
    ) -> None:
        """Test get_by_id when metadata is not found."""
        # Arrange
        metadata_id = 999

        with patch.object(metadata_repository, "_get") as mock_get:
            mock_get.return_value = None

            # Act & Assert
            with pytest.raises(NotFoundError):
                await metadata_repository.get_by_id(metadata_id)

    @pytest.mark.asyncio
    async def test_get_by_key_success(
        self,
        metadata_repository: MetadataRepository,
        mock_metadata_table: MetadataTable,
        mock_metadata: Metadata,
    ) -> None:
        """Test successful get_by_key execution."""
        # Arrange
        key = "test_key"

        mock_session = AsyncMock()
        mock_result = Mock()
        mock_result.scalars.return_value.one_or_none.return_value = mock_metadata_table
        mock_session.execute.return_value = mock_result

        with patch.object(
            MetadataRepository, "_session", new_callable=PropertyMock
        ) as mock_session_prop:
            mock_session_prop.return_value = mock_session

            with patch.object(Metadata, "model_validate") as mock_validate:
                mock_validate.return_value = mock_metadata

                # Act
                result = await metadata_repository.get_by_key(key)

                # Assert
                assert result == mock_metadata
                mock_session.execute.assert_called_once()
                mock_validate.assert_called_once_with(mock_metadata_table)

    @pytest.mark.asyncio
    async def test_get_by_key_not_found(
        self, metadata_repository: MetadataRepository
    ) -> None:
        """Test get_by_key when metadata is not found."""
        # Arrange
        key = "nonexistent_key"

        mock_session = AsyncMock()
        mock_result = Mock()
        mock_result.scalars.return_value.one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        with patch.object(
            MetadataRepository, "_session", new_callable=PropertyMock
        ) as mock_session_prop:
            mock_session_prop.return_value = mock_session

            # Act & Assert
            with pytest.raises(NotFoundError):
                await metadata_repository.get_by_key(key)

    @pytest.mark.asyncio
    async def test_create_success(
        self,
        metadata_repository: MetadataRepository,
        mock_metadata_uncommitted: MetadataUncommitted,
        mock_metadata_table: MetadataTable,
        mock_metadata: Metadata,
    ) -> None:
        """Test successful create execution."""
        # Arrange
        with patch.object(metadata_repository, "_save") as mock_save:
            mock_save.return_value = mock_metadata_table

            with patch.object(Metadata, "model_validate") as mock_validate:
                mock_validate.return_value = mock_metadata

                # Act
                result = await metadata_repository.create(mock_metadata_uncommitted)

                # Assert
                assert result == mock_metadata
                mock_save.assert_called_once()
                mock_validate.assert_called_once_with(mock_metadata_table)

    @pytest.mark.asyncio
    async def test_update_success(
        self,
        metadata_repository: MetadataRepository,
        mock_metadata_table: MetadataTable,
        mock_metadata: Metadata,
    ) -> None:
        """Test successful update execution."""
        # Arrange
        payload = {"metadata_value": "updated_value"}
        mock_session = AsyncMock()
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_metadata_table
        mock_session.execute.return_value = mock_result

        with patch.object(
            MetadataRepository, "_session", new_callable=PropertyMock
        ) as mock_session_prop:
            mock_session_prop.return_value = mock_session

            with patch.object(Metadata, "model_validate") as mock_validate:
                mock_entity_instance = Mock()
                mock_entity_instance.to_domain.return_value = mock_metadata
                mock_validate.return_value = mock_entity_instance

                # Act
                result = await metadata_repository.update(payload)

                # Assert
                assert result == mock_metadata
                mock_session.execute.assert_called_once()
                mock_validate.assert_called_once_with(mock_metadata_table)

    def test_schema_class_is_set(self, metadata_repository: MetadataRepository) -> None:
        """Test that schema_class is properly set."""
        assert metadata_repository.schema_class == MetadataTable

    def test_repository_initialization_success(self) -> None:
        """Test successful repository initialization."""
        repo = MetadataRepository()
        assert repo.schema_class == MetadataTable

    @pytest.mark.asyncio
    async def test_all_empty_result(
        self, metadata_repository: MetadataRepository
    ) -> None:
        """Test all() method with empty result."""
        # Arrange
        with patch.object(metadata_repository, "_all") as mock_all:
            # noinspection PyUnreachableCode
            async def empty_async_iterator() -> AsyncGenerator[None, None]:
                return
                yield  # This yield will never be reached, creating an empty iterator

            mock_all.return_value = empty_async_iterator()

            # Act
            results = []
            async for metadata in metadata_repository.all():
                results.append(metadata)

            # Assert
            assert len(results) == 0

    @pytest.mark.asyncio
    async def test_create_with_database_error(
        self,
        metadata_repository: MetadataRepository,
        mock_metadata_uncommitted: MetadataUncommitted,
    ) -> None:
        """Test create execution with database error."""
        # Arrange
        with patch.object(metadata_repository, "_save") as mock_save:
            mock_save.side_effect = DatabaseError(message="Save failed")

            # Act & Assert
            with pytest.raises(DatabaseError):
                await metadata_repository.create(mock_metadata_uncommitted)

    @pytest.mark.asyncio
    async def test_update_with_database_error(
        self, metadata_repository: MetadataRepository
    ) -> None:
        """Test update execution with database error."""
        # Arrange
        payload = {"metadata_value": "updated_value"}
        mock_session = AsyncMock()
        mock_session.execute.side_effect = DatabaseError(message="Update failed")

        with patch.object(
            MetadataRepository, "_session", new_callable=PropertyMock
        ) as mock_session_prop:
            mock_session_prop.return_value = mock_session

            # Act & Assert
            with pytest.raises(DatabaseError):
                await metadata_repository.update(payload)
