"""
Unit tests for musigree.loader.loader module.
"""
import pytest
from unittest.mock import Mock, patch, call
from pathlib import Path
from functools import partial

from musigree.config import SqliteTestConfiguration
from musigree.loader.loader import (
    load_offline_tables,
    load_offline_table_stage,
    get_load_offline_table_stages,
    load_runtime_tables,
    load_offline_test_tables,
    load_runtime_test_tables,
    loader_main
)


class TestLoaderFunctions:
    """Test cases for loader functions."""

    @pytest.fixture
    def test_config(self):
        """Provide test configuration."""
        return SqliteTestConfiguration()

    @pytest.fixture
    def mock_data_directory(self):
        """Provide mock data directory."""
        return Path("/test/data")

    @pytest.fixture
    def mock_date(self):
        """Provide mock date."""
        return "2024-11-01"

    @patch('musigree.loader.loader.get_load_offline_table_stages')
    def test_load_offline_tables_success(self, mock_get_stages, mock_data_directory, mock_date):
        """Test successful loading of offline tables."""
        # Arrange
        mock_stage1 = Mock()
        mock_stage2 = Mock()
        mock_get_stages.return_value = [mock_stage1, mock_stage2]
        
        # Act
        load_offline_tables(mock_data_directory, mock_date, is_bulk_inserts=True)
        
        # Assert
        mock_get_stages.assert_called_once_with(mock_data_directory, mock_date, True)
        mock_stage1.assert_called_once()
        mock_stage2.assert_called_once()

    @patch('musigree.loader.loader.get_load_offline_table_stages')
    def test_load_offline_table_stage_success(self, mock_get_stages, mock_data_directory, mock_date):
        """Test successful loading of a specific offline table stage."""
        # Arrange
        mock_stage1 = Mock()
        mock_stage2 = Mock()
        mock_stage3 = Mock()
        mock_get_stages.return_value = [mock_stage1, mock_stage2, mock_stage3]
        
        # Act
        load_offline_table_stage(mock_data_directory, mock_date, is_bulk_inserts=False, stage=1)
        
        # Assert
        mock_get_stages.assert_called_once_with(mock_data_directory, mock_date, False)
        mock_stage1.assert_not_called()
        mock_stage2.assert_called_once()  # Stage 1 (0-indexed)
        mock_stage3.assert_not_called()

    @patch('musigree.loader.loader.OfflineDatabaseManager')
    @patch('musigree.offline.loader.loader_entity.LoaderEntity')
    @patch('musigree.offline.loader.loader_release.LoaderRelease')
    @patch('musigree.offline.loader.loader_relation.LoaderRelation')
    @patch('musigree.loader.loader.RoleDataAccess')
    def test_get_load_offline_table_stages_success(
        self,
        _mock_role_data_access,
        mock_loader_relation,
        mock_loader_release,
        mock_loader_entity,
        mock_db_manager,
        mock_data_directory,
        mock_date
    ):
        """Test successful creation of load offline table stages."""
        # Arrange
        mock_helper = Mock()
        mock_helper.is_vacuum_full.return_value = False
        mock_helper.is_vacuum_analyze.return_value = True
        mock_helper.offline_engine = Mock()
        mock_db_manager.offline_database_helper = mock_helper
        
        mock_entity_instance = Mock()
        mock_release_instance = Mock()
        mock_relation_instance = Mock()
        mock_loader_entity.return_value = mock_entity_instance
        mock_loader_release.return_value = mock_release_instance
        mock_loader_relation.return_value = mock_relation_instance
        
        # Act
        result = get_load_offline_table_stages(mock_data_directory, mock_date, is_bulk_inserts=True)
        
        # Assert
        assert isinstance(result, list)
        assert len(result) > 0
        assert all(isinstance(stage, partial) for stage in result)
        
        # Verify that database helper methods were called
        mock_helper.is_vacuum_full.assert_called_once()
        mock_helper.is_vacuum_analyze.assert_called_once()

    @patch('musigree.loader.loader.OfflineDatabaseManager')
    def test_get_load_offline_table_stages_assertion_error_no_helper(self, mock_db_manager, mock_data_directory, mock_date):
        """Test get_load_offline_table_stages raises assertion error when helper is None."""
        # Arrange
        mock_db_manager.offline_database_helper = None
        
        # Act & Assert
        with pytest.raises(AssertionError) as excinfo:
            get_load_offline_table_stages(mock_data_directory, mock_date, is_bulk_inserts=True)
        
        assert "OfflineDatabaseManager.offline_database_helper must be initialized" in str(excinfo.value)

    @patch('musigree.loader.loader.OfflineDatabaseManager')
    def test_get_load_offline_table_stages_assertion_error_no_engine(self, mock_db_manager, mock_data_directory, mock_date):
        """Test get_load_offline_table_stages raises assertion error when engine is None."""
        # Arrange
        mock_helper = Mock()
        mock_helper.offline_engine = None
        mock_db_manager.offline_database_helper = mock_helper
        
        # Act & Assert
        with pytest.raises(AssertionError) as excinfo:
            get_load_offline_table_stages(mock_data_directory, mock_date, is_bulk_inserts=True)
        
        assert "OfflineDatabaseManager.offline_database_helper.offline_engine must be initialized" in str(excinfo.value)

    @patch('musigree.loader.loader.RuntimeDatabaseHelper')
    @patch('musigree.loader.loader.TextSearchIndex')
    @patch('musigree.loader.loader.RuntimeRoleDataAccess')
    def test_load_runtime_tables_success(
        self,
        mock_runtime_role_data_access,
        mock_text_search_index,
        mock_runtime_db_helper,
        mock_data_directory
    ):
        """Test successful loading of runtime tables."""
        # Arrange
        mock_text_search_index.load_text_search_index_from_file.return_value = Mock()
        
        # Act
        load_runtime_tables(mock_data_directory)
        
        # Assert
        mock_runtime_role_data_access.load_all_roles.assert_called_once()
        mock_text_search_index.load_text_search_index_from_file.assert_called_once()
        # Verify that text_search_index was set
        assert hasattr(mock_runtime_db_helper, 'text_search_index')

    @patch('musigree.loader.loader.LoaderRole')
    @patch('musigree.loader.loader.load_offline_tables')
    @patch('musigree.loader.loader.OfflineDatabaseManager')
    def test_load_offline_test_tables_success(
        self,
        mock_db_manager,
        mock_load_offline_tables,
        mock_loader_role,
        mock_data_directory,
        mock_date
    ):
        """Test successful loading of offline test tables."""
        # Arrange
        mock_db_manager.offline_database_helper = Mock()
        
        # Act
        load_offline_test_tables(mock_data_directory, mock_date, is_bulk_inserts=False)
        
        # Assert
        mock_loader_role.load_roles_into_database.assert_called_once()
        mock_load_offline_tables.assert_called_once_with(
            mock_data_directory, mock_date, is_bulk_inserts=False
        )

    @patch('musigree.loader.loader.OfflineDatabaseManager')
    def test_load_offline_test_tables_assertion_error(self, mock_db_manager, mock_data_directory, mock_date):
        """Test load_offline_test_tables raises assertion error when helper is None."""
        # Arrange
        mock_db_manager.offline_database_helper = None
        
        # Act & Assert
        with pytest.raises(AssertionError) as excinfo:
            load_offline_test_tables(mock_data_directory, mock_date, is_bulk_inserts=False)
        
        assert "OfflineDatabaseManager.offline_database_helper must be initialized" in str(excinfo.value)

    @patch('musigree.loader.loader.load_runtime_tables')
    @patch('musigree.loader.loader.TransferManager')
    def test_load_runtime_test_tables_success(
        self,
        mock_transfer_manager,
        mock_load_runtime_tables,
        mock_data_directory
    ):
        """Test successful loading of runtime test tables."""
        # Act
        load_runtime_test_tables(mock_data_directory)
        
        # Assert
        mock_transfer_manager.transfer_all.assert_called_once_with(mock_data_directory)
        mock_load_runtime_tables.assert_called_once_with(mock_data_directory)

    @patch('musigree.loader.loader.luigi')
    @patch('musigree.loader.loader.atexit')
    @patch('musigree.loader.loader.RuntimeDatabaseManager')
    @patch('musigree.loader.loader.OfflineDatabaseManager')
    @patch('musigree.loader.loader.CacheManager')
    @patch('musigree.loader.loader.setup_logging')
    @patch('musigree.loader.loader.sys')
    def test_loader_main_success(
        self,
        _mock_sys,
        mock_setup_logging,
        mock_cache_manager,
        mock_offline_db_manager,
        mock_runtime_db_manager,
        mock_atexit,
        mock_luigi
    ):
        """Test successful execution of loader_main."""
        # Arrange
        mock_cache = Mock()
        mock_cache_manager.get_cache.return_value = mock_cache
        
        mock_build_result = Mock()
        mock_build_result.summary_text = "Build completed successfully"
        mock_luigi.build.return_value = mock_build_result
        
        # Act
        loader_main()
        
        # Assert
        mock_setup_logging.assert_called_once()
        mock_cache_manager.setup_cache.assert_called_once()
        mock_cache_manager.get_cache.assert_called_once()
        mock_cache_manager.clear.assert_called_once()
        mock_offline_db_manager.setup_database.assert_called_once()
        mock_runtime_db_manager.setup_database.assert_called_once()
        
        # Verify atexit registrations
        expected_atexit_calls = [
            call(mock_cache_manager.shutdown_cache),
            call(mock_offline_db_manager.shutdown_database),
            call(mock_runtime_db_manager.shutdown_database)
        ]
        mock_atexit.register.assert_has_calls(expected_atexit_calls)
        
        # Verify Luigi build was called
        mock_luigi.build.assert_called_once()

    @patch('musigree.loader.loader.luigi')
    @patch('musigree.loader.loader.atexit')
    @patch('musigree.loader.loader.RuntimeDatabaseManager')
    @patch('musigree.loader.loader.OfflineDatabaseManager')
    @patch('musigree.loader.loader.CacheManager')
    @patch('musigree.loader.loader.setup_logging')
    @patch('musigree.loader.loader.sys')
    def test_loader_main_cache_error(
        self,
        mock_sys,
        mock_setup_logging,
        mock_cache_manager,
        mock_offline_db_manager,
        mock_runtime_db_manager,
        _mock_atexit,
        _mock_luigi
    ):
        """Test loader_main when cache is not set."""
        # Arrange
        mock_cache_manager.get_cache.return_value = None
        mock_sys.exit.side_effect = SystemExit(1)  # Make sys.exit actually exit
        
        # Act & Assert
        with pytest.raises(SystemExit):
            loader_main()
        
        # Verify setup calls before exit
        mock_setup_logging.assert_called_once()
        mock_cache_manager.setup_cache.assert_called_once()
        mock_cache_manager.get_cache.assert_called_once()
        mock_sys.exit.assert_called_once()
        
        # Database setup should not be called due to early exit
        mock_offline_db_manager.setup_database.assert_not_called()
        mock_runtime_db_manager.setup_database.assert_not_called()


