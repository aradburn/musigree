"""
Unit tests for musigree.loader.runtime_process_runner module.
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from musigree.constants import ENTITY_DETAILS_DATA, ENTITY_DETAILS_FILENAME
from musigree.loader.runtime_process_runner import (
    run_runtime_loading_process,
    shutdown_process_runner,
)


class TestShutdownProcessRunner:
    """Test cases for shutdown_process_runner."""

    @pytest.mark.asyncio
    @patch("musigree.loader.runtime_process_runner.shutdown_logging")
    @patch("musigree.loader.runtime_process_runner.RuntimeDatabaseManager")
    @patch("musigree.loader.runtime_process_runner.OfflineDatabaseManager")
    @patch("musigree.loader.runtime_process_runner.CacheManager")
    @patch("musigree.loader.runtime_process_runner.setup_logging")
    async def test_shutdown_process_runner_calls_managers(
        self,
        mock_setup_logging: MagicMock,
        mock_cache: MagicMock,
        mock_offline_manager: MagicMock,
        mock_runtime_manager: MagicMock,
        mock_shutdown_logging: MagicMock,
    ) -> None:
        """Test shutdown_process_runner shuts down offline, runtime, and cache."""
        mock_offline_manager.offline_database_helper = MagicMock()
        mock_runtime_manager.runtime_database_helper = MagicMock()
        mock_offline_manager.shutdown_database = AsyncMock()
        mock_runtime_manager.shutdown_database = AsyncMock()
        mock_cache.shutdown_cache = AsyncMock()

        await shutdown_process_runner()

        mock_setup_logging.assert_called_once()
        mock_offline_manager.shutdown_database.assert_called_once()
        mock_runtime_manager.shutdown_database.assert_called_once()
        mock_cache.shutdown_cache.assert_called_once()
        mock_shutdown_logging.assert_called_once()


class TestRunRuntimeLoadingProcess:
    """Test cases for run_runtime_loading_process."""

    @patch("musigree.loader.runtime_process_runner.asyncio.Runner")
    @patch("musigree.loader.runtime_process_runner.TransferManager")
    @patch("musigree.loader.runtime_process_runner.OfflineRoleDataAccess")
    @patch("musigree.loader.runtime_process_runner.asyncio_atexit")
    @patch("musigree.loader.runtime_process_runner.RuntimeDatabaseManager")
    @patch("musigree.loader.runtime_process_runner.OfflineDatabaseManager")
    @patch("musigree.loader.runtime_process_runner.CacheManager")
    @patch("musigree.loader.runtime_process_runner.log_banner")
    @patch("musigree.loader.runtime_process_runner.setup_logging")
    def test_run_runtime_loading_process_success(
        self,
        mock_setup_logging: MagicMock,
        mock_log_banner: MagicMock,
        mock_cache: MagicMock,
        mock_offline_manager: MagicMock,
        mock_runtime_manager: MagicMock,
        mock_atexit: MagicMock,
        mock_role_data_access: MagicMock,
        mock_transfer_manager: MagicMock,
        mock_runner: MagicMock,
    ) -> None:
        """Test run_runtime_loading_process sets up databases and runs the process."""
        offline_config = MagicMock()
        offline_config.__class__.__name__ = "OfflineConfig"
        runtime_config = MagicMock()
        runtime_config.__class__.__name__ = "RuntimeConfig"
        runtime_config.DATA_DIR = Path("/test/runtime")

        async def noop() -> None:
            pass

        mock_cache.setup_and_clear_cache = AsyncMock(return_value=None)
        mock_offline_manager.setup_database = AsyncMock(return_value=None)
        mock_offline_manager.offline_database_helper = MagicMock()
        mock_runtime_manager.setup_database = AsyncMock(return_value=None)
        mock_runtime_manager.runtime_database_helper = MagicMock()
        mock_role_data_access.load_all_roles_into_cache = AsyncMock(return_value=None)
        mock_transfer_manager.transfer_load_entity_details_index = AsyncMock(return_value=None)

        mock_runner_instance = MagicMock()
        mock_runner.return_value.__enter__.return_value = mock_runner_instance
        mock_runner.return_value.__exit__.return_value = None
        mock_runner_instance.get_loop.return_value = MagicMock()

        process_coro = noop()

        run_runtime_loading_process(offline_config, runtime_config, process_coro)

        mock_setup_logging.assert_called_once()
        mock_log_banner.assert_called_once()
        mock_cache.setup_and_clear_cache.assert_called_once()
        mock_offline_manager.setup_database.assert_called_once_with(offline_config)
        mock_runtime_manager.setup_database.assert_called_once_with(runtime_config)
        assert mock_atexit.register.call_count >= 1
        assert mock_runner_instance.run.call_count >= 1

    @patch("musigree.loader.runtime_process_runner.asyncio.Runner")
    @patch("musigree.loader.runtime_process_runner.TransferManager")
    @patch("musigree.loader.runtime_process_runner.OfflineRoleDataAccess")
    @patch("musigree.loader.runtime_process_runner.asyncio_atexit")
    @patch("musigree.loader.runtime_process_runner.RuntimeDatabaseManager")
    @patch("musigree.loader.runtime_process_runner.OfflineDatabaseManager")
    @patch("musigree.loader.runtime_process_runner.CacheManager")
    @patch("musigree.loader.runtime_process_runner.log_banner")
    @patch("musigree.loader.runtime_process_runner.setup_logging")
    def test_run_runtime_loading_process_loads_entity_details_index(
        self,
        _mock_setup_logging: MagicMock,
        _mock_log_banner: MagicMock,
        mock_cache: MagicMock,
        mock_offline_manager: MagicMock,
        mock_runtime_manager: MagicMock,
        _mock_atexit: MagicMock,
        mock_role_data_access: MagicMock,
        mock_transfer_manager: MagicMock,
        mock_runner: MagicMock,
    ) -> None:
        """Test run_runtime_loading_process preloads entity details via transfer_load_entity_details_index."""
        offline_config = MagicMock()
        runtime_config = MagicMock()
        runtime_config.DATA_DIR = Path("/test/runtime")
        entity_details_path = (
            runtime_config.DATA_DIR / ENTITY_DETAILS_DATA / ENTITY_DETAILS_FILENAME
        )

        async def noop() -> None:
            pass

        mock_cache.setup_and_clear_cache = AsyncMock(return_value=None)
        mock_offline_manager.setup_database = AsyncMock(return_value=None)
        mock_offline_manager.offline_database_helper = MagicMock()
        mock_runtime_manager.setup_database = AsyncMock(return_value=None)
        mock_runtime_manager.runtime_database_helper = MagicMock()
        mock_role_data_access.load_all_roles_into_cache = AsyncMock(return_value=None)
        mock_transfer_manager.transfer_load_entity_details_index = AsyncMock(return_value=None)

        mock_runner_instance = MagicMock()
        mock_runner.return_value.__enter__.return_value = mock_runner_instance
        mock_runner.return_value.__exit__.return_value = None
        mock_runner_instance.get_loop.return_value = MagicMock()

        run_runtime_loading_process(offline_config, runtime_config, noop())

        mock_transfer_manager.transfer_load_entity_details_index.assert_called_once_with(
            entity_details_path
        )
