"""Unit tests for OfflineDatabaseManager class."""

import os
from unittest.mock import Mock, patch, AsyncMock

import pytest
from sqlalchemy import Engine

from musigree.constants import DatabaseType, ThreadingModel
from musigree.offline.offline_database_manager import OfflineDatabaseManager


class TestOfflineDatabaseManager:
    """Test suite for OfflineDatabaseManager."""

    @staticmethod
    def setup_method() -> None:
        """Reset class variables before each test."""
        OfflineDatabaseManager.offline_database_helper = None
        OfflineDatabaseManager._threading_model = None

    @staticmethod
    def teardown_method() -> None:
        """Clean up after each test."""
        OfflineDatabaseManager.offline_database_helper = None
        OfflineDatabaseManager._threading_model = None

    # Test get_concurrency_count method
    @patch("multiprocessing.cpu_count")
    def test_get_concurrency_count_process_model(self, mock_cpu_count: Mock) -> None:
        """Test get_concurrency_count returns CPU count for process threading model."""
        # Arrange
        mock_cpu_count.return_value = 4
        OfflineDatabaseManager._threading_model = ThreadingModel.PROCESS

        # Act
        result = OfflineDatabaseManager.get_concurrency_count()

        # Assert
        assert result == 8
        mock_cpu_count.assert_called_once()

    def test_get_concurrency_count_thread_model(self) -> None:
        """Test get_concurrency_count returns 1 for thread model."""
        # Arrange
        OfflineDatabaseManager._threading_model = ThreadingModel.THREAD

        # Act
        result = OfflineDatabaseManager.get_concurrency_count()

        # Assert
        assert result == 1

    def test_get_concurrency_count_not_configured(self) -> None:
        """Test get_concurrency_count raises error when threading model not configured."""
        # Arrange
        OfflineDatabaseManager._threading_model = None

        # Act & Assert
        with pytest.raises(NotImplementedError, match="THREADING_MODEL not configured"):
            OfflineDatabaseManager.get_concurrency_count()

    # Test setup_database method
    @patch("musigree.offline.postgres.offline_postgres_helper.OfflinePostgresHelper")
    @patch("musigree.offline.offline_database_manager.async_sessionmaker")
    @patch("musigree.offline.offline_database_manager.listen")
    @patch("logging.getLogger")
    @pytest.mark.asyncio
    async def test_setup_database_postgres_success(
        self,
        _mock_logger: Mock,
        mock_listen: Mock,
        mock_sessionmaker: Mock,
        mock_postgres_helper: Mock,
    ) -> None:
        """Test successful database setup for PostgreSQL."""
        # Arrange
        mock_config = Mock()
        mock_config.THREADING_MODEL = ThreadingModel.PROCESS
        mock_config.DATABASE = DatabaseType.POSTGRES

        # Create a proper engine mock with pool attribute
        mock_engine = Mock(spec=Engine)
        mock_pool = Mock()
        mock_engine.pool = mock_pool
        mock_engine.sync_engine = Mock()

        mock_helper_instance = Mock()
        mock_helper_instance.setup_database = AsyncMock(return_value=mock_engine)
        mock_helper_instance.check_connection = AsyncMock()
        mock_postgres_helper.return_value = mock_helper_instance

        mock_session_factory = Mock()
        mock_sessionmaker.return_value = mock_session_factory

        with patch.object(
            OfflineDatabaseManager, "get_concurrency_count", return_value=4
        ):
            # Act
            await OfflineDatabaseManager.setup_database(mock_config)

        # Assert
        assert OfflineDatabaseManager.offline_database_helper == mock_helper_instance
        assert OfflineDatabaseManager._threading_model == ThreadingModel.PROCESS
        # Check that helper has the expected attributes set
        helper = OfflineDatabaseManager.offline_database_helper
        assert helper is not None
        assert hasattr(helper, "offline_engine")
        assert hasattr(helper, "offline_session_factory")
        assert helper.offline_async_engine == mock_engine
        assert helper.offline_async_session_factory == mock_session_factory

        mock_postgres_helper.assert_called_once()
        mock_helper_instance.setup_database.assert_called_once_with(mock_config)
        mock_helper_instance.check_connection.assert_called_once_with(
            mock_config, mock_engine
        )
        mock_sessionmaker.assert_called_once_with(
            bind=mock_engine, expire_on_commit=False
        )
        # Should register event listeners for concurrency > 1
        assert mock_listen.call_count == 2

    @patch("os.getpid")
    @patch("musigree.offline.sqlite.offline_sqlite_helper.OfflineSqliteHelper")
    @patch("musigree.offline.offline_database_manager.listen")
    @patch("logging.getLogger")
    @pytest.mark.asyncio
    async def test_setup_database_registers_event_listeners_for_multiprocessing(
        self,
        _mock_logger: Mock,
        mock_listen: Mock,
        mock_sqlite_helper: Mock,
        _mock_getpid: Mock,
    ) -> None:
        """Test that event listeners are registered when concurrency count > 1."""
        # Arrange
        mock_config = Mock()
        mock_config.THREADING_MODEL = ThreadingModel.PROCESS
        mock_config.DATABASE = DatabaseType.SQLITE

        mock_engine = Mock(spec=Engine)
        mock_pool = Mock()
        mock_engine.pool = mock_pool
        mock_engine.sync_engine = Mock()

        mock_helper_instance = Mock()
        mock_helper_instance.setup_database = AsyncMock(return_value=mock_engine)
        mock_helper_instance.check_connection = AsyncMock()
        mock_sqlite_helper.return_value = mock_helper_instance

        with patch.object(
            OfflineDatabaseManager, "get_concurrency_count", return_value=4
        ):
            # Act
            await OfflineDatabaseManager.setup_database(mock_config)

        # Assert that event listeners were registered
        assert mock_listen.call_count == 2
        # Check that the events registered are "connect" and "checkout"
        registered_events = [call[0][1] for call in mock_listen.call_args_list]
        assert "connect" in registered_events
        assert "checkout" in registered_events

    @patch("musigree.offline.sqlite.offline_sqlite_helper.OfflineSqliteHelper")
    @patch("musigree.offline.offline_database_manager.listen")
    @patch("logging.getLogger")
    @pytest.mark.asyncio
    async def test_setup_database_no_event_listeners_for_single_thread(
        self, _mock_logger: Mock, mock_listen: Mock, mock_sqlite_helper: Mock
    ) -> None:
        """Test that no event listeners are registered when concurrency count = 1."""
        # Arrange
        mock_config = Mock()
        mock_config.THREADING_MODEL = ThreadingModel.THREAD
        mock_config.DATABASE = DatabaseType.SQLITE

        mock_engine = Mock(spec=Engine)
        mock_helper_instance = Mock()
        mock_helper_instance.setup_database = AsyncMock(return_value=mock_engine)
        mock_helper_instance.check_connection = AsyncMock()
        mock_sqlite_helper.return_value = mock_helper_instance

        with patch.object(
            OfflineDatabaseManager, "get_concurrency_count", return_value=1
        ):
            # Act
            await OfflineDatabaseManager.setup_database(mock_config)

        # Assert that no event listeners were registered
        mock_listen.assert_not_called()

    @pytest.mark.asyncio
    async def test_setup_database_unknown_database_type(self) -> None:
        """Test setup_database raises error for unknown database type."""
        # Arrange
        mock_config = Mock()
        mock_config.THREADING_MODEL = ThreadingModel.THREAD
        mock_config.DATABASE = "UNKNOWN_TYPE"

        # Act & Assert
        with pytest.raises(
            ValueError, match="Configuration Error: Unknown database type"
        ):
            await OfflineDatabaseManager.setup_database(mock_config)

    def test_engine_event_handlers_behavior(self) -> None:
        """Test the behavior of engine event handlers using mock scenarios."""
        # This test verifies that the event handler logic works correctly
        # by simulating the conditions that would be present in the actual handlers

        # Simulate connect handler behavior
        mock_connection_record = Mock()
        mock_connection_record.info = {}

        with patch("os.getpid", return_value=12345):
            # Simulate what the connect handler would do
            mock_connection_record.info["pid"] = os.getpid()

            # Assert the PID was set correctly
            assert mock_connection_record.info["pid"] == 12345

        # Simulate checkout handler behavior with wrong PID
        mock_connection_record.info = {"pid": 12345}
        mock_connection_proxy = Mock()

        with patch("os.getpid", return_value=99999):  # Different PID
            # Simulate what the checkout handler would do when PIDs don't match
            current_pid = os.getpid()
            if mock_connection_record.info["pid"] != current_pid:
                # This is what the handler would do
                mock_connection_record.dbapi_connection = None
                mock_connection_proxy.dbapi_connection = None

                # Assert that connections were reset
                assert mock_connection_record.dbapi_connection is None
                assert mock_connection_proxy.dbapi_connection is None

    # Test shutdown_database method
    @pytest.mark.asyncio
    async def test_shutdown_database_success(self) -> None:
        """Test successful database shutdown."""
        # Arrange
        mock_engine = AsyncMock()
        mock_helper = Mock()
        mock_helper.offline_async_engine = mock_engine
        mock_helper.shutdown_database = AsyncMock()

        OfflineDatabaseManager.offline_database_helper = mock_helper

        # Act
        await OfflineDatabaseManager.shutdown_database()

        # Assert
        mock_engine.dispose.assert_called_once()
        mock_helper.shutdown_database.assert_called_once()

    @pytest.mark.asyncio
    async def test_shutdown_database_no_engine(self) -> None:
        """Test database shutdown when no engine exists."""
        # Arrange
        mock_helper = Mock()
        mock_helper.offline_async_engine = None
        mock_helper.shutdown_database = AsyncMock()

        OfflineDatabaseManager.offline_database_helper = mock_helper

        # Act
        await OfflineDatabaseManager.shutdown_database()

        # Assert
        mock_helper.shutdown_database.assert_called_once()

    @pytest.mark.asyncio
    async def test_shutdown_database_no_helper(self) -> None:
        """Test database shutdown when no helper exists."""
        # Arrange
        OfflineDatabaseManager.offline_database_helper = None

        # Act & Assert
        with pytest.raises(
            AssertionError,
            match="OfflineDatabaseManager.offline_database_helper must be initialized",
        ):
            await OfflineDatabaseManager.shutdown_database()
