"""
Unit tests for musigree.loader.run_runtime_loader module.
"""

from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

import pytest

from musigree.config import SqliteTestConfiguration, Configuration
from musigree.constants import (
    ENTITY_DETAILS_DATA,
    ENTITY_DETAILS_FILENAME,
    TEXT_SEARCH_DATA,
    TEXT_SEARCH_FILENAME,
)
from musigree.loader.run_runtime_loader import (
    load_runtime_table_stage,
    get_load_runtime_table_stages,
    load_runtime_tables,
    runtime_loader_main,
)
from musigree.runtime.data_access_layer.runtime_role_data_access import RuntimeRoleDataAccess
from musigree.transfer.transfer_manager import TransferManager


def _configure_runtime_db_helper(mock_db_manager: Mock) -> Mock:
    """Return a runtime database helper mock with analyze/optimize hooks."""
    mock_helper = Mock()
    mock_helper.runtime_async_engine = Mock()
    mock_helper.analyze = Mock()
    mock_helper.optimize = Mock()
    mock_db_manager.runtime_database_helper = mock_helper
    return mock_helper


def _configure_transfer_manager_mocks(mock_transfer_manager: Mock) -> None:
    """Configure TransferManager mocks used by get_load_runtime_table_stages."""
    mock_transfer_manager.transfer_role = Mock()
    mock_transfer_manager.transfer_load_text_search_index = Mock()
    mock_transfer_manager.transfer_load_entity_details_index = Mock()
    mock_transfer_manager.transfer_entity_details = Mock()
    mock_transfer_manager.transfer_entity = Mock()
    mock_transfer_manager.transfer_relation = Mock()


