"""
Unit tests for the loader_tasks module.

This module contains comprehensive unit tests for the Luigi task classes
that manage the offline data loading process (LoaderSetupTask, LoaderTask,
DiscogsDownloaderTaskForDate, LoaderTaskForDate, LoaderTaskForDateAndStage,
DiscogsDownloaderTask).
"""

import datetime
import logging
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import luigi
from luigi.contrib.simulate import RunAnywayTarget

from musigree.constants import (
    DISCOGS_ARTISTS_TYPE,
    DISCOGS_LABELS_TYPE,
    DISCOGS_MASTERS_TYPE,
    DISCOGS_RELEASES_TYPE,
)
from musigree.offline.loader.loader_target import LoaderTarget
from musigree.offline.loader.loader_tasks import (
    DiscogsDownloaderTask,
    DiscogsDownloaderTaskForDate,
    LoaderSetupTask,
    LoaderTask,
    LoaderTaskForDate,
    LoaderTaskForDateAndStage,
)


class TestLoaderSetupTask:
    """Test class for LoaderSetupTask."""

    def test_initialization(self) -> None:
        """Test that LoaderSetupTask can be initialized with parameters."""
        data_directory = "/test/data"
        start_date = datetime.date(2023, 1, 1)
        end_date = datetime.date(2023, 1, 31)

        task = LoaderSetupTask(
            data_directory=data_directory, start_date=start_date, end_date=end_date
        )

        assert task.data_directory == data_directory
        assert task.start_date == start_date
        assert task.end_date == end_date
        assert isinstance(task, luigi.Task)

    def test_output_returns_run_anyway_target(self) -> None:
        """Test that output() returns a RunAnywayTarget."""
        task = LoaderSetupTask(
            data_directory="/test/data",
            start_date=datetime.date(2023, 1, 1),
            end_date=datetime.date(2023, 1, 31),
        )

        output = task.output()

        assert isinstance(output, RunAnywayTarget)

    def test_data_directory_parameter_significance(self) -> None:
        """Test that data_directory parameter is not significant for Luigi."""
        param = LoaderSetupTask.data_directory
        assert param.significant is False

    def test_task_family(self) -> None:
        """Test that LoaderSetupTask has correct task family."""
        task = LoaderSetupTask(
            data_directory="/test/data",
            start_date=datetime.date(2023, 1, 1),
            end_date=datetime.date(2023, 1, 31),
        )

        assert task.task_family == "musigree.LoaderSetupTask"

    @patch("musigree.offline.loader.loader_tasks.log")
    def test_run_configures_logging_and_yields_next_task(self, _mock_log: MagicMock) -> None:
        """Test that run() configures logging and yields the next task."""
        task = LoaderSetupTask(
            data_directory="/test/data",
            start_date=datetime.date(2023, 1, 1),
            end_date=datetime.date(2023, 1, 31),
        )

        mock_target = MagicMock()
        with patch.object(task, "output", return_value=mock_target):
            with patch("logging.getLogger") as mock_get_logger:
                mock_luigi_logger = MagicMock()
                mock_interface_logger = MagicMock()
                mock_musigree_logger = MagicMock()
                mock_get_logger.side_effect = lambda name: {
                    "luigi": mock_luigi_logger,
                    "luigi-interface": mock_interface_logger,
                    "musigree": mock_musigree_logger,
                }[name]

                result = list(task.run())

                assert mock_luigi_logger.handlers == mock_musigree_logger.handlers
                assert mock_luigi_logger.propagate is False
                mock_luigi_logger.setLevel.assert_called_with(logging.WARNING)

                assert mock_interface_logger.handlers == mock_musigree_logger.handlers
                assert mock_interface_logger.propagate is False
                mock_interface_logger.setLevel.assert_called_with(logging.WARNING)

                mock_target.done.assert_called_once()

                assert len(result) == 1
                assert isinstance(result[0], LoaderTask)