class TestLoaderIntegration:
    """Integration tests for loader functions."""

    @pytest.fixture
    def test_config(self):
        """Provide test configuration."""
        return SqliteTestConfiguration()

    @patch('musigree.loader.loader.OfflineDatabaseManager')
    @patch('musigree.offline.loader.loader_entity.LoaderEntity')
    @patch('musigree.offline.loader.loader_release.LoaderRelease')
    @patch('musigree.offline.loader.loader_relation.LoaderRelation')
    @patch('musigree.loader.loader.RoleDataAccess')
    def test_load_offline_tables_integration(
        self,
        mock_role_data_access,
        mock_loader_relation,
        mock_loader_release,
        mock_loader_entity,
        mock_db_manager
    ):
        """Test integration of load_offline_tables with actual stage execution."""
        # Arrange
        mock_helper = Mock()
        mock_helper.is_vacuum_full.return_value = False
        mock_helper.is_vacuum_analyze.return_value = True
        mock_helper.offline_engine = Mock()
        mock_db_manager.offline_database_helper = mock_helper
        
        mock_entity_instance = Mock()
        mock_release_instance = Mock()
        mock_relation_instance = Mock()
        mock_loader_entity.return_value = mock_entity_instance
        mock_loader_release.return_value = mock_release_instance
        mock_loader_relation.return_value = mock_relation_instance
        
        data_directory = Path("/test/data")
        date = "2024-11-01"
        
        # Act
        load_offline_tables(data_directory, date, is_bulk_inserts=True)
        
        # Assert
        # Verify that role loading was called
        mock_role_data_access.load_all_roles.assert_called()
        
        # Verify that entity loader methods were called
        mock_entity_instance.loader_entity_pass_one.assert_called()
        mock_entity_instance.loader_entity_pass_two.assert_called()
        mock_entity_instance.loader_entity_pass_three.assert_called()
        mock_entity_instance.loader_create_text_search_index.assert_called()
        
        # Verify that release loader methods were called
        mock_release_instance.loader_release_pass_one.assert_called()
        mock_release_instance.loader_release_pass_two.assert_called()

        # Verify that relation loader methods were called
        mock_relation_instance.loader_relation_pass_one.assert_called()

    def test_load_offline_table_stage_bounds_checking(self):
        """Test bounds checking for stage parameter."""
        # Arrange
        data_directory = Path("/test/data")
        date = "2024-11-01"
        
        with patch('musigree.loader.loader.get_load_offline_table_stages') as mock_get_stages:
            mock_get_stages.return_value = [Mock(), Mock()]  # Only 2 stages
            
            # Act & Assert - Should not raise error for valid stage index
            load_offline_table_stage(data_directory, date, is_bulk_inserts=True, stage=0)
            load_offline_table_stage(data_directory, date, is_bulk_inserts=True, stage=1)
            
            # Should raise IndexError for invalid stage index
            with pytest.raises(IndexError):
                load_offline_table_stage(data_directory, date, is_bulk_inserts=True, stage=2)


