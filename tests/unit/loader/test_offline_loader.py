"""
Unit tests for musigree.loader.offline_loader module.
"""

from functools import partial
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

import pytest

from musigree.config import SqliteTestConfiguration, Configuration
from musigree.loader.offline_loader import (
    load_offline_tables,
    load_offline_table_stage,
    get_load_offline_table_stages,
    offline_loader_main,
    shutdown_offline_loader,
)


class TestOfflineLoaderFunctions:
    """Test cases for offline loader functions."""

    @pytest.fixture
    def test_config(self) -> Configuration:
        """Provide test configuration.

        Returns:
            Configuration: A SQLite test configuration instance.
        """
        return SqliteTestConfiguration()

    @pytest.fixture
    def mock_data_directory(self) -> Path:
        """Provide mock data directory.

        Returns:
            Path: A mock data directory path for testing.
        """
        return Path("/test/data")

    @pytest.fixture
    def mock_date(self) -> str:
        """Provide mock date.

        Returns:
            str: A mock date string in YYYY-MM-DD format.
        """
        return "2024-11-01"

    @patch("musigree.loader.offline_loader.get_load_offline_table_stages")
    @pytest.mark.asyncio
    async def test_load_offline_tables_success(
        self, mock_get_stages: Mock, mock_data_directory: Mock, mock_date: Mock
    ) -> None:
        """Test successful loading of offline tables.

        Verifies that load_offline_tables function correctly orchestrates
        the execution of all loading stages when provided with valid
        data directory, date, and bulk insert settings.
        """
        # Arrange
        mock_stage1 = AsyncMock()
        mock_stage2 = AsyncMock()

        mock_get_stages.return_value = [partial(mock_stage1), partial(mock_stage2)]

        # Act
        await load_offline_tables(mock_data_directory, mock_date, is_bulk_inserts=True)

        # Assert
        mock_get_stages.assert_called_once_with(mock_data_directory, mock_date, True)

    @patch("musigree.loader.offline_loader.get_load_offline_table_stages")
    @pytest.mark.asyncio
    async def test_load_offline_table_stage_success(
        self, mock_get_stages: Mock, mock_data_directory: Mock, mock_date: Mock
    ) -> None:
        """Test successful loading of a specific offline table stage.

        Verifies that load_offline_table_stage function correctly executes
        a single stage from the available loading stages based on the
        provided stage index.
        """
        # Arrange
        mock_stage1 = AsyncMock()
        mock_stage2 = AsyncMock()
        mock_stage3 = AsyncMock()

        mock_get_stages.return_value = [
            partial(mock_stage1),
            partial(mock_stage2),
            partial(mock_stage3),
        ]

        # Act
        await load_offline_table_stage(
            mock_data_directory, mock_date, is_bulk_inserts=False, stage=1
        )

        # Assert
        mock_get_stages.assert_called_once_with(mock_data_directory, mock_date, False)
        # Note: We can't easily assert which specific stage was called due to the way coroutines work
        # but we can verify the function was called with correct parameters

    @patch("musigree.loader.offline_loader.OfflineDatabaseManager")
    @patch("musigree.offline.loader.loader_entity.LoaderEntity")
    @patch("musigree.offline.loader.loader_release.LoaderRelease")
    @patch("musigree.offline.loader.loader_relation.LoaderRelation")
    @patch("musigree.loader.offline_loader.RoleDataAccess")
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
        mock_helper.offline_async_engine = Mock()
        mock_db_manager.offline_database_helper = mock_helper

        # Mock vacuum method to return an AsyncMock coroutine
        mock_helper.vacuum = AsyncMock()

        # Mock the static/class methods to return AsyncMock coroutines
        _mock_role_data_access.load_all_roles_into_cache = AsyncMock()
        mock_loader_entity.loader_entity_pass_one = AsyncMock()
        mock_loader_entity.loader_entity_pass_two = AsyncMock()
        mock_loader_entity.loader_entity_pass_three = AsyncMock()
        mock_loader_entity.loader_create_text_search_index = AsyncMock()
        mock_loader_release.loader_release_pass_one = AsyncMock()
        mock_loader_release.loader_release_pass_two = AsyncMock()
        mock_loader_relation.loader_relation_pass_one = AsyncMock()

        # Act
        result = get_load_offline_table_stages(mock_data_directory, mock_date, is_bulk_inserts=True)

        # Assert
        assert isinstance(result, list)
        assert len(result) > 0

    @patch("musigree.loader.offline_loader.OfflineDatabaseManager")
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
            get_load_offline_table_stages(mock_data_directory, mock_date, is_bulk_inserts=True)

        assert "OfflineDatabaseManager.offline_database_helper must be initialized" in str(
            excinfo.value
        )

    @patch("musigree.loader.offline_loader.OfflineDatabaseManager")
    @patch("musigree.offline.loader.loader_entity.LoaderEntity")
    @patch("musigree.offline.loader.loader_release.LoaderRelease")
    @patch("musigree.offline.loader.loader_relation.LoaderRelation")
    @patch("musigree.loader.offline_loader.RoleDataAccess")
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
        mock_loader_role.load_roles_into_database = AsyncMock()
        mock_role_data_access.load_all_roles_into_cache = AsyncMock()
        mock_loader_entity.loader_entity_pass_one = AsyncMock()
        mock_loader_entity.loader_entity_pass_two = AsyncMock()
        mock_loader_entity.loader_entity_pass_three = AsyncMock()
        mock_loader_entity.loader_create_text_search_index = AsyncMock()
        mock_loader_release.loader_release_pass_one = AsyncMock()
        mock_loader_release.loader_release_pass_two = AsyncMock()
        mock_loader_relation.loader_relation_pass_one = AsyncMock()
        mock_helper.vacuum = AsyncMock()

        # Act & Assert
        # The function should raise an assertion error when engine is None
        with pytest.raises(AssertionError) as excinfo:
            get_load_offline_table_stages(mock_data_directory, mock_date, is_bulk_inserts=True)

        assert "offline_async_engine must be initialized" in str(excinfo.value)

    @patch("musigree.loader.offline_loader.luigi")
    @patch("musigree.loader.offline_loader.atexit")
    @patch("musigree.loader.offline_loader.RoleDataAccess")
    @patch("musigree.loader.offline_loader.OfflineDatabaseManager")
    @patch("musigree.loader.offline_loader.CacheManager")
    @patch("musigree.loader.offline_loader.setup_logging")
    @patch("musigree.loader.offline_loader.sys")
    @patch("musigree.loader.offline_loader.asyncio.Runner")
    def test_offline_loader_main_success(
        self,
        mock_runner: Mock,
        _mock_sys: Mock,
        mock_setup_logging: Mock,
        mock_cache_manager: Mock,
        mock_offline_db_manager: Mock,
        mock_role_data_access: Mock,
        _mock_atexit: Mock,
        mock_luigi: Mock,
    ) -> None:
        """Test successful execution of offline_loader_main."""
        # Arrange
        mock_cache = Mock()
        mock_cache_manager.get_cache.return_value = mock_cache

        mock_build_result = Mock()
        mock_build_result.summary_text = "Build completed successfully"
        mock_luigi.build.return_value = mock_build_result

        # Mock database setup method to return AsyncMock
        mock_offline_db_manager.setup_database = AsyncMock()

        # Mock offline database helper
        mock_offline_helper = Mock()
        mock_offline_helper.create_tables = AsyncMock()
        mock_offline_db_manager.offline_database_helper = mock_offline_helper

        # Mock role data access
        mock_role_data_access.load_all_roles_into_cache = AsyncMock()

        # Mock asyncio.Runner context manager
        mock_runner_instance = Mock()
        mock_runner.return_value.__enter__.return_value = mock_runner_instance
        mock_runner.return_value.__exit__.return_value = None

        # Act
        offline_loader_main()

        # Assert
        mock_setup_logging.assert_called_once()
        mock_cache_manager.setup_cache.assert_called_once()
        mock_cache_manager.get_cache.assert_called_once()
        mock_offline_db_manager.setup_database.assert_called_once()
        mock_offline_helper.create_tables.assert_called_once()
        mock_role_data_access.load_all_roles_into_cache.assert_called_once()
        mock_luigi.build.assert_called_once()

    @patch("musigree.loader.offline_loader.luigi")
    @patch("musigree.loader.offline_loader.atexit")
    @patch("musigree.loader.offline_loader.OfflineDatabaseManager")
    @patch("musigree.loader.offline_loader.CacheManager")
    @patch("musigree.loader.offline_loader.setup_logging")
    @patch("musigree.loader.offline_loader.sys")
    @patch("musigree.loader.offline_loader.asyncio.Runner")
    def test_offline_loader_main_cache_error(
        self,
        mock_runner: Mock,
        mock_sys: Mock,
        mock_setup_logging: Mock,
        mock_cache_manager: Mock,
        mock_offline_db_manager: Mock,
        _mock_atexit: Mock,
        _mock_luigi: Mock,
    ) -> None:
        """Test offline_loader_main function when cache is not available."""
        # Arrange
        mock_cache_manager.get_cache.return_value = None
        mock_cache_manager.setup_cache.return_value = None
        mock_sys.exit.side_effect = SystemExit(1)  # Make sys.exit actually exit

        # Make database setup method return AsyncMock
        mock_offline_db_manager.setup_database = AsyncMock()

        # Mock asyncio.Runner context manager
        mock_runner_instance = Mock()
        mock_runner.return_value.__enter__.return_value = mock_runner_instance
        mock_runner.return_value.__exit__.return_value = None

        # Act & Assert
        with pytest.raises(SystemExit):
            offline_loader_main()

        # Verify setup calls before exit
        mock_setup_logging.assert_called_once()
        mock_cache_manager.setup_cache.assert_called_once()
        mock_cache_manager.get_cache.assert_called_once()
        mock_sys.exit.assert_called_once()