class TestRuntimeLoaderFunctions:
    """Test cases for runtime loader functions."""

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

    @patch("musigree.loader.run_runtime_loader.get_load_runtime_table_stages")
    @pytest.mark.asyncio
    async def test_load_runtime_tables_success(
        self, mock_get_stages: Mock, mock_data_directory: Mock, mock_date: Mock
    ) -> None:
        """Test successful loading of runtime tables."""
        # Arrange
        mock_stage1 = AsyncMock()
        mock_stage2 = AsyncMock()

        mock_get_stages.return_value = [mock_stage1, mock_stage2]

        # Act
        await load_runtime_tables(mock_data_directory, mock_date)

        # Assert
        mock_get_stages.assert_called_once_with(mock_data_directory, mock_date)

    @patch("musigree.loader.run_runtime_loader.get_load_runtime_table_stages")
    @pytest.mark.asyncio
    async def test_load_runtime_table_stage_success(
        self, mock_get_stages: Mock, mock_data_directory: Mock, mock_date: Mock
    ) -> None:
        """Test successful loading of a specific runtime table stage."""
        # Arrange
        mock_stage1 = AsyncMock()
        mock_stage2 = AsyncMock()
        mock_stage3 = AsyncMock()

        mock_get_stages.return_value = [mock_stage1, mock_stage2, mock_stage3]

        # Act
        await load_runtime_table_stage(mock_data_directory, mock_date, stage=1)

        # Assert
        mock_get_stages.assert_called_once_with(mock_data_directory, mock_date)
        # Note: We can't easily assert which specific stage was called due to the way coroutines work
        # but we can verify the function was called with correct parameters

    @patch("musigree.loader.run_runtime_loader.RuntimeDatabaseManager")
    @patch("musigree.transfer.transfer_manager.TransferManager")
    @patch("musigree.runtime.data_access_layer.runtime_role_data_access.RuntimeRoleDataAccess")
    def test_get_load_runtime_table_stages_success(
        self,
        mock_runtime_role_data_access: Mock,
        mock_transfer_manager: Mock,
        mock_db_manager: Mock,
        mock_data_directory: Mock,
        mock_date: Mock,
    ) -> None:
        """Test successful creation of load runtime table stages."""
        # Arrange
        _configure_runtime_db_helper(mock_db_manager)

        _configure_transfer_manager_mocks(mock_transfer_manager)

        # Mock the runtime role data access method
        mock_runtime_role_data_access.load_all_roles_into_cache = AsyncMock()

        # Act
        result = get_load_runtime_table_stages(mock_data_directory, mock_date)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 13

    @patch("musigree.loader.run_runtime_loader.RuntimeDatabaseManager")
    def test_get_load_runtime_table_stages_assertion_error_no_helper(
        self,
        mock_db_manager: Mock,
        mock_data_directory: Mock,
        mock_date: Mock,
    ) -> None:
        """Test get_load_runtime_table_stages raises assertion error when helper is None."""
        # Arrange
        mock_db_manager.runtime_database_helper = None

        # Act & Assert
        with pytest.raises(AssertionError) as excinfo:
            get_load_runtime_table_stages(mock_data_directory, mock_date)

        assert "RuntimeDatabaseManager.runtime_database_helper must be initialized" in str(
            excinfo.value
        )

    @patch("musigree.loader.run_runtime_loader.RuntimeDatabaseManager")
    @patch("musigree.transfer.transfer_manager.TransferManager")
    @patch("musigree.runtime.data_access_layer.runtime_role_data_access.RuntimeRoleDataAccess")
    def test_get_load_runtime_table_stages_assertion_error_no_engine(
        self,
        mock_runtime_role_data_access: Mock,
        mock_transfer_manager: Mock,
        mock_db_manager: Mock,
        mock_data_directory: Mock,
        mock_date: Mock,
    ) -> None:
        """Test get_load_runtime_table_stages raises assertion error when engine is None."""
        # Arrange
        mock_helper = Mock()
        mock_helper.runtime_async_engine = None
        mock_db_manager.runtime_database_helper = mock_helper

        _configure_transfer_manager_mocks(mock_transfer_manager)
        mock_runtime_role_data_access.load_all_roles_into_cache = AsyncMock()
        mock_helper.analyze = Mock()
        mock_helper.optimize = Mock()

        # Act & Assert
        # The function should raise an assertion error when engine is None
        with pytest.raises(AssertionError) as excinfo:
            get_load_runtime_table_stages(mock_data_directory, mock_date)

        assert "runtime_async_engine must be initialized" in str(excinfo.value)

    @patch("musigree.loader.run_runtime_loader.RuntimeDatabaseManager")
    def test_get_load_runtime_table_stages_stage_definitions(
        self,
        mock_db_manager: Mock,
        mock_data_directory: Path,
        mock_date: str,
    ) -> None:
        """Test runtime stage list references current transfer and cleanup methods."""
        mock_helper = _configure_runtime_db_helper(mock_db_manager)

        stages = get_load_runtime_table_stages(mock_data_directory, mock_date)

        assert len(stages) == 13
        assert stages[0].func == TransferManager.transfer_role
        assert stages[1].func == RuntimeRoleDataAccess.load_all_roles_into_cache
        assert stages[2].func == TransferManager.transfer_load_text_search_index
        assert stages[2].args == (
            mock_data_directory / TEXT_SEARCH_DATA / TEXT_SEARCH_FILENAME,
        )
        assert stages[3].func == TransferManager.transfer_load_entity_details_index
        assert stages[3].args == (
            mock_data_directory / ENTITY_DETAILS_DATA / ENTITY_DETAILS_FILENAME,
        )
        assert stages[4].func == mock_helper.analyze
        assert stages[5].func == mock_helper.optimize
        assert stages[6].func == TransferManager.transfer_entity_details
        assert stages[7].func == TransferManager.transfer_entity
        assert stages[8].func == mock_helper.analyze
        assert stages[9].func == mock_helper.optimize
        assert stages[10].func == TransferManager.transfer_relation
        assert stages[11].func == mock_helper.analyze
        assert stages[12].func == mock_helper.optimize

    @patch("musigree.loader.run_runtime_loader.luigi")
    @patch("musigree.loader.run_runtime_loader.asyncio_atexit")
    @patch("musigree.loader.run_runtime_loader.OfflineRoleDataAccess")
    @patch("musigree.loader.run_runtime_loader.RuntimeDatabaseManager")
    @patch("musigree.loader.run_runtime_loader.OfflineDatabaseManager")
    @patch("musigree.loader.run_runtime_loader.CacheManager")
    @patch("musigree.loader.run_runtime_loader.setup_logging")
    @patch("musigree.loader.run_runtime_loader.asyncio.Runner")
    def test_runtime_loader_main_success(
        self,
        mock_runner: Mock,
        mock_setup_logging: Mock,
        mock_cache_manager: Mock,
        mock_offline_db_manager: Mock,
        mock_runtime_db_manager: Mock,
        mock_role_data_access: Mock,
        _mock_asyncio_atexit: Mock,
        mock_luigi: Mock,
    ) -> None:
        """Test successful execution of loader_main."""
        # Arrange
        mock_cache_manager.setup_and_clear_cache = AsyncMock()

        mock_build_result = Mock()
        mock_build_result.summary_text = "Build completed successfully"
        mock_luigi.build.return_value = mock_build_result

        # Mock database setup methods to return AsyncMock
        mock_offline_db_manager.setup_database = AsyncMock()
        mock_runtime_db_manager.setup_database = AsyncMock()

        # Mock offline database helper
        mock_offline_helper = Mock()
        mock_offline_helper.create_tables = AsyncMock()
        mock_offline_db_manager.offline_database_helper = mock_offline_helper

        # Mock runtime database helper
        mock_runtime_helper = Mock()
        mock_runtime_helper.drop_tables = AsyncMock()
        mock_runtime_helper.create_tables = AsyncMock()
        mock_runtime_db_manager.runtime_database_helper = mock_runtime_helper

        mock_role_data_access.load_all_roles_into_cache = AsyncMock()

        # Mock asyncio.Runner context manager
        mock_runner_instance = Mock()
        mock_runner.return_value.__enter__.return_value = mock_runner_instance
        mock_runner.return_value.__exit__.return_value = None

        # Act
        runtime_loader_main()

        # Assert
        mock_setup_logging.assert_called_once()
        mock_offline_db_manager.setup_database.assert_called_once()
        mock_runtime_db_manager.setup_database.assert_called_once()
        mock_offline_helper.drop_tables.assert_not_called()
        mock_offline_helper.create_tables.assert_not_called()
        mock_runtime_helper.drop_tables.assert_not_called()
        mock_runtime_helper.create_tables.assert_called_once()
        mock_luigi.build.assert_called_once()

    @patch("musigree.loader.run_runtime_loader.luigi")
    @patch("musigree.loader.run_runtime_loader.asyncio_atexit")
    @patch("musigree.loader.run_runtime_loader.RuntimeDatabaseManager")
    @patch("musigree.loader.run_runtime_loader.OfflineDatabaseManager")
    @patch("musigree.loader.run_runtime_loader.CacheManager")
    @patch("musigree.loader.run_runtime_loader.setup_logging")
    @patch("musigree.loader.run_runtime_loader.asyncio.Runner")
    def test_loader_main_cache_error(
        self,
        mock_runner: Mock,
        mock_setup_logging: Mock,
        mock_cache_manager: Mock,
        mock_offline_db_manager: Mock,
        mock_runtime_db_manager: Mock,
        _mock_asyncio_atexit: Mock,
        _mock_luigi: Mock,
    ) -> None:
        """Test loader main function when cache setup fails."""
        # Arrange
        mock_cache_manager.setup_and_clear_cache = AsyncMock()

        # Make database setup methods return AsyncMock
        mock_offline_db_manager.setup_database = AsyncMock()
        mock_runtime_db_manager.setup_database = AsyncMock()

        # Mock runtime database helper
        mock_runtime_helper = Mock()
        mock_runtime_helper.drop_tables = AsyncMock()
        mock_runtime_helper.create_tables = AsyncMock()
        mock_runtime_db_manager.runtime_database_helper = mock_runtime_helper

        # Mock asyncio.Runner context manager - fail on cache setup, then allow finalize
        mock_runner_instance = Mock()
        mock_runner_instance.run.side_effect = [
            RuntimeError("Cache not initialized after setup"),
            None,
        ]
        mock_runner.return_value.__enter__.return_value = mock_runner_instance
        mock_runner.return_value.__exit__.return_value = None
        mock_runner_instance.get_loop.return_value = Mock()

        # Act & Assert
        with pytest.raises(SystemExit):
            runtime_loader_main()

        # Verify setup calls before exit
        mock_setup_logging.assert_called_once()


