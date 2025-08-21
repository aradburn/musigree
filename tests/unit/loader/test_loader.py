"""
Unit tests for musigree.loader.loader module.
"""

from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

import pytest

from musigree.config import SqliteTestConfiguration, Configuration
from musigree.loader.loader import (
    load_offline_tables,
    load_offline_table_stage,
    get_load_offline_table_stages,
    load_runtime_tables,
    loader_main,
)


class TestLoaderFunctions:
    """Test cases for loader functions."""

    @pytest.fixture
    def test_config(self) -> Configuration:
        """Provide test configuration."""
        return SqliteTestConfiguration()

    @pytest.fixture
    def mock_data_directory(self) -> Path:
        """Provide mock data directory."""
        return Path("/test/data")

    @pytest.fixture
    def mock_date(self) -> str:
        """Provide mock date."""
        return "2024-11-01"

    @patch("musigree.loader.loader.get_load_offline_table_stages")
    @pytest.mark.asyncio
    async def test_load_offline_tables_success(
        self, mock_get_stages: Mock, mock_data_directory: Mock, mock_date: Mock
    ) -> None:
        """Test successful loading of offline tables."""
        # Arrange
        mock_stage1 = AsyncMock()
        mock_stage2 = AsyncMock()

        mock_get_stages.return_value = [mock_stage1(), mock_stage2()]

        # Act
        await load_offline_tables(mock_data_directory, mock_date, is_bulk_inserts=True)

        # Assert
        mock_get_stages.assert_called_once_with(mock_data_directory, mock_date, True)

    @patch("musigree.loader.loader.get_load_offline_table_stages")
    @pytest.mark.asyncio
    async def test_load_offline_table_stage_success(
        self, mock_get_stages: Mock, mock_data_directory: Mock, mock_date: Mock
    ) -> None:
        """Test successful loading of a specific offline table stage."""
        # Arrange
        mock_stage1 = AsyncMock()
        mock_stage2 = AsyncMock()
        mock_stage3 = AsyncMock()

        mock_get_stages.return_value = [mock_stage1(), mock_stage2(), mock_stage3()]

        # Act
        await load_offline_table_stage(
            mock_data_directory, mock_date, is_bulk_inserts=False, stage=1
        )

        # Assert
        mock_get_stages.assert_called_once_with(mock_data_directory, mock_date, False)
        # Note: We can't easily assert which specific stage was called due to the way coroutines work
        # but we can verify the function was called with correct parameters

    @patch("musigree.loader.loader.OfflineDatabaseManager")
    @patch("musigree.offline.loader.loader_entity.LoaderEntity")
    @patch("musigree.offline.loader.loader_release.LoaderRelease")
    @patch("musigree.offline.loader.loader_relation.LoaderRelation")
    @patch("musigree.loader.loader.RoleDataAccess")
    def test_get_load_offline_table_stages_success(
        self,
        _mock_role_data_access: Mock,
        mock_loader_relation: Mock,
        mock_loader_release: Mock,
        mock_loader_entity: Mock,
        mock_db_manager: Mock,
        mock_data_directory: Mock,
        mock_date: Mock,
    ) -> None:
        """Test successful creation of load offline table stages."""
        # Arrange
        mock_helper = Mock()
        mock_helper.is_vacuum_full.return_value = False
        mock_helper.is_vacuum_analyze.return_value = True
        mock_helper.offline_async_engine = (
            Mock()
        )  # Changed from offline_engine to offline_async_engine
        mock_db_manager.offline_database_helper = mock_helper

        # Mock vacuum method to return an AsyncMock coroutine
        mock_helper.vacuum.return_value = AsyncMock()()

        # Mock the static/class methods to return AsyncMock coroutines
        _mock_role_data_access.load_all_roles_into_cache.return_value = AsyncMock()()
        mock_loader_entity.loader_entity_pass_one.return_value = AsyncMock()()
        mock_loader_entity.loader_entity_pass_two.return_value = AsyncMock()()
        mock_loader_entity.loader_entity_pass_three.return_value = AsyncMock()()
        mock_loader_entity.loader_create_text_search_index.return_value = AsyncMock()()
        mock_loader_release.loader_release_pass_one.return_value = AsyncMock()()
        mock_loader_release.loader_release_pass_two.return_value = AsyncMock()()
        mock_loader_relation.loader_relation_pass_one.return_value = AsyncMock()()

        # Act
        result = get_load_offline_table_stages(
            mock_data_directory, mock_date, is_bulk_inserts=True
        )

        # Assert
        assert isinstance(result, list)
        assert len(result) > 0
        # Check that the result contains awaitable objects
        import inspect

        # All stages should be either coroutines or other awaitable objects
        assert all(
            inspect.iscoroutine(stage) or inspect.isawaitable(stage) for stage in result
        )

    @patch("musigree.loader.loader.OfflineDatabaseManager")
    def test_get_load_offline_table_stages_assertion_error_no_helper(
        self,
        mock_db_manager: Mock,
        mock_data_directory: Mock,
        mock_date: Mock,
    ) -> None:
        """Test get_load_offline_table_stages raises assertion error when helper is None."""
        # Arrange
        mock_db_manager.offline_database_helper = None

        # Act & Assert
        with pytest.raises(AssertionError) as excinfo:
            get_load_offline_table_stages(
                mock_data_directory, mock_date, is_bulk_inserts=True
            )

        assert (
            "OfflineDatabaseManager.offline_database_helper must be initialized"
            in str(excinfo.value)
        )

    @patch("musigree.loader.loader.OfflineDatabaseManager")
    @patch("musigree.offline.loader.loader_entity.LoaderEntity")
    @patch("musigree.offline.loader.loader_release.LoaderRelease")
    @patch("musigree.offline.loader.loader_relation.LoaderRelation")
    @patch("musigree.loader.loader.RoleDataAccess")
    @patch("musigree.offline.loader.loader_role.LoaderRole")
    def test_get_load_offline_table_stages_assertion_error_no_engine(
        self,
        mock_loader_role: Mock,
        mock_role_data_access: Mock,
        mock_loader_relation: Mock,
        mock_loader_release: Mock,
        mock_loader_entity: Mock,
        mock_db_manager: Mock,
        mock_data_directory: Mock,
        mock_date: Mock,
    ) -> None:
        """Test get_load_offline_table_stages raises assertion error when engine is None."""
        # Arrange
        mock_helper = Mock()
        mock_helper.offline_async_engine = None
        mock_db_manager.offline_database_helper = mock_helper

        # Mock all the loader methods to avoid creating actual coroutines
        mock_loader_role.load_roles_into_database.return_value = AsyncMock()()
        mock_role_data_access.load_all_roles_into_cache.return_value = AsyncMock()()
        mock_loader_entity.loader_entity_pass_one.return_value = AsyncMock()()
        mock_loader_entity.loader_entity_pass_two.return_value = AsyncMock()()
        mock_loader_entity.loader_entity_pass_three.return_value = AsyncMock()()
        mock_loader_entity.loader_create_text_search_index.return_value = AsyncMock()()
        mock_loader_release.loader_release_pass_one.return_value = AsyncMock()()
        mock_loader_release.loader_release_pass_two.return_value = AsyncMock()()
        mock_loader_relation.loader_relation_pass_one.return_value = AsyncMock()()
        mock_helper.vacuum.return_value = AsyncMock()()

        # Act & Assert
        # The function should raise an assertion error when engine is None
        with pytest.raises(AssertionError) as excinfo:
            get_load_offline_table_stages(
                mock_data_directory, mock_date, is_bulk_inserts=True
            )

        assert "offline_engine must be initialized" in str(excinfo.value)

    @patch("musigree.loader.loader.get_load_runtime_table_stages")
    @pytest.mark.asyncio
    async def test_load_runtime_tables_success(
        self, mock_get_stages: Mock, mock_data_directory: Mock
    ) -> None:
        """Test successful loading of runtime tables."""
        # Arrange
        mock_stage1 = AsyncMock()
        mock_stage2 = AsyncMock()

        mock_get_stages.return_value = [mock_stage1(), mock_stage2()]

        # Act
        await load_runtime_tables(mock_data_directory, "2024-11-01")

        # Assert
        mock_get_stages.assert_called_once_with(mock_data_directory, "2024-11-01")

    @patch("musigree.loader.loader.luigi")
    @patch("musigree.loader.loader.atexit")
    @patch("musigree.loader.loader.RuntimeDatabaseManager")
    @patch("musigree.loader.loader.OfflineDatabaseManager")
    @patch("musigree.loader.loader.CacheManager")
    @patch("musigree.loader.loader.setup_logging")
    @patch("musigree.loader.loader.sys")
    def test_loader_main_success(
        self,
        _mock_sys: Mock,
        mock_setup_logging: Mock,
        mock_cache_manager: Mock,
        mock_offline_db_manager: Mock,
        mock_runtime_db_manager: Mock,
        _mock_atexit: Mock,
        mock_luigi: Mock,
    ) -> None:
        """Test successful execution of loader_main."""
        # Arrange
        mock_cache = Mock()
        mock_cache_manager.get_cache.return_value = mock_cache

        mock_build_result = Mock()
        mock_build_result.summary_text = "Build completed successfully"
        mock_luigi.build.return_value = mock_build_result

        # Mock database setup methods to return AsyncMock
        mock_offline_db_manager.setup_database = AsyncMock()
        mock_runtime_db_manager.setup_database = AsyncMock()

        # Mock runtime database helper
        mock_runtime_helper = Mock()
        mock_runtime_helper.drop_tables = AsyncMock()
        mock_runtime_helper.create_tables = AsyncMock()
        mock_runtime_db_manager.runtime_database_helper = mock_runtime_helper

        # Act
        loader_main()

        # Assert
        mock_setup_logging.assert_called_once()
        mock_cache_manager.setup_cache.assert_called_once()
        mock_cache_manager.get_cache.assert_called_once()
        mock_offline_db_manager.setup_database.assert_called_once()
        mock_runtime_db_manager.setup_database.assert_called_once()
        mock_runtime_helper.drop_tables.assert_called_once()
        mock_runtime_helper.create_tables.assert_called_once()
        mock_luigi.build.assert_called_once()

    @patch("musigree.loader.loader.luigi")
    @patch("musigree.loader.loader.atexit")
    @patch("musigree.loader.loader.RuntimeDatabaseManager")
    @patch("musigree.loader.loader.OfflineDatabaseManager")
    @patch("musigree.loader.loader.CacheManager")
    @patch("musigree.loader.loader.setup_logging")
    @patch("musigree.loader.loader.sys")
    def test_loader_main_cache_error(
        self,
        mock_sys: Mock,
        mock_setup_logging: Mock,
        mock_cache_manager: Mock,
        mock_offline_db_manager: Mock,
        mock_runtime_db_manager: Mock,
        _mock_atexit: Mock,
        _mock_luigi: Mock,
    ) -> None:
        """Test loader main function when cache is not available."""
        # Arrange
        mock_cache_manager.get_cache.return_value = None
        mock_cache_manager.setup_cache.return_value = None
        mock_sys.exit.side_effect = SystemExit(1)  # Make sys.exit actually exit

        # Make database setup methods return AsyncMock
        mock_offline_db_manager.setup_database = AsyncMock()
        mock_runtime_db_manager.setup_database = AsyncMock()

        # Mock runtime database helper
        mock_runtime_helper = Mock()
        mock_runtime_helper.drop_tables = AsyncMock()
        mock_runtime_helper.create_tables = AsyncMock()
        mock_runtime_db_manager.runtime_database_helper = mock_runtime_helper

        # Act & Assert
        with pytest.raises(SystemExit):
            loader_main()

        # Verify setup calls before exit
        mock_setup_logging.assert_called_once()
        mock_cache_manager.setup_cache.assert_called_once()
        mock_cache_manager.get_cache.assert_called_once()
        mock_sys.exit.assert_called_once()