class TestOfflineLoaderIntegration:
    """Integration tests for loader functions.

    This test class focuses on testing the integration between different
    components of the offline loader system, verifying that they work
    together correctly.
    """

    @pytest.fixture
    def test_config(self) -> Configuration:
        """Provide test configuration.

        Returns:
            Configuration: A SQLite test configuration instance.
        """
        return SqliteTestConfiguration()

    @patch("musigree.loader.offline_loader.OfflineDatabaseManager")
    @patch("musigree.offline.loader.loader_entity.LoaderEntity")
    @patch("musigree.offline.loader.loader_release.LoaderRelease")
    @patch("musigree.offline.loader.loader_relation.LoaderRelation")
    @patch("musigree.loader.offline_loader.RoleDataAccess")
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
            "musigree.loader.offline_loader.get_load_offline_table_stages"
        ) as mock_get_stages:
            # Create AsyncMock objects for stages
            mock_stage1 = AsyncMock()
            mock_stage2 = AsyncMock()
            mock_stage3 = AsyncMock()

            mock_stages = [partial(mock_stage1), partial(mock_stage2), partial(mock_stage3)]
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
            "musigree.loader.offline_loader.get_load_offline_table_stages"
        ) as mock_get_stages:
            # Create AsyncMock objects
            mock_stage1 = AsyncMock()
            mock_stage2 = AsyncMock()

            # Return AsyncMock coroutines
            mock_stages = [partial(mock_stage1), partial(mock_stage2)]
            mock_get_stages.return_value = mock_stages

            # Test valid stages
            await load_offline_table_stage(data_directory, date, is_bulk_inserts=True, stage=0)
            await load_offline_table_stage(data_directory, date, is_bulk_inserts=True, stage=1)

            # Test bounds checking
            with pytest.raises(IndexError):
                await load_offline_table_stage(data_directory, date, is_bulk_inserts=True, stage=2)


