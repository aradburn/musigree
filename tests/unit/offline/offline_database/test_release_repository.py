"""
Unit tests for the ReleaseRepository class.

This module tests the ReleaseRepository class which manages Release objects
in the offline database.
"""

from typing import AsyncGenerator
from unittest.mock import AsyncMock, Mock, PropertyMock, patch

import pytest
from sqlalchemy.engine import Result

from musigree.config import SqliteTestConfiguration
from musigree.exceptions import NotFoundError
from musigree.offline.offline_database.release_repository import ReleaseRepository
from musigree.offline.offline_database.release_table import ReleaseTable
from musigree.offline.offline_domain.release import Release


class TestReleaseRepository:
    """Test class for ReleaseRepository."""

    @pytest.fixture(autouse=True)
    def setup_config(self) -> None:
        """Set up test configuration."""
        self.config = SqliteTestConfiguration()

    @pytest.fixture
    def mock_release(self) -> Release:
        """Create a mock release for testing."""
        return Release(
            release_id=200,
            title="Test Release",
        )

    @pytest.fixture
    def mock_release_table(self) -> ReleaseTable:
        """Create a mock release table record."""
        table_mock = Mock(spec=ReleaseTable)
        table_mock.release_id = 200
        table_mock.title = "Test Release"
        return table_mock

    @pytest.fixture
    def release_repository(self) -> ReleaseRepository:
        """Create a ReleaseRepository instance for testing."""
        return ReleaseRepository()

    @pytest.mark.asyncio
    async def test_all_success(
        self,
        release_repository: ReleaseRepository,
        mock_release_table: ReleaseTable,
        mock_release: Release,
    ) -> None:
        """Test successful all() method execution."""

        async def mock_partitions() -> AsyncGenerator[list, None]:
            yield [(mock_release_table,)]

        mock_result = Mock()
        mock_result.partitions.return_value = mock_partitions()
        mock_session = AsyncMock()
        mock_session.stream = AsyncMock(return_value=mock_result)

        with patch.object(
            ReleaseRepository, "_session", new_callable=PropertyMock, return_value=mock_session
        ):
            with patch.object(Release, "model_validate", return_value=mock_release):
                results = []
                async for batch in release_repository.all():
                    results.extend(batch)

                assert len(results) == 1
                assert results[0] == mock_release

    @pytest.mark.asyncio
    async def test_get_by_id_success(
        self,
        release_repository: ReleaseRepository,
        mock_release_table: ReleaseTable,
        mock_release: Release,
    ) -> None:
        """Test successful get_by_id execution."""
        with patch.object(
            release_repository, "_get", AsyncMock(return_value=mock_release_table)
        ):
            with patch.object(Release, "model_validate", return_value=mock_release):
                result = await release_repository.get_by_id(200)
                assert result == mock_release

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, release_repository: ReleaseRepository) -> None:
        """Test get_by_id when release is not found."""
        with patch.object(release_repository, "_get", AsyncMock(return_value=None)):
            with pytest.raises(NotFoundError):
                await release_repository.get_by_id(999)

    @pytest.mark.asyncio
    async def test_get_by_master_id_success(
        self,
        release_repository: ReleaseRepository,
        mock_release_table: ReleaseTable,
        mock_release: Release,
    ) -> None:
        """Test get_by_master_id returns list of releases."""
        mock_result = Mock(spec=Result)
        mock_result.scalars.return_value.all.return_value = [mock_release_table]
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=mock_result)

        with patch.object(
            ReleaseRepository, "_session", new_callable=PropertyMock, return_value=mock_session
        ):
            with patch.object(Release, "model_validate", return_value=mock_release):
                result = await release_repository.get_by_master_id(100)
                assert result == [mock_release]

    @pytest.mark.asyncio
    async def test_create_success(
        self,
        release_repository: ReleaseRepository,
        mock_release: Release,
        mock_release_table: ReleaseTable,
    ) -> None:
        """Test successful create execution."""
        with patch.object(
            release_repository, "_save", AsyncMock(return_value=mock_release_table)
        ):
            with patch.object(Release, "model_validate", return_value=mock_release):
                result = await release_repository.create(mock_release)
                assert result == mock_release

    @pytest.mark.asyncio
    async def test_get_ids_success(self, release_repository: ReleaseRepository) -> None:
        """Test get_ids returns sequence of ids."""
        mock_result = Mock(spec=Result)
        mock_result.scalars.return_value.all.return_value = [1, 2, 3]
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=mock_result)

        with patch.object(
            ReleaseRepository, "_session", new_callable=PropertyMock, return_value=mock_session
        ):
            result = await release_repository.get_ids()
            assert result == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_update_success(self, release_repository: ReleaseRepository) -> None:
        """Test successful update execution."""
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock()
        mock_session.flush = AsyncMock()

        with patch.object(
            ReleaseRepository, "_session", new_callable=PropertyMock, return_value=mock_session
        ):
            await release_repository.update(200, {"title": "Updated Title"})
            mock_session.execute.assert_called_once()
            mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_by_id_success(self, release_repository: ReleaseRepository) -> None:
        """Test successful delete_by_id execution."""
        mock_session = AsyncMock()
        mock_session.flush = AsyncMock()

        with patch.object(
            ReleaseRepository, "_session", new_callable=PropertyMock, return_value=mock_session
        ):
            with patch.object(release_repository, "execute", AsyncMock()):
                await release_repository.delete_by_id(200)
                mock_session.flush.assert_called_once()

    def test_schema_class_is_set(self, release_repository: ReleaseRepository) -> None:
        """Test that schema_class is properly set."""
        assert release_repository.schema_class == ReleaseTable
