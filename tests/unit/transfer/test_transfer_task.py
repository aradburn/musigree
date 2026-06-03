"""
Unit tests for the runtime loader tasks.

This module contains comprehensive unit tests for the runtime loader task classes,
which are Luigi tasks responsible for orchestrating data loading from offline
to runtime database.
"""

import asyncio
import datetime
import logging
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import luigi
from luigi.contrib.simulate import RunAnywayTarget

from musigree.transfer.transfer_task import (
    RuntimeLoaderSetupTask,
    RuntimeLoaderTask,
    RuntimeLoaderTaskForDate,
    RuntimeLoaderTaskForDateAndStage,
)


class TestRuntimeLoaderSetupTask:
    """Test class for RuntimeLoaderSetupTask."""

    def test_initialization(self) -> None:
        """Test that RuntimeLoaderSetupTask can be initialized with parameters."""
        data_directory = "/test/data"
        start_date = datetime.date(2023, 1, 1)
        end_date = datetime.date(2023, 1, 31)

        task = RuntimeLoaderSetupTask(
            data_directory=data_directory, start_date=start_date, end_date=end_date
        )

        assert task.data_directory == data_directory
        assert task.start_date == start_date
        assert task.end_date == end_date
        assert isinstance(task, luigi.Task)

    def test_output_returns_run_anyway_target(self) -> None:
        """Test that output() returns a RunAnywayTarget."""
        task = RuntimeLoaderSetupTask(
            data_directory="/test/data",
            start_date=datetime.date(2023, 1, 1),
            end_date=datetime.date(2023, 1, 31),
        )

        output = task.output()

        assert isinstance(output, RunAnywayTarget)

    def test_data_directory_parameter_significance(self) -> None:
        """Test that data_directory parameter is not significant for Luigi."""
        param = RuntimeLoaderSetupTask.data_directory
        assert param.significant is False

    def test_task_family(self) -> None:
        """Test that RuntimeLoaderSetupTask has correct task family."""
        task = RuntimeLoaderSetupTask(
            data_directory="/test/data",
            start_date=datetime.date(2023, 1, 1),
            end_date=datetime.date(2023, 1, 31),
        )

        assert task.task_family == "RuntimeLoaderSetupTask"

    @patch("musigree.transfer.transfer_task.log")
    def test_run_configures_logging_and_yields_next_task(self, _mock_log: Mock) -> None:
        """Test that run() configures logging and yields the next task."""
        task = RuntimeLoaderSetupTask(
            data_directory="/test/data",
            start_date=datetime.date(2023, 1, 1),
            end_date=datetime.date(2023, 1, 31),
        )

        # Mock the output target
        mock_target = Mock()
        with patch.object(task, "output", return_value=mock_target):
            # Mock logging configuration
            with patch("logging.getLogger") as mock_get_logger:
                mock_luigi_logger = Mock()
                mock_interface_logger = Mock()
                mock_musigree_logger = Mock()
                mock_get_logger.side_effect = lambda name: {
                    "luigi": mock_luigi_logger,
                    "luigi-interface": mock_interface_logger,
                    "musigree": mock_musigree_logger,
                }[name]

                # Run the task and collect yielded tasks
                result = list(task.run())

                # Verify logging configuration
                assert mock_luigi_logger.handlers == mock_musigree_logger.handlers
                assert mock_luigi_logger.propagate is False
                mock_luigi_logger.setLevel.assert_called_with(logging.WARNING)

                assert mock_interface_logger.handlers == mock_musigree_logger.handlers
                assert mock_interface_logger.propagate is False
                mock_interface_logger.setLevel.assert_called_with(logging.WARNING)

                # Verify target.done() was called
                mock_target.done.assert_called_once()

                # Verify next task was yielded
                assert len(result) == 1
                assert isinstance(result[0], RuntimeLoaderTask)