class TestLoaderEdgeCases:
    """Test edge cases for loader functions."""

    def test_empty_data_directory(self):
        """Test handling of empty data directory."""
        empty_directory = Path("/empty")
        date = "2024-11-01"
        
        with patch('musigree.loader.loader.OfflineDatabaseManager') as mock_db_manager:
            mock_helper = Mock()
            mock_helper.is_vacuum_full.return_value = False
            mock_helper.is_vacuum_analyze.return_value = False
            mock_helper.offline_engine = Mock()
            mock_db_manager.offline_database_helper = mock_helper
            
            # Should not raise error even with empty directory
            stages = get_load_offline_table_stages(empty_directory, date, is_bulk_inserts=False)
            assert isinstance(stages, list)
            assert len(stages) > 0

    @patch('musigree.loader.loader.RuntimeRoleDataAccess')
    def test_load_runtime_tables_missing_text_search(self, _mock_runtime_role_data_access):
        """Test load_runtime_tables when text search file is missing."""
        # Arrange
        missing_directory = Path("/missing")
        
        with patch('musigree.loader.loader.TextSearchIndex') as mock_text_search_index:
            # Simulate file not found
            mock_text_search_index.load_text_search_index_from_file.side_effect = FileNotFoundError()
            
            # Act & Assert - Should raise FileNotFoundError
            with pytest.raises(FileNotFoundError):
                load_runtime_tables(missing_directory) 