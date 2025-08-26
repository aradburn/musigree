"""
This module defines the `LoaderTasks` for managing the offline data loading process
in the Musigree system using Luigi.

It defines various tasks for setting up the data loading environment, downloading
Discogs XML data dumps, and loading the data into the offline database. The
tasks are organized into a workflow that can be run using Luigi's task
management capabilities.

Key functionalities include:
    - **`LoaderSetupTask`**: Sets up the logging environment for the data loading
      process. It ensures that Luigi's logging is properly configured to use
      the same handlers as the Musigree logging system.
    - **`LoaderTask`**: The main wrapper task that orchestrates the overall
      data loading process. It defines the sequence of tasks to be executed,
      including downloading and loading data for a range of dates.
    - **`DiscogsDownloaderTaskForDate`**: A wrapper task that manages the
      downloading of Discogs XML dumps for a specific date. It ensures that
      all required dump types (artists, releases, labels, masters) are downloaded.
    - **`LoaderTaskForDate`**: A wrapper task that manages the loading of
      data for a specific date. It ensures that the data is downloaded and
      then proceeds to load the data into the database through several stages.
    - **`LoaderTaskForDateAndStage`**: A task that performs a specific stage
      of the data loading process for a given date. It is used to break down
      the loading process into smaller, manageable steps.
    - **`DiscogsDownloaderTask`**: A task that downloads a specific Discogs
      XML dump file (e.g., artists, releases) for a given date and dump type.
    - **Concurrency and Prioritization**: Utilizes Luigi's task dependencies
      and prioritization to manage concurrent execution and prioritize tasks
      based on their dates and stages.
    - **Error Handling**: Uses `try...except` blocks to handle `RuntimeError`
      exceptions during the data loading process.
    - **Date and Type Management**: Employs `datetime` objects and custom
      parameters (e.g., `dump_type`) to manage different dates and dump types.
    - **Database Integration**: Interacts with `OfflineDatabaseManager` to
      retrieve loading stages and perform data loading operations.
    - **Data Storage**: Uses `luigi.LocalTarget` to represent local files
      and `LoaderTarget` to track the completion status of data loading stages
      in the database.
    - **Dynamic Task Generation**: Employs `yield` statements to dynamically
      generate subtasks based on the data and configuration.
    - **Path Management**: Uses `os.path.join` and `urlparse` to manage file
      paths and URLs.
    - **Logging**: Uses `logging` to provide detailed information about the
      progress and status of the data loading process.

The `LoaderTasks` interact with the following components:
    - `luigi`: For workflow management and task definition.
    - `luigi.contrib.simulate`: For creating always run target.
    - `musigree.config`: For configuration settings (e.g., `ROOT_DIR`,
      `DISCOGS_ARTISTS_TYPE`).
    - `musigree.offline.loader.loader_target`: For managing the task
      completion status in the database.
    - `musigree.offline.offline_database_manager`: For managing the offline
      database and retrieving loading stages.
    - `musigree.utils`: For utility functions like `get_discogs_dump_dates`,
      `download_file`, and `get_discogs_url`.
    - `datetime`: For date and time handling.
    - `logging`: For logging operations.
    - `os`: For file system operations.
    - `urllib.parse`: For parsing URLs.

This module utilizes `luigi` for workflow management, `datetime` for date
and time handling, `logging` for logging operations, `os` for file system
operations, `urllib.parse` for URL parsing and `musigree` library.
"""

import asyncio
import datetime
import logging
from collections.abc import Iterator
from pathlib import Path
from urllib.parse import urlparse

import luigi
from luigi.contrib.simulate import RunAnywayTarget

from musigree.constants import (
    DISCOGS_DATA,
    DISCOGS_ARTISTS_TYPE,
    DISCOGS_RELEASES_TYPE,
    DISCOGS_LABELS_TYPE,
    DISCOGS_MASTERS_TYPE,
)
from musigree.offline.loader.loader_target import LoaderTarget
from musigree.utils import (
    get_discogs_dump_dates,
    download_file,
    get_discogs_url,
)