class TestRuntimeLoaderTask:
    """Test class for RuntimeLoaderTask."""

    def test_initialization(self) -> None:
        """Test that RuntimeLoaderTask can be initialized with parameters."""
        data_directory = "/test/data"
        start_date = datetime.date(2023, 1, 1)
        end_date = datetime.date(2023, 1, 31)

        task = RuntimeLoaderTask(
            data_directory=data_directory, start_date=start_date, end_date=end_date
        )

        assert task.data_directory == data_directory
        assert task.start_date == start_date
        assert task.end_date == end_date
        assert isinstance(task, luigi.WrapperTask)

    def test_requires_yields_correct_dependencies(self) -> None:
        """Test that requires() yields the correct dependencies."""
        task = RuntimeLoaderTask(
            data_directory="/test/data",
            start_date=datetime.date(2023, 1, 1),
            end_date=datetime.date(2023, 1, 31),
        )

        dependencies = list(task.requires())

        assert len(dependencies) == 2
        assert isinstance(dependencies[0], RuntimeLoaderSetupTask)
        assert isinstance(dependencies[1], RuntimeLoaderTaskForDate)

        # Verify the setup task has correct parameters
        setup_task = dependencies[0]
        # noinspection PyUnresolvedReferences
        assert setup_task.data_directory == task.data_directory
        # noinspection PyUnresolvedReferences
        assert setup_task.start_date == task.start_date
        # noinspection PyUnresolvedReferences
        assert setup_task.end_date == task.end_date

        # Verify the date task has correct parameters
        date_task = dependencies[1]
        # noinspection PyUnresolvedReferences
        assert date_task.data_directory == task.data_directory
        # noinspection PyUnresolvedReferences
        assert date_task.dump_date == task.end_date

    def test_task_family(self) -> None:
        """Test that RuntimeLoaderTask has correct task family."""
        task = RuntimeLoaderTask(
            data_directory="/test/data",
            start_date=datetime.date(2023, 1, 1),
            end_date=datetime.date(2023, 1, 31),
        )

        assert task.task_family == "RuntimeLoaderTask"


class TestRuntimeLoaderTaskForDate:
    """Test class for RuntimeLoaderTaskForDate."""

    def test_initialization(self) -> None:
        """Test that RuntimeLoaderTaskForDate can be initialized with parameters."""
        data_directory = "/test/data"
        dump_date = datetime.date(2023, 1, 15)

        task = RuntimeLoaderTaskForDate(data_directory=data_directory, dump_date=dump_date)

        assert task.data_directory == data_directory
        assert task.dump_date == dump_date
        assert isinstance(task, luigi.WrapperTask)

    def test_priority_calculation(self) -> None:
        """Test that priority is calculated based on date difference."""
        # Use a past date to ensure positive priority
        past_date = datetime.date(2020, 1, 1)
        task = RuntimeLoaderTaskForDate(data_directory="/test/data", dump_date=past_date)

        priority = task.priority

        # Priority should be positive for past dates
        assert isinstance(priority, int)
        assert priority > 0

    @patch("musigree.transfer.transfer_task.get_load_runtime_table_stages")
    def test_requires_yields_stage_tasks(self, mock_get_stages: Mock) -> None:
        """Test that requires() yields stage tasks based on available stages."""
        # Mock stages
        mock_get_stages.return_value = [Mock(), Mock(), Mock()]  # 3 stages

        task = RuntimeLoaderTaskForDate(
            data_directory="/test/data", dump_date=datetime.date(2023, 1, 15)
        )

        dependencies = list(task.requires())

        assert len(dependencies) == 3
        for i, dep in enumerate(dependencies):
            assert isinstance(dep, RuntimeLoaderTaskForDateAndStage)
            assert dep.data_directory == task.data_directory
            assert dep.dump_date == task.dump_date
            assert dep.stage == i

    def test_task_family(self) -> None:
        """Test that RuntimeLoaderTaskForDate has correct task family."""
        task = RuntimeLoaderTaskForDate(
            data_directory="/test/data", dump_date=datetime.date(2023, 1, 15)
        )

        assert task.task_family == "RuntimeLoaderTaskForDate"

    def test_data_directory_parameter_significance(self) -> None:
        """Test that data_directory parameter is not significant for Luigi."""
        param = RuntimeLoaderTaskForDate.data_directory
        assert param.significant is False