class TestLoaderIntegration:
    """Integration tests for loader functions."""

    @pytest.fixture
    def test_config(self) -> Configuration:
        """Provide test configuration."""
        return SqliteTestConfiguration()

    @patch("musigree.loader.loader.OfflineDatabaseManager")
    @patch("musigree.offline.loader.loader_entity.LoaderEntity")
    @patch("musigree.offline.loader.loader_release.LoaderRelease")
    @patch("musigree.offline.loader.loader_relation.LoaderRelation")
    @patch("musigree.loader.loader.RoleDataAccess")
    @pytest.mark.asyncio
    async def test_load_offline_tables_integration(
        self,
        _mock_role_data_access: Mock,
        _mock_loader_relation: Mock,
        _mock_loader_release: Mock,
        _mock_loader_entity: Mock,
        _mock_db_manager: Mock,
    ) -> None:
        """Test integration of load_offline_tables with all components."""
        # Mock get_load_offline_table_stages to return awaitable mock stages
        with patch(
            "musigree.loader.loader.get_load_offline_table_stages"
        ) as mock_get_stages:
            # Create AsyncMock objects for stages
            mock_stage1 = AsyncMock()
            mock_stage2 = AsyncMock()
            mock_stage3 = AsyncMock()

            mock_stages = [mock_stage1(), mock_stage2(), mock_stage3()]
            mock_get_stages.return_value = mock_stages

            data_directory = Path("/test/data")
            date = "2024-11-01"

            # Act
            await load_offline_tables(data_directory, date, is_bulk_inserts=True)

            # Assert - just verify it completes without error since all stages are mocked
            assert True

    @pytest.mark.asyncio
    async def test_load_offline_table_stage_bounds_checking(self) -> None:
        """Test load_offline_table_stage with various stage bounds."""
        data_directory = Path("/test/data")
        date = "2024-11-01"

        with patch(
            "musigree.loader.loader.get_load_offline_table_stages"
        ) as mock_get_stages:
            # Create AsyncMock objects
            mock_stage1 = AsyncMock()
            mock_stage2 = AsyncMock()

            # Return AsyncMock coroutines
            mock_stages = [mock_stage1(), mock_stage2()]
            mock_get_stages.return_value = mock_stages

            # Test valid stages
            await load_offline_table_stage(
                data_directory, date, is_bulk_inserts=True, stage=0
            )
            await load_offline_table_stage(
                data_directory, date, is_bulk_inserts=True, stage=1
            )

            # Test bounds checking
            with pytest.raises(IndexError):
                await load_offline_table_stage(
                    data_directory, date, is_bulk_inserts=True, stage=2
                )