log = logging.getLogger(__name__)
"""
The logger for the LoaderTasks module.
"""


class LoaderSetupTask(luigi.Task):
    """
    Sets up the logging environment for the data loading process.

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
        log.debug(f"Running loader setup task: {self.task_id}")
        logging.getLogger("luigi").handlers = logging.getLogger("musigree").handlers
        logging.getLogger("luigi").propagate = False
        logging.getLogger("luigi").setLevel(logging.WARNING)
        logging.getLogger("luigi-interface").handlers = logging.getLogger(
            "musigree"
        ).handlers
        logging.getLogger("luigi-interface").propagate = False
        logging.getLogger("luigi-interface").setLevel(logging.WARNING)
        self.output().done()

        yield LoaderTask(
            data_directory=self.data_directory,
            start_date=self.start_date,
            end_date=self.end_date,
        )


class LoaderTask(luigi.WrapperTask):
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
        yield LoaderSetupTask(
            data_directory=self.data_directory,
            start_date=self.start_date,
            end_date=self.end_date,
        )
        dates = get_discogs_dump_dates(
            datetime.date.fromisoformat(str(self.start_date)),
            datetime.date.fromisoformat(str(self.end_date)),
        )
        for date in dates:
            yield DiscogsDownloaderTaskForDate(
                data_directory=self.data_directory, dump_date=date
            )
            yield LoaderTaskForDate(data_directory=self.data_directory, dump_date=date)


class DiscogsDownloaderTaskForDate(luigi.WrapperTask):
    """
    A wrapper task for downloading Discogs XML dumps for a specific date.

    This task ensures that all required dump types (artists, releases, labels,
    masters) are downloaded for a given date.
    """

    data_directory = luigi.Parameter(significant=False)

    dump_date = luigi.DateParameter()
    """The date for which to download the Discogs dumps."""

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
                datetime.datetime.now()
                - datetime.datetime.fromisoformat(str(self.dump_date))
            ).total_seconds()
        )
        log.debug(f"DiscogsDownloaderTaskForDate priority: {diff}")
        return diff

    def requires(self) -> Iterator[luigi.Task]:
        """
        Defines the dependencies for this task.

        This method returns a generator that yields the `DiscogsDownloaderTask`
        for each required dump type.

        Yields:
            luigi.Task: The dependency tasks.
        """
        yield DiscogsDownloaderTask(
            data_directory=self.data_directory,
            dump_date=self.dump_date,
            dump_type=DISCOGS_ARTISTS_TYPE,
        )
        yield DiscogsDownloaderTask(
            data_directory=self.data_directory,
            dump_date=self.dump_date,
            dump_type=DISCOGS_RELEASES_TYPE,
        )
        yield DiscogsDownloaderTask(
            data_directory=self.data_directory,
            dump_date=self.dump_date,
            dump_type=DISCOGS_LABELS_TYPE,
        )
        yield DiscogsDownloaderTask(
            data_directory=self.data_directory,
            dump_date=self.dump_date,
            dump_type=DISCOGS_MASTERS_TYPE,
        )


class LoaderTaskForDate(luigi.WrapperTask):
    """
    A wrapper task for loading data for a specific date.

    This task manages the loading of data into the database for a given date,
    ensuring that the required downloads are completed and that the loading
    process is executed through multiple stages.
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
                datetime.datetime.now()
                - datetime.datetime.fromisoformat(str(self.dump_date))
            ).total_seconds()
        )
        log.debug(f"LoaderTaskForDate priority: {diff}")
        return diff

    def requires(self) -> Iterator[luigi.Task]:
        """
        Defines the dependencies for this task.

        This method returns a generator that yields the dependencies for this
        task, including `DiscogsDownloaderTaskForDate` and
        `LoaderTaskForDateAndStage` for each loading stage.

        Yields:
            luigi.Task: The dependency tasks.
        """
        yield DiscogsDownloaderTaskForDate(
            data_directory=self.data_directory, dump_date=self.dump_date
        )
        from musigree.loader.loader import get_load_offline_table_stages

        stages = get_load_offline_table_stages(
            Path(str(self.data_directory)),
            datetime.date.fromisoformat(str(self.dump_date)).strftime("%Y%m%d"),
            is_bulk_inserts=False,
        )
        for stage in range(0, len(stages)):
            yield LoaderTaskForDateAndStage(
                data_directory=self.data_directory,
                dump_date=self.dump_date,
                stage=stage,
            )