class TestRuntimeLoaderTaskForDateAndStage:
    """Test class for RuntimeLoaderTaskForDateAndStage."""

    def test_initialization(self) -> None:
        """Test that RuntimeLoaderTaskForDateAndStage can be initialized with parameters."""
        data_directory = "/test/data"
        dump_date = datetime.date(2023, 1, 15)
        stage = 2

        task = RuntimeLoaderTaskForDateAndStage(
            data_directory=data_directory, dump_date=dump_date, stage=stage
        )

        assert task.data_directory == data_directory
        assert task.dump_date == dump_date
        assert task.stage == stage
        assert isinstance(task, luigi.Task)

    def test_priority_calculation_with_stage(self) -> None:
        """Test that priority is calculated including stage number."""
        past_date = datetime.date(2020, 1, 1)
        task = RuntimeLoaderTaskForDateAndStage(
            data_directory="/test/data", dump_date=past_date, stage=5
        )

        priority = task.priority

        # Priority should be positive and include stage adjustment
        assert isinstance(priority, int)
        assert priority > 0

    def test_requires_returns_previous_stage(self) -> None:
        """Test that requires() returns the previous stage task."""
        task = RuntimeLoaderTaskForDateAndStage(
            data_directory="/test/data", dump_date=datetime.date(2023, 1, 15), stage=3
        )

        dependencies = list(task.requires())

        assert len(dependencies) == 1
        dep = dependencies[0]
        assert isinstance(dep, RuntimeLoaderTaskForDateAndStage)
        assert dep.data_directory == task.data_directory
        assert dep.dump_date == task.dump_date
        assert dep.stage == 2  # Previous stage

    def test_requires_returns_empty_for_stage_zero(self) -> None:
        """Test that requires() returns empty for stage 0."""
        task = RuntimeLoaderTaskForDateAndStage(
            data_directory="/test/data", dump_date=datetime.date(2023, 1, 15), stage=0
        )

        dependencies = list(task.requires())

        assert len(dependencies) == 0

    def test_output_returns_loader_target(self) -> None:
        """Test that output() returns a LoaderTarget."""
        task = RuntimeLoaderTaskForDateAndStage(
            data_directory="/test/data", dump_date=datetime.date(2023, 1, 15), stage=1
        )

        output = task.output()

        # Import here to avoid circular imports in test setup
        from musigree.offline.loader.loader_target import LoaderTarget

        assert isinstance(output, LoaderTarget)

    def test_task_family(self) -> None:
        """Test that RuntimeLoaderTaskForDateAndStage has correct task family."""
        task = RuntimeLoaderTaskForDateAndStage(
            data_directory="/test/data", dump_date=datetime.date(2023, 1, 15), stage=2
        )

        assert task.task_family == "RuntimeLoaderTaskForDateAndStage"

    def test_data_directory_parameter_significance(self) -> None:
        """Test that data_directory parameter is not significant for Luigi."""
        param = RuntimeLoaderTaskForDateAndStage.data_directory
        assert param.significant is False

    @patch("musigree.transfer.transfer_task.get_load_runtime_table_stages")
    @patch("asyncio.new_event_loop")
    @patch("asyncio.set_event_loop")
    @patch("musigree.transfer.transfer_task.log")
    def test_run_executes_stage_successfully(
        self, mock_log: Mock, mock_set_loop: Mock, mock_new_loop: Mock, mock_get_stages: Mock
    ) -> None:
        """Test that run() executes the stage successfully."""
        # Mock the async stage function
        mock_stage_func = AsyncMock()
        mock_get_stages.return_value = [mock_stage_func, Mock(), Mock()]

        # Mock the event loop
        mock_loop = Mock()
        mock_new_loop.return_value = mock_loop
        mock_task = Mock()
        mock_loop.create_task.return_value = mock_task

        # Mock the output target
        mock_output = Mock()
        mock_output.done = Mock()

        task = RuntimeLoaderTaskForDateAndStage(
            data_directory="/test/data", dump_date=datetime.date(2023, 1, 15), stage=0
        )

        with patch.object(task, "output", return_value=mock_output):
            # Mock RuntimeError to trigger new event loop creation
            with patch("asyncio.get_running_loop", side_effect=RuntimeError):
                # Need to patch the second call to get_load_runtime_table_stages in the run method
                with patch(
                    "musigree.loader.run_runtime_loader.get_load_runtime_table_stages", mock_get_stages
                ):
                    task.run()

        # Verify logging
        mock_log.debug.assert_called()

        # Verify event loop setup
        mock_new_loop.assert_called_once()
        mock_set_loop.assert_called_once_with(mock_loop)

        # Verify task creation and execution
        mock_loop.create_task.assert_called_once()
        mock_loop.run_until_complete.assert_called_once_with(mock_task)

    @patch("musigree.transfer.transfer_task.get_load_runtime_table_stages")
    @patch("musigree.transfer.transfer_task.log")
    def test_run_handles_invalid_stage(self, mock_log: Mock, mock_get_stages: Mock) -> None:
        """Test that run() handles invalid stage numbers."""
        mock_stage = AsyncMock()
        mock_get_stages.return_value = [mock_stage]  # Only 1 stage

        task = RuntimeLoaderTaskForDateAndStage(
            data_directory="/test/data",
            dump_date=datetime.date(2023, 1, 15),
            stage=5,  # Invalid stage
        )

        # Mock the event loop setup
        with patch("asyncio.get_running_loop", side_effect=RuntimeError):
            with patch("asyncio.new_event_loop") as mock_new_loop:
                with patch("asyncio.set_event_loop") as _mock_set_loop:
                    mock_loop = Mock()
                    mock_new_loop.return_value = mock_loop

                    mock_task = Mock()
                    mock_task.add_done_callback = Mock()

                    # Run the coroutine when create_task is called so it is not left unawaited
                    def create_task_and_run(coro: Any) -> Mock:
                        run_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(run_loop)
                        try:
                            run_loop.run_until_complete(coro)
                        finally:
                            run_loop.close()
                        return mock_task

                    mock_loop.create_task.side_effect = create_task_and_run
                    mock_loop.run_until_complete.side_effect = lambda _: None

                    with patch(
                        "musigree.loader.run_runtime_loader.get_load_runtime_table_stages",
                        mock_get_stages,
                    ):
                        task.run()

        # Should still run without error but log the invalid stage
        mock_log.debug.assert_called()

    @patch("musigree.transfer.transfer_task.get_load_runtime_table_stages")
    @patch("musigree.transfer.transfer_task.log")
    def test_run_with_existing_event_loop(self, _mock_log: Mock, mock_get_stages: Mock) -> None:
        """Test that run() works with an existing event loop."""
        # Mock the async stage function
        mock_stage_func = AsyncMock()
        mock_get_stages.return_value = [mock_stage_func]

        # Mock the output target
        mock_output = Mock()
        mock_output.done = Mock()

        task = RuntimeLoaderTaskForDateAndStage(
            data_directory="/test/data", dump_date=datetime.date(2023, 1, 15), stage=0
        )

        with patch.object(task, "output", return_value=mock_output):
            # Mock existing event loop (no RuntimeError)
            with patch("asyncio.get_running_loop") as mock_get_loop:
                mock_loop = Mock()
                mock_get_loop.return_value = mock_loop

                # Create a mock task that behaves like an asyncio Task
                mock_task = Mock()
                mock_task.add_done_callback = Mock()
                mock_loop.create_task.return_value = mock_task

                # Make sure the task is properly awaited
                def mock_run_until_complete(_task: Any) -> None:
                    # Just return None since we're mocking the execution
                    return None

                mock_loop.run_until_complete.side_effect = mock_run_until_complete

                # Need to patch the second call to get_load_runtime_table_stages in the run method
                with patch(
                    "musigree.loader.run_runtime_loader.get_load_runtime_table_stages", mock_get_stages
                ):
                    task.run()

        # Verify existing loop was used
        mock_get_loop.assert_called_once()
        mock_loop.create_task.assert_called_once()
        mock_loop.run_until_complete.assert_called_once_with(mock_task)

    @patch("musigree.transfer.transfer_task.get_load_runtime_table_stages")
    @patch("musigree.transfer.transfer_task.log")
    def test_run_handles_runtime_error_during_execution(
        self, mock_log: Mock, mock_get_stages: Mock
    ) -> None:
        """Test that run() handles RuntimeError during task execution."""
        mock_stage = AsyncMock()
        mock_get_stages.return_value = [mock_stage]

        task = RuntimeLoaderTaskForDateAndStage(
            data_directory="/test/data", dump_date=datetime.date(2023, 1, 15), stage=0
        )

        mock_output = Mock()
        mock_output.done = AsyncMock()

        # Mock the event loop setup
        with patch.object(task, "output", return_value=mock_output):
            with patch("asyncio.get_running_loop", side_effect=RuntimeError):
                with patch("asyncio.new_event_loop") as mock_new_loop:
                    with patch("asyncio.set_event_loop") as _mock_set_loop:
                        mock_loop = Mock()
                        mock_new_loop.return_value = mock_loop
                        mock_task = Mock()
                        mock_task.add_done_callback = Mock()

                        # Run the coroutine when create_task is called so it is not left unawaited
                        def create_task_and_run(coro: Any) -> Mock:
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            try:
                                loop.run_until_complete(coro)
                            except RuntimeError:
                                pass  # test expects run_until_complete to raise
                            finally:
                                loop.close()
                            return mock_task

                        mock_loop.create_task.side_effect = create_task_and_run
                        mock_loop.run_until_complete.side_effect = RuntimeError("Test error")

                        with patch(
                            "musigree.loader.run_runtime_loader.get_load_runtime_table_stages",
                            mock_get_stages,
                        ):
                            task.run()  # Should not raise, should handle the exception

        # Verify the exception was logged
        mock_log.exception.assert_called_once()


