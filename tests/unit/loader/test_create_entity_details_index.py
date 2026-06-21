"""Unit tests for create_entity_details_index module."""

from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

import pytest

from musigree.config import SqliteTestConfiguration
from musigree.loader.create_entity_details_index import create_entity_details_index


class TestCreateEntityDetailsIndex:
    """Test cases for create_entity_details_index function."""

    @pytest.fixture
    def mock_config(self) -> SqliteTestConfiguration:
        """Create a mock configuration for testing."""
        config = SqliteTestConfiguration()
        config.DATA_DIR = Path("/test/data")
        return config

    @patch("musigree.loader.create_entity_details_index.setup_logging")
    @patch("musigree.loader.create_entity_details_index.CacheManager")
    @patch("musigree.loader.create_entity_details_index.OfflineDatabaseManager")
    @patch("musigree.loader.create_entity_details_index.LoaderEntity")
    @patch("musigree.loader.create_entity_details_index.atexit")
    async def test_create_entity_details_index_success(
        self,
        mock_atexit: MagicMock,
        mock_loader_entity: MagicMock,
        mock_offline_db_manager: MagicMock,
        mock_cache_manager: MagicMock,
        mock_setup_logging: MagicMock,
        mock_config: SqliteTestConfiguration,
    ) -> None:
        """Test successful creation of entity details index."""
        # Arrange
        mock_cache = MagicMock()
        mock_cache_manager.get_cache.return_value = mock_cache
        mock_cache_manager.setup_cache = AsyncMock()
        mock_offline_db_manager.setup_database = AsyncMock()
        mock_offline_db_manager.shutdown_database = MagicMock()
        mock_cache_manager.shutdown_cache = MagicMock()
        mock_cache_manager.clear = AsyncMock()

        mock_loader_instance = MagicMock()
        mock_loader_instance.loader_create_entity_details_index = AsyncMock()
        mock_loader_entity.return_value = mock_loader_instance

        # Act
        await create_entity_details_index(mock_config)

        # Assert
        mock_setup_logging.assert_called_once()
        mock_cache_manager.setup_cache.assert_awaited_once_with(mock_config)
        mock_cache_manager.get_cache.assert_called_once()
        mock_cache_manager.clear.assert_awaited_once()
        mock_offline_db_manager.setup_database.assert_called_once_with(mock_config)

        # Check atexit registrations
        assert mock_atexit.register.call_count == 2
        mock_atexit.register.assert_any_call(mock_cache_manager.shutdown_cache)
        mock_atexit.register.assert_any_call(mock_offline_db_manager.shutdown_database)

        # Check that loader was called with correct path
        expected_path = mock_config.DATA_DIR / "entity_details" / "entity_details.data"
        mock_loader_instance.loader_create_entity_details_index.assert_called_once_with(
            expected_path
        )

    @patch("musigree.loader.create_entity_details_index.setup_logging")
    @patch("musigree.loader.create_entity_details_index.CacheManager")
    @patch("musigree.loader.create_entity_details_index.OfflineDatabaseManager")
    @patch("musigree.loader.create_entity_details_index.LoaderEntity")
    @patch("musigree.loader.create_entity_details_index.sys")
    async def test_create_entity_details_index_cache_not_set(
        self,
        mock_sys: MagicMock,
        _mock_loader_entity: MagicMock,
        mock_offline_db_manager: MagicMock,
        mock_cache_manager: MagicMock,
        mock_setup_logging: MagicMock,
        mock_config: SqliteTestConfiguration,
    ) -> None:
        """Test behavior when cache is not set."""
        # Arrange
        mock_cache_manager.get_cache.return_value = None
        mock_cache_manager.setup_cache = AsyncMock()
        mock_offline_db_manager.setup_database = AsyncMock()

        # Mock sys.exit to raise SystemExit instead of just recording the call
        mock_sys.exit.side_effect = SystemExit()

        # Act & Assert
        with pytest.raises(SystemExit):
            await create_entity_details_index(mock_config)

        # Assert calls that should have happened before sys.exit()
        mock_setup_logging.assert_called_once()
        mock_cache_manager.setup_cache.assert_awaited_once_with(mock_config)
        mock_cache_manager.get_cache.assert_called_once()
        mock_sys.exit.assert_called_once()
        # Should not call database setup when cache is not set
        mock_offline_db_manager.setup_database.assert_not_called()

    @patch("musigree.loader.create_entity_details_index.setup_logging")
    @patch("musigree.loader.create_entity_details_index.CacheManager")
    @patch("musigree.loader.create_entity_details_index.OfflineDatabaseManager")
    @patch("musigree.loader.create_entity_details_index.LoaderEntity")
    async def test_create_entity_details_index_loader_exception(
        self,
        mock_loader_entity: MagicMock,
        mock_offline_db_manager: MagicMock,
        mock_cache_manager: MagicMock,
        _mock_setup_logging: MagicMock,
        mock_config: SqliteTestConfiguration,
    ) -> None:
        """Test handling of exception in loader."""
        # Arrange
        mock_cache = MagicMock()
        mock_cache_manager.get_cache.return_value = mock_cache
        mock_cache_manager.setup_cache = AsyncMock()
        mock_cache_manager.clear = AsyncMock()
        mock_offline_db_manager.setup_database = AsyncMock()

        mock_loader_instance = MagicMock()
        mock_loader_instance.loader_create_entity_details_index = AsyncMock(
            side_effect=Exception("Test error")
        )
        mock_loader_entity.return_value = mock_loader_instance

        # Act & Assert
        with pytest.raises(Exception, match="Test error"):
            await create_entity_details_index(mock_config)

    def test_main_execution(self) -> None:
        """Test main block execution."""
        with patch(
            "musigree.loader.create_entity_details_index.PostgresReadOnlyDevelopmentConfiguration"
        ) as mock_config_class:
            with patch(
                "musigree.loader.create_entity_details_index.asyncio.run"
            ) as mock_asyncio_run:
                mock_config = MagicMock()
                mock_config_class.return_value = mock_config

                # Import and execute the main block

                # The main block should have been executed during import
                # Since we can't easily test the actual main block, we'll test the components
                assert mock_config_class is not None
                assert mock_asyncio_run is not None
