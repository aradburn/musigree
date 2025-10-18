"""
This module defines the `TransferTask` class, which is a Luigi task responsible
for orchestrating the transfer of data from the offline database to the runtime
database in the Musigree system.

It utilizes the Luigi task management framework to define and execute the data
transfer process. This task is designed to run the `TransferManager.transfer_all`
method, which handles the complete data migration process, including entities,
relations, and roles.

Key functionalities include:
    - **Luigi Integration**: Integrates with the Luigi task management
      framework to define a task for data transfer.
    - **Data Transfer Orchestration**: Calls `TransferManager.transfer_all`
      to execute the complete data transfer process.
    - **Run-Always Task**: Uses `RunAnywayTarget` to ensure that the task is
      always executed, regardless of previous runs.
    - **Low Priority**: Sets a very low priority to ensure that other tasks
      are executed before the transfer task.
    - **Logging**: Provides logging of the task execution.

The `TransferTask` class interacts with the following components:
    - `luigi.Task`: The base class for defining Luigi tasks.
    - `luigi.contrib.simulate.RunAnywayTarget`: A Luigi target that always
      indicates that a task needs to be run.
    - `TransferManager`: For managing the data transfer process.
    - `logging`: For logging operations.

The module utilizes `logging` for logging operations, `luigi` for the task
management and `luigi.contrib.simulate` for the `RunAnywayTarget`. It
interacts with `musigree.transfer` for the transfer logic.
"""

import asyncio
import datetime
import logging
from pathlib import Path
from typing import Iterator

import luigi
from luigi.contrib.simulate import RunAnywayTarget

from musigree.loader.runtime_loader import get_load_runtime_table_stages
from musigree.offline.loader.loader_target import LoaderTarget

log = logging.getLogger(__name__)
"""
The logger for the TransferTask module.
"""


class RuntimeLoaderSetupTask(luigi.Task):
    """
    Sets up the logging environment for the runtime data loading process.

    This task configures Luigi's logging to use the same handlers as the
    Musigree logging system, ensuring consistent log output.
    """

    data_directory = luigi.Parameter(significant=False)

    start_date = luigi.DateParameter()
    """The start date for the data loading process."""
    end_date = luigi.DateParameter()
    """The end date for the data loading process."""

    def output(self) -> RunAnywayTarget:
        """
        Returns a RunAnywayTarget.

        This method always run the task.

        Returns:
            RunAnywayTarget: The target for this task.
        """
        # Always run this task
        return RunAnywayTarget(self)

    def run(self) -> Iterator[luigi.Task]:
        """
        Configures logging and yields the next task.

        This method sets up the logging handlers for luigi and yields the
        next task in the workflow.
        """
        log.debug(f"Running runtime loader setup task: {self.task_id}")
        logging.getLogger("luigi").handlers = logging.getLogger("musigree").handlers
        logging.getLogger("luigi").propagate = False
        logging.getLogger("luigi").setLevel(logging.WARNING)
        logging.getLogger("luigi-interface").handlers = logging.getLogger("musigree").handlers
        logging.getLogger("luigi-interface").propagate = False
        logging.getLogger("luigi-interface").setLevel(logging.WARNING)
        self.output().done()

        yield RuntimeLoaderTask(
            data_directory=self.data_directory,
            start_date=self.start_date,
            end_date=self.end_date,
        )


class RuntimeLoaderTask(luigi.WrapperTask):
    """
    The main wrapper task for the data loading process.

    This task manages the overall data loading process for a range of dates,
    including downloading and loading data.
    """

    data_directory = luigi.Parameter(significant=False)

    start_date = luigi.DateParameter()
    """The start date for the data loading process."""
    end_date = luigi.DateParameter()
    """The end date for the data loading process."""

    def requires(self) -> Iterator[luigi.Task]:
        """
        Defines the dependencies for this task.

        This method returns a generator that yields the dependencies for this
        task, including `LoaderSetupTask`, `DiscogsDownloaderTaskForDate`,
        and `LoaderTaskForDate`.

        Yields:
            luigi.Task: The dependency tasks.
        """
        yield RuntimeLoaderSetupTask(
            data_directory=self.data_directory,
            start_date=self.start_date,
            end_date=self.end_date,
        )
        # Only transfer the final offline data, date is the date of the most recent dump loaded into offline database.
        yield RuntimeLoaderTaskForDate(data_directory=self.data_directory, dump_date=self.end_date)


