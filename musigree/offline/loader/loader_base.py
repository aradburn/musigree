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
from abc import abstractmethod, ABC
from collections.abc import Iterator
from pathlib import Path
from typing import Any, Generator, Callable

from sortedcontainers import SortedSet
from sqlalchemy.exc import DataError

from musigree import utils
from musigree.constants import BULK_INSERT_BATCH_SIZE
from musigree.library.fields.entity_type import EntityType
from musigree.offline.loader.loader_utils import LoaderUtils
from musigree.offline.loader.parser_base import ParserBase
from musigree.offline.loader.parser_utils import ParserUtils
from musigree.offline.offline_database.base_repository import BaseRepository
from musigree.offline.offline_database.offline_transaction import offline_transaction
from musigree.offline.offline_database_manager import OfflineDatabaseManager

log = logging.getLogger(__name__)
"""
The logger for the LoaderBase module.
"""


class LoaderBase(ABC):
    """
    Abstract base class for data loaders.

    This class provides a framework for loading data from XML files into the
    database, handling bulk operations, concurrency, and data preprocessing.

    Attributes:
        _tags_to_fields_mapping (dict): A mapping from XML tags to database fields and procedures.
    """

    _tags_to_fields_mapping: dict[str, Any] | None = None
    """A mapping from XML tags to database fields and procedures."""

    @staticmethod
    def process_xml(
        parser: ParserBase,
        xml_path: str,
        xml_tag: str,
        skip_without: list[str],
    ) -> Generator[dict[str, Any], None, None]:
        with gzip.GzipFile(xml_path, "r") as file_pointer:
            iterator = ParserUtils.iterparse(file_pointer, xml_tag)

            for element in iterator:
                try:
                    data = parser.tags_to_fields(element)
                    if skip_without:
                        if any(not data.get(_) for _ in skip_without):
                            continue
                    # if element.get("id"):
                    #     data[id_attr] = element.get("id")
                    # log.debug(f"data: {data}")

                    yield data

                except DataError as e:
                    log.exception("Error in loader_pass_one", exc_info=True)
                    raise e

    @classmethod
    async def loader_pass_one_manager(
        cls,
        repository: BaseRepository,
        parser: ParserBase,
        discogs_data_directory: Path,
        date: str,
        xml_tag: str,
        id_attr: str,
        skip_without: list[str],
        is_bulk_inserts: bool = False,
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
        id_accumulator: list[int] = []
        """A list to accumulate IDs of processed records."""
        set_of_updated_ids: SortedSet[int] = SortedSet()
        """A sorted set to keep track of updated IDs."""

        async with offline_transaction():
            initial_count = await repository.count()
        log.debug(f"initial_count: {initial_count}")

        processed_count = 0
        xml_path = LoaderUtils.get_xml_path(discogs_data_directory, xml_tag, date)
        log.info(f"Loading data from {xml_path}")

        worker = (
            cls.get_insert_worker_function()
            if is_bulk_inserts
            else cls.get_update_worker_function()
        )

        records = cls.process_xml(parser, xml_path, xml_tag, skip_without)

        records_with_accumulated_ids = utils.generator_with_id_accumulator(
            records, id_accumulator, id_attr
        )

        batch_records = utils.batched(records_with_accumulated_ids, BULK_INSERT_BATCH_SIZE)

        worker_coroutines = utils.worker_generator(worker, batch_records, 0)

        assert OfflineDatabaseManager.offline_config is not None

        await utils.queue_worker_functions(
            OfflineDatabaseManager.get_concurrency_count(),
            worker_coroutines,
            OfflineDatabaseManager.offline_config.THREADING_MODEL,
        )

        for _id in id_accumulator:
            set_of_updated_ids.add(_id)

        async with offline_transaction():
            repository_count = await repository.count()
        log.debug(f"repository_count: {repository_count}")

        new_inserts_count = repository_count - initial_count
        log.debug(f"processed_count: {processed_count}")
        log.debug(f"new_inserts_count: {new_inserts_count}")

        entity_type: EntityType | None = None
        if xml_tag == "artist":
            entity_type = EntityType.ARTIST
        elif xml_tag == "label":
            entity_type = EntityType.LABEL

        set_of_database_ids: set[int] = await cls.get_set_of_ids(entity_type)

        # Check if any records need to be deleted
        # (present in database and not present in the xml dump)
        ids_to_be_deleted: set[int] = set_of_database_ids - set_of_updated_ids

        log.debug(f"number of update ids  : {len(set_of_updated_ids)}")
        log.debug(f"number of database ids: {len(set_of_database_ids)}")
        log.debug(f"number to be deleted  : {len(ids_to_be_deleted)}")

        if len(ids_to_be_deleted) > 0:
            delete_worker = cls.get_delete_worker_function()

            batched_ids_to_be_deleted: Iterator[list[int]] = utils.batched(
                list(ids_to_be_deleted), BULK_INSERT_BATCH_SIZE
            )

            worker_coroutines = utils.worker_generator(
                delete_worker, batched_ids_to_be_deleted, len(ids_to_be_deleted)
            )

            assert OfflineDatabaseManager.offline_config is not None

            await utils.queue_worker_functions(
                OfflineDatabaseManager.get_concurrency_count(),
                worker_coroutines,
                OfflineDatabaseManager.offline_config.THREADING_MODEL,
            )

        return processed_count

    @staticmethod
    @abstractmethod
    def get_insert_worker_function() -> Callable[[list[dict[str, Any]], int, int], None]:
        pass

    @staticmethod
    @abstractmethod
    def get_update_worker_function() -> Callable[[list[dict[str, Any]], int, int], None]:
        pass

    @staticmethod
    @abstractmethod
    def get_delete_worker_function() -> Callable[[list[int], int, int], None]:
        pass

    @classmethod
    @abstractmethod
    async def get_set_of_ids(cls, entity_type: EntityType | None) -> set[int]:
        """
        Retrieves a set of IDs from the database.

        This method is called to get a set of IDs for a specific entity type.
        It must be implemented by subclasses to provide database-specific logic.

        Args:
            entity_type: The type of entity to retrieve IDs for.

        Returns:
            set[int]: The set of IDs.
        """
        pass