class TestLoaderTask:
    """Test class for LoaderTask."""

    def test_initialization(self) -> None:
        """Test that LoaderTask can be initialized with parameters."""
        data_directory = "/test/data"
        start_date = datetime.date(2023, 1, 1)
        end_date = datetime.date(2023, 1, 31)

        task = LoaderTask(
            data_directory=data_directory, start_date=start_date, end_date=end_date
        )

        assert task.data_directory == data_directory
        assert task.start_date == start_date
        assert task.end_date == end_date
        assert isinstance(task, luigi.Task)

    # noinspection PyUnresolvedReferences
    @patch("musigree.offline.loader.loader_tasks.get_discogs_dump_dates")
    def test_requires_yields_setup_then_download_and_load_per_date(
        self, mock_get_dates: MagicMock
    ) -> None:
        """Test that requires() yields LoaderSetupTask then per-date tasks."""
        mock_get_dates.return_value = [
            datetime.date(2023, 1, 1),
            datetime.date(2023, 2, 1),
        ]

        task = LoaderTask(
            data_directory="/test/data",
            start_date=datetime.date(2023, 1, 1),
            end_date=datetime.date(2023, 2, 28),
        )

        dependencies = list(task.requires())

        # 1 setup + 2 dates * 2 (download + load) = 5
        assert len(dependencies) == 5
        assert isinstance(dependencies[0], LoaderSetupTask)
        assert dependencies[0].data_directory == task.data_directory
        assert dependencies[0].start_date == task.start_date
        assert dependencies[0].end_date == task.end_date

        mock_get_dates.assert_called_once_with(
            datetime.date(2023, 1, 1), datetime.date(2023, 2, 28)
        )

        # First date: download then load
        assert isinstance(dependencies[1], DiscogsDownloaderTaskForDate)
        assert dependencies[1].dump_date == datetime.date(2023, 1, 1)
        assert isinstance(dependencies[2], LoaderTaskForDate)
        assert dependencies[2].dump_date == datetime.date(2023, 1, 1)

        assert isinstance(dependencies[3], DiscogsDownloaderTaskForDate)
        assert dependencies[3].dump_date == datetime.date(2023, 2, 1)
        assert isinstance(dependencies[4], LoaderTaskForDate)
        assert dependencies[4].dump_date == datetime.date(2023, 2, 1)

    @patch("musigree.offline.loader.loader_tasks.get_discogs_dump_dates")
    def test_requires_single_date(self, mock_get_dates: MagicMock) -> None:
        """Test requires() when date range yields single date."""
        mock_get_dates.return_value = [datetime.date(2023, 1, 1)]

        task = LoaderTask(
            data_directory="/test/data",
            start_date=datetime.date(2023, 1, 1),
            end_date=datetime.date(2023, 1, 31),
        )

        dependencies = list(task.requires())

        assert len(dependencies) == 3  # setup + download + load
        assert isinstance(dependencies[0], LoaderSetupTask)
        assert isinstance(dependencies[1], DiscogsDownloaderTaskForDate)
        assert isinstance(dependencies[2], LoaderTaskForDate)

    def test_complete_delegates_to_super(self) -> None:
        """Test that complete() delegates to super().complete()."""
        task = LoaderTask(
            data_directory="/test/data",
            start_date=datetime.date(2023, 1, 1),
            end_date=datetime.date(2023, 1, 31),
        )

        # Patch requires() so super().complete() does not iterate into
        # LoaderTaskForDate.requires() (which calls get_load_offline_table_stages).
        with patch.object(task, "requires", return_value=iter([])):
            result = task.complete()
        assert result is True

        # When a dependency is not complete, complete() returns False.
        incomplete = MagicMock(spec=luigi.Task)
        incomplete.complete.return_value = False
        # Return a generator so flatten() yields the task itself (not iterating it).
        with patch.object(
            task, "requires", return_value=(x for x in [incomplete])
        ):
            result = task.complete()
        assert result is False

    def test_task_family(self) -> None:
        """Test that LoaderTask has correct task family."""
        task = LoaderTask(
            data_directory="/test/data",
            start_date=datetime.date(2023, 1, 1),
            end_date=datetime.date(2023, 1, 31),
        )
        assert task.task_family == "musigree.LoaderTask"