class LoaderTaskForDateAndStage(luigi.Task):
    """
    A task that performs a specific stage of the data loading process.

    This task is responsible for executing a single stage of the data loading
    process for a given date, as defined by the `OfflineDatabaseManager`.
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
                datetime.datetime.now()
                - datetime.datetime.fromisoformat(str(self.dump_date))
            ).total_seconds()
        ) + (100 - int(str(self.stage)))
        log.debug(
            f"LoaderTaskForDateAndStage date: {self.dump_date} stage: {self.stage} priority: {diff}"
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
            yield LoaderTaskForDateAndStage(
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
            f"Run LoaderTaskForDateAndStage tasks for stage: {self.stage} date: {self.dump_date}"
        )

        from musigree.loader.loader import get_load_offline_table_stages

        stages = get_load_offline_table_stages(
            Path(str(self.data_directory)),
            datetime.date.fromisoformat(str(self.dump_date)).strftime("%Y%m%d"),
            is_bulk_inserts=False,
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
                await stages[int(str(self.stage))]
                await self.output().done()
            else:
                log.error(f"Invalid stage: {self.stage} for date: {self.dump_date}")

        try:
            loop = asyncio.get_running_loop()
            task = loop.create_task(worker_function())
            # Add task to the set. This creates a strong reference.
            background_tasks.add(task)

            # To prevent keeping references to finished tasks forever,
            # make each task remove its own reference from the set after
            # completion:
            task.add_done_callback(background_tasks.discard)

            # asyncio.run()
            # Mark task done in the database
            # await self.output().done()
        except RuntimeError as e:
            log.exception(e, exc_info=True)


class DiscogsDownloaderTask(luigi.Task):
    """
    A task for downloading a specific Discogs XML dump file.

    This task handles the downloading of a single Discogs XML dump file for
    a given date and dump type (e.g., artists, releases).
    """

    data_directory = luigi.Parameter(significant=False)

    dump_date = luigi.DateParameter()
    """The date for which to download the Discogs dump."""
    dump_type = luigi.Parameter()
    """The type of the Discogs dump (e.g., artists, releases)."""

    @property
    def url(self) -> str:
        """
        Generates the URL for the Discogs dump file.

        Returns:
            str: The URL of the Discogs dump file.
        """
        dump_date_date = datetime.date.fromisoformat(str(self.dump_date))
        return get_discogs_url(dump_date_date, str(self.dump_type))

    def requires(self) -> Iterator[luigi.Task] | None:
        """
        Defines the dependencies for this task.

        This method returns `None` as this task has no dependencies.

        Returns:
            None
        """
        return None

    def output(self) -> luigi.LocalTarget:
        """
        Defines the output target for this task.

        This method returns a `luigi.LocalTarget` that represents the local
        file where the Discogs dump will be stored.

        Returns:
            luigi.LocalTarget: The local target for this task.
        """
        output_url = urlparse(self.url)
        filename = output_url.path.rsplit("/", 1)[-1]
        filepath = Path(str(self.data_directory)) / DISCOGS_DATA / filename
        # filepath = os.path.join(ROOT_DIR, "musigree", "data", filename)
        log.debug(f"DiscogsDownloaderTask output: {filepath}")
        return luigi.LocalTarget(filepath)

    def run(self) -> None:
        """
        Downloads the Discogs dump file.

        This method downloads the Discogs dump file from the specified URL
        and saves it to the output path.
        """
        log.debug(f"Running task: {self.task_id} for date: {self.dump_date}")
        log.debug(f"download_file({self.url}, {self.output().path})")
        with self.output().temporary_path() as temporary_binary_file_path:
            with open(temporary_binary_file_path, "wb") as output_file:
                download_file(self.url, output_file)
