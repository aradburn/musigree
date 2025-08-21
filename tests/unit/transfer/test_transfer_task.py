"""
Unit tests for the TransferTask class.

This module contains comprehensive unit tests for the TransferTask class,
which is a Luigi task responsible for orchestrating data transfer from
the offline database to the runtime database.
"""

import logging
from unittest.mock import Mock, patch

import luigi
from luigi.contrib.simulate import RunAnywayTarget

from musigree.transfer.transfer_task import TransferTask


class TestTransferTask:
    """Test class for TransferTask."""

    def test_transfer_task_initialization(self) -> None:
        """Test that TransferTask can be initialized with parameters."""
        data_directory = "/test/data"
        task = TransferTask(data_directory=data_directory)

        assert task.data_directory == data_directory
        assert isinstance(task, luigi.Task)

    def test_output_returns_run_anyway_target(self) -> None:
        """Test that output() returns a RunAnywayTarget."""
        task = TransferTask(data_directory="/test/data")

        output = task.output()

        assert isinstance(output, RunAnywayTarget)

    def test_requires_returns_none(self) -> None:
        """Test that requires() returns None (no dependencies)."""
        task = TransferTask(data_directory="/test/data")

        requires = task.requires()

        assert requires is None

    def test_priority_returns_very_low_value(self) -> None:
        """Test that priority property returns a very low value."""
        task = TransferTask(data_directory="/test/data")

        priority = task.priority

        assert priority == -1000000000

    @patch("musigree.transfer.transfer_task.log")
    def test_run_logs_task_start(self, mock_log: Mock) -> None:
        """Test that run() logs the task start."""
        task = TransferTask(data_directory="/test/data")

        # Mock the output target
        mock_target = Mock()
        with patch.object(task, "output", return_value=mock_target):
            task.run()

        # Verify logging was called
        mock_log.debug.assert_called_once_with(f"Running transfer task: {task.task_id}")

        # Verify target.done() was called
        mock_target.done.assert_called_once()

    def test_run_calls_output_done(self) -> None:
        """Test that run() calls done() on the output target."""
        task = TransferTask(data_directory="/test/data")

        # Mock the output target
        mock_target = Mock()
        with patch.object(task, "output", return_value=mock_target):
            task.run()

        # Verify target.done() was called
        mock_target.done.assert_called_once()

    def test_data_directory_parameter_significance(self) -> None:
        """Test that data_directory parameter is not significant for Luigi."""
        # This tests that the parameter was configured with significant=False
        # We can test this by checking the parameter definition
        param = TransferTask.data_directory
        assert param.significant is False

    def test_task_id_generation(self) -> None:
        """Test that task IDs are generated correctly."""
        task1 = TransferTask(data_directory="/test/data1")
        task2 = TransferTask(data_directory="/test/data2")

        # Since data_directory is not significant for Luigi, tasks with different
        # data_directory values are considered equal by Luigi's design
        # But they are still different object instances
        assert task1 is not task2
        # Task IDs should be the same because data_directory is not significant
        assert task1.task_id == task2.task_id

    def test_multiple_runs_idempotent(self) -> None:
        """Test that multiple runs of the same task work correctly."""
        task = TransferTask(data_directory="/test/data")

        # Mock the output target
        mock_target = Mock()
        with patch.object(task, "output", return_value=mock_target):
            # Run the task multiple times
            task.run()
            task.run()

        # Verify target.done() was called twice
        assert mock_target.done.call_count == 2


class TestTransferTaskLogging:
    """Test class for TransferTask logging behavior."""

    def test_logger_exists(self) -> None:
        """Test that the module logger is properly configured."""
        from musigree.transfer.transfer_task import log

        assert isinstance(log, logging.Logger)
        assert log.name == "musigree.transfer.transfer_task"

    @patch("musigree.transfer.transfer_task.log")
    def test_run_logging_with_different_data_directories(self, mock_log: Mock) -> None:
        """Test that run() logs correctly with different data directories."""
        data_dir = "/custom/path/to/data"
        task = TransferTask(data_directory=data_dir)

        # Mock the output target
        mock_target = Mock()
        with patch.object(task, "output", return_value=mock_target):
            task.run()

        # Verify the correct task ID was logged
        mock_log.debug.assert_called_once()
        call_args = mock_log.debug.call_args[0][0]
        assert "Running transfer task:" in call_args
        assert task.task_id in call_args


class TestTransferTaskIntegration:
    """Integration-style tests for TransferTask without external dependencies."""

    def test_full_task_workflow(self) -> None:
        """Test the complete workflow of a TransferTask."""
        task = TransferTask(data_directory="/integration/test/data")

        # Verify initial state
        assert task.requires() is None
        assert task.priority == -1000000000

        # Verify output
        output = task.output()
        assert isinstance(output, RunAnywayTarget)

        # Mock the output method to return a mock target with done method
        mock_target = Mock()
        with patch.object(task, "output", return_value=mock_target):
            with patch("musigree.transfer.transfer_task.log") as mock_log:
                task.run()

                mock_log.debug.assert_called_once()
                mock_target.done.assert_called_once()

    def test_luigi_task_registration(self) -> None:
        """Test that TransferTask is properly registered as a Luigi task."""
        task = TransferTask(data_directory="/test/data")

        # Verify it's a proper Luigi task
        assert hasattr(task, "task_id")
        assert hasattr(task, "task_family")
        assert callable(task.run)
        assert callable(task.output)
        assert callable(task.requires)

        # Verify task family
        assert task.task_family == "TransferTask"