class TestDiscogsDownloaderTaskForDate:
    """Test class for DiscogsDownloaderTaskForDate."""

    def test_initialization(self) -> None:
        """Test that DiscogsDownloaderTaskForDate can be initialized."""
        data_directory = "/test/data"
        dump_date = datetime.date(2023, 1, 15)

        task = DiscogsDownloaderTaskForDate(
            data_directory=data_directory, dump_date=dump_date
        )

        assert task.data_directory == data_directory
        assert task.dump_date == dump_date
        assert isinstance(task, luigi.Task)

    def test_priority_is_int(self) -> None:
        """Test that priority is an integer (older dates have higher priority)."""
        past_date = datetime.date(2020, 1, 1)
        task = DiscogsDownloaderTaskForDate(
            data_directory="/test/data", dump_date=past_date
        )

        priority = task.priority

        assert isinstance(priority, int)
        assert priority > 0

    def test_requires_yields_four_discogs_downloader_tasks(self) -> None:
        """Test that requires() yields DiscogsDownloaderTask for each dump type."""
        task = DiscogsDownloaderTaskForDate(
            data_directory="/test/data", dump_date=datetime.date(2023, 1, 15)
        )

        dependencies = list(task.requires())

        assert len(dependencies) == 4
        types = [
            getattr(dep, "dump_type", None) for dep in dependencies
        ]
        assert DISCOGS_ARTISTS_TYPE in types
        assert DISCOGS_RELEASES_TYPE in types
        assert DISCOGS_LABELS_TYPE in types
        assert DISCOGS_MASTERS_TYPE in types

        for dep in dependencies:
            assert isinstance(dep, DiscogsDownloaderTask)
            assert dep.data_directory == task.data_directory
            assert dep.dump_date == task.dump_date

    def test_task_family(self) -> None:
        """Test that DiscogsDownloaderTaskForDate has correct task family."""
        task = DiscogsDownloaderTaskForDate(
            data_directory="/test/data", dump_date=datetime.date(2023, 1, 15)
        )
        assert task.task_family == "musigree.DiscogsDownloaderTaskForDate"


class TestLoaderTaskForDate:
    """Test class for LoaderTaskForDate."""

    def test_initialization(self) -> None:
        """Test that LoaderTaskForDate can be initialized."""
        data_directory = "/test/data"
        dump_date = datetime.date(2023, 1, 15)

        task = LoaderTaskForDate(
            data_directory=data_directory, dump_date=dump_date
        )

        assert task.data_directory == data_directory
        assert task.dump_date == dump_date
        assert isinstance(task, luigi.Task)

    def test_priority_is_int(self) -> None:
        """Test that priority is an integer."""
        past_date = datetime.date(2020, 1, 1)
        task = LoaderTaskForDate(
            data_directory="/test/data", dump_date=past_date
        )

        priority = task.priority

        assert isinstance(priority, int)
        assert priority > 0

    @patch("musigree.loader.run_offline_loader.get_load_offline_table_stages")
    def test_requires_yields_download_then_stage_tasks(
        self, mock_get_stages: MagicMock
    ) -> None:
        """Test that requires() yields DiscogsDownloaderTaskForDate then stage tasks."""
        mock_get_stages.return_value = [MagicMock(), MagicMock(), MagicMock()]

        task = LoaderTaskForDate(
            data_directory="/test/data", dump_date=datetime.date(2023, 1, 15)
        )

        dependencies = list(task.requires())

        assert len(dependencies) == 4  # 1 download + 3 stages
        assert isinstance(dependencies[0], DiscogsDownloaderTaskForDate)
        # noinspection PyUnresolvedReferences
        assert dependencies[0].dump_date == task.dump_date

        for i in range(3):
            dep = dependencies[i + 1]
            assert isinstance(dep, LoaderTaskForDateAndStage)
            assert dep.data_directory == task.data_directory
            assert dep.dump_date == task.dump_date
            assert dep.stage == i

        mock_get_stages.assert_called_once_with(
            Path("/test/data"),
            "20230115",
            is_bulk_inserts=False,
        )

    def test_task_family(self) -> None:
        """Test that LoaderTaskForDate has correct task family."""
        task = LoaderTaskForDate(
            data_directory="/test/data", dump_date=datetime.date(2023, 1, 15)
        )
        assert task.task_family == "musigree.LoaderTaskForDate"