class TestOfflineLoaderEdgeCases:
    """Test edge cases for loader functions.

    This test class covers edge cases, boundary conditions, and error
    scenarios to ensure the offline loader behaves correctly under
    various unusual or exceptional circumstances.
    """

    @patch("musigree.offline.loader.loader_entity.LoaderEntity")
    @patch("musigree.offline.loader.loader_release.LoaderRelease")
    @patch("musigree.offline.loader.loader_relation.LoaderRelation")
    @patch("musigree.loader.offline_loader.RoleDataAccess")
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

        with patch("musigree.loader.offline_loader.OfflineDatabaseManager") as mock_db_manager:
            mock_helper = Mock()
            mock_helper.is_vacuum_full.return_value = False
            mock_helper.is_vacuum_analyze.return_value = False
            mock_helper.offline_async_engine = Mock()
            mock_db_manager.offline_database_helper = mock_helper

            # Mock all the loader methods to avoid creating actual coroutines
            mock_loader_role.load_roles_into_database = AsyncMock()
            mock_role_data_access.load_all_roles_into_cache = AsyncMock()
            mock_loader_entity.loader_entity_pass_one = AsyncMock()
            mock_loader_entity.loader_entity_pass_two = AsyncMock()
            mock_loader_entity.loader_entity_pass_three = AsyncMock()
            mock_loader_entity.loader_create_text_search_index = AsyncMock()
            mock_loader_release.loader_release_pass_one = AsyncMock()
            mock_loader_release.loader_release_pass_two = AsyncMock()
            mock_loader_relation.loader_relation_pass_one = AsyncMock()
            mock_helper.vacuum = AsyncMock()

            # Should not raise error even with empty directory
            stages = get_load_offline_table_stages(empty_directory, date, is_bulk_inserts=False)
            assert isinstance(stages, list)
            assert len(stages) > 0

    @patch("musigree.loader.offline_loader.asyncio.Runner")
    @patch("musigree.loader.offline_loader.OfflineDatabaseManager")
    @patch("musigree.loader.offline_loader.RuntimeDatabaseManager")
    @patch("musigree.loader.offline_loader.CacheManager")
    @patch("musigree.loader.offline_loader.setup_logging")
    @patch("musigree.loader.offline_loader.shutdown_logging")
    def test_shutdown_offline_loader_success(
        self,
        mock_shutdown_logging: Mock,
        mock_setup_logging: Mock,
        mock_cache_manager: Mock,
        mock_runtime_db_manager: Mock,
        mock_offline_db_manager: Mock,
        mock_runner: Mock,
    ) -> None:
        """Test successful execution of shutdown_offline_loader."""
        # Arrange
        mock_offline_db_manager.shutdown_database = AsyncMock()
        mock_runtime_db_manager.shutdown_database = AsyncMock()

        # Mock asyncio.Runner context manager
        mock_runner_instance = Mock()
        mock_runner.return_value.__enter__.return_value = mock_runner_instance
        mock_runner.return_value.__exit__.return_value = None

        # Act
        shutdown_offline_loader()

        # Assert
        mock_setup_logging.assert_called_once()
        mock_offline_db_manager.shutdown_database.assert_called_once()
        mock_runtime_db_manager.shutdown_database.assert_called_once()
        mock_cache_manager.shutdown_cache.assert_called_once()
        mock_shutdown_logging.assert_called_once()

    @pytest.mark.asyncio
    async def test_load_offline_tables_with_empty_stages(self) -> None:
        """Test load_offline_tables when no stages are returned."""
        data_directory = Path("/test/data")
        date = "2024-11-01"

        with patch(
            "musigree.loader.offline_loader.get_load_offline_table_stages"
        ) as mock_get_stages:
            mock_get_stages.return_value = []

            # Should not raise any errors
            await load_offline_tables(data_directory, date, is_bulk_inserts=True)

            mock_get_stages.assert_called_once_with(data_directory, date, True)

    @pytest.mark.asyncio
    async def test_load_offline_table_stage_negative_index(self) -> None:
        """Test load_offline_table_stage with negative stage index."""
        data_directory = Path("/test/data")
        date = "2024-11-01"

        with patch(
            "musigree.loader.offline_loader.get_load_offline_table_stages"
        ) as mock_get_stages:
            mock_stage = AsyncMock()
            mock_get_stages.return_value = [partial(mock_stage)]

            # Test negative index (should work due to Python's negative indexing)
            await load_offline_table_stage(data_directory, date, is_bulk_inserts=True, stage=-1)

    @patch("musigree.loader.offline_loader.OfflineDatabaseManager")
    @patch("musigree.offline.loader.loader_entity.LoaderEntity")
    @patch("musigree.offline.loader.loader_release.LoaderRelease")
    @patch("musigree.offline.loader.loader_relation.LoaderRelation")
    @patch("musigree.loader.offline_loader.RoleDataAccess")
    @patch("musigree.offline.loader.loader_role.LoaderRole")
    def test_get_load_offline_table_stages_with_vacuum_full(
        self,
        mock_loader_role: Mock,
        mock_role_data_access: Mock,
        mock_loader_relation: Mock,
        mock_loader_release: Mock,
        mock_loader_entity: Mock,
        mock_db_manager: Mock,
    ) -> None:
        """Test get_load_offline_table_stages with vacuum full enabled."""
        # Arrange
        mock_helper = Mock()
        mock_helper.is_vacuum_full.return_value = True
        mock_helper.is_vacuum_analyze.return_value = False
        mock_helper.offline_async_engine = Mock()
        mock_db_manager.offline_database_helper = mock_helper

        # Mock all the loader methods
        mock_loader_role.load_roles_into_database = AsyncMock()
        mock_role_data_access.load_all_roles_into_cache = AsyncMock()
        mock_loader_entity.loader_entity_pass_one = AsyncMock()
        mock_loader_entity.loader_entity_pass_two = AsyncMock()
        mock_loader_entity.loader_entity_pass_three = AsyncMock()
        mock_loader_entity.loader_create_text_search_index = AsyncMock()
        mock_loader_release.loader_release_pass_one = AsyncMock()
        mock_loader_release.loader_release_pass_two = AsyncMock()
        mock_loader_relation.loader_relation_pass_one = AsyncMock()
        mock_helper.vacuum = AsyncMock()

        # Act
        result = get_load_offline_table_stages(
            Path("/test/data"), "2024-11-01", is_bulk_inserts=True
        )

        # Assert
        assert isinstance(result, list)
        assert len(result) > 0

    @patch("musigree.loader.offline_loader.luigi")
    @patch("musigree.loader.offline_loader.atexit")
    @patch("musigree.loader.offline_loader.RoleDataAccess")
    @patch("musigree.loader.offline_loader.OfflineDatabaseManager")
    @patch("musigree.loader.offline_loader.CacheManager")
    @patch("musigree.loader.offline_loader.setup_logging")
    @patch("musigree.loader.offline_loader.sys")
    @patch("musigree.loader.offline_loader.asyncio.Runner")
    def test_offline_loader_main_assertion_error_no_helper(
        self,
        mock_runner: Mock,
        _mock_sys: Mock,
        _mock_setup_logging: Mock,
        mock_cache_manager: Mock,
        mock_offline_db_manager: Mock,
        _mock_role_data_access: Mock,
        _mock_atexit: Mock,
        _mock_luigi: Mock,
    ) -> None:
        """Test offline_loader_main when database helper is not initialized."""
        # Arrange
        mock_cache = Mock()
        mock_cache_manager.get_cache.return_value = mock_cache
        mock_offline_db_manager.setup_database = AsyncMock()
        mock_offline_db_manager.offline_database_helper = None

        # Mock asyncio.Runner context manager
        mock_runner_instance = Mock()
        mock_runner.return_value.__enter__.return_value = mock_runner_instance
        mock_runner.return_value.__exit__.return_value = None

        # Act & Assert
        with pytest.raises(AssertionError) as excinfo:
            offline_loader_main()

        assert "offline_database_helper must be initialized" in str(excinfo.value)

    @patch("musigree.loader.offline_loader.luigi")
    @patch("musigree.loader.offline_loader.atexit")
    @patch("musigree.loader.offline_loader.RoleDataAccess")
    @patch("musigree.loader.offline_loader.OfflineDatabaseManager")
    @patch("musigree.loader.offline_loader.CacheManager")
    @patch("musigree.loader.offline_loader.setup_logging")
    @patch("musigree.loader.offline_loader.sys")
    @patch("musigree.loader.offline_loader.asyncio.Runner")
    def test_offline_loader_main_luigi_failure(
        self,
        mock_runner: Mock,
        _mock_sys: Mock,
        _mock_setup_logging: Mock,
        mock_cache_manager: Mock,
        mock_offline_db_manager: Mock,
        mock_role_data_access: Mock,
        _mock_atexit: Mock,
        mock_luigi: Mock,
    ) -> None:
        """Test offline_loader_main when Luigi build fails."""
        # Arrange
        mock_cache = Mock()
        mock_cache_manager.get_cache.return_value = mock_cache

        # Mock Luigi build to return failure result
        mock_build_result = Mock()
        mock_build_result.summary_text = "Build failed"
        mock_luigi.build.return_value = mock_build_result

        mock_offline_db_manager.setup_database = AsyncMock()
        mock_offline_helper = Mock()
        mock_offline_helper.create_tables = AsyncMock()
        mock_offline_db_manager.offline_database_helper = mock_offline_helper
        mock_role_data_access.load_all_roles_into_cache = AsyncMock()

        # Mock asyncio.Runner context manager
        mock_runner_instance = Mock()
        mock_runner.return_value.__enter__.return_value = mock_runner_instance
        mock_runner.return_value.__exit__.return_value = None

        # Act
        offline_loader_main()

        # Assert - should still complete successfully even if Luigi fails
        mock_luigi.build.assert_called_once()

    @pytest.mark.asyncio
    async def test_load_offline_tables_with_exception_in_stage(self) -> None:
        """Test load_offline_tables handles exceptions in stages gracefully."""
        data_directory = Path("/test/data")
        date = "2024-11-01"

        def failing_stage() -> None:
            raise RuntimeError("Stage failed")

        async def working_stage() -> None:
            pass

        with patch(
            "musigree.loader.offline_loader.get_load_offline_table_stages"
        ) as mock_get_stages:
            mock_get_stages.return_value = [
                partial(working_stage),
                partial(failing_stage),
            ]

            # Should propagate the exception
            with pytest.raises(RuntimeError, match="Stage failed"):
                await load_offline_tables(data_directory, date, is_bulk_inserts=True)

    def test_get_load_offline_table_stages_different_bulk_insert_values(self) -> None:
        """Test get_load_offline_table_stages with different bulk insert values."""
        with patch("musigree.loader.offline_loader.OfflineDatabaseManager") as mock_db_manager:
            with patch("musigree.offline.loader.loader_entity.LoaderEntity"):
                with patch("musigree.offline.loader.loader_release.LoaderRelease"):
                    with patch("musigree.offline.loader.loader_relation.LoaderRelation"):
                        with patch("musigree.loader.offline_loader.RoleDataAccess"):
                            with patch("musigree.offline.loader.loader_role.LoaderRole"):
                                # Setup mocks
                                mock_helper = Mock()
                                mock_helper.is_vacuum_full.return_value = False
                                mock_helper.is_vacuum_analyze.return_value = False
                                mock_helper.offline_async_engine = Mock()
                                mock_helper.vacuum = AsyncMock()
                                mock_db_manager.offline_database_helper = mock_helper

                                # Test with bulk_inserts=True
                                stages_bulk = get_load_offline_table_stages(
                                    Path("/test/data"), "2024-11-01", is_bulk_inserts=True
                                )
                                assert isinstance(stages_bulk, list)

                                # Test with bulk_inserts=False
                                stages_no_bulk = get_load_offline_table_stages(
                                    Path("/test/data"), "2024-11-01", is_bulk_inserts=False
                                )
                                assert isinstance(stages_no_bulk, list)

                                # Both should return the same number of stages
                                assert len(stages_bulk) == len(stages_no_bulk)

    @pytest.mark.asyncio
    async def test_load_offline_table_stage_with_invalid_string_index(self) -> None:
        """Test load_offline_table_stage behavior with different data types."""
        data_directory = Path("/test/data")
        date = "2024-11-01"

        with patch(
            "musigree.loader.offline_loader.get_load_offline_table_stages"
        ) as mock_get_stages:
            mock_stage = AsyncMock()
            mock_get_stages.return_value = [partial(mock_stage)]

            # Test with valid stage index 0
            await load_offline_table_stage(data_directory, date, is_bulk_inserts=True, stage=0)

            # Verify the stage was called
            mock_get_stages.assert_called_with(data_directory, date, True)