class TestRuntimeLoaderIntegration:
    """Integration tests for runtime loader functions."""

    @pytest.fixture
    def test_config(self) -> Configuration:
        """Provide test configuration."""
        return SqliteTestConfiguration()

    @pytest.mark.asyncio
    async def test_load_runtime_tables_integration(
        self,
    ) -> None:
        """Test integration of load_runtime_tables with all components."""
        # Mock get_load_runtime_table_stages to return awaitable mock stages
        with patch(
            "musigree.loader.run_runtime_loader.get_load_runtime_table_stages"
        ) as mock_get_stages:
            # Create async mock stages
            mock_stage1 = AsyncMock()
            mock_stage2 = AsyncMock()
            mock_stage3 = AsyncMock()

            mock_stages = [mock_stage1, mock_stage2, mock_stage3]
            mock_get_stages.return_value = mock_stages

            data_directory = Path("/test/data")
            date = "2024-11-01"

            # Act
            await load_runtime_tables(data_directory, date)

            # Assert - just verify it completes without error since all stages are mocked
            assert True

    @pytest.mark.asyncio
    async def test_load_runtime_table_stage_bounds_checking(self) -> None:
        """Test load_runtime_table_stage with various stage bounds."""
        data_directory = Path("/test/data")
        date = "2024-11-01"

        with patch(
            "musigree.loader.run_runtime_loader.get_load_runtime_table_stages"
        ) as mock_get_stages:
            # Create async mock stages
            mock_stage1 = AsyncMock()
            mock_stage2 = AsyncMock()

            # Return async mock stages
            mock_stages = [mock_stage1, mock_stage2]
            mock_get_stages.return_value = mock_stages

            # Test valid stages
            await load_runtime_table_stage(data_directory, date, stage=0)
            await load_runtime_table_stage(data_directory, date, stage=1)

            # Test bounds checking
            with pytest.raises(IndexError):
                await load_runtime_table_stage(data_directory, date, stage=2)