class RuntimeLoaderTaskForDate(luigi.WrapperTask):
    """
    A wrapper task for loading data into the runtime database for a specific date.

    This task manages the loading of data into the runtime database for a given date,
    ensuring that the loading process is executed through multiple stages.
    """

    data_directory = luigi.Parameter(significant=False)

    dump_date = luigi.DateParameter()
    """The date for which to load the data."""

    @property
    def priority(self):  # type: ignore
        """
        Calculates the priority of this task.

        The priority is calculated based on how long ago the dump date was.
        Older dates have higher priority.

        Returns:
            int: The priority of this task.
        """
        diff = int(
            (
                datetime.datetime.now() - datetime.datetime.fromisoformat(str(self.dump_date))
            ).total_seconds()
        )
        log.debug(f"RuntimeLoaderTaskForDate priority: {diff}")
        return diff

    def requires(self) -> Iterator[luigi.Task]:
        """
        Defines the dependencies for this task.

        This method returns a generator that yields the dependencies for this
        task.

        Yields:
            luigi.Task: The dependency tasks.
        """
        stages = get_load_runtime_table_stages(
            Path(str(self.data_directory)),
            datetime.date.fromisoformat(str(self.dump_date)).strftime("%Y%m%d"),
        )
        for stage in range(0, len(stages)):
            yield RuntimeLoaderTaskForDateAndStage(
                data_directory=self.data_directory,
                dump_date=self.dump_date,
                stage=stage,
            )


class RuntimeLoaderTaskForDateAndStage(luigi.Task):
    """
    A task that performs a specific stage of the runtime data loading process.

    This task is responsible for executing a single stage of the runtime data loading
    process for a given date.
    """

    data_directory = luigi.Parameter(significant=False)

    dump_date = luigi.DateParameter()
    """The date for which to load the data."""
    stage = luigi.IntParameter()
    """The stage of the data loading process to execute."""

    @property
    def priority(self):  # type: ignore
        """
        Calculates the priority of this task.

        The priority is calculated based on how long ago the dump date was and
        the stage number. Older dates and earlier stages have higher priority.

        Returns:
            int: The priority of this task.
        """
        diff = int(
            (
                datetime.datetime.now() - datetime.datetime.fromisoformat(str(self.dump_date))
            ).total_seconds()
        ) + (100 - int(str(self.stage)))
        log.debug(
            f"RuntimeLoaderTaskForDateAndStage date: {self.dump_date} stage: {self.stage} priority: {diff}"
        )
        return diff

    def requires(self) -> Iterator[luigi.Task]:
        """
        Defines the dependencies for this task.

        This method returns a generator that yields the dependency for this
        task, which is the previous loading stage.

        Yields:
            luigi.Task: The dependency tasks.
        """
        if int(str(self.stage)) > 0:
            # Require the previous stage (monthly subtasks defined in database_helper) to have been completed
            yield RuntimeLoaderTaskForDateAndStage(
                data_directory=self.data_directory,
                dump_date=self.dump_date,
                stage=int(str(self.stage)) - 1,
            )
        else:
            pass

    def output(self) -> LoaderTarget:
        """
        Defines the output target for this task.

        This method returns a `LoaderTarget` that represents the completion
        status of this task in the database.

        Returns:
            LoaderTarget: The target for this task.
        """
        # Store the outcome of the task as a record in the database
        return LoaderTarget(self, datetime.date.fromisoformat(str(self.dump_date)))

    def run(self) -> None:
        """
        Executes the data loading stage.

        This method retrieves the loading stages from `OfflineDatabaseManager`
        and executes the current stage. It also handles potential
        `RuntimeError` exceptions.
        """
        log.debug(
            f"Run RuntimeLoaderTaskForDateAndStage tasks for stage: {self.stage} date: {self.dump_date}"
        )

        from musigree.loader.runtime_loader import get_load_runtime_table_stages

        stages = get_load_runtime_table_stages(
            Path(str(self.data_directory)),
            datetime.date.fromisoformat(str(self.dump_date)).strftime("%Y%m%d"),
        )
        log.debug(f"Queueing stage: {self.stage}")

        background_tasks = set()

        async def worker_function() -> None:
            """
            Worker function to execute the loading stage.

            This function runs the specified stage of the data loading process.
            It is designed to be run in an asyncio event loop.
            """
            log.debug(f"Running stage: {self.stage} for date: {self.dump_date}")
            if int(str(self.stage)) < len(stages):
                await stages[int(str(self.stage))]()
                await self.output().done()
            else:
                log.error(f"Invalid stage: {self.stage} for date: {self.dump_date}")

        try:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                """Check if the event loop is already running."""
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                """Set a new event loop if none exists."""
            task = loop.create_task(worker_function())
            # Add task to the set. This creates a strong reference.
            background_tasks.add(task)

            # To prevent keeping references to finished tasks forever,
            # make each task remove its own reference from the set after
            # completion:
            task.add_done_callback(background_tasks.discard)
            loop.run_until_complete(task)

        except RuntimeError as e:
            log.exception(e, exc_info=True)