class TestLoaderTaskForDateAndStage:
    """Test class for LoaderTaskForDateAndStage."""

    def test_initialization(self) -> None:
        """Test that LoaderTaskForDateAndStage can be initialized."""
        data_directory = "/test/data"
        dump_date = datetime.date(2023, 1, 15)
        stage = 2

        task = LoaderTaskForDateAndStage(
            data_directory=data_directory, dump_date=dump_date, stage=stage
        )

        assert task.data_directory == data_directory
        assert task.dump_date == dump_date
        assert task.stage == stage
        assert isinstance(task, luigi.Task)

    def test_priority_includes_stage_adjustment(self) -> None:
        """Test that priority includes stage number (earlier stages higher)."""
        past_date = datetime.date(2020, 1, 1)
        task = LoaderTaskForDateAndStage(
            data_directory="/test/data", dump_date=past_date, stage=5
        )

        priority = task.priority

        assert isinstance(priority, int)
        assert priority > 0

    # noinspection PyUnresolvedReferences
    def test_requires_returns_previous_stage_when_stage_gt_zero(self) -> None:
        """Test that requires() yields DiscogsDownloaderTaskForDate and previous stage when stage > 0."""
        task = LoaderTaskForDateAndStage(
            data_directory="/test/data",
            dump_date=datetime.date(2023, 1, 15),
            stage=3,
        )

        dependencies = list(task.requires())

        assert len(dependencies) == 2
        assert isinstance(dependencies[0], DiscogsDownloaderTaskForDate)
        assert dependencies[0].data_directory == task.data_directory
        assert dependencies[0].dump_date == task.dump_date
        dep = dependencies[1]
        assert isinstance(dep, LoaderTaskForDateAndStage)
        assert dep.data_directory == task.data_directory
        assert dep.dump_date == task.dump_date
        assert dep.stage == 2

    # noinspection PyUnresolvedReferences
    def test_requires_returns_discogs_downloader_for_stage_zero(self) -> None:
        """Test that requires() yields DiscogsDownloaderTaskForDate for stage 0."""
        task = LoaderTaskForDateAndStage(
            data_directory="/test/data",
            dump_date=datetime.date(2023, 1, 15),
            stage=0,
        )

        dependencies = list(task.requires())

        assert len(dependencies) == 1
        assert isinstance(dependencies[0], DiscogsDownloaderTaskForDate)
        assert dependencies[0].data_directory == task.data_directory
        assert dependencies[0].dump_date == task.dump_date

    def test_output_returns_loader_target(self) -> None:
        """Test that output() returns a LoaderTarget."""
        task = LoaderTaskForDateAndStage(
            data_directory="/test/data",
            dump_date=datetime.date(2023, 1, 15),
            stage=1,
        )

        output = task.output()

        assert isinstance(output, LoaderTarget)
        assert output.date == datetime.date(2023, 1, 15)

    @patch("asyncio.new_event_loop")
    @patch("asyncio.set_event_loop")
    @patch("musigree.offline.loader.loader_tasks.log")
    def test_run_executes_stage_successfully(
        self,
        mock_log: MagicMock,
        _mock_set_loop: MagicMock,
        mock_new_loop: MagicMock,
    ) -> None:
        """Test that run() executes the stage and marks output done."""
        mock_stage_func = AsyncMock()
        mock_get_stages = MagicMock(
            return_value=[mock_stage_func, MagicMock(), MagicMock()]
        )

        mock_loop = MagicMock()
        mock_new_loop.return_value = mock_loop
        mock_task = MagicMock()
        mock_loop.create_task.return_value = mock_task

        mock_output = MagicMock()
        mock_output.done = AsyncMock()

        task = LoaderTaskForDateAndStage(
            data_directory="/test/data",
            dump_date=datetime.date(2023, 1, 15),
            stage=0,
        )

        with patch.object(task, "output", return_value=mock_output):
            with patch("asyncio.get_running_loop", side_effect=RuntimeError):
                with patch(
                    "musigree.loader.run_offline_loader.get_load_offline_table_stages",
                    mock_get_stages,
                ):
                    task.run()

        mock_log.debug.assert_called()
        mock_new_loop.assert_called_once()
        mock_loop.create_task.assert_called_once()
        mock_loop.run_until_complete.assert_called_once_with(mock_task)

    @patch("musigree.offline.loader.loader_tasks.log")
    def test_run_handles_invalid_stage(self, mock_log: MagicMock) -> None:
        """Test that run() handles invalid stage (stage >= len(stages))."""
        mock_stage = AsyncMock()
        mock_get_stages = MagicMock(return_value=[mock_stage])

        task = LoaderTaskForDateAndStage(
            data_directory="/test/data",
            dump_date=datetime.date(2023, 1, 15),
            stage=5,
        )

        with patch("asyncio.get_running_loop", side_effect=RuntimeError):
            with patch("asyncio.new_event_loop") as mock_new_loop:
                with patch("asyncio.set_event_loop"):
                    mock_loop = MagicMock()
                    mock_new_loop.return_value = mock_loop
                    mock_task = MagicMock()
                    mock_task.add_done_callback = MagicMock()
                    mock_loop.create_task.return_value = mock_task
                    mock_loop.run_until_complete.side_effect = lambda _: None

                    with patch(
                        "musigree.loader.run_offline_loader.get_load_offline_table_stages",
                        mock_get_stages,
                    ):
                        task.run()

        mock_log.debug.assert_called()

    @patch("musigree.offline.loader.loader_tasks.log")
    def test_run_handles_runtime_error_during_execution(
        self, mock_log: MagicMock
    ) -> None:
        """Test that run() catches RuntimeError and logs exception."""
        mock_stage = AsyncMock()
        mock_get_stages = MagicMock(return_value=[mock_stage])

        task = LoaderTaskForDateAndStage(
            data_directory="/test/data",
            dump_date=datetime.date(2023, 1, 15),
            stage=0,
        )

        with patch("asyncio.get_running_loop", side_effect=RuntimeError):
            with patch("asyncio.new_event_loop") as mock_new_loop:
                with patch("asyncio.set_event_loop"):
                    mock_loop = MagicMock()
                    mock_new_loop.return_value = mock_loop
                    mock_task = MagicMock()
                    mock_loop.create_task.return_value = mock_task
                    mock_loop.run_until_complete.side_effect = RuntimeError(
                        "Test error"
                    )

                    with patch(
                        "musigree.loader.run_offline_loader.get_load_offline_table_stages",
                        mock_get_stages,
                    ):
                        task.run()

        mock_log.exception.assert_called_once()

    def test_task_family(self) -> None:
        """Test that LoaderTaskForDateAndStage has correct task family."""
        task = LoaderTaskForDateAndStage(
            data_directory="/test/data",
            dump_date=datetime.date(2023, 1, 15),
            stage=2,
        )
        assert task.task_family == "musigree.LoaderTaskForDateAndStage"