class TestRuntimeLoaderEdgeCases:
    """Test edge cases for runtime loader functions."""

    @patch("musigree.loader.run_runtime_loader.RuntimeDatabaseManager")
    @patch("musigree.transfer.transfer_manager.TransferManager")
    @patch("musigree.runtime.data_access_layer.runtime_role_data_access.RuntimeRoleDataAccess")
    def test_empty_data_directory(
        self,
        mock_runtime_role_data_access: Mock,
        mock_transfer_manager: Mock,
        mock_db_manager: Mock,
    ) -> None:
        """Test handling of empty data directory."""
        empty_directory = Path("/empty")
        date = "2024-11-01"

        _configure_runtime_db_helper(mock_db_manager)

        _configure_transfer_manager_mocks(mock_transfer_manager)
        mock_runtime_role_data_access.load_all_roles_into_cache = AsyncMock()

        # Should not raise error even with empty directory
        stages = get_load_runtime_table_stages(empty_directory, date)
        assert isinstance(stages, list)
        assert len(stages) == 13

    @patch("musigree.loader.run_runtime_loader.get_load_runtime_table_stages")
    @pytest.mark.asyncio
    async def test_load_runtime_tables_missing_text_search(self, mock_get_stages: Mock) -> None:
        """Test load_runtime_tables when text search file is missing."""
        # Arrange
        missing_directory = Path("/missing")

        # Mock the stages but have one of them raise FileNotFoundError
        mock_stage_that_fails = AsyncMock(
            side_effect=FileNotFoundError("Text search file not found")
        )

        mock_get_stages.return_value = [mock_stage_that_fails]

        # Act & Assert - Should raise FileNotFoundError
        with pytest.raises(FileNotFoundError, match="Text search file not found"):
            await load_runtime_tables(missing_directory, "2024-11-01")

    @patch("musigree.loader.run_runtime_loader.get_load_runtime_table_stages")
    @pytest.mark.asyncio
    async def test_load_runtime_table_stage_with_exception(self, mock_get_stages: Mock) -> None:
        """Test load_runtime_table_stage when a stage raises an exception."""
        # Arrange
        data_directory = Path("/test/data")
        date = "2024-11-01"

        mock_stage_that_fails = AsyncMock(side_effect=RuntimeError("Stage execution failed"))

        mock_get_stages.return_value = [mock_stage_that_fails]

        # Act & Assert - Should raise RuntimeError
        with pytest.raises(RuntimeError, match="Stage execution failed"):
            await load_runtime_table_stage(data_directory, date, stage=0)

    @patch("musigree.loader.run_runtime_loader.get_load_runtime_table_stages")
    @pytest.mark.asyncio
    async def test_load_runtime_tables_empty_stages_list(self, mock_get_stages: Mock) -> None:
        """Test load_runtime_tables with empty stages list."""
        # Arrange
        data_directory = Path("/test/data")
        date = "2024-11-01"

        mock_get_stages.return_value = []

        # Act - Should complete without error even with empty stages
        await load_runtime_tables(data_directory, date)

        # Assert
        mock_get_stages.assert_called_once_with(data_directory, date)

    @patch("musigree.loader.run_runtime_loader.RuntimeDatabaseManager")
    def test_get_load_runtime_table_stages_includes_analyze_and_optimize(
        self,
        mock_db_manager: Mock,
    ) -> None:
        """Test get_load_runtime_table_stages wires analyze and optimize cleanup stages."""
        data_directory = Path("/test/data")
        date = "2024-11-01"
        mock_helper = _configure_runtime_db_helper(mock_db_manager)

        stages = get_load_runtime_table_stages(data_directory, date)

        analyze_stages = [stage for stage in stages if stage.func == mock_helper.analyze]
        optimize_stages = [stage for stage in stages if stage.func == mock_helper.optimize]

        assert len(analyze_stages) == 3
        assert len(optimize_stages) == 3
        for stage in analyze_stages + optimize_stages:
            assert stage.args[0] is None
            assert stage.args[1] is mock_helper.runtime_async_engine

    def test_load_runtime_table_stage_negative_index(self) -> None:
        """Test load_runtime_table_stage with negative stage index."""
        # This would be handled by Python's list indexing, which allows negative indices
        # We'll test this behavior
        with patch(
            "musigree.loader.run_runtime_loader.get_load_runtime_table_stages"
        ) as mock_get_stages:
            mock_stage = AsyncMock()
            mock_get_stages.return_value = [mock_stage]

            # This should work with negative indexing (accessing last element)
            import asyncio

            asyncio.run(load_runtime_table_stage(Path("/test"), "2024-11-01", stage=-1))

            mock_get_stages.assert_called_once()

    @patch("musigree.loader.run_runtime_loader.RuntimeDatabaseManager")
    def test_get_load_runtime_table_stages_none_date(
        self,
        mock_db_manager: Mock,
    ) -> None:
        """Test get_load_runtime_table_stages with None date parameter."""
        # Arrange
        data_directory = Path("/test/data")

        _configure_runtime_db_helper(mock_db_manager)

        with patch("musigree.transfer.transfer_manager.TransferManager") as mock_transfer_manager:
            with patch(
                "musigree.runtime.data_access_layer.runtime_role_data_access.RuntimeRoleDataAccess"
            ) as mock_runtime_role_data_access:
                _configure_transfer_manager_mocks(mock_transfer_manager)
                mock_transfer_manager.transfer_role = AsyncMock()
                mock_transfer_manager.transfer_load_text_search_index = AsyncMock()
                mock_transfer_manager.transfer_load_entity_details_index = AsyncMock()
                mock_transfer_manager.transfer_entity_details = AsyncMock()
                mock_transfer_manager.transfer_entity = AsyncMock()
                mock_transfer_manager.transfer_relation = AsyncMock()
                mock_runtime_role_data_access.load_all_roles_into_cache = AsyncMock()

                # Act - Should work with None date
                stages = get_load_runtime_table_stages(data_directory, None)

                # Assert
                assert isinstance(stages, list)
                assert len(stages) == 13


