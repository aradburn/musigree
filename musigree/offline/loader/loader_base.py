"""
This module defines the base class for data loaders in the Musigree offline system.

It provides a foundation for loading data from XML files into the database,
handling bulk inserts, updates, and deletes. It also includes functionality
for managing concurrency and tracking the progress of data loading operations.

Key components:
    - `LoaderBase`: An abstract base class for data loaders.
    - Methods for bulk database operations (insert, update, delete).
    - Methods for iterating through and parsing XML files.
    - Methods for managing concurrency and waiting for worker processes.
    - Methods for handling data preprocessing and transformation.
    - Methods for tracking updated IDs and identifying records to be deleted.
    - Constants for batch sizes, reporting frequency, and retry limits.
    - Helper functions for getting XML paths and setting up iterators.

The `LoaderBase` class is designed to be subclassed by specific data loaders,
which implement the abstract methods to provide database-specific and
domain-specific logic.

The module utilizes `gzip` for handling compressed XML files, `logging` for
logging operations, `abc` for abstract base classes, `typing` for type
hinting, `SortedSet` for managing sorted sets of IDs, and `sqlalchemy.exc.DataError`
for database-related exceptions. It interacts with `musigree.utils` for utility
functions, `musigree.offline.offline_database_manager` for database management,
`musigree.offline.database.base_repository` for database operations,
`musigree.library.fields.entity_type` for entity types, `musigree.offline.loader.loader_utils`
for loader-specific utilities, and `musigree.logging_config` for logging.
"""

import gzip
import logging
from abc import abstractmethod
from pathlib import Path
from typing import List, Any

from sortedcontainers import SortedSet
from sqlalchemy.exc import DataError

from musigree import utils
from musigree.library.fields.entity_type import EntityType
from musigree.logging_config import LOGGING_TRACE
from musigree.offline.database.base_repository import BaseRepository
from musigree.offline.loader.loader_utils import LoaderUtils
from musigree.offline.loader.parser_base import ParserBase
from musigree.offline.loader.parser_utils import ParserUtils
from musigree.offline.offline_database_manager import OfflineDatabaseManager

log = logging.getLogger(__name__)
"""
The logger for the LoaderBase module.
"""


