"""
Unit tests for musigree.loader.run_offline_create_text_search_index module.
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from sqlalchemy.exc import OperationalError

from musigree.loader.run_offline_create_text_search_index import (
    create_text_search_index,
    shutdown_loader,
)


class TestShutdownLoader:
    """Test cases for shutdown_loader function."""

    @pytest.mark.asyncio
    @patch("musigree.loader.run_offline_create_text_search_index.shutdown_logging")
    @patch("musigree.loader.run_offline_create_text_search_index.CacheManager")
    @patch("musigree.loader.run_offline_create_text_search_index.OfflineDatabaseManager")
    @patch("musigree.loader.run_offline_create_text_search_index.setup_logging")
    async def test_shutdown_loader_calls_managers(
        self,
        mock_setup_logging: MagicMock,
        mock_offline_manager: MagicMock,
        mock_cache_manager: MagicMock,
        mock_shutdown_logging: MagicMock,
    ) -> None:
        """Test shutdown_loader calls database shutdown and cache shutdown."""
        mock_offline_manager.shutdown_database = AsyncMock()
        mock_cache_manager.shutdown_cache = AsyncMock()

        await shutdown_loader()

        mock_setup_logging.assert_called_once()
        mock_offline_manager.shutdown_database.assert_awaited_once()
        mock_cache_manager.shutdown_cache.assert_awaited_once()
        mock_shutdown_logging.assert_called_once()

    @pytest.mark.asyncio
    @patch("musigree.loader.run_offline_create_text_search_index.shutdown_logging")
    @patch("musigree.loader.run_offline_create_text_search_index.CacheManager")
    @patch("musigree.loader.run_offline_create_text_search_index.OfflineDatabaseManager")
    @patch("musigree.loader.run_offline_create_text_search_index.setup_logging")
    async def test_shutdown_loader_handles_operational_error(
        self,
        _mock_setup_logging: MagicMock,
        mock_offline_manager: MagicMock,
        mock_cache_manager: MagicMock,
        mock_shutdown_logging: MagicMock,
    ) -> None:
        """Test shutdown_loader swallows OperationalError from database shutdown."""
        mock_offline_manager.shutdown_database = AsyncMock(
            side_effect=OperationalError("stmt", {}, Exception("db error"))
        )
        mock_cache_manager.shutdown_cache = AsyncMock()

        await shutdown_loader()

        mock_cache_manager.shutdown_cache.assert_awaited_once()
        mock_shutdown_logging.assert_called_once()


class TestCreateSearchIndex:
    """Test cases for create_text_search_index function."""

    @patch("musigree.loader.run_offline_create_text_search_index.LoaderEntity")
    @patch("musigree.loader.run_offline_create_text_search_index.OfflineDatabaseManager")
    @patch("musigree.loader.run_offline_create_text_search_index.CacheManager")
    @patch("musigree.loader.run_offline_create_text_search_index.asyncio_atexit")
    @patch("musigree.loader.run_offline_create_text_search_index.log_banner")
    @patch("musigree.loader.run_offline_create_text_search_index.setup_logging")
    @patch("musigree.loader.run_offline_create_text_search_index.asyncio.Runner")
    def test_create_text_search_index_success(
        self,
        mock_runner: Mock,
        mock_setup_logging: Mock,
        mock_log_banner: Mock,
        _mock_asyncio_atexit: Mock,
        mock_cache_manager: Mock,
        mock_offline_manager: Mock,
        mock_loader_entity_cls: Mock,
    ) -> None:
        """create_text_search_index runs setup and index creation when cache is available."""
        mock_config = MagicMock()
        mock_config.DATA_DIR = Path("/test/data")

        mock_cache_manager.setup_and_clear_cache = AsyncMock()
        mock_offline_manager.setup_database = AsyncMock()
        mock_offline_manager.offline_database_helper = MagicMock()
        mock_loader = MagicMock()
        mock_loader.loader_create_text_search_index = AsyncMock()
        mock_loader_entity_cls.return_value = mock_loader

        mock_runner_instance = Mock()
        mock_runner.return_value.__enter__.return_value = mock_runner_instance
        mock_runner.return_value.__exit__.return_value = None

        create_text_search_index(mock_config)

        mock_setup_logging.assert_called_once()
        mock_log_banner.assert_called_once()
        mock_offline_manager.setup_database.assert_called()
        mock_loader.loader_create_text_search_index.assert_called_once()
        assert mock_runner_instance.run.call_count >= 2

    @patch("musigree.loader.run_offline_create_text_search_index.CacheManager")
    @patch("musigree.loader.run_offline_create_text_search_index.asyncio_atexit")
    @patch("musigree.loader.run_offline_create_text_search_index.log_banner")
    @patch("musigree.loader.run_offline_create_text_search_index.setup_logging")
    @patch("musigree.loader.run_offline_create_text_search_index.asyncio.Runner")
    def test_create_text_search_index_exits_when_cache_not_set(
        self,
        mock_runner: Mock,
        _mock_setup_logging: Mock,
        _mock_log_banner: Mock,
        _mock_asyncio_atexit: Mock,
        _mock_cache_manager: Mock,
    ) -> None:
        """create_text_search_index exits when cache setup fails."""
        mock_config = MagicMock()
        mock_config.DATA_DIR = Path("/test/data")

        mock_runner_instance = Mock()
        mock_runner_instance.run.side_effect = [
            RuntimeError("Cache not initialized after setup"),
            None,
        ]
        mock_runner.return_value.__enter__.return_value = mock_runner_instance
        mock_runner.return_value.__exit__.return_value = None

        with pytest.raises(SystemExit):
            create_text_search_index(mock_config)
