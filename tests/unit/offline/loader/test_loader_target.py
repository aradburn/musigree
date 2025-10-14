"""Unit tests for LoaderTarget class."""

import datetime
from typing import Any
from unittest.mock import patch, MagicMock, AsyncMock

import luigi
import pytest

from musigree.exceptions import NotFoundError
from musigree.offline.loader.loader_target import LoaderTarget


class TestLoaderTarget:
    """Test cases for LoaderTarget class."""

    @pytest.fixture
    def mock_task(self) -> MagicMock:
        """Create a mock Luigi task for testing."""
        task = MagicMock(spec=luigi.Task)
        task.task_id = "test_task_123"
        return task

    @pytest.fixture
    def test_date(self) -> datetime.date:
        """Create a test date."""
        return datetime.date(2023, 12, 15)

    @pytest.fixture
    def loader_target(self, mock_task: MagicMock, test_date: datetime.date) -> LoaderTarget:
        """Create a LoaderTarget instance for testing."""
        return LoaderTarget(mock_task, test_date)

    def test_init(self, mock_task: MagicMock, test_date: datetime.date) -> None:
        """Test LoaderTarget initialization."""
        # Act
        target = LoaderTarget(mock_task, test_date)

        # Assert
        assert target.task_id == "test_task_123"
        assert target.date == test_date

    def test_str(self, loader_target: LoaderTarget) -> None:
        """Test string representation of LoaderTarget."""
        # Act
        result = str(loader_target)

        # Assert
        assert result == "test_task_123"

    def test_get_key(self, loader_target: LoaderTarget) -> None:
        """Test get_key method."""
        # Act
        result = loader_target.get_key()

        # Assert
        assert result == "task-test_task_123-2023-12-15"

    @patch('musigree.offline.loader.loader_target.asyncio.Runner')
    @patch('musigree.offline.loader.loader_target.offline_transaction')
    @patch('musigree.offline.loader.loader_target.MetadataRepository')
    def test_exists_true(
        self,
        mock_metadata_repo: MagicMock,
        _mock_transaction: MagicMock,
        mock_asyncio_runner: MagicMock,
        loader_target: LoaderTarget
    ) -> None:
        """Test exists method when metadata exists."""
        # Arrange
        mock_repo_instance = MagicMock()
        mock_metadata_repo.return_value = mock_repo_instance
        mock_repo_instance.get_by_key = AsyncMock(return_value=MagicMock())
        
        # Mock the Runner context manager
        mock_runner_instance = MagicMock()
        mock_runner_instance.run.return_value = True
        mock_asyncio_runner.return_value.__enter__ = MagicMock(return_value=mock_runner_instance)
        mock_asyncio_runner.return_value.__exit__ = MagicMock(return_value=None)

        # Act
        result = loader_target.exists()

        # Assert
        assert result is True
        mock_asyncio_runner.assert_called_once()
        mock_runner_instance.run.assert_called_once()

    @patch('musigree.offline.loader.loader_target.asyncio.Runner')
    @patch('musigree.offline.loader.loader_target.offline_transaction')
    @patch('musigree.offline.loader.loader_target.MetadataRepository')
    def test_exists_false_not_found(
        self,
        mock_metadata_repo: MagicMock,
        _mock_transaction: MagicMock,
        mock_asyncio_runner: MagicMock,
        loader_target: LoaderTarget
    ) -> None:
        """Test exists method when metadata not found."""
        # Arrange
        mock_repo_instance = MagicMock()
        mock_metadata_repo.return_value = mock_repo_instance
        mock_repo_instance.get_by_key = AsyncMock(side_effect=NotFoundError(("Not found",)))
        
        # Mock the Runner context manager
        mock_runner_instance = MagicMock()
        mock_runner_instance.run.return_value = False
        mock_asyncio_runner.return_value.__enter__ = MagicMock(return_value=mock_runner_instance)
        mock_asyncio_runner.return_value.__exit__ = MagicMock(return_value=None)

        # Act
        result = loader_target.exists()

        # Assert
        assert result is False
        mock_asyncio_runner.assert_called_once()
        mock_runner_instance.run.assert_called_once()

    @patch('musigree.offline.loader.loader_target.asyncio.Runner')
    @patch('musigree.offline.loader.loader_target.offline_transaction')
    @patch('musigree.offline.loader.loader_target.MetadataRepository')
    def test_exists_false_none_returned(
        self,
        mock_metadata_repo: MagicMock,
        _mock_transaction: MagicMock,
        mock_asyncio_runner: MagicMock,
        loader_target: LoaderTarget
    ) -> None:
        """Test exists method when repository returns None."""
        # Arrange
        mock_repo_instance = MagicMock()
        mock_metadata_repo.return_value = mock_repo_instance
        mock_repo_instance.get_by_key = AsyncMock(return_value=None)
        
        # Mock the Runner context manager
        mock_runner_instance = MagicMock()
        # Make sure the runner properly executes the async function
        def mock_run(coro: Any) -> Any:
            # Simulate proper async execution
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(coro)
            finally:
                loop.close()
        mock_runner_instance.run.side_effect = mock_run
        mock_asyncio_runner.return_value.__enter__ = MagicMock(return_value=mock_runner_instance)
        mock_asyncio_runner.return_value.__exit__ = MagicMock(return_value=None)

        # Act
        result = loader_target.exists()

        # Assert
        assert result is False
        mock_asyncio_runner.assert_called_once()
        mock_runner_instance.run.assert_called_once()

    @patch('musigree.offline.loader.loader_target.offline_transaction')
    @patch('musigree.offline.loader.loader_target.MetadataRepository')
    @patch('musigree.offline.loader.loader_target.MetadataUncommitted')
    @patch('musigree.offline.loader.loader_target.datetime')
    async def test_done(
        self,
        mock_datetime: MagicMock,
        mock_metadata_uncommitted: MagicMock,
        mock_metadata_repo: MagicMock,
        _mock_transaction: MagicMock,
        loader_target: LoaderTarget
    ) -> None:
        """Test done method."""
        # Arrange
        test_datetime = datetime.datetime(2023, 12, 15, 10, 30, 0)
        mock_datetime.datetime.now.return_value = test_datetime
        
        mock_metadata_instance = MagicMock()
        mock_metadata_uncommitted.return_value = mock_metadata_instance
        
        mock_repo_instance = MagicMock()
        mock_repo_instance.create = AsyncMock()
        mock_metadata_repo.return_value = mock_repo_instance

        # Act
        await loader_target.done()

        # Assert
        mock_metadata_uncommitted.assert_called_once_with(
            metadata_key="task-test_task_123-2023-12-15",
            metadata_value="done",
            metadata_timestamp=test_datetime
        )
        mock_repo_instance.create.assert_called_once_with(mock_metadata_instance)

    @patch('musigree.offline.loader.loader_target.offline_transaction')
    @patch('musigree.offline.loader.loader_target.MetadataRepository')
    async def test_done_repository_exception(
        self,
        mock_metadata_repo: MagicMock,
        _mock_transaction: MagicMock,
        loader_target: LoaderTarget
    ) -> None:
        """Test done method when repository raises exception."""
        # Arrange
        mock_repo_instance = MagicMock()
        mock_repo_instance.create = AsyncMock(side_effect=Exception("Database error"))
        mock_metadata_repo.return_value = mock_repo_instance

        # Act & Assert
        with pytest.raises(Exception, match="Database error"):
            await loader_target.done()