class TestRuntimeLoaderShutdown:
    """Test cases for runtime loader shutdown functionality."""

    @pytest.mark.asyncio
    @patch("musigree.loader.run_runtime_loader.OfflineDatabaseManager")
    @patch("musigree.loader.run_runtime_loader.RuntimeDatabaseManager")
    @patch("musigree.loader.run_runtime_loader.CacheManager")
    @patch("musigree.loader.run_runtime_loader.setup_logging")
    @patch("musigree.loader.run_runtime_loader.shutdown_logging")
    @patch("musigree.loader.run_runtime_loader.asyncio.Runner")
    async def test_shutdown_loader_success(
        self,
        mock_runner: Mock,
        mock_shutdown_logging: Mock,
        mock_setup_logging: Mock,
        mock_cache_manager: Mock,
        mock_runtime_db_manager: Mock,
        mock_offline_db_manager: Mock,
    ) -> None:
        """Test successful shutdown of the loader."""
        # Arrange
        mock_offline_db_manager.shutdown_database = AsyncMock()
        mock_runtime_db_manager.shutdown_database = AsyncMock()
        mock_cache_manager.shutdown_cache = AsyncMock()

        # Mock asyncio.Runner context manager
        mock_runner_instance = Mock()
        mock_runner.return_value.__enter__.return_value = mock_runner_instance
        mock_runner.return_value.__exit__.return_value = None

        # Act
        from musigree.loader.run_runtime_loader import shutdown_runtime_loader

        await shutdown_runtime_loader()

        # Assert
        mock_setup_logging.assert_called_once()
        mock_offline_db_manager.shutdown_database.assert_called_once()
        mock_runtime_db_manager.shutdown_database.assert_called_once()
        mock_cache_manager.shutdown_cache.assert_called_once()
        mock_shutdown_logging.assert_called_once()

    @pytest.mark.asyncio
    @patch("musigree.loader.run_runtime_loader.OfflineDatabaseManager")
    @patch("musigree.loader.run_runtime_loader.RuntimeDatabaseManager")
    @patch("musigree.loader.run_runtime_loader.CacheManager")
    @patch("musigree.loader.run_runtime_loader.setup_logging")
    @patch("musigree.loader.run_runtime_loader.shutdown_logging")
    @patch("musigree.loader.run_runtime_loader.asyncio.Runner")
    async def test_shutdown_loader_with_database_error(
        self,
        mock_runner: Mock,
        _mock_shutdown_logging: Mock,
        _mock_setup_logging: Mock,
        _mock_cache_manager: Mock,
        mock_runtime_db_manager: Mock,
        mock_offline_db_manager: Mock,
    ) -> None:
        """Test shutdown_loader when database shutdown fails."""
        # Arrange
        mock_offline_db_manager.shutdown_database = AsyncMock(
            side_effect=Exception("Database shutdown failed")
        )
        mock_runtime_db_manager.shutdown_database = AsyncMock()

        # Mock asyncio.Runner context manager to propagate the exception
        mock_runner_instance = Mock()
        mock_runner_instance.run.side_effect = Exception("Database shutdown failed")
        mock_runner.return_value.__enter__.return_value = mock_runner_instance
        mock_runner.return_value.__exit__.return_value = None

        # Act & Assert - Should propagate the exception when runner.run is called
        from musigree.loader.run_runtime_loader import shutdown_runtime_loader

        with pytest.raises(Exception, match="Database shutdown failed"):
            await shutdown_runtime_loader()