class LoaderBase:
    """
    Abstract base class for data loaders.

    This class provides a framework for loading data from XML files into the
    database, handling bulk operations, concurrency, and data preprocessing.

    Attributes:
        BULK_INSERT_BATCH_SIZE (int): The batch size for bulk insert operations.
        BULK_UPDATE_BATCH_SIZE (int): The batch size for bulk update operations.
        BULK_REPORTING_SIZE (int): The number of records to process before reporting progress.
        MAX_RETRYS (int): The maximum number of retries for database operations.
        _tags_to_fields_mapping (dict): A mapping from XML tags to database fields and procedures.
    """

    BULK_INSERT_BATCH_SIZE = 1000
    """The batch size for bulk insert operations."""
    BULK_UPDATE_BATCH_SIZE = 100
    """The batch size for bulk update operations."""
    BULK_REPORTING_SIZE = 1000
    """The number of records to process before reporting progress."""
    # BULK_INSERT_BATCH_SIZE = 10000
    # BULK_UPDATE_BATCH_SIZE = 1000
    # BULK_REPORTING_SIZE = 10000
    MAX_RETRYS = 10
    """The maximum number of retries for database operations."""
    _tags_to_fields_mapping: dict[str, Any] | None = None
    """A mapping from XML tags to database fields and procedures."""

    @classmethod
    def loader_pass_one_manager(
        cls,
        repository: BaseRepository,
        parser: ParserBase,
        discogs_data_directory: Path,
        date: str,
        xml_tag: str,
        id_attr: str,
        skip_without: list[str],
        is_bulk_inserts=False,
    ) -> int:
        """
        Manages the first pass of the data loading process.

        This method iterates through an XML file, extracts data, and performs
        bulk insert or update operations in the database. It also manages
        concurrency and identifies records that need to be deleted.

        Args:
            repository (BaseRepository): The repository for database operations.
            parser: Parser to parse the XML data.
            discogs_data_directory (Path): The directory containing the XML files.
            date (str): The date of the XML data dump.
            xml_tag (str): The XML tag representing the records to load.
            id_attr (str): The attribute name for the ID in the data.
            skip_without (List[str]): A list of required fields, skip record if any are missing.
            is_bulk_inserts (bool): Whether to perform bulk inserts or updates.

        Returns:
            int: The number of processed records.

        Raises:
            DataError: If there is an error during a database operation.
            RuntimeError: If an error occurs in a worker process.

        """
        # Loader pass one.
        set_of_updated_ids: SortedSet[int] = SortedSet()
        """A sorted set to keep track of updated IDs."""

        initial_count = repository.count()
        """The initial count of records in the database."""

        processed_count = 0
        xml_path = LoaderUtils.get_xml_path(discogs_data_directory, xml_tag, date)
        log.info(f"Loading data from {xml_path}")
        with gzip.GzipFile(xml_path, "r") as file_pointer:
            iterator = ParserUtils.iterparse(file_pointer, xml_tag)
            bulk_records = []
            workers = []
            for i, element in enumerate(iterator):
                try:
                    data = parser.tags_to_fields(element)
                    if skip_without:
                        if any(not data.get(_) for _ in skip_without):
                            continue
                    # if element.get("id"):
                    #     data[id_attr] = element.get("id")
                    # log.debug(f"data: {data}")

                    set_of_updated_ids.add(int(data[id_attr]))

                    bulk_records.append(data)
                    processed_count += 1

                    if OfflineDatabaseManager.get_concurrency_count() > 1:
                        # Can do multi threading
                        if len(bulk_records) >= LoaderBase.BULK_INSERT_BATCH_SIZE:
                            if is_bulk_inserts:
                                worker = cls.insert_bulk(
                                    bulk_records,
                                    processed_count,
                                )
                            else:
                                worker = cls.update_bulk(
                                    bulk_records,
                                    processed_count,
                                )
                            worker.start()
                            workers.append(worker)
                            bulk_records.clear()
                        if (
                            len(workers)
                            > OfflineDatabaseManager.get_concurrency_count()
                        ):
                            worker = workers.pop(0)
                            cls.loader_wait_for_worker(worker)

                except DataError as e:
                    log.exception("Error in loader_pass_one", exc_info=True)
                    raise e

            if len(bulk_records) > 0:
                if is_bulk_inserts:
                    worker = cls.insert_bulk(
                        bulk_records,
                        processed_count,
                    )
                else:
                    worker = cls.update_bulk(
                        bulk_records,
                        processed_count,
                    )
                worker.start()
                workers.append(worker)
                bulk_records.clear()

            while len(workers) > 0:
                worker = workers.pop(0)
                cls.loader_wait_for_worker(worker)

            repository_count = repository.count()
            log.debug(f"repository_count: {repository_count}")

            new_inserts_count = repository_count - initial_count
            log.debug(f"processed_count: {processed_count}")
            log.debug(f"new_inserts_count: {new_inserts_count}")

            if xml_tag == "artist":
                entity_type = EntityType.ARTIST
            elif xml_tag == "label":
                entity_type = EntityType.LABEL
            elif xml_tag == "release":
                entity_type = None
            set_of_database_ids = cls.get_set_of_ids(entity_type)

            # Check if any records need to be deleted
            # (present in database and not present in the xml dump)
            ids_to_be_deleted = set_of_database_ids - set_of_updated_ids

            log.debug(f"number of update ids  : {len(set_of_updated_ids)}")
            log.debug(f"number of database ids: {len(set_of_database_ids)}")
            log.debug(f"number to be deleted  : {len(ids_to_be_deleted)}")

            number_in_batch = int(LoaderBase.BULK_INSERT_BATCH_SIZE / 10)

            if len(ids_to_be_deleted) > 0:
                workers = []
                batched_ids_to_be_deleted = utils.batched(
                    ids_to_be_deleted, number_in_batch
                )

                for batch_of_ids_to_be_deleted in batched_ids_to_be_deleted:
                    worker = cls.delete_bulk(
                        batch_of_ids_to_be_deleted,
                        len(batch_of_ids_to_be_deleted),
                    )
                    worker.start()
                    workers.append(worker)

                    if len(workers) > OfflineDatabaseManager.get_concurrency_count():
                        worker = workers.pop(0)
                        cls.loader_wait_for_worker(worker)

                while len(workers) > 0:
                    worker = workers.pop(0)
                    cls.loader_wait_for_worker(worker)

        return processed_count

    @classmethod
    @abstractmethod
    def insert_bulk(cls, bulk_inserts: list[dict[str, Any]], processed_count: int):
        """
        Performs a bulk insert operation.

        This method is called to insert a batch of records into the database.
        It must be implemented by subclasses to provide database-specific
        logic.

        Args:
            bulk_inserts (list[dict[str, Any]]): The list of records to insert.
            processed_count (int): The number of records processed so far.
        """
        pass

    @classmethod
    @abstractmethod
    def update_bulk(cls, bulk_updates: list[dict[str, Any]], processed_count: int):
        """
        Performs a bulk update operation.

        This method is called to update a batch of records in the database.
        It must be implemented by subclasses to provide database-specific
        logic.

        Args:
            bulk_updates (list[dict[str, Any]]): The list of records to update.
            processed_count (int): The number of records processed so far.
        """
        pass

    @classmethod
    @abstractmethod
    def delete_bulk(cls, bulk_deletes: list[int], processed_count: int):
        """
        Performs a bulk delete operation.

        This method is called to delete a batch of records from the database.
        It must be implemented by subclasses to provide database-specific
        logic.

        Args:
            bulk_deletes (list[int]): The list of IDs to delete.
            processed_count (int): The number of records processed so far.
        """
        pass

    @classmethod
    @abstractmethod
    def get_set_of_ids(cls, entity_type):
        """
        Retrieves a set of IDs from the database.

        This method is called to get a set of IDs for a specific entity type.
        It must be implemented by subclasses to provide database-specific logic.

        Args:
            entity_type: The type of entity to retrieve IDs for.
        """
        pass

    @classmethod
    def loader_wait_for_worker(cls, worker) -> None:
        """
        Waits for a worker process to finish.

        This method waits for a worker process to complete its task and checks
        for errors.

        Args:
            worker: The worker process to wait for.

        Raises:
            RuntimeError: If the worker process exits with a non-zero exit code.
        """
        if LOGGING_TRACE:
            log.debug(f"wait for worker {worker.name}")
        worker.join()
        worker.terminate()
        if worker.exitcode > 0:
            log.error(f"worker {worker.name} exitcode: {worker.exitcode}")
            raise RuntimeError("Error in worker process")