class TestTransferTaskLogging:
    """Test class for transfer task logging behavior."""

    def test_logger_exists(self) -> None:
        """Test that the module logger is properly configured."""
        from musigree.transfer.transfer_task import log

        assert isinstance(log, logging.Logger)
        assert log.name == "musigree.transfer.transfer_task"


class TestTransferTaskIntegration:
    """Integration-style tests for transfer tasks without external dependencies."""

    @patch("musigree.transfer.transfer_task.get_load_runtime_table_stages")
    def test_full_workflow_integration(self, mock_get_stages: Mock) -> None:
        """Test the complete workflow of runtime loader tasks."""
        mock_stage1 = AsyncMock()
        mock_stage2 = AsyncMock()
        mock_get_stages.return_value = [mock_stage1, mock_stage2]  # 2 stages

        # Create the main task
        main_task = RuntimeLoaderTask(
            data_directory="/integration/test/data",
            start_date=datetime.date(2023, 1, 1),
            end_date=datetime.date(2023, 1, 31),
        )

        # Test the dependency chain
        dependencies = list(main_task.requires())

        assert len(dependencies) == 2
        _setup_task = dependencies[0]
        date_task = dependencies[1]

        # Test date task dependencies
        stage_dependencies = list(date_task.requires())
        assert len(stage_dependencies) == 2

        # Verify stage dependencies are correctly chained
        stage_0 = stage_dependencies[0]
        stage_1 = stage_dependencies[1]

        assert stage_0.stage == 0
        assert stage_1.stage == 1

        # Stage 0 should have no dependencies
        assert len(list(stage_0.requires())) == 0

        # Stage 1 should depend on stage 0
        stage_1_deps = list(stage_1.requires())
        assert len(stage_1_deps) == 1
        assert stage_1_deps[0].stage == 0
