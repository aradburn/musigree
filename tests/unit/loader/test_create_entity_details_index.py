"""Unit tests for run_offline_create_entity_details_index module."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from musigree.config import SqliteTestConfiguration
from musigree.loader.run_offline_create_entity_details_index import create_entity_details_index


class TestCreateEntityDetailsIndex:
    """Test cases for create_entity_details_index function."""

    @pytest.fixture
    def mock_config(self) -> SqliteTestConfiguration:
        """Create a mock configuration for testing."""
        config = SqliteTestConfiguration()
        config.DATA_DIR = Path("/test/data")
        return config

    def test_create_entity_details_index_success(
        self,
        mock_config: SqliteTestConfiguration,
    ) -> None:
        """Test successful creation of entity details index."""
        with (
            patch(
                "musigree.loader.run_offline_create_entity_details_index.setup_logging"
            ) as mock_setup_logging,
            patch("musigree.loader.run_offline_create_entity_details_index.log_banner"),
            patch(
                "musigree.loader.run_offline_create_entity_details_index.CacheManager"
            ) as mock_cache_manager,
            patch(
                "musigree.loader.run_offline_create_entity_details_index.OfflineDatabaseManager"
            ) as mock_offline_db_manager,
            patch(
                "musigree.loader.run_offline_create_entity_details_index.LoaderEntity"
            ) as mock_loader_entity,
            patch(
                "musigree.loader.run_offline_create_entity_details_index.asyncio.Runner"
            ) as mock_runner,
        ):
            mock_cache_manager.setup_and_clear_cache = AsyncMock()
            mock_offline_db_manager.setup_database = AsyncMock()

            mock_loader_instance = MagicMock()
            mock_loader_instance.loader_create_entity_details_index = AsyncMock()
            mock_loader_entity.return_value = mock_loader_instance

            mock_runner_instance = Mock()
            mock_runner.return_value.__enter__.return_value = mock_runner_instance
            mock_runner.return_value.__exit__.return_value = None

            create_entity_details_index(mock_config)

            mock_setup_logging.assert_called_once()
            mock_offline_db_manager.setup_database.assert_called()

            expected_path = mock_config.DATA_DIR / "entity_details" / "entity_details.data"
            mock_loader_instance.loader_create_entity_details_index.assert_called_once_with(
                expected_path
            )
            assert mock_runner_instance.run.call_count >= 2

    def test_create_entity_details_index_cache_not_set(
        self,
        mock_config: SqliteTestConfiguration,
    ) -> None:
        """Test behavior when cache setup fails."""
        with (
            patch(
                "musigree.loader.run_offline_create_entity_details_index.setup_logging"
            ) as mock_setup_logging,
            patch("musigree.loader.run_offline_create_entity_details_index.log_banner"),
            patch("musigree.loader.run_offline_create_entity_details_index.CacheManager"),
            patch(
                "musigree.loader.run_offline_create_entity_details_index.OfflineDatabaseManager"
            ) as mock_offline_db_manager,
            patch("musigree.loader.run_offline_create_entity_details_index.LoaderEntity"),
            patch(
                "musigree.loader.run_offline_create_entity_details_index.asyncio.Runner"
            ) as mock_runner,
        ):
            mock_offline_db_manager.setup_database = AsyncMock()

            mock_runner_instance = Mock()
            mock_runner_instance.run.side_effect = [
                RuntimeError("Cache not initialized after setup"),
                None,
            ]
            mock_runner.return_value.__enter__.return_value = mock_runner_instance
            mock_runner.return_value.__exit__.return_value = None

            with pytest.raises(SystemExit):
                create_entity_details_index(mock_config)

            mock_setup_logging.assert_called_once()
            mock_offline_db_manager.setup_database.assert_not_called()

    def test_create_entity_details_index_loader_exception(
        self,
        mock_config: SqliteTestConfiguration,
    ) -> None:
        """Test handling of exception in loader."""
        with (
            patch("musigree.loader.run_offline_create_entity_details_index.setup_logging"),
            patch("musigree.loader.run_offline_create_entity_details_index.log_banner"),
            patch(
                "musigree.loader.run_offline_create_entity_details_index.CacheManager"
            ) as mock_cache_manager,
            patch(
                "musigree.loader.run_offline_create_entity_details_index.OfflineDatabaseManager"
            ) as mock_offline_db_manager,
            patch(
                "musigree.loader.run_offline_create_entity_details_index.LoaderEntity"
            ) as mock_loader_entity,
            patch(
                "musigree.loader.run_offline_create_entity_details_index.asyncio.Runner"
            ) as mock_runner,
        ):
            mock_cache_manager.setup_and_clear_cache = AsyncMock()
            mock_offline_db_manager.setup_database = AsyncMock()

            mock_loader_instance = MagicMock()
            mock_loader_instance.loader_create_entity_details_index = AsyncMock(
                side_effect=Exception("Test error")
            )
            mock_loader_entity.return_value = mock_loader_instance

            mock_runner_instance = Mock()
            mock_runner_instance.run.side_effect = Exception("Test error")
            mock_runner.return_value.__enter__.return_value = mock_runner_instance
            mock_runner.return_value.__exit__.return_value = None

            with pytest.raises(Exception, match="Test error"):
                create_entity_details_index(mock_config)

    @patch("musigree.loader.run_offline_create_entity_details_index.create_entity_details_index")
    @patch(
        "musigree.loader.run_offline_create_entity_details_index.PostgresReadOnlyDevelopmentConfiguration"
    )
    def test_main_execution(
        self,
        mock_config_class: Mock,
        mock_create: Mock,
    ) -> None:
        """Test main block execution."""
        import musigree.loader.run_offline_create_entity_details_index as module

        mock_config = MagicMock()
        mock_config_class.return_value = mock_config

        offline_config = module.PostgresReadOnlyDevelopmentConfiguration()
        module.create_entity_details_index(offline_config)

        mock_create.assert_called_once_with(mock_config)
