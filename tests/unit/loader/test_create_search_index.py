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
    @patch("musigree.loader.create_text_search_index.RuntimeDatabaseManager")
    @patch("musigree.loader.create_text_search_index.OfflineDatabaseManager")
    @patch("musigree.loader.create_text_search_index.setup_logging")
    def test_shutdown_loader_calls_managers(
        self,
        mock_setup_logging: MagicMock,
        mock_offline_manager: MagicMock,
        mock_runtime_manager: MagicMock,
        mock_cache_manager: MagicMock,
        mock_shutdown_logging: MagicMock,
    ) -> None:
        """Test shutdown_loader calls database shutdown and cache shutdown."""
        async def noop() -> None:
            pass

        mock_offline_manager.shutdown_database = MagicMock(side_effect=lambda: noop())
        mock_runtime_manager.shutdown_database = MagicMock(side_effect=lambda: noop())
        mock_cache_manager.shutdown_cache = MagicMock(return_value=noop())

        shutdown_loader()

        mock_setup_logging.assert_called_once()
        mock_offline_manager.shutdown_database.assert_called_once()
        mock_runtime_manager.shutdown_database.assert_called_once()
        mock_cache_manager.shutdown_cache.assert_called_once()
        mock_shutdown_logging.assert_called_once()

    @patch("musigree.loader.create_text_search_index.shutdown_logging")
    @patch("musigree.loader.create_text_search_index.CacheManager")
    @patch("musigree.loader.create_text_search_index.RuntimeDatabaseManager")
    @patch("musigree.loader.create_text_search_index.OfflineDatabaseManager")
    @patch("musigree.loader.create_text_search_index.setup_logging")
    def test_shutdown_loader_handles_operational_error(
        self,
        mock_setup_logging: MagicMock,
        mock_offline_manager: MagicMock,
        mock_runtime_manager: MagicMock,
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
        mock_runtime_manager.shutdown_database = MagicMock(side_effect=lambda: raise_op_error())
        mock_cache_manager.shutdown_cache = MagicMock(return_value=noop())

        shutdown_loader()

        mock_cache_manager.shutdown_cache.assert_called_once()
        mock_shutdown_logging.assert_called_once()


class TestCreateSearchIndex:
    """Test cases for create_text_search_index function."""

    @patch("musigree.loader.create_text_search_index.TransferManager")
    @patch("musigree.loader.create_text_search_index.LoaderEntity")
    @patch("musigree.loader.create_text_search_index.ALL_RUNTIME_DATABASE_TABLE_NAMES", ["table1"])
    @patch("musigree.loader.create_text_search_index.RuntimeDatabaseManager")
    @patch("musigree.loader.create_text_search_index.OfflineDatabaseManager")
    @patch("musigree.loader.create_text_search_index.CacheManager")
    @patch("musigree.loader.create_text_search_index.atexit")
    @patch("musigree.loader.create_text_search_index.log_banner")
    @patch("musigree.loader.create_text_search_index.setup_logging")
    def test_create_text_search_index_success(
        self,
        mock_setup_logging: MagicMock,
        mock_log_banner: MagicMock,
        mock_atexit: MagicMock,
        mock_cache_manager: MagicMock,
        mock_offline_manager: MagicMock,
        mock_runtime_manager: MagicMock,
        mock_loader_entity_cls: MagicMock,
        mock_transfer_manager_cls: MagicMock,
    ) -> None:
        """create_text_search_index runs setup and index creation when cache is available."""
        async def noop() -> None:
            pass

        mock_cache_manager.setup_cache = MagicMock(return_value=noop())
        mock_cache_manager.get_cache.return_value = MagicMock()
        mock_cache_manager.clear = MagicMock(return_value=noop())
        mock_offline_manager.setup_database = MagicMock(return_value=noop())
        mock_offline_manager.offline_database_helper = MagicMock()
        mock_runtime_manager.setup_database = MagicMock(return_value=noop())
        mock_runtime_manager.runtime_database_helper = MagicMock()
        mock_runtime_manager.runtime_database_helper.create_tables = MagicMock(
            return_value=noop()
        )
        mock_loader = MagicMock()
        mock_loader.loader_create_text_search_index = MagicMock(return_value=noop())
        mock_loader_entity_cls.return_value = mock_loader
        mock_transfer = MagicMock()
        mock_transfer.transfer_load_text_search_index = MagicMock(return_value=noop())
        mock_transfer_manager_cls.return_value = mock_transfer

        with patch(
            "musigree.loader.create_text_search_index.SqliteDevelopmentConfiguration"
        ) as mock_config_cls:
            mock_config = MagicMock()
            mock_config.DATA_DIR = Path(".")
            mock_config_cls.return_value = mock_config

            create_text_search_index()

        mock_setup_logging.assert_called_once()
        mock_log_banner.assert_called_once()
        mock_atexit.register.assert_called_once()
        mock_cache_manager.setup_cache.assert_called_once()
        mock_cache_manager.get_cache.assert_called()
        mock_offline_manager.setup_database.assert_called_once()
        mock_runtime_manager.setup_database.assert_called_once()
        mock_runtime_manager.runtime_database_helper.create_tables.assert_called_once_with(
            ["table1"]
        )
        mock_loader.loader_create_text_search_index.assert_called_once()
        mock_transfer.transfer_load_text_search_index.assert_called_once()

    @patch("musigree.loader.create_text_search_index.sys")
    @patch("musigree.loader.create_text_search_index.CacheManager")
    @patch("musigree.loader.create_text_search_index.atexit")
    @patch("musigree.loader.create_text_search_index.log_banner")
    @patch("musigree.loader.create_text_search_index.setup_logging")
    def test_create_text_search_index_exits_when_cache_not_set(
        self,
        mock_setup_logging: MagicMock,
        mock_log_banner: MagicMock,
        mock_atexit: MagicMock,
        mock_cache_manager: MagicMock,
        mock_sys: MagicMock,
    ) -> None:
        """create_text_search_index exits when CacheManager.get_cache() returns None."""
        async def noop() -> None:
            pass

        mock_cache_manager.setup_cache = MagicMock(return_value=noop())
        mock_cache_manager.get_cache.return_value = None
        mock_sys.exit.side_effect = SystemExit

        with patch(
            "musigree.loader.create_text_search_index.SqliteDevelopmentConfiguration"
        ):
            with pytest.raises(SystemExit):
                create_text_search_index()

        mock_sys.exit.assert_called_once()
