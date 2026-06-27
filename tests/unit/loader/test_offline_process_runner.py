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

    @patch("musigree.loader.offline_process_runner.asyncio.Runner")
    @patch("musigree.loader.offline_process_runner.OfflineRoleDataAccess")
    @patch("musigree.loader.offline_process_runner.asyncio_atexit")
    @patch("musigree.loader.offline_process_runner.OfflineDatabaseManager")
    @patch("musigree.loader.offline_process_runner.CacheManager")
    @patch("musigree.loader.offline_process_runner.log_banner")
    @patch("musigree.loader.offline_process_runner.setup_logging")
    def test_run_offline_loading_process_success(
        self,
        mock_setup_logging: MagicMock,
        mock_log_banner: MagicMock,
        mock_cache: MagicMock,
        mock_offline_manager: MagicMock,
        mock_atexit: MagicMock,
        mock_role_data_access: MagicMock,
        mock_runner: MagicMock,
    ) -> None:
        """Test run_offline_loading_process sets up cache and db and runs process."""
        config = MagicMock()
        config.__class__.__name__ = "TestConfig"

        async def noop() -> None:
            pass

        mock_cache.setup_and_clear_cache = AsyncMock(return_value=None)
        mock_offline_manager.setup_database = AsyncMock(return_value=None)
        mock_offline_manager.offline_database_helper = MagicMock()
        mock_role_data_access.load_all_roles_into_cache = AsyncMock(return_value=None)

        mock_runner_instance = MagicMock()
        mock_runner.return_value.__enter__.return_value = mock_runner_instance
        mock_runner.return_value.__exit__.return_value = None
        mock_runner_instance.get_loop.return_value = MagicMock()

        process_coro = noop()

        run_offline_loading_process(config, process_coro)

        mock_setup_logging.assert_called_once()
        mock_log_banner.assert_called_once()
        mock_cache.setup_and_clear_cache.assert_called_once()
        mock_offline_manager.setup_database.assert_called_once_with(config)
        assert mock_atexit.register.call_count >= 1
        assert mock_runner_instance.run.call_count >= 1
