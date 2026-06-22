"""
Unit tests for musigree.loader.create_text_search_index module.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from musigree.loader.create_text_search_index import create_text_search_index, shutdown_loader


class TestShutdownLoader:
    """Test cases for shutdown_loader function."""

    @patch("musigree.loader.create_text_search_index.shutdown_logging")
    @patch("musigree.loader.create_text_search_index.CacheManager")
    @patch("musigree.loader.create_text_search_index.OfflineDatabaseManager")
    @patch("musigree.loader.create_text_search_index.setup_logging")
    def test_shutdown_loader_calls_managers(
        self,
        mock_setup_logging: MagicMock,
        mock_offline_manager: MagicMock,
        mock_cache_manager: MagicMock,
        mock_shutdown_logging: MagicMock,
    ) -> None:
        """Test shutdown_loader calls database shutdown and cache shutdown."""

        async def noop() -> None:
            pass

        mock_offline_manager.shutdown_database = MagicMock(side_effect=lambda: noop())
        mock_cache_manager.shutdown_cache = MagicMock(return_value=noop())

        shutdown_loader()

        mock_setup_logging.assert_called_once()
        mock_offline_manager.shutdown_database.assert_called_once()
        mock_cache_manager.shutdown_cache.assert_called_once()
        mock_shutdown_logging.assert_called_once()

    @patch("musigree.loader.create_text_search_index.shutdown_logging")
    @patch("musigree.loader.create_text_search_index.CacheManager")
    @patch("musigree.loader.create_text_search_index.OfflineDatabaseManager")
    @patch("musigree.loader.create_text_search_index.setup_logging")
    def test_shutdown_loader_handles_operational_error(
        self,
        _mock_setup_logging: MagicMock,
        mock_offline_manager: MagicMock,
        mock_cache_manager: MagicMock,
        mock_shutdown_logging: MagicMock,
    ) -> None:
        """Test shutdown_loader swallows OperationalError from database shutdown."""
        from sqlalchemy.exc import OperationalError

        async def raise_op_error() -> None:
            raise OperationalError("stmt", {}, Exception("db error"))

        async def noop() -> None:
            pass

        mock_offline_manager.shutdown_database = MagicMock(side_effect=lambda: raise_op_error())
        mock_cache_manager.shutdown_cache = MagicMock(return_value=noop())

        shutdown_loader()

        mock_cache_manager.shutdown_cache.assert_called_once()
        mock_shutdown_logging.assert_called_once()


class TestCreateSearchIndex:
    """Test cases for create_text_search_index function."""

    @patch("musigree.loader.create_text_search_index.LoaderEntity")
    @patch("musigree.loader.create_text_search_index.OfflineDatabaseManager")
    @patch("musigree.loader.create_text_search_index.CacheManager")
    @patch("musigree.loader.create_text_search_index.atexit")
    @patch("musigree.loader.create_text_search_index.log_banner")
    @patch("musigree.loader.create_text_search_index.setup_logging")
    @patch("musigree.loader.create_text_search_index.asyncio.Runner")
    def test_create_text_search_index_success(
        self,
        mock_runner: MagicMock,
        mock_setup_logging: MagicMock,
        mock_log_banner: MagicMock,
        mock_atexit: MagicMock,
        mock_cache_manager: MagicMock,
        mock_offline_manager: MagicMock,
        mock_loader_entity_cls: MagicMock,
    ) -> None:
        """create_text_search_index runs setup and index creation when cache is available."""

        async def noop() -> None:
            pass

        mock_cache_manager.setup_and_clear_cache = MagicMock(return_value=noop())
        mock_offline_manager.setup_database = MagicMock(return_value=noop())
        mock_offline_manager.offline_database_helper = MagicMock()
        mock_loader = MagicMock()
        mock_loader.loader_create_text_search_index = MagicMock(return_value=noop())
        mock_loader_entity_cls.return_value = mock_loader

        mock_runner_instance = MagicMock()
        mock_runner.return_value.__enter__.return_value = mock_runner_instance
        mock_runner.return_value.__exit__.return_value = None

        with patch(
            "musigree.loader.create_text_search_index.PostgresReadOnlyDevelopmentConfiguration"
        ) as mock_config_cls:
            mock_config = MagicMock()
            mock_config.DATA_DIR = Path(".")
            mock_config_cls.return_value = mock_config

            create_text_search_index()

        mock_setup_logging.assert_called_once()
        mock_log_banner.assert_called_once()
        mock_atexit.register.assert_called_once()
        mock_offline_manager.setup_database.assert_called_once()
        mock_loader.loader_create_text_search_index.assert_called_once()
        assert mock_runner_instance.run.call_count >= 2

    @patch("musigree.loader.create_text_search_index.CacheManager")
    @patch("musigree.loader.create_text_search_index.atexit")
    @patch("musigree.loader.create_text_search_index.log_banner")
    @patch("musigree.loader.create_text_search_index.setup_logging")
    @patch("musigree.loader.create_text_search_index.asyncio.Runner")
    def test_create_text_search_index_exits_when_cache_not_set(
        self,
        mock_runner: MagicMock,
        _mock_setup_logging: MagicMock,
        _mock_log_banner: MagicMock,
        _mock_atexit: MagicMock,
        mock_cache_manager: MagicMock,
    ) -> None:
        """create_text_search_index exits when cache setup fails."""

        async def raise_runtime_error() -> None:
            raise RuntimeError("Cache not initialized after setup")

        mock_cache_manager.setup_and_clear_cache = MagicMock(return_value=raise_runtime_error())

        mock_runner_instance = MagicMock()
        mock_runner_instance.run.side_effect = RuntimeError("Cache not initialized after setup")
        mock_runner.return_value.__enter__.return_value = mock_runner_instance
        mock_runner.return_value.__exit__.return_value = None

        with patch(
            "musigree.loader.create_text_search_index.PostgresReadOnlyDevelopmentConfiguration"
        ):
            with pytest.raises(SystemExit):
                create_text_search_index()
