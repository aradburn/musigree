"""
Unit tests for musigree.loader.create_search_index module.
"""
from pathlib import Path
from unittest.mock import Mock, patch, call

import pytest

from musigree.config import Configuration, SqliteTestConfiguration
from musigree.loader.create_search_index import create_search_index


class TestCreateSearchIndex:
    """Test cases for create_search_index function."""

    @patch('musigree.loader.create_search_index.LoaderEntity')
    @patch('musigree.loader.create_search_index.OfflineDatabaseManager')
    @patch('musigree.loader.create_search_index.CacheManager')
    @patch('musigree.loader.create_search_index.setup_logging')
    @patch('musigree.loader.create_search_index.atexit')
    def test_create_search_index_success(
        self,
        mock_atexit,
        mock_setup_logging,
        mock_cache_manager,
        mock_offline_db_manager,
        mock_loader_entity_class
    ):
        """Test successful execution of create_search_index."""
        # Arrange
        mock_config = Mock(spec=Configuration)
        mock_config.DATA_DIR = Path("/test/data")
        
        mock_cache = Mock()
        mock_cache_manager.get_cache.return_value = mock_cache
        
        mock_loader_entity = Mock()
        mock_loader_entity_class.return_value = mock_loader_entity
        
        expected_text_search_path = mock_config.DATA_DIR / "text_search" / "text_search.data"

        # Act
        create_search_index(mock_config)

        # Assert
        mock_setup_logging.assert_called_once()
        mock_cache_manager.setup_cache.assert_called_once_with(mock_config)
        mock_cache_manager.get_cache.assert_called_once()
        mock_cache_manager.clear.assert_called_once()
        mock_offline_db_manager.setup_database.assert_called_once_with(mock_config)
        mock_loader_entity.loader_create_text_search_index.assert_called_once_with(expected_text_search_path)
        
        # Verify atexit registrations
        expected_calls = [
            call(mock_cache_manager.shutdown_cache),
            call(mock_offline_db_manager.shutdown_database)
        ]
        mock_atexit.register.assert_has_calls(expected_calls)

    @patch('musigree.loader.create_search_index.LoaderEntity')
    @patch('musigree.loader.create_search_index.OfflineDatabaseManager')
    @patch('musigree.loader.create_search_index.CacheManager')
    @patch('musigree.loader.create_search_index.setup_logging')
    @patch('musigree.loader.create_search_index.atexit')
    @patch('musigree.loader.create_search_index.sys')
    def test_create_search_index_cache_not_set(
        self,
        mock_sys,
        _mock_atexit,
        mock_setup_logging,
        mock_cache_manager,
        _mock_offline_db_manager,
        _mock_loader_entity_class
    ):
        """Test behavior when cache is not set (None)."""
        # Arrange
        mock_config = Mock(spec=Configuration)
        mock_config.DATA_DIR = Path("/test/data")
        
        mock_cache_manager.get_cache.return_value = None

        # Act
        create_search_index(mock_config)

        # Assert
        mock_setup_logging.assert_called_once()
        mock_cache_manager.setup_cache.assert_called_once_with(mock_config)
        mock_cache_manager.get_cache.assert_called_once()
        mock_cache_manager.clear.assert_not_called()
        mock_sys.exit.assert_called_once()

    @patch('musigree.loader.create_search_index.LoaderEntity')
    @patch('musigree.loader.create_search_index.OfflineDatabaseManager')
    @patch('musigree.loader.create_search_index.CacheManager')
    @patch('musigree.loader.create_search_index.setup_logging')
    @patch('musigree.loader.create_search_index.atexit')
    def test_create_search_index_text_search_path_construction(
        self,
        _mock_atexit,
        _mock_setup_logging,
        mock_cache_manager,
        _mock_offline_db_manager,
        mock_loader_entity_class
    ):
        """Test that text search path is constructed correctly."""
        # Arrange
        mock_config = Mock(spec=Configuration)
        test_data_dir = Path("/custom/data/dir")
        mock_config.DATA_DIR = test_data_dir
        
        mock_cache = Mock()
        mock_cache_manager.get_cache.return_value = mock_cache
        
        mock_loader_entity = Mock()
        mock_loader_entity_class.return_value = mock_loader_entity

        # Act
        create_search_index(mock_config)

        # Assert
        expected_path = test_data_dir / "text_search" / "text_search.data"
        mock_loader_entity.loader_create_text_search_index.assert_called_once_with(expected_path)

    @patch('musigree.loader.create_search_index.LoaderEntity')
    @patch('musigree.loader.create_search_index.OfflineDatabaseManager')
    @patch('musigree.loader.create_search_index.CacheManager')
    @patch('musigree.loader.create_search_index.setup_logging')
    @patch('musigree.loader.create_search_index.atexit')
    def test_create_search_index_exception_handling(
        self,
        _mock_atexit,
        _mock_setup_logging,
        mock_cache_manager,
        _mock_offline_db_manager,
        mock_loader_entity_class
    ):
        """Test exception handling in create_search_index."""
        # Arrange
        mock_config = Mock(spec=Configuration)
        mock_config.DATA_DIR = Path("/test/data")
        
        mock_cache = Mock()
        mock_cache_manager.get_cache.return_value = mock_cache
        
        mock_loader_entity = Mock()
        mock_loader_entity_class.return_value = mock_loader_entity
        mock_loader_entity.loader_create_text_search_index.side_effect = RuntimeError("Index creation failed")

        # Act & Assert
        with pytest.raises(RuntimeError, match="Index creation failed"):
            create_search_index(mock_config)

    @patch('musigree.loader.create_search_index.LoaderEntity')
    @patch('musigree.loader.create_search_index.OfflineDatabaseManager')
    @patch('musigree.loader.create_search_index.CacheManager')
    @patch('musigree.loader.create_search_index.setup_logging')
    @patch('musigree.loader.create_search_index.atexit')
    def test_create_search_index_cache_manager_exception(
        self,
        _mock_atexit,
        _mock_setup_logging,
        mock_cache_manager,
        _mock_offline_db_manager,
        _mock_loader_entity_class
    ):
        """Test exception handling when CacheManager setup fails."""
        # Arrange
        mock_config = Mock(spec=Configuration)
        mock_cache_manager.setup_cache.side_effect = RuntimeError("Cache setup failed")

        # Act & Assert
        with pytest.raises(RuntimeError, match="Cache setup failed"):
            create_search_index(mock_config)

    @patch('musigree.loader.create_search_index.LoaderEntity')
    @patch('musigree.loader.create_search_index.OfflineDatabaseManager')
    @patch('musigree.loader.create_search_index.CacheManager')
    @patch('musigree.loader.create_search_index.setup_logging')
    @patch('musigree.loader.create_search_index.atexit')
    def test_create_search_index_database_manager_exception(
        self,
        _mock_atexit,
        _mock_setup_logging,
        mock_cache_manager,
        mock_offline_db_manager,
        _mock_loader_entity_class
    ):
        """Test exception handling when OfflineDatabaseManager setup fails."""
        # Arrange
        mock_config = Mock(spec=Configuration)
        mock_config.DATA_DIR = Path("/test/data")
        
        mock_cache = Mock()
        mock_cache_manager.get_cache.return_value = mock_cache
        
        mock_offline_db_manager.setup_database.side_effect = RuntimeError("Database setup failed")

        # Act & Assert
        with pytest.raises(RuntimeError, match="Database setup failed"):
            create_search_index(mock_config)