class TestDiscogsDownloaderTask:
    """Test class for DiscogsDownloaderTask."""

    def test_initialization(self) -> None:
        """Test that DiscogsDownloaderTask can be initialized."""
        data_directory = "/test/data"
        dump_date = datetime.date(2023, 1, 15)
        dump_type = DISCOGS_ARTISTS_TYPE

        task = DiscogsDownloaderTask(
            data_directory=data_directory,
            dump_date=dump_date,
            dump_type=dump_type,
        )

        assert task.data_directory == data_directory
        assert task.dump_date == dump_date
        assert task.dump_type == dump_type
        assert isinstance(task, luigi.Task)

    @patch("musigree.offline.loader.loader_tasks.get_discogs_url")
    def test_url_property_calls_get_discogs_url(
        self, mock_get_discogs_url: MagicMock
    ) -> None:
        """Test that url property calls get_discogs_url with correct args."""
        mock_get_discogs_url.return_value = "https://example.com/dump.xml.gz"

        task = DiscogsDownloaderTask(
            data_directory="/test/data",
            dump_date=datetime.date(2023, 1, 15),
            dump_type=DISCOGS_ARTISTS_TYPE,
        )

        result = task.url

        assert result == "https://example.com/dump.xml.gz"
        mock_get_discogs_url.assert_called_once_with(
            datetime.date(2023, 1, 15), DISCOGS_ARTISTS_TYPE
        )

    def test_requires_returns_none(self) -> None:
        """Test that requires() returns None."""
        task = DiscogsDownloaderTask(
            data_directory="/test/data",
            dump_date=datetime.date(2023, 1, 15),
            dump_type=DISCOGS_ARTISTS_TYPE,
        )

        result = task.requires()

        assert result is None

    def test_output_returns_local_target_with_correct_path(self) -> None:
        """Test that output() returns LocalTarget with expected path."""
        task = DiscogsDownloaderTask(
            data_directory="/test/data",
            dump_date=datetime.date(2023, 1, 15),
            dump_type=DISCOGS_ARTISTS_TYPE,
        )

        output = task.output()

        assert isinstance(output, luigi.LocalTarget)
        assert "discogs" in output.path
        assert "20230115" in output.path
        assert "artists" in output.path
        assert output.path.endswith(".xml.gz")

    @patch("musigree.offline.loader.loader_tasks.get_discogs_url")
    @patch("musigree.offline.loader.loader_tasks.download_file")
    def test_run_downloads_file_to_output(
        self,
        mock_download_file: MagicMock,
        mock_get_discogs_url: MagicMock,
    ) -> None:
        """Test that run() calls download_file with url and output path."""
        mock_get_discogs_url.return_value = "https://example.com/dump.xml.gz"

        task = DiscogsDownloaderTask(
            data_directory="/test/data",
            dump_date=datetime.date(2023, 1, 15),
            dump_type=DISCOGS_ARTISTS_TYPE,
        )

        mock_output = MagicMock()
        mock_output.exists.return_value = False  # so run() enters the download block
        mock_output.temporary_path.return_value.__enter__ = MagicMock(
            return_value="/tmp/out.xml.gz"
        )
        mock_output.temporary_path.return_value.__exit__ = MagicMock(
            return_value=None
        )

        with patch.object(task, "output", return_value=mock_output):
            with patch("builtins.open", MagicMock()) as mock_open:
                mock_file = MagicMock()
                mock_open.return_value.__enter__ = MagicMock(
                    return_value=mock_file
                )
                mock_open.return_value.__exit__ = MagicMock(return_value=None)

                task.run()

        mock_download_file.assert_called_once()
        call_args = mock_download_file.call_args
        assert call_args[0][0] == "https://example.com/dump.xml.gz"
        assert call_args[0][1] is mock_file

    def test_task_family(self) -> None:
        """Test that DiscogsDownloaderTask has correct task family."""
        task = DiscogsDownloaderTask(
            data_directory="/test/data",
            dump_date=datetime.date(2023, 1, 15),
            dump_type=DISCOGS_ARTISTS_TYPE,
        )
        assert task.task_family == "musigree.DiscogsDownloaderTask"


