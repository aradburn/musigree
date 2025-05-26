import logging
import multiprocessing
from typing import Any

from retrying import retry
from sqlalchemy.exc import DatabaseError

from musigree.runtime.runtime_database.runtime_database_helper import (
    RuntimeDatabaseHelper,
)
from musigree.runtime.runtime_database.runtime_relation_repository import (
    RuntimeRelationRepository,
)
from musigree.runtime.runtime_database.runtime_transaction import runtime_transaction
from musigree.runtime.runtime_database_manager import RuntimeDatabaseManager

log = logging.getLogger(__name__)


class TransferWorkerRelationInserter(multiprocessing.Process):
    """
    A multiprocessing.Process subclass that handles the insertion of bulk data into the database.

    Attributes:
        bulk_inserts (list[dict[str, Any]]): A list of dictionaries containing the data to be inserted.
        inserted_count (int): The count of inserted records.
    """

    def __init__(self, bulk_inserts: list[dict[str, Any]], inserted_count: int):
        """
        Initializes the TransferWorkerRelationInserter with the given bulk inserts and inserted count.

        Args:
            bulk_inserts (list[dict[str, Any]]): The data to be inserted.
            inserted_count (int): The count of inserted records.
        """
        super().__init__()
        self.bulk_inserts = bulk_inserts
        self.inserted_count = inserted_count

    def run(self):
        """
        The main process method that initializes the database if needed and saves all bulk inserts.
        """
        proc_name = self.name

        if RuntimeDatabaseManager.get_concurrency_count() > 1:
            RuntimeDatabaseHelper.initialize()

        self.save_all(self.bulk_inserts)

        log.info(f"[{proc_name}] inserted_count: {self.inserted_count}")

    @staticmethod
    def retry_if_db_error(exception):
        """
        Determines if the operation should be retried based on the exception type.

        Args:
            exception (Exception): The exception that was raised.

        Returns:
            bool: True if the exception is a DatabaseError, False otherwise.
        """
        return isinstance(exception, DatabaseError)

    @staticmethod
    @retry(
        stop_max_attempt_number=3,
        wait_fixed=60000,
        retry_on_exception=retry_if_db_error,
    )
    def save_all(bulk_inserts: list[dict[str, Any]]) -> None:
        """
        Saves all bulk inserts to the database with retry logic in case of DatabaseError.

        Args:
            bulk_inserts (list[dict[str, Any]]): The data to be inserted.

        Raises:
            DatabaseError: If there is an error during the database operation.
        """
        with runtime_transaction():
            runtime_relation_repository = RuntimeRelationRepository()
            try:
                runtime_relation_repository.save_all(bulk_inserts)
                runtime_relation_repository.commit()
            except DatabaseError:
                log.error("Error in TransferWorkerRelationInserter worker")
                # log.exception("Error in TransferWorkerRelationInserter worker", exc_info=True)
                raise
