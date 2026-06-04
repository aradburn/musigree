"""
Unit tests for musigree.loader.offline_process_runner module.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from musigree.loader.offline_process_runner import (
    run_offline_loading_process,
    shutdown_process_runner,
)


class TestShutdownProcessRunner:
    """Test cases for shutdown_process_runner."""

    @pytest.mark.asyncio
    @patch("musigree.loader.offline_process_runner.shutdown_logging")
    @patch("musigree.loader.offline_process_runner.OfflineDatabaseManager")
    @patch("musigree.loader.offline_process_runner.CacheManager")
    @patch("musigree.loader.offline_process_runner.setup_logging")
    async def test_shutdown_process_runner_calls_managers(
        self,
        mock_setup_logging: MagicMock,
        mock_cache: MagicMock,
        mock_offline_manager: MagicMock,
        mock_shutdown_logging: MagicMock,
    ) -> None:
        """Test shutdown_process_runner calls database and cache shutdown."""
        async def noop() -> None:
            pass

        mock_offline_manager.shutdown_database = MagicMock(side_effect=lambda: noop())
        mock_cache.shutdown_cache = MagicMock(side_effect=lambda: noop())

        await shutdown_process_runner()

        mock_setup_logging.assert_called_once()
        mock_offline_manager.shutdown_database.assert_called_once()
        mock_cache.shutdown_cache.assert_called_once()
        mock_shutdown_logging.assert_called_once()


class TestRunOfflineLoadingProcess:
    """Test cases for run_offline_loading_process."""

    @pytest.mark.asyncio
    @patch("musigree.loader.offline_process_runner.OfflineRoleDataAccess")
    @patch("musigree.loader.offline_process_runner.asyncio_atexit")
    @patch("musigree.loader.offline_process_runner.OfflineDatabaseManager")
    @patch("musigree.loader.offline_process_runner.CacheManager")
    @patch("musigree.loader.offline_process_runner.log_banner")
    @patch("musigree.loader.offline_process_runner.setup_logging")
    async def test_run_offline_loading_process_success(
        self,
        mock_setup_logging: MagicMock,
        mock_log_banner: MagicMock,
        mock_cache: MagicMock,
        mock_offline_manager: MagicMock,
        mock_atexit: MagicMock,
        mock_role_data_access: MagicMock,
    ) -> None:
        """Test run_offline_loading_process sets up cache and db and runs process."""
        config = MagicMock()
        config.__class__.__name__ = "TestConfig"

        async def noop() -> None:
            pass

        mock_cache.setup_cache = AsyncMock(return_value=None)
        mock_cache.get_cache = MagicMock(return_value=MagicMock())
        mock_cache.clear = AsyncMock(return_value=None)
        mock_offline_manager.setup_database = AsyncMock(return_value=None)
        mock_role_data_access.load_all_roles_into_cache = AsyncMock(return_value=None)

        process_coro = noop()

        await run_offline_loading_process(config, process_coro)

        mock_setup_logging.assert_called_once()
        mock_log_banner.assert_called_once()
        mock_cache.setup_cache.assert_called_once_with(config)
        mock_cache.get_cache.assert_called_once()
        mock_cache.clear.assert_called_once()
        mock_offline_manager.setup_database.assert_called_once_with(config)
        mock_atexit.register.assert_called_once()
        mock_role_data_access.load_all_roles_into_cache.assert_called_once()