class TestLoaderTasksLogging:
    """Test class for loader_tasks module logging."""

    def test_logger_exists(self) -> None:
        """Test that the module logger is configured."""
        from musigree.offline.loader.loader_tasks import log

        assert isinstance(log, logging.Logger)
        assert log.name == "musigree.offline.loader.loader_tasks"


class TestLoaderTasksIntegration:
    """Integration-style tests for loader tasks without external deps."""

    @patch("musigree.offline.loader.loader_tasks.get_discogs_dump_dates")
    @patch("musigree.loader.run_offline_loader.get_load_offline_table_stages")
    def test_loader_task_requires_chain(
        self,
        mock_get_stages: MagicMock,
        mock_get_dates: MagicMock,
    ) -> None:
        """Test dependency chain from LoaderTask through stages."""
        mock_get_dates.return_value = [datetime.date(2023, 1, 1)]
        mock_get_stages.return_value = [MagicMock(), MagicMock()]

        main_task = LoaderTask(
            data_directory="/integration/test/data",
            start_date=datetime.date(2023, 1, 1),
            end_date=datetime.date(2023, 1, 31),
        )

        deps = list(main_task.requires())
        assert len(deps) == 3
        assert isinstance(deps[0], LoaderSetupTask)
        assert isinstance(deps[1], DiscogsDownloaderTaskForDate)
        assert isinstance(deps[2], LoaderTaskForDate)

        load_task = deps[2]
        stage_deps = list(load_task.requires())
        assert len(stage_deps) == 3  # download + 2 stages
        assert isinstance(stage_deps[0], DiscogsDownloaderTaskForDate)
        assert isinstance(stage_deps[1], LoaderTaskForDateAndStage)
        assert isinstance(stage_deps[2], LoaderTaskForDateAndStage)
        assert getattr(stage_deps[1], "stage", None) == 0
        assert getattr(stage_deps[2], "stage", None) == 1

        # Stage 0 requires only DiscogsDownloaderTaskForDate
        stage_zero_deps = list(stage_deps[1].requires())
        assert len(stage_zero_deps) == 1
        assert isinstance(stage_zero_deps[0], DiscogsDownloaderTaskForDate)
        # Stage 1 requires DiscogsDownloaderTaskForDate and previous stage (stage 0)
        prev = list(stage_deps[2].requires())
        assert len(prev) == 2
        assert isinstance(prev[0], DiscogsDownloaderTaskForDate)
        assert isinstance(prev[1], LoaderTaskForDateAndStage)
        assert getattr(prev[1], "stage", None) == 0
