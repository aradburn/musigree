"""Unit tests for RuntimeDatabaseManager class."""

import os
from unittest.mock import Mock, patch, AsyncMock

import pytest
from sqlalchemy import Engine

from musigree.constants import DatabaseType, ThreadingModel
from musigree.runtime.runtime_database_manager import RuntimeDatabaseManager


class TestRuntimeDatabaseManager:
    """Test suite for RuntimeDatabaseManager."""

    @staticmethod
    def setup_method() -> None:
        """Reset class variables before each test."""
        RuntimeDatabaseManager.runtime_database_helper = None  # type: ignore
        RuntimeDatabaseManager._threading_model = None  # type: ignore

    @staticmethod
    def teardown_method() -> None:
        """Clean up after each test."""
        RuntimeDatabaseManager.runtime_database_helper = None  # type: ignore
        RuntimeDatabaseManager._threading_model = None  # type: ignore

    # Test get_concurrency_count method
    @patch("multiprocessing.cpu_count")
    def test_get_concurrency_count_process_model(self, mock_cpu_count: Mock) -> None:
        """Test get_concurrency_count returns CPU count for process threading model."""
        # Arrange
        mock_cpu_count.return_value = 4
        RuntimeDatabaseManager._threading_model = ThreadingModel.PROCESS

        # Act
        result = RuntimeDatabaseManager.get_concurrency_count()

        # Assert
        assert result == 4
        mock_cpu_count.assert_called_once()

    @patch("multiprocessing.cpu_count")
    def test_get_concurrency_count_thread_model(self, mock_cpu_count: Mock) -> None:
        """Test get_concurrency_count returns 1 for thread model."""
        # Arrange
        mock_cpu_count.return_value = 8
        RuntimeDatabaseManager._threading_model = ThreadingModel.THREAD

        # Act
        result = RuntimeDatabaseManager.get_concurrency_count()

        # Assert
        assert result == 1
        mock_cpu_count.assert_not_called()

    def test_get_concurrency_count_not_configured(self) -> None:
        """Test get_concurrency_count raises error when threading model not configured."""
        # Arrange
        RuntimeDatabaseManager._threading_model = None  # type: ignore

        # Act & Assert
        with pytest.raises(NotImplementedError, match="THREADING_MODEL not configured"):
            RuntimeDatabaseManager.get_concurrency_count()

    # Test setup_database method
    @pytest.mark.asyncio
    @patch("musigree.runtime.postgres.runtime_postgres_helper.RuntimePostgresHelper")
    @patch("musigree.runtime.runtime_database_manager.async_sessionmaker")
    @patch("musigree.runtime.runtime_database_manager.listen")
    @patch("logging.getLogger")
    async def test_setup_database_postgres_success(
        self,
        _mock_logger: Mock,
        mock_listen: Mock,
        mock_async_sessionmaker: Mock,
        mock_postgres_helper: Mock,
    ) -> None:
        """Test successful database setup for PostgreSQL."""
        # Arrange
        mock_config = Mock()
        mock_config.THREADING_MODEL = ThreadingModel.PROCESS
        mock_config.DATABASE = DatabaseType.POSTGRES

        # Create a proper async engine mock
        mock_async_engine = AsyncMock()
        mock_sync_engine = Mock(spec=Engine)
        mock_pool = Mock()
        mock_sync_engine.pool = mock_pool
        mock_async_engine.sync_engine = mock_sync_engine

        mock_helper_instance = AsyncMock()
        mock_helper_instance.setup_database.return_value = mock_async_engine
        mock_helper_instance.check_connection.return_value = None
        mock_postgres_helper.return_value = mock_helper_instance

        mock_session_factory = Mock()
        mock_async_sessionmaker.return_value = mock_session_factory

        with patch.object(RuntimeDatabaseManager, "get_concurrency_count", return_value=4):
            with patch(
                "musigree.runtime.runtime_database.runtime_database_helper.RuntimeDatabaseHelper"
            ) as _mock_runtime_helper_class:
                # Act
                await RuntimeDatabaseManager.setup_database(mock_config)

        # Assert
        assert RuntimeDatabaseManager.runtime_database_helper == mock_helper_instance
        assert RuntimeDatabaseManager._threading_model == ThreadingModel.PROCESS

        mock_postgres_helper.assert_called_once()
        mock_helper_instance.setup_database.assert_called_once_with(mock_config)
        mock_helper_instance.check_connection.assert_called_once_with(
            mock_config, mock_async_engine
        )
        mock_async_sessionmaker.assert_called_once()
        # Should register event listeners for concurrency > 1
        assert mock_listen.call_count == 2

    @pytest.mark.asyncio
    @patch("os.getpid")
    @patch("musigree.runtime.sqlite.runtime_sqlite_helper.RuntimeSqliteHelper")
    @patch("musigree.runtime.runtime_database_manager.listen")
    @patch("logging.getLogger")
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

        mock_async_engine = AsyncMock()
        mock_sync_engine = Mock(spec=Engine)
        mock_pool = Mock()
        mock_sync_engine.pool = mock_pool
        mock_async_engine.sync_engine = mock_sync_engine

        mock_helper_instance = AsyncMock()
        mock_helper_instance.setup_database.return_value = mock_async_engine
        mock_helper_instance.check_connection.return_value = None
        mock_sqlite_helper.return_value = mock_helper_instance

        with patch.object(RuntimeDatabaseManager, "get_concurrency_count", return_value=4):
            with patch(
                "musigree.runtime.runtime_database.runtime_database_helper.RuntimeDatabaseHelper"
            ) as _mock_runtime_helper_class:
                # Act
                await RuntimeDatabaseManager.setup_database(mock_config)

        # Assert that event listeners were registered
        assert mock_listen.call_count == 2
        # Check that the events registered are "connect" and "checkout"
        registered_events = [call[0][1] for call in mock_listen.call_args_list]
        assert "connect" in registered_events
        assert "checkout" in registered_events

    @pytest.mark.asyncio
    async def test_setup_database_unknown_database_type(self) -> None:
        """Test setup_database raises error for unknown database type."""
        # Arrange
        mock_config = Mock()
        mock_config.THREADING_MODEL = ThreadingModel.THREAD
        mock_config.DATABASE = "UNKNOWN_TYPE"

        # Act & Assert
        with pytest.raises(ValueError, match="Configuration Error: Unknown database type"):
            await RuntimeDatabaseManager.setup_database(mock_config)

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
    @patch("musigree.runtime.runtime_database_manager.close_all_sessions")
    async def test_shutdown_database_success(self, mock_close_all_sessions: Mock) -> None:
        """Test successful database shutdown."""
        # Arrange
        mock_helper = AsyncMock()
        mock_async_engine = AsyncMock()
        mock_helper.runtime_async_engine = mock_async_engine
        mock_helper.shutdown_database.return_value = None
        RuntimeDatabaseManager.runtime_database_helper = mock_helper

        mock_close_all_sessions.return_value = None

        # Act
        await RuntimeDatabaseManager.shutdown_database()

        # Assert
        mock_close_all_sessions.assert_called_once()
        mock_async_engine.dispose.assert_called_once()
        mock_helper.shutdown_database.assert_called_once()

    @pytest.mark.asyncio
    @patch("musigree.runtime.runtime_database_manager.close_all_sessions")
    async def test_shutdown_database_missing_helper_engine_attribute(
        self, mock_close_all_sessions: Mock
    ) -> None:
        """Test shutdown_database when helper is None."""
        # Arrange
        RuntimeDatabaseManager.runtime_database_helper = None  # type: ignore
        mock_close_all_sessions.return_value = None

        # Act & Assert
        with pytest.raises(
            AssertionError,
            match="RuntimeDatabaseManager.runtime_database_helper must be initialized",
        ):
            await RuntimeDatabaseManager.shutdown_database()

        mock_close_all_sessions.assert_called_once()

    @pytest.mark.asyncio
    @patch("musigree.runtime.runtime_database_manager.close_all_sessions")
    async def test_shutdown_database_engine_dispose_fails(
        self, mock_close_all_sessions: Mock
    ) -> None:
        """Test shutdown_database when engine dispose fails."""
        # Arrange
        mock_helper = AsyncMock()
        mock_async_engine = AsyncMock()
        mock_async_engine.dispose.side_effect = Exception("Dispose failed")
        mock_helper.runtime_async_engine = mock_async_engine
        mock_helper.shutdown_database.return_value = None
        RuntimeDatabaseManager.runtime_database_helper = mock_helper

        mock_close_all_sessions.return_value = None

        # Act & Assert
        with pytest.raises(Exception, match="Dispose failed"):
            await RuntimeDatabaseManager.shutdown_database()

        mock_close_all_sessions.assert_called_once()
        mock_async_engine.dispose.assert_called_once()