class TestLoaderEdgeCases:
    """Test edge cases for loader functions."""

    @patch("musigree.offline.loader.loader_entity.LoaderEntity")
    @patch("musigree.offline.loader.loader_release.LoaderRelease")
    @patch("musigree.offline.loader.loader_relation.LoaderRelation")
    @patch("musigree.loader.loader.RoleDataAccess")
    @patch("musigree.offline.loader.loader_role.LoaderRole")
    def test_empty_data_directory(
        self,
        mock_loader_role: Mock,
        mock_role_data_access: Mock,
        mock_loader_relation: Mock,
        mock_loader_release: Mock,
        mock_loader_entity: Mock,
    ) -> None:
        """Test handling of empty data directory."""
        empty_directory = Path("/empty")
        date = "2024-11-01"

        with patch("musigree.loader.loader.OfflineDatabaseManager") as mock_db_manager:
            mock_helper = Mock()
            mock_helper.is_vacuum_full.return_value = False
            mock_helper.is_vacuum_analyze.return_value = False
            mock_helper.offline_async_engine = Mock()
            mock_db_manager.offline_database_helper = mock_helper

            # Mock all the loader methods to avoid creating actual coroutines
            mock_loader_role.load_roles_into_database.return_value = AsyncMock()()
            mock_role_data_access.load_all_roles_into_cache.return_value = AsyncMock()()
            mock_loader_entity.loader_entity_pass_one.return_value = AsyncMock()()
            mock_loader_entity.loader_entity_pass_two.return_value = AsyncMock()()
            mock_loader_entity.loader_entity_pass_three.return_value = AsyncMock()()
            mock_loader_entity.loader_create_text_search_index.return_value = (
                AsyncMock()()
            )
            mock_loader_release.loader_release_pass_one.return_value = AsyncMock()()
            mock_loader_release.loader_release_pass_two.return_value = AsyncMock()()
            mock_loader_relation.loader_relation_pass_one.return_value = AsyncMock()()
            mock_helper.vacuum.return_value = AsyncMock()()

            # Should not raise error even with empty directory
            stages = get_load_offline_table_stages(
                empty_directory, date, is_bulk_inserts=False
            )
            assert isinstance(stages, list)
            assert len(stages) > 0

    @patch("musigree.loader.loader.get_load_runtime_table_stages")
    @pytest.mark.asyncio
    async def test_load_runtime_tables_missing_text_search(
        self, mock_get_stages: Mock
    ) -> None:
        """Test load_runtime_tables when text search file is missing."""
        # Arrange
        missing_directory = Path("/missing")

        # Mock the stages but have one of them raise FileNotFoundError
        mock_stage_that_fails = AsyncMock()
        mock_stage_that_fails.side_effect = FileNotFoundError(
            "Text search file not found"
        )

        mock_get_stages.return_value = [mock_stage_that_fails()]

        # Act & Assert - Should raise FileNotFoundError
        with pytest.raises(FileNotFoundError, match="Text search file not found"):
            await load_runtime_tables(missing_directory, "2024-11-01")