class TestRuntimeLoaderMainAdditional:
    """Additional test cases for runtime_loader_main function."""

    @patch("musigree.loader.run_runtime_loader.luigi")
    @patch("musigree.loader.run_runtime_loader.asyncio_atexit")
    @patch("musigree.loader.run_runtime_loader.OfflineRoleDataAccess")
    @patch("musigree.loader.run_runtime_loader.RuntimeDatabaseManager")
    @patch("musigree.loader.run_runtime_loader.OfflineDatabaseManager")
    @patch("musigree.loader.run_runtime_loader.CacheManager")
    @patch("musigree.loader.run_runtime_loader.setup_logging")
    @patch("musigree.loader.run_runtime_loader.asyncio.Runner")
    def test_runtime_loader_main_luigi_failure(
        self,
        mock_runner: Mock,
        _mock_setup_logging: Mock,
        mock_cache_manager: Mock,
        mock_offline_db_manager: Mock,
        mock_runtime_db_manager: Mock,
        mock_role_data_access: Mock,
        _mock_asyncio_atexit: Mock,
        mock_luigi: Mock,
    ) -> None:
        """Test runtime_loader_main when Luigi build fails."""
        # Arrange
        mock_cache_manager.setup_and_clear_cache = AsyncMock()

        mock_build_result = Mock()
        mock_build_result.summary_text = "Build failed with errors"
        mock_luigi.build.return_value = mock_build_result

        # Mock database setup methods to return AsyncMock
        mock_offline_db_manager.setup_database = AsyncMock()
        mock_runtime_db_manager.setup_database = AsyncMock()

        # Mock offline database helper
        mock_offline_helper = Mock()
        mock_offline_helper.create_tables = AsyncMock()
        mock_offline_db_manager.offline_database_helper = mock_offline_helper

        # Mock runtime database helper
        mock_runtime_helper = Mock()
        mock_runtime_helper.drop_tables = AsyncMock()
        mock_runtime_helper.create_tables = AsyncMock()
        mock_runtime_db_manager.runtime_database_helper = mock_runtime_helper

        mock_role_data_access.load_all_roles_into_cache = AsyncMock()

        # Mock asyncio.Runner context manager
        mock_runner_instance = Mock()
        mock_runner.return_value.__enter__.return_value = mock_runner_instance
        mock_runner.return_value.__exit__.return_value = None

        # Act
        runtime_loader_main()

        # Assert
        mock_luigi.build.assert_called_once()

    @patch("musigree.loader.run_runtime_loader.luigi")
    @patch("musigree.loader.run_runtime_loader.asyncio_atexit")
    @patch("musigree.loader.run_runtime_loader.RuntimeDatabaseManager")
    @patch("musigree.loader.run_runtime_loader.OfflineDatabaseManager")
    @patch("musigree.loader.run_runtime_loader.CacheManager")
    @patch("musigree.loader.run_runtime_loader.setup_logging")
    @patch("musigree.loader.run_runtime_loader.asyncio.Runner")
    def test_runtime_loader_main_database_setup_failure(
        self,
        mock_runner: Mock,
        _mock_setup_logging: Mock,
        mock_cache_manager: Mock,
        mock_offline_db_manager: Mock,
        mock_runtime_db_manager: Mock,
        _mock_asyncio_atexit: Mock,
        _mock_luigi: Mock,
    ) -> None:
        """Test runtime_loader_main when database setup fails."""
        # Arrange
        mock_cache_manager.setup_and_clear_cache = AsyncMock()

        # Make database setup fail by making runner.run fail
        mock_offline_db_manager.setup_database = AsyncMock()
        mock_runtime_db_manager.setup_database = AsyncMock()

        # Mock asyncio.Runner context manager to fail on run
        mock_runner_instance = Mock()
        mock_runner_instance.run.side_effect = Exception("Database setup failed")
        mock_runner.return_value.__enter__.return_value = mock_runner_instance
        mock_runner.return_value.__exit__.return_value = None

        # Act & Assert - Should propagate the exception
        with pytest.raises(Exception, match="Database setup failed"):
            runtime_loader_main()
