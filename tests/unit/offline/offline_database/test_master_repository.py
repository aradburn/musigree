"""
Unit tests for the MasterRepository class.

This module tests the MasterRepository class which manages Master objects
in the offline database.
"""

from typing import AsyncGenerator
from unittest.mock import AsyncMock, Mock, PropertyMock, patch

import pytest
from sqlalchemy.engine import Result

from musigree.config import SqliteTestConfiguration
from musigree.exceptions import NotFoundError
from musigree.offline.offline_database.master_repository import MasterRepository
from musigree.offline.offline_database.master_table import MasterTable
from musigree.offline.offline_domain.master import Master


class TestMasterRepository:
    """Test class for MasterRepository."""

    @pytest.fixture(autouse=True)
    def setup_config(self) -> None:
        """Set up test configuration."""
        self.config = SqliteTestConfiguration()

    @pytest.fixture
    def mock_master(self) -> Master:
        """Create a mock master for testing."""
        return Master(
            master_id=100,
            title="Test Master",
            year=2020,
            main_release="12345",
            data_quality="Complete",
        )

    @pytest.fixture
    def mock_master_table(self) -> MasterTable:
        """Create a mock master table record."""
        table_mock = Mock(spec=MasterTable)
        table_mock.master_id = 100
        table_mock.title = "Test Master"
        table_mock.year = 2020
        table_mock.main_release = "12345"
        table_mock.data_quality = "Complete"
        return table_mock

    @pytest.fixture
    def master_repository(self) -> MasterRepository:
        """Create a MasterRepository instance for testing."""
        return MasterRepository()

    @pytest.mark.asyncio
    async def test_all_success(
        self,
        master_repository: MasterRepository,
        mock_master_table: MasterTable,
        mock_master: Master,
    ) -> None:
        """Test successful all() method execution."""

        async def mock_partitions() -> AsyncGenerator[list, None]:
            yield [(mock_master_table,)]

        mock_result = Mock()
        mock_result.partitions.return_value = mock_partitions()
        mock_session = AsyncMock()
        mock_session.stream = AsyncMock(return_value=mock_result)

        with patch.object(
            MasterRepository, "_session", new_callable=PropertyMock, return_value=mock_session
        ):
            with patch.object(Master, "model_validate", return_value=mock_master):
                results = []
                async for batch in master_repository.all():
                    results.extend(batch)

                assert len(results) == 1
                assert results[0] == mock_master

    @pytest.mark.asyncio
    async def test_get_by_id_success(
        self,
        master_repository: MasterRepository,
        mock_master_table: MasterTable,
        mock_master: Master,
    ) -> None:
        """Test successful get_by_id execution."""
        with patch.object(master_repository, "_get", AsyncMock(return_value=mock_master_table)):
            with patch.object(Master, "model_validate", return_value=mock_master):
                result = await master_repository.get_by_id(100)
                assert result == mock_master

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, master_repository: MasterRepository) -> None:
        """Test get_by_id when master is not found."""
        with patch.object(master_repository, "_get", AsyncMock(return_value=None)):
            with pytest.raises(NotFoundError):
                await master_repository.get_by_id(999)

    @pytest.mark.asyncio
    async def test_create_success(
        self,
        master_repository: MasterRepository,
        mock_master: Master,
        mock_master_table: MasterTable,
    ) -> None:
        """Test successful create execution."""
        with patch.object(master_repository, "_save", AsyncMock(return_value=mock_master_table)):
            with patch.object(Master, "model_validate", return_value=mock_master):
                result = await master_repository.create(mock_master)
                assert result == mock_master

    @pytest.mark.asyncio
    async def test_get_ids_success(
        self,
        master_repository: MasterRepository,
    ) -> None:
        """Test get_ids returns sequence of ids."""
        mock_result = Mock(spec=Result)
        mock_result.scalars.return_value.all.return_value = [1, 2, 3]
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=mock_result)

        with patch.object(
            MasterRepository, "_session", new_callable=PropertyMock, return_value=mock_session
        ):
            result = await master_repository.get_ids()
            assert result == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_update_success(self, master_repository: MasterRepository) -> None:
        """Test successful update execution."""
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock()
        mock_session.flush = AsyncMock()

        with patch.object(
            MasterRepository, "_session", new_callable=PropertyMock, return_value=mock_session
        ):
            await master_repository.update(100, {"title": "Updated Title"})
            mock_session.execute.assert_called_once()
            mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_by_id_success(self, master_repository: MasterRepository) -> None:
        """Test successful delete_by_id execution."""
        mock_session = AsyncMock()
        mock_session.flush = AsyncMock()

        with patch.object(
            MasterRepository, "_session", new_callable=PropertyMock, return_value=mock_session
        ):
            with patch.object(master_repository, "execute", AsyncMock()):
                await master_repository.delete_by_id(100)
                mock_session.flush.assert_called_once()

    def test_schema_class_is_set(self, master_repository: MasterRepository) -> None:
        """Test that schema_class is properly set."""
        assert master_repository.schema_class == MasterTable
