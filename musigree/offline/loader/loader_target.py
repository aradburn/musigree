"""
This module defines the `LoaderTarget` class, which is a custom Luigi target
used to track the completion status of tasks in the Musigree offline system.

It leverages the `luigi.Target` interface to determine if a task has been
successfully completed and to mark a task as done. It stores the task
completion status in the database using the `MetadataRepository`.

Key functionalities include:
    - **Task Tracking**: Records the completion status of tasks using a unique
      key that includes the task ID and the date.
    - **Existence Check (`exists`)**: Determines if a task has been completed
      by checking for a corresponding record in the database.
    - **Completion Marking (`done`)**: Marks a task as completed by creating
      a new record in the database with a timestamp.
    - **Database Interaction**: Uses `MetadataRepository` to interact with the
      database and store task completion metadata.
    - **Unique Key Generation (`get_key`)**: Creates a unique key for each task
      based on its task ID and date.
    - **Database Transactions**: Uses `offline_transaction` to ensure
      data consistency during database operations.

The `LoaderTarget` class interacts with the following components:
    - `luigi.Target`: The base class for defining targets in Luigi workflows.
    - `luigi.Task`: Represents a task in a Luigi workflow.
    - `MetadataRepository`: For database operations related to task metadata.
    - `MetadataUncommitted`: For representing task completion metadata before
      it is committed to the database.
    - `offline_transaction`: A decorator for managing database transactions.

The module utilizes `logging` for logging operations, `datetime` for date
and time handling, and `luigi` for workflow management.
"""

import datetime
import logging
import luigi

from musigree.exceptions import NotFoundError
from musigree.offline.database.metadata_repository import MetadataRepository
from musigree.offline.database.offline_transaction import offline_transaction
from musigree.offline.domain.metadata import MetadataUncommitted

log = logging.getLogger(__name__)
"""
The logger for the LoaderTarget module.
"""


class LoaderTarget(luigi.Target):
    """
    A custom Luigi target for tracking the completion status of tasks.

    This class implements the `luigi.Target` interface to check if a task
    has been completed and to mark it as done. It stores task completion
    metadata in the database.

    Inherits from:
        luigi.Target: The base class for defining targets in Luigi workflows.
    """

    def __init__(self, task_obj: luigi.Task, date: datetime.date):
        """
        Initializes the LoaderTarget.

        Args:
            task_obj (luigi.Task): The task object associated with this target.
            date (datetime.date): The date associated with the task.
        """
        self.task_id = task_obj.task_id
        """The ID of the task associated with this target."""
        self.date = date
        """The date associated with the task."""

    def __str__(self):
        """
        Returns a string representation of the target.

        Returns:
            str: The task ID.
        """
        return self.task_id

    def get_key(self) -> str:
        """
        Generates a unique key for the task.

        The key is used to identify the task's completion status in the
        database.

        Returns:
            str: The unique key for the task.
        """
        return f"task-{self.task_id}-{self.date}"

    def exists(self):
        """
        Checks if the target exists, i.e., if the task has been completed.

        This method queries the database to see if a record exists with the
        task's unique key.

        Returns:
            bool: True if the task is completed (a record exists), False otherwise.
        """
        key = self.get_key()
        """Get the unique key for the task."""
        with offline_transaction():
            """Ensure that database operations are performed within a transaction."""
            repository = MetadataRepository()
            """Instance of MetadataRepository for database operations."""
            try:
                log.debug(f"Checking task key: {key}")
                """Log the task key being checked."""
                created_metadata = repository.get_by_key(key)
                """Retrieve the metadata record from the database."""
                if created_metadata is not None:
                    metadata_exists = True
                else:
                    metadata_exists = False
            except NotFoundError:
                """Handle the case where the metadata record is not found."""
                metadata_exists = False
        log.debug(f"key exists: {metadata_exists}")
        """Log whether the key exists."""
        return metadata_exists

    def done(self):
        """
        Marks the task as done by creating a database record.

        This method creates a new record in the database with the task's
        unique key and a timestamp, indicating that the task has been
        successfully completed.
        """
        key = self.get_key()
        """Get the unique key for the task."""
        metadata = MetadataUncommitted(
            metadata_key=key,
            metadata_value="done",
            metadata_timestamp=datetime.datetime.now(),
        )
        """Create a MetadataUncommitted object to represent the task's completion."""

        # WHEN
        with offline_transaction():
            """Ensure that database operations are performed within a transaction."""
            repository = MetadataRepository()
            """Instance of MetadataRepository for database operations."""
            repository.create(metadata)
            """Create the metadata record in the database."""
            log.debug(f"Created task done key: {key}")
            """Log the creation of the task completion record."""

        log.info(f"Marking {key} as done")
        """Log that the task has been marked as done."""
