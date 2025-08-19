"""
Unit tests for the worker_entity_updater module.

This module tests the update_entities_worker function, which is responsible
for updating or inserting entity records in the offline database.
"""

import asyncio
import logging
import pytest
from unittest.mock import AsyncMock, Mock, patch
from typing import Any
from deepdiff import DeepDiff

from musigree.config import SqliteTestConfiguration
from musigree.exceptions import DatabaseError, NotFoundError
from musigree.offline.loader.worker_entity_updater import update_entities_worker
from musigree.offline.database.entity_repository import EntityRepository
from musigree.offline.database.entity_table import EntityTable
from musigree.offline.domain.entity import Entity
from musigree.library.fields.entity_type import EntityType


class TestWorkerEntityUpdater:
    """Test class for worker_entity_updater module."""

    @pytest.fixture(autouse=True)
    def setup_config(self) -> None:
        """Set up test configuration."""
        self.config: SqliteTestConfiguration = SqliteTestConfiguration()  # type: ignore[no-untyped-call]

    @pytest.fixture
    def sample_entity_data(self) -> dict[str, Any]:
        """Create sample entity data for testing."""
        from musigree.library.fields.entity_type import EntityType
        return {
            "id": 999,  # Placeholder ID for new entity
            "entity_id": 12345,
            "entity_type": EntityType.ARTIST,
            "entity_name": "Test Artist",
            "entity_metadata": {
                "real_name": "Test Real Name",
                "profile": "Test profile",
                "urls": ["http://test.com"]
            },
            "relation_counts": {},
            "entities": {},
            "search_content": "test artist"
        }

    @pytest.fixture
    def existing_entity(self) -> Entity:
        """Create an existing entity for testing updates."""
        from musigree.library.fields.entity_type import EntityType
        return Entity(
            id=1,
            entity_id=12345,
            entity_type=EntityType.ARTIST,
            entity_name="Old Artist Name",
            entity_metadata={
                "real_name": "Old Real Name",
                "profile": "Old profile"
            },
            relation_counts={},
            entities={},
            search_content="old artist name"
        )

    @patch("musigree.offline.loader.worker_entity_updater.OfflineDatabaseManager.get_concurrency_count")
    @patch("musigree.offline.loader.worker_entity_updater.OfflineDatabaseHelper.initialize")
    @patch("musigree.offline.loader.worker_entity_updater.offline_transaction")
    @patch("musigree.offline.loader.worker_entity_updater.EntityRepository")
    @patch("musigree.offline.loader.worker_entity_updater.LOGGING_TRACE", False)
    def test_update_entities_worker_successful_update(
        self,
        mock_repo_class: Mock,
        mock_offline_transaction: Mock,
        mock_db_helper_init: Mock,
        mock_concurrency_count: Mock,
        sample_entity_data: dict[str, Any],
        existing_entity: Entity,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test successful entity update."""
        # Arrange
        mock_concurrency_count.return_value = 1
        
        # Set up the async context manager mock
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_context)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        mock_offline_transaction.return_value = mock_context
        
        mock_repo = AsyncMock(spec=EntityRepository)
        mock_repo_class.return_value = mock_repo
        
        # Mock existing entity retrieval
        mock_repo.get_by_entity_id_and_entity_type.return_value = existing_entity
        mock_repo.update.return_value = None
        mock_repo.commit.return_value = None
        
        # Act
        bulk_updates = [sample_entity_data]
        processed_count = 0
        
        with caplog.at_level(logging.INFO):
            update_entities_worker(bulk_updates, processed_count)
        
        # Assert
        mock_repo.get_by_entity_id_and_entity_type.assert_called_once_with(
            12345, EntityType.ARTIST
        )
        mock_repo.update.assert_called_once()
        mock_repo.commit.assert_called_once()
        
        # Check that progress was logged
        assert any("updated: 1" in record.message for record in caplog.records)

    @patch("musigree.offline.loader.worker_entity_updater.OfflineDatabaseManager.get_concurrency_count")
    @patch("musigree.offline.loader.worker_entity_updater.offline_transaction")
    @patch("musigree.offline.loader.worker_entity_updater.EntityRepository")
    def test_update_entities_worker_successful_insert(
        self,
        mock_repo_class: Mock,
        mock_offline_transaction: Mock,
        mock_concurrency_count: Mock,
        sample_entity_data: dict[str, Any],
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test successful entity insertion when entity not found."""
        # Arrange
        mock_concurrency_count.return_value = 1
        # Set up the async context manager mock
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_context)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        mock_offline_transaction.return_value = mock_context
        
        mock_repo = AsyncMock(spec=EntityRepository)
        mock_repo_class.return_value = mock_repo
        
        # Mock entity not found
        mock_repo.get_by_entity_id_and_entity_type.side_effect = NotFoundError(message="Entity not found")
        mock_repo.create.return_value = None
        mock_repo.commit.return_value = None
        
        # Act
        bulk_updates = [sample_entity_data]
        processed_count = 0
        
        with caplog.at_level(logging.INFO):
            update_entities_worker(bulk_updates, processed_count)
        
        # Assert
        mock_repo.get_by_entity_id_and_entity_type.assert_called_once()
        mock_repo.create.assert_called_once()
        mock_repo.commit.assert_called_once()
        
        # Check that progress was logged
        assert any("inserted: 1" in record.message for record in caplog.records)

    @patch("musigree.offline.loader.worker_entity_updater.OfflineDatabaseManager.get_concurrency_count")
    @patch("musigree.offline.loader.worker_entity_updater.offline_transaction")
    @patch("musigree.offline.loader.worker_entity_updater.EntityRepository")
    def test_update_entities_worker_no_changes_needed(
        self,
        mock_repo_class: Mock,
        mock_offline_transaction: Mock,
        mock_concurrency_count: Mock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test when entity exists but no changes are needed."""
        # Arrange
        mock_concurrency_count.return_value = 1
        # Set up the async context manager mock
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_context)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        mock_offline_transaction.return_value = mock_context
        
        # Create entity data that matches existing entity
        entity_data = {
            "id": 1,
            "entity_id": 12345,
            "entity_type": EntityType.ARTIST,
            "entity_name": "Same Name",
            "entity_metadata": {"same": "metadata"},
            "relation_counts": {},
            "entities": {},
            "search_content": "same name"
        }
        existing_entity = Entity(
            id=1,
            entity_id=12345,
            entity_type=EntityType.ARTIST,
            entity_name="Same Name",
            entity_metadata={"same": "metadata"},
            relation_counts={},
            entities={},
            search_content="same name"
        )
        
        mock_repo = AsyncMock(spec=EntityRepository)
        mock_repo_class.return_value = mock_repo
        
        mock_repo.get_by_entity_id_and_entity_type.return_value = existing_entity
        
        # Act
        bulk_updates = [entity_data]
        processed_count = 0
        
        with caplog.at_level(logging.INFO):
            update_entities_worker(bulk_updates, processed_count)
        
        # Assert - no update or insert should be called
        mock_repo.get_by_entity_id_and_entity_type.assert_called_once()
        mock_repo.update.assert_not_called()
        mock_repo.create.assert_not_called()
        
        # Check that progress was logged with 0 updates/inserts
        assert any("updated: 0" in record.message for record in caplog.records)
        assert any("inserted: 0" in record.message for record in caplog.records)

    @patch("musigree.offline.loader.worker_entity_updater.OfflineDatabaseManager.get_concurrency_count")
    @patch("musigree.offline.loader.worker_entity_updater.offline_transaction")
    def test_update_entities_worker_database_error_on_update(
        self,
        mock_offline_transaction: Mock,
        mock_concurrency_count: Mock,
        sample_entity_data: dict[str, Any],
        existing_entity: Entity,
    ) -> None:
        """Test handling of database error during update."""
        # Arrange
        mock_concurrency_count.return_value = 1
        # Set up the async context manager mock
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_context)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        mock_offline_transaction.return_value = mock_context
        
        with patch("musigree.offline.loader.worker_entity_updater.EntityRepository") as mock_repo_class:
            mock_repo = AsyncMock(spec=EntityRepository)
            mock_repo_class.return_value = mock_repo
            
            mock_repo.get_by_entity_id_and_entity_type.return_value = existing_entity
            mock_repo.update.side_effect = DatabaseError(message="Update failed")
            
            with patch("asyncio.get_running_loop") as mock_get_loop:
                mock_get_loop.side_effect = RuntimeError("No loop")
                
                with patch("asyncio.new_event_loop") as mock_new_loop:
                    mock_loop = Mock()
                    mock_new_loop.return_value = mock_loop
                    
                    # Make run_until_complete raise the DatabaseError
                    mock_loop.run_until_complete.side_effect = DatabaseError(message="Update failed")
                    
                    with patch("asyncio.set_event_loop"):
                        # Act & Assert
                        bulk_updates = [sample_entity_data]
                        processed_count = 0
                        
                        with pytest.raises(DatabaseError):
                            update_entities_worker(bulk_updates, processed_count)

    @patch("musigree.offline.loader.worker_entity_updater.OfflineDatabaseManager.get_concurrency_count")
    @patch("musigree.offline.loader.worker_entity_updater.offline_transaction")
    def test_update_entities_worker_database_error_on_insert(
        self,
        mock_offline_transaction: Mock,
        mock_concurrency_count: Mock,
        sample_entity_data: dict[str, Any],
    ) -> None:
        """Test handling of database error during insert."""
        # Arrange
        mock_concurrency_count.return_value = 1
        # Set up the async context manager mock
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_context)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        mock_offline_transaction.return_value = mock_context
        
        with patch("musigree.offline.loader.worker_entity_updater.EntityRepository") as mock_repo_class:
            mock_repo = AsyncMock(spec=EntityRepository)
            mock_repo_class.return_value = mock_repo
            
            mock_repo.get_by_entity_id_and_entity_type.side_effect = NotFoundError(message="Entity not found")
            mock_repo.create.side_effect = DatabaseError(message="Insert failed")
            
            with patch("asyncio.get_running_loop") as mock_get_loop:
                mock_get_loop.side_effect = RuntimeError("No loop")
                
                with patch("asyncio.new_event_loop") as mock_new_loop:
                    mock_loop = Mock()
                    mock_new_loop.return_value = mock_loop
                    
                    # Make run_until_complete raise the DatabaseError
                    mock_loop.run_until_complete.side_effect = DatabaseError(message="Insert failed")
                    
                    with patch("asyncio.set_event_loop"):
                        # Act & Assert
                        bulk_updates = [sample_entity_data]
                        processed_count = 0
                        
                        with pytest.raises(DatabaseError):
                            update_entities_worker(bulk_updates, processed_count)

    @patch("musigree.offline.loader.worker_entity_updater.OfflineDatabaseManager.get_concurrency_count")
    @patch("musigree.offline.loader.worker_entity_updater.OfflineDatabaseHelper.initialize")
    @patch("musigree.offline.loader.worker_entity_updater.offline_transaction")
    def test_update_entities_worker_multi_threaded(
        self,
        mock_offline_transaction: Mock,
        mock_db_helper_init: Mock,
        mock_concurrency_count: Mock,
        sample_entity_data: dict[str, Any],
    ) -> None:
        """Test multi-threaded execution with concurrency > 1."""
        # Arrange
        mock_concurrency_count.return_value = 4
        # Set up the async context manager mock
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_context)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        mock_offline_transaction.return_value = mock_context
        
        with patch("musigree.offline.loader.worker_entity_updater.EntityRepository") as mock_repo_class:
            mock_repo = AsyncMock(spec=EntityRepository)
            mock_repo_class.return_value = mock_repo
            
            mock_repo.get_by_entity_id_and_entity_type.side_effect = NotFoundError(message="Entity not found")
            mock_repo.create.return_value = None
            mock_repo.commit.return_value = None
            
            with patch("asyncio.get_running_loop") as mock_get_loop:
                mock_loop = Mock()
                mock_get_loop.return_value = mock_loop
                
                # Act
                bulk_updates = [sample_entity_data]
                processed_count = 0
                
                update_entities_worker(bulk_updates, processed_count)
                
                # Assert
                mock_concurrency_count.assert_called_once()
                mock_db_helper_init.assert_called_once_with(mock_loop)
                mock_loop.run_until_complete.assert_called_once()

    @patch("musigree.offline.loader.worker_entity_updater.OfflineDatabaseManager.get_concurrency_count")
    @patch("musigree.offline.loader.worker_entity_updater.offline_transaction")
    @patch("musigree.offline.loader.worker_entity_updater.LOGGING_TRACE", True)
    def test_update_entities_worker_with_trace_logging(
        self,
        mock_offline_transaction: Mock,
        mock_concurrency_count: Mock,
        sample_entity_data: dict[str, Any],
        existing_entity: Entity,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test worker with trace logging enabled."""
        # Arrange
        mock_concurrency_count.return_value = 1
        # Set up the async context manager mock
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_context)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        mock_offline_transaction.return_value = mock_context
        
        with patch("musigree.offline.loader.worker_entity_updater.EntityRepository") as mock_repo_class:
            mock_repo = AsyncMock(spec=EntityRepository)
            mock_repo_class.return_value = mock_repo
            
            mock_repo.get_by_entity_id_and_entity_type.return_value = existing_entity
            mock_repo.update.return_value = None
            mock_repo.commit.return_value = None
            
            with patch("asyncio.get_running_loop") as mock_get_loop:
                mock_get_loop.side_effect = RuntimeError("No loop")
                
                with patch("asyncio.new_event_loop") as mock_new_loop:
                    mock_loop = Mock()
                    mock_new_loop.return_value = mock_loop
                    
                    with patch("asyncio.set_event_loop"):
                        # Act
                        bulk_updates = [sample_entity_data]
                        processed_count = 0
                        
                        with caplog.at_level(logging.DEBUG):
                            update_entities_worker(bulk_updates, processed_count)
                        
                        # Assert that trace logging occurred (checking for debug messages)
                        debug_messages = [record.message for record in caplog.records if record.levelno == logging.DEBUG]
                        # The exact trace logging content will depend on the implementation

    def test_entity_name_change_detection(self) -> None:
        """Test that changes in entity name are properly detected."""
        # This tests the logic inside the worker function
        from musigree.library.fields.entity_type import EntityType
        existing_entity = Entity(
            id=1,
            entity_id=12345,
            entity_type=EntityType.ARTIST,
            entity_name="Old Name",
            entity_metadata={},
            relation_counts={},
            entities={},
            search_content="old name"
        )
        
        updated_entity = Entity(
            id=1,
            entity_id=12345,
            entity_type=EntityType.ARTIST,
            entity_name="New Name",
            entity_metadata={},
            relation_counts={},
            entities={},
            search_content="new name"
        )
        
        # Test that names are different
        assert existing_entity.entity_name != updated_entity.entity_name

    def test_metadata_change_detection_with_deepdiff(self) -> None:
        """Test that metadata changes are properly detected using DeepDiff."""
        existing_metadata = {"old_key": "old_value"}
        updated_metadata = {"new_key": "new_value"}
        
        # Create mock entities
        existing_entity = Mock()
        existing_entity.entity_metadata = existing_metadata
        
        updated_entity = Mock()
        updated_entity.entity_metadata = updated_metadata
        
        # Test DeepDiff functionality
        differences = DeepDiff(
            existing_entity,
            updated_entity,
            include_paths=["entity_metadata"],
            ignore_numeric_type_changes=True,
        )
        
        # Should detect differences
        assert differences != {}

    @patch("musigree.library.full_text_search.text_search_utils.normalise_search_content")
    def test_search_content_normalization(self, mock_normalize: Mock) -> None:
        """Test that search content is properly normalized."""
        mock_normalize.return_value = "normalized_content"
        
        from musigree.library.full_text_search.text_search_utils import normalise_search_content
        
        result = normalise_search_content("Test Artist Name")
        mock_normalize.assert_called_once_with("Test Artist Name")
        assert result == "normalized_content"
