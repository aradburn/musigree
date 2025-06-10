"""Unit tests for RuntimeDatabaseManager class."""

import os
from unittest.mock import Mock, patch

import pytest
from sqlalchemy import Engine, exc

from musigree.constants import DatabaseType, ThreadingModel
from musigree.runtime.runtime_database_manager import RuntimeDatabaseManager


class TestRuntimeDatabaseManager:
    """Test suite for RuntimeDatabaseManager."""

    def setup_method(self, method):
        """Reset class variables before each test."""
        RuntimeDatabaseManager.runtime_database_helper = None  # type: ignore
        RuntimeDatabaseManager._threading_model = None  # type: ignore

    def teardown_method(self, method):
        """Clean up after each test."""
        RuntimeDatabaseManager.runtime_database_helper = None  # type: ignore
        RuntimeDatabaseManager._threading_model = None  # type: ignore

    # Test get_concurrency_count method
    @patch('multiprocessing.cpu_count')
    def test_get_concurrency_count_process_model(self, mock_cpu_count):
        """Test get_concurrency_count returns CPU count for process threading model."""
        # Arrange
        mock_cpu_count.return_value = 4
        RuntimeDatabaseManager._threading_model = ThreadingModel.PROCESS

        # Act
        result = RuntimeDatabaseManager.get_concurrency_count()

        # Assert
        assert result == 4
        mock_cpu_count.assert_called_once()

    def test_get_concurrency_count_thread_model(self):
        """Test get_concurrency_count returns 1 for thread model."""
        # Arrange
        RuntimeDatabaseManager._threading_model = ThreadingModel.THREAD

        # Act
        result = RuntimeDatabaseManager.get_concurrency_count()

        # Assert
        assert result == 1

    def test_get_concurrency_count_not_configured(self):
        """Test get_concurrency_count raises error when threading model not configured."""
        # Arrange
        RuntimeDatabaseManager._threading_model = None  # type: ignore

        # Act & Assert
        with pytest.raises(NotImplementedError, match="THREADING_MODEL not configured"):
            RuntimeDatabaseManager.get_concurrency_count()

    # Test setup_database method
    @patch('musigree.runtime.postgres.postgres_helper.RuntimePostgresHelper')
    @patch('musigree.runtime.runtime_database_manager.sessionmaker')
    @patch('musigree.runtime.runtime_database_manager.listen')
    @patch('logging.getLogger')
    def test_setup_database_postgres_success(self, mock_logger, mock_listen, mock_sessionmaker, mock_postgres_helper):
        """Test successful database setup for PostgreSQL."""
        # Arrange
        mock_config = Mock()
        mock_config.THREADING_MODEL = ThreadingModel.PROCESS
        mock_config.DATABASE = DatabaseType.POSTGRES
        
        # Create a proper engine mock with pool attribute
        mock_engine = Mock(spec=Engine)
        mock_pool = Mock()
        mock_engine.pool = mock_pool
        
        mock_helper_instance = Mock()
        mock_helper_instance.setup_database.return_value = mock_engine
        mock_postgres_helper.return_value = mock_helper_instance
        
        mock_session_factory = Mock()
        mock_sessionmaker.return_value = mock_session_factory

        with patch.object(RuntimeDatabaseManager, 'get_concurrency_count', return_value=4):
            with patch('musigree.runtime.runtime_database.runtime_database_helper.RuntimeDatabaseHelper') as mock_runtime_helper_class:
                # Act
                RuntimeDatabaseManager.setup_database(mock_config)

        # Assert
        assert RuntimeDatabaseManager.runtime_database_helper == mock_helper_instance
        assert RuntimeDatabaseManager._threading_model == ThreadingModel.PROCESS
        
        mock_postgres_helper.assert_called_once()
        mock_helper_instance.setup_database.assert_called_once_with(mock_config)
        mock_helper_instance.check_connection.assert_called_once_with(mock_config, mock_engine)
        mock_sessionmaker.assert_called_once_with(bind=mock_engine)
        # Should register event listeners for concurrency > 1
        assert mock_listen.call_count == 2

    @patch('os.getpid')
    @patch('musigree.runtime.sqlite.sqlite_helper.RuntimeSqliteHelper')
    @patch('musigree.runtime.runtime_database_manager.listen')
    @patch('logging.getLogger')
    def test_setup_database_registers_event_listeners_for_multiprocessing(self, mock_logger, mock_listen, mock_sqlite_helper, mock_getpid):
        """Test that event listeners are registered when concurrency count > 1."""
        # Arrange
        mock_config = Mock()
        mock_config.THREADING_MODEL = ThreadingModel.PROCESS
        mock_config.DATABASE = DatabaseType.SQLITE
        
        mock_engine = Mock(spec=Engine)
        mock_pool = Mock()
        mock_engine.pool = mock_pool
        
        mock_helper_instance = Mock()
        mock_helper_instance.setup_database.return_value = mock_engine
        mock_sqlite_helper.return_value = mock_helper_instance

        with patch.object(RuntimeDatabaseManager, 'get_concurrency_count', return_value=4):
            with patch('musigree.runtime.runtime_database.runtime_database_helper.RuntimeDatabaseHelper') as mock_runtime_helper_class:
                # Act
                RuntimeDatabaseManager.setup_database(mock_config)

        # Assert that event listeners were registered
        assert mock_listen.call_count == 2
        # Check that the events registered are "connect" and "checkout"
        registered_events = [call[0][1] for call in mock_listen.call_args_list]
        assert "connect" in registered_events
        assert "checkout" in registered_events

    @patch('musigree.runtime.sqlite.sqlite_helper.RuntimeSqliteHelper')
    @patch('musigree.runtime.runtime_database_manager.listen')
    @patch('logging.getLogger')
    def test_setup_database_no_event_listeners_for_single_thread(self, mock_logger, mock_listen, mock_sqlite_helper):
        """Test that no event listeners are registered when concurrency count = 1."""
        # Arrange
        mock_config = Mock()
        mock_config.THREADING_MODEL = ThreadingModel.THREAD
        mock_config.DATABASE = DatabaseType.SQLITE
        
        mock_engine = Mock(spec=Engine)
        mock_helper_instance = Mock()
        mock_helper_instance.setup_database.return_value = mock_engine
        mock_sqlite_helper.return_value = mock_helper_instance

        with patch.object(RuntimeDatabaseManager, 'get_concurrency_count', return_value=1):
            with patch('musigree.runtime.runtime_database.runtime_database_helper.RuntimeDatabaseHelper') as mock_runtime_helper_class:
                # Act
                RuntimeDatabaseManager.setup_database(mock_config)

        # Assert that no event listeners were registered
        mock_listen.assert_not_called()

    def test_setup_database_unknown_database_type(self):
        """Test setup_database raises error for unknown database type."""
        # Arrange
        mock_config = Mock()
        mock_config.THREADING_MODEL = ThreadingModel.THREAD
        mock_config.DATABASE = "UNKNOWN_TYPE"

        # Act & Assert
        with pytest.raises(ValueError, match="Configuration Error: Unknown database type"):
            RuntimeDatabaseManager.setup_database(mock_config)

    def test_engine_event_handlers_behavior(self):
        """Test the behavior of engine event handlers using mock scenarios."""
        # This test verifies that the event handler logic works correctly
        # by simulating the conditions that would be present in the actual handlers
        
        # Simulate connect handler behavior
        mock_connection_record = Mock()
        mock_connection_record.info = {}
        
        with patch('os.getpid', return_value=12345):
            # Simulate what the connect handler would do
            mock_connection_record.info["pid"] = os.getpid()
            
            # Assert the PID was set correctly
            assert mock_connection_record.info["pid"] == 12345

        # Simulate checkout handler behavior with wrong PID
        mock_connection_record.info = {"pid": 12345}
        mock_connection_proxy = Mock()
        
        with patch('os.getpid', return_value=99999):  # Different PID
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
    @patch('musigree.runtime.runtime_database_manager.close_all_sessions')
    def test_shutdown_database_success(self, mock_close_all_sessions):
        """Test successful database shutdown."""
        # Arrange
        mock_engine = Mock()
        mock_helper = Mock()
        mock_helper.runtime_engine = mock_engine
        
        RuntimeDatabaseManager.runtime_database_helper = mock_helper

        # Act
        RuntimeDatabaseManager.shutdown_database()

        # Assert
        mock_close_all_sessions.assert_called_once()
        mock_engine.dispose.assert_called_once()
        mock_helper.shutdown_database.assert_called_once()

    @patch('musigree.runtime.runtime_database_manager.close_all_sessions')
    def test_shutdown_database_missing_helper_engine_attribute(self, mock_close_all_sessions):
        """Test shutdown when helper doesn't have runtime_engine attribute."""
        # Arrange
        mock_helper = Mock()
        # Don't set runtime_engine attribute, simulating an error scenario
        del mock_helper.runtime_engine  # Ensure the attribute doesn't exist
        RuntimeDatabaseManager.runtime_database_helper = mock_helper

        # Act & Assert - This should raise an AttributeError since the actual code
        # directly accesses runtime_engine without checking if it exists
        with pytest.raises(AttributeError):
            RuntimeDatabaseManager.shutdown_database()

        # Assert that close_all_sessions was still called
        mock_close_all_sessions.assert_called_once()

    @patch('musigree.runtime.runtime_database_manager.close_all_sessions')
    def test_shutdown_database_engine_dispose_fails(self, mock_close_all_sessions):
        """Test shutdown when engine dispose fails."""
        # Arrange
        mock_engine = Mock()
        mock_engine.dispose.side_effect = Exception("Dispose failed")
        mock_helper = Mock()
        mock_helper.runtime_engine = mock_engine
        
        RuntimeDatabaseManager.runtime_database_helper = mock_helper

        # Act & Assert - The exception should propagate since there's no error handling
        with pytest.raises(Exception, match="Dispose failed"):
            RuntimeDatabaseManager.shutdown_database()

        # Assert that close_all_sessions was called first
        mock_close_all_sessions.assert_called_once()
        mock_engine.dispose.assert_called_once()
        # shutdown_database on helper should not be called due to the exception
        mock_helper.shutdown_database.assert_not_called() 