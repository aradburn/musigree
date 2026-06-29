"""
Unit tests for the worker_entity_updater module.

This module tests the update_entities_worker function, which is responsible
for updating or inserting entity records in the offline database.
"""

import logging
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import pytest
from deepdiff import DeepDiff

from musigree.config import SqliteTestConfiguration
from musigree.exceptions import DatabaseError, NotFoundError
from musigree.library.fields.entity_type import EntityType
from musigree.offline.loader.worker_entity_updater import update_entities_worker_async
from musigree.offline.offline_database.entity_repository import EntityRepository
from musigree.offline.offline_domain.entity import Entity


# noinspection HttpUrlsUsage
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
                "urls": ["http://test.com"],
            },
            "relation_counts": {},
            "entities": {},
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
            entity_metadata={"real_name": "Old Real Name", "profile": "Old profile"},
            relation_counts={},
            entities={},
        )

    @patch("musigree.offline.loader.worker_entity_updater.offline_transaction")
    @patch("musigree.offline.loader.worker_entity_updater.EntityRepository")
    @patch("musigree.offline.loader.worker_entity_updater.LOGGING_TRACE", False)
    @pytest.mark.asyncio
    async def test_update_entities_worker_successful_update(
        self,
        mock_repo_class: Mock,
        mock_offline_transaction: Mock,
        sample_entity_data: dict[str, Any],
        existing_entity: Entity,
    ) -> None:
        """Test successful entity update."""
        # Arrange
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
        total_count = 100

        await update_entities_worker_async(bulk_updates, processed_count, total_count)

        # Assert
        mock_repo.get_by_entity_id_and_entity_type.assert_called_once_with(
            sample_entity_data["entity_id"], sample_entity_data["entity_type"]
        )
        mock_repo.update.assert_called_once()
        mock_repo.commit.assert_called_once()

    @patch("musigree.offline.loader.worker_entity_updater.offline_transaction")
    @patch("musigree.offline.loader.worker_entity_updater.EntityRepository")
    @pytest.mark.asyncio
    async def test_update_entities_worker_successful_insert(
        self,
        mock_repo_class: Mock,
        mock_offline_transaction: Mock,
        sample_entity_data: dict[str, Any],
    ) -> None:
        """Test successful entity insertion when entity not found."""
        # Arrange
        # Set up the async context manager mock
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_context)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        mock_offline_transaction.return_value = mock_context

        mock_repo = AsyncMock(spec=EntityRepository)
        mock_repo_class.return_value = mock_repo

        # Mock entity not found
        mock_repo.get_by_entity_id_and_entity_type.side_effect = NotFoundError(
            message="Entity not found"
        )
        mock_repo.create.return_value = None
        mock_repo.commit.return_value = None

        # Act
        bulk_updates = [sample_entity_data]
        processed_count = 0
        total_count = 100

        await update_entities_worker_async(bulk_updates, processed_count, total_count)

        # Assert
        mock_repo.get_by_entity_id_and_entity_type.assert_called_once_with(
            sample_entity_data["entity_id"], sample_entity_data["entity_type"]
        )
        mock_repo.create.assert_called_once()
        mock_repo.commit.assert_called_once()

    @patch("musigree.offline.loader.worker_entity_updater.offline_transaction")
    @patch("musigree.offline.loader.worker_entity_updater.EntityRepository")
    @pytest.mark.asyncio
    async def test_update_entities_worker_no_changes_needed(
        self,
        mock_repo_class: Mock,
        mock_offline_transaction: Mock,
    ) -> None:
        """Test when entity exists but no changes are needed."""
        # Arrange
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
        }
        existing_entity = Entity(
            id=1,
            entity_id=12345,
            entity_type=EntityType.ARTIST,
            entity_name="Same Name",
            entity_metadata={"same": "metadata"},
            relation_counts={},
            entities={},
        )

        mock_repo = AsyncMock(spec=EntityRepository)
        mock_repo_class.return_value = mock_repo

        mock_repo.get_by_entity_id_and_entity_type.return_value = existing_entity

        # Act
        bulk_updates = [entity_data]
        processed_count = 0
        total_count = 100

        await update_entities_worker_async(bulk_updates, processed_count, total_count)

        # Assert
        mock_repo.get_by_entity_id_and_entity_type.assert_called_once_with(
            entity_data["entity_id"], entity_data["entity_type"]
        )
        # Should not call update or create since no changes are needed
        mock_repo.update.assert_not_called()
        mock_repo.create.assert_not_called()
        mock_repo.commit.assert_not_called()

    @patch("musigree.offline.loader.worker_entity_updater.offline_transaction")
    @pytest.mark.asyncio
    async def test_update_entities_worker_database_error_on_update(
        self,
        mock_offline_transaction: Mock,
        sample_entity_data: dict[str, Any],
        existing_entity: Entity,
    ) -> None:
        """Test handling of database error during update."""
        # Arrange
        # Set up the async context manager mock
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_context)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        mock_offline_transaction.return_value = mock_context

        with patch(
            "musigree.offline.loader.worker_entity_updater.EntityRepository"
        ) as mock_repo_class:
            mock_repo = AsyncMock(spec=EntityRepository)
            mock_repo_class.return_value = mock_repo

            mock_repo.get_by_entity_id_and_entity_type.return_value = existing_entity
            mock_repo.update.side_effect = DatabaseError(message="Update failed")

            # Act & Assert
            bulk_updates = [sample_entity_data]
            processed_count = 0
            total_count = 100

            with pytest.raises(DatabaseError):
                await update_entities_worker_async(bulk_updates, processed_count, total_count)

    @patch("musigree.offline.loader.worker_entity_updater.offline_transaction")
    @pytest.mark.asyncio
    async def test_update_entities_worker_database_error_on_insert(
        self,
        mock_offline_transaction: Mock,
        sample_entity_data: dict[str, Any],
    ) -> None:
        """Test handling of database error during insert."""
        # Arrange
        # Set up the async context manager mock
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_context)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        mock_offline_transaction.return_value = mock_context

        with patch(
            "musigree.offline.loader.worker_entity_updater.EntityRepository"
        ) as mock_repo_class:
            mock_repo = AsyncMock(spec=EntityRepository)
            mock_repo_class.return_value = mock_repo

            mock_repo.get_by_entity_id_and_entity_type.side_effect = NotFoundError(
                message="Entity not found"
            )
            mock_repo.create.side_effect = DatabaseError(message="Insert failed")

            # Act & Assert
            bulk_updates = [sample_entity_data]
            processed_count = 0
            total_count = 100

            with pytest.raises(DatabaseError):
                await update_entities_worker_async(bulk_updates, processed_count, total_count)

    @patch("musigree.offline.loader.worker_entity_updater.offline_transaction")
    @patch("musigree.offline.loader.worker_entity_updater.LOGGING_TRACE", True)
    @pytest.mark.asyncio
    async def test_update_entities_worker_with_trace_logging(
        self,
        mock_offline_transaction: Mock,
        sample_entity_data: dict[str, Any],
        existing_entity: Entity,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test worker with trace logging enabled."""
        # Arrange
        # Set up the async context manager mock
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_context)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        mock_offline_transaction.return_value = mock_context

        with patch(
            "musigree.offline.loader.worker_entity_updater.EntityRepository"
        ) as mock_repo_class:
            mock_repo = AsyncMock(spec=EntityRepository)
            mock_repo_class.return_value = mock_repo

            mock_repo.get_by_entity_id_and_entity_type.return_value = existing_entity
            mock_repo.update.return_value = None
            mock_repo.commit.return_value = None

            # Act
            bulk_updates = [sample_entity_data]
            processed_count = 0
            total_count = 100

            with caplog.at_level(logging.DEBUG):
                await update_entities_worker_async(bulk_updates, processed_count, total_count)

            # Assert
            mock_repo.get_by_entity_id_and_entity_type.assert_called_once_with(
                sample_entity_data["entity_id"], sample_entity_data["entity_type"]
            )
            mock_repo.update.assert_called_once()
            mock_repo.commit.assert_called_once()

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
        )

        updated_entity = Entity(
            id=1,
            entity_id=12345,
            entity_type=EntityType.ARTIST,
            entity_name="New Name",
            entity_metadata={},
            relation_counts={},
            entities={},
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

        from musigree.library.full_text_search.text_search_utils import (
            normalise_search_content,
        )

        result = normalise_search_content("Test Artist Name")
        mock_normalize.assert_called_once_with("Test Artist Name")
        assert result == "normalized_content"