class TestIntegration:
    """Integration tests for create_search_index."""

    @patch('musigree.loader.create_search_index.LoaderEntity')
    @patch('musigree.loader.create_search_index.OfflineDatabaseManager')
    @patch('musigree.loader.create_search_index.CacheManager')
    @patch('musigree.loader.create_search_index.setup_logging')
    @patch('musigree.loader.create_search_index.atexit')
    def test_integration_with_real_config(
        self,
        _mock_atexit,
        mock_setup_logging,
        mock_cache_manager,
        mock_offline_db_manager,
        mock_loader_entity_class
    ):
        """Test integration with real SqliteTestConfiguration."""
        # Arrange
        real_config = SqliteTestConfiguration()
        
        mock_cache = Mock()
        mock_cache_manager.get_cache.return_value = mock_cache
        
        mock_loader_entity = Mock()
        mock_loader_entity_class.return_value = mock_loader_entity

        # Act
        create_search_index(real_config)

        # Assert
        mock_setup_logging.assert_called_once()
        mock_cache_manager.setup_cache.assert_called_once_with(real_config)
        mock_offline_db_manager.setup_database.assert_called_once_with(real_config)
        
        # Verify the path is constructed with real config
        args, _ = mock_loader_entity.loader_create_text_search_index.call_args
        actual_path = args[0]
        expected_path = real_config.DATA_DIR / "text_search" / "text_search.data"
        assert actual_path == expected_path 