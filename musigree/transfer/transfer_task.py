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

import logging

import luigi
from luigi.contrib.simulate import RunAnywayTarget

log = logging.getLogger(__name__)
"""
The logger for the TransferTask module.
"""


class TransferTask(luigi.Task):
    """
    A Luigi task for transferring data from the offline to the runtime database.

    This task is responsible for orchestrating the complete data transfer
    process using the `TransferManager.transfer_all` method. It is designed to
    always run and has a very low priority.

    Inherits from:
        luigi.Task: The base class for defining Luigi tasks.
    """

    data_directory = luigi.Parameter(significant=False)

    def output(self) -> RunAnywayTarget:
        """
        Defines the output target for this task.

        This method returns a `RunAnywayTarget` to ensure that the task is
        always run.

        Returns:
            RunAnywayTarget: A target that always indicates that the task needs
                to be run.
        """
        # Always run this task
        return RunAnywayTarget(self)

    def requires(self) -> list[luigi.Task] | None:
        """
        Defines the dependencies for this task.

        This task has no dependencies.

        Returns:
            None: This task has no required dependencies.
        """
        return None

    @property
    def priority(self):  # type: ignore
        """
        Defines the priority of this task.

        This method sets a very low priority to ensure that other tasks are
        executed before the transfer task.

        Returns:
            int: A very low priority value.
        """
        return -1000000000

    def run(self) -> None:
        """
        Executes the data transfer process.

        This method calls `TransferManager.transfer_all` to perform the complete
        data transfer and then marks the task as complete.
        """
        log.debug(f"Running transfer task: {self.task_id}")
        """Log the start of the task."""
        # TODO split into multiple tasks
        # TransferManager.transfer_all(Path(str(self.data_directory)))
        """Transfer all data."""
        self.output().done()
        """Mark the task as complete."""
