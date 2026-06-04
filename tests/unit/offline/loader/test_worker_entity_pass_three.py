"""
Unit tests for the worker_entity_pass_three module.

This module tests the process_entity_pass_three_worker function and the
worker_pass_three_single function, which are responsible for calculating
and updating relation counts for entities in the offline database.
"""

import logging
from unittest.mock import AsyncMock, patch

import pytest

from musigree.config import SqliteTestConfiguration
from musigree.exceptions import DatabaseError
from musigree.offline.loader.worker_entity_pass_three import (
    process_entity_pass_three_worker_async,
    worker_pass_three_single,
)
from musigree.offline.offline_database.entity_repository import EntityRepository
from musigree.offline.offline_database.entity_table import EntityTable
from musigree.offline.offline_database.relation_repository import RelationRepository


class TestWorkerEntityPassThree:
    """Test class for worker_entity_pass_three module."""

    @pytest.fixture(autouse=True)
    def setup_config(self) -> None:
        """Set up test configuration."""
        self.config = SqliteTestConfiguration()

    @pytest.mark.asyncio
    async def test_worker_pass_three_single_success(self) -> None:
        """Test successful processing of a single entity in pass three."""
        # Arrange
        entity_id = 1
        mock_entity_repo = AsyncMock(spec=EntityRepository)
        mock_relation_repo = AsyncMock(spec=RelationRepository)

        mock_relation_repo.find_role_counts_by_entity.return_value = {
            "performer": 2,
            "producer": 1,
        }

        # Mock entity repository update and commit
        mock_entity_repo.update.return_value = None
        mock_entity_repo.commit.return_value = None

        # Act
        await worker_pass_three_single(mock_entity_repo, mock_relation_repo, entity_id)

        # Assert
        mock_relation_repo.find_role_counts_by_entity.assert_called_once_with(entity_id)

        # Check that update was called with correct relation counts
        expected_counts = {
            "performer": 2,  # Two unique relations
            "producer": 1,  # One unique relation
        }
        mock_entity_repo.update.assert_called_once()

        # Get the actual call arguments
        call_args = mock_entity_repo.update.call_args
        actual_id = call_args[0][0]
        actual_payload = call_args[0][1]

        assert actual_id == entity_id
        assert EntityTable.relation_counts.key in actual_payload
        assert actual_payload[EntityTable.relation_counts.key] == expected_counts

        mock_entity_repo.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_worker_pass_three_single_no_relations(self) -> None:
        """Test processing of an entity with no relations."""
        # Arrange
        entity_id = 1
        mock_entity_repo = AsyncMock(spec=EntityRepository)
        mock_relation_repo = AsyncMock(spec=RelationRepository)

        # Mock relation repository: no relations touching this entity
        mock_relation_repo.find_role_counts_by_entity.return_value = {}

        # Act
        await worker_pass_three_single(mock_entity_repo, mock_relation_repo, entity_id)

        # Assert
        mock_relation_repo.find_role_counts_by_entity.assert_called_once_with(entity_id)

        # Should not call update with empty relation counts
        mock_entity_repo.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_worker_pass_three_single_database_error(self) -> None:
        """Test handling of database error during entity update."""
        # Arrange
        entity_id = 1
        mock_entity_repo = AsyncMock(spec=EntityRepository)
        mock_relation_repo = AsyncMock(spec=RelationRepository)

        mock_relation_repo.find_role_counts_by_entity.return_value = {
            "performer": 2,
            "producer": 1,
        }
        mock_entity_repo.update.side_effect = DatabaseError(message="Update failed")

        # Act & Assert
        with pytest.raises(DatabaseError):
            await worker_pass_three_single(mock_entity_repo, mock_relation_repo, entity_id)

    @pytest.mark.asyncio
    async def test_worker_pass_three_single_duplicate_relations(self) -> None:
        """Test processing when SQL aggregate dedupes duplicate subject-object pairs."""
        # Arrange
        entity_id = 1
        mock_entity_repo = AsyncMock(spec=EntityRepository)
        mock_relation_repo = AsyncMock(spec=RelationRepository)

        mock_relation_repo.find_role_counts_by_entity.return_value = {"performer": 2}

        # Act
        await worker_pass_three_single(mock_entity_repo, mock_relation_repo, entity_id)

        # Assert
        call_args = mock_entity_repo.update.call_args
        actual_payload = call_args[0][1]
        assert actual_payload[EntityTable.relation_counts.key] == {"performer": 2}

    @pytest.mark.asyncio
    async def test_process_entity_pass_three_worker_single_threaded(
        self,
    ) -> None:
        """Test process_entity_pass_three_worker with single-threaded execution."""
        # Arrange
        with patch(
            "musigree.offline.loader.worker_entity_pass_three.offline_transaction"
        ) as mock_offline_transaction:
            mock_context = AsyncMock()
            mock_context.__aenter__ = AsyncMock(return_value=mock_context)
            mock_context.__aexit__ = AsyncMock(return_value=None)
            mock_offline_transaction.return_value = mock_context

            with patch(
                "musigree.offline.loader.worker_entity_pass_three.worker_pass_three_single"
            ) as mock_worker_single:
                mock_worker_single.return_value = None

                # Act
                ids = [1, 2, 3]
                current_total = 0
                total_count = 100

                await process_entity_pass_three_worker_async(ids, current_total, total_count)

                # Assert
                assert mock_worker_single.call_count == len(ids)

    @pytest.mark.asyncio
    async def test_process_entity_pass_three_worker_multi_threaded(
        self,
    ) -> None:
        """Test process_entity_pass_three_worker with multi-threaded execution."""
        # Arrange
        with patch(
            "musigree.offline.loader.worker_entity_pass_three.offline_transaction"
        ) as mock_offline_transaction:
            mock_context = AsyncMock()
            mock_context.__aenter__ = AsyncMock(return_value=mock_context)
            mock_context.__aexit__ = AsyncMock(return_value=None)
            mock_offline_transaction.return_value = mock_context

            with patch(
                "musigree.offline.loader.worker_entity_pass_three.worker_pass_three_single"
            ) as mock_worker_single:
                mock_worker_single.return_value = None

                # Act
                ids = [1, 2, 3]
                current_total = 0
                total_count = 100

                await process_entity_pass_three_worker_async(ids, current_total, total_count)

                # Assert
                assert mock_worker_single.call_count == len(ids)

    @pytest.mark.asyncio
    @patch("musigree.constants.BULK_REPORTING_SIZE", 2)
    async def test_process_entity_pass_three_worker_with_reporting(
        self,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test process_entity_pass_three_worker with progress reporting."""
        # Arrange
        with patch(
            "musigree.offline.loader.worker_entity_pass_three.offline_transaction"
        ) as mock_offline_transaction:
            mock_context = AsyncMock()
            mock_context.__aenter__ = AsyncMock(return_value=mock_context)
            mock_context.__aexit__ = AsyncMock(return_value=None)
            mock_offline_transaction.return_value = mock_context

            with patch(
                "musigree.offline.loader.worker_entity_pass_three.worker_pass_three_single"
            ) as mock_worker_single:
                mock_worker_single.return_value = None

                # Act
                ids = [
                    1,
                    2,
                    3,
                    4,
                    5,
                ]  # 5 entities, should trigger reporting at 2 and 4
                current_total = 0
                total_count = 100

                with caplog.at_level(logging.DEBUG):
                    await process_entity_pass_three_worker_async(ids, current_total, total_count)

                # Assert that the worker was called for all entities
                assert mock_worker_single.call_count == len(ids)

    @pytest.mark.asyncio
    async def test_process_entity_pass_three_worker_database_error_handling(
        self,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test process_entity_pass_three_worker handles database errors properly."""
        # Arrange
        with patch(
            "musigree.offline.loader.worker_entity_pass_three.offline_transaction"
        ) as mock_offline_transaction:
            mock_context = AsyncMock()
            mock_context.__aenter__ = AsyncMock(return_value=mock_context)
            mock_context.__aexit__ = AsyncMock(return_value=None)
            mock_offline_transaction.return_value = mock_context

            with patch(
                "musigree.offline.loader.worker_entity_pass_three.worker_pass_three_single"
            ) as mock_worker_single:
                mock_worker_single.side_effect = DatabaseError(message="Test error")

                # Act & Assert
                ids = [1]
                current_total = 0
                total_count = 100

                with pytest.raises(DatabaseError):
                    await process_entity_pass_three_worker_async(ids, current_total, total_count)
