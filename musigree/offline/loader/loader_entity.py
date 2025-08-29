import logging
import pickle
from pathlib import Path
from typing import Callable, Any

from musigree import utils
from musigree.library.fields.entity_type import EntityType
from musigree.library.full_text_search.text_search_index import TextSearchIndex
from musigree.offline.data_access_layer.entity_data_access import EntityDataAccess
from musigree.offline.database.entity_repository import EntityRepository
from musigree.offline.database.entity_table import EntityTable
from musigree.offline.database.offline_transaction import offline_transaction
from musigree.offline.loader.loader_base import LoaderBase
from musigree.offline.loader.parser_entity import ParserEntity
from musigree.offline.loader.worker_entity_deleter import delete_entities_worker
from musigree.offline.loader.worker_entity_inserter import insert_entities_worker
from musigree.offline.loader.worker_entity_pass_three import (
    process_entity_pass_three_worker,
)
from musigree.offline.loader.worker_entity_pass_two import (
    process_entity_pass_two_worker,
)
from musigree.offline.loader.worker_entity_updater import update_entities_worker
from musigree.offline.offline_database_manager import OfflineDatabaseManager

log = logging.getLogger(__name__)


class LoaderEntity(LoaderBase):
    # CLASS METHODS

    @classmethod
    # @timeit
    async def loader_entity_pass_one(
        cls, discogs_data_directory: Path, data_date: str, is_bulk_inserts: bool = False
    ) -> int:
        log.debug(f"loader entity pass one - artist - date: {data_date}")
        entity_repository = EntityRepository()
        entity_parser = ParserEntity()
        artists_loaded = await cls.loader_pass_one_manager(
            repository=entity_repository,
            parser=entity_parser,
            discogs_data_directory=discogs_data_directory,
            date=data_date,
            xml_tag="artist",
            id_attr=EntityTable.id.name,
            skip_without=["entity_name"],
            is_bulk_inserts=is_bulk_inserts,
        )
        log.debug(f"loader entity pass one - label - date: {data_date}")
        entity_repository = EntityRepository()
        entity_parser = ParserEntity()
        labels_loaded = await cls.loader_pass_one_manager(
            repository=entity_repository,
            parser=entity_parser,
            discogs_data_directory=discogs_data_directory,
            date=data_date,
            xml_tag="label",
            id_attr=EntityTable.id.name,
            skip_without=["entity_name"],
            is_bulk_inserts=is_bulk_inserts,
        )
        return artists_loaded + labels_loaded

    @staticmethod
    def get_insert_worker_function() -> Callable[[list[dict[str, Any]], int, int], None]:
        return insert_entities_worker

    @staticmethod
    def get_update_worker_function() -> Callable[[list[dict[str, Any]], int, int], None]:
        return update_entities_worker

    @staticmethod
    def get_delete_worker_function() -> Callable[[list[int], int, int], None]:
        return delete_entities_worker

    @classmethod
    async def get_set_of_ids(cls, entity_type: EntityType | None) -> set[int]:
        """
        Retrieves a set of entity IDs from the database.

        This method is called to get a set of all entity IDs for a specific type.

        Args:
            entity_type: The type of entity to retrieve IDs for.
        Returns:
            set[int]: The set of entity IDs.
        """
        async with offline_transaction():
            entity_repository = EntityRepository()
            """Instance of EntityRepository for database operations on entities."""
            assert entity_type is not None, "Entity type must be specified"
            ids = await entity_repository.get_ids_by_type(entity_type)
        set_of_ids = set(ids)
        return set_of_ids

    @classmethod
    # @timeit
    async def loader_entity_pass_two(cls) -> None:
        log.debug("loader entity pass two")
        await cls.loader_start_workers(process_entity_pass_two_worker)

    @classmethod
    # @timeit
    async def loader_entity_pass_three(cls) -> None:
        log.debug("loader entity pass three")
        await cls.loader_start_workers(process_entity_pass_three_worker)

    @classmethod
    async def loader_start_workers(cls, worker_function: Callable) -> None:
        number_in_batch = int(LoaderBase.BULK_INSERT_BATCH_SIZE)

        async with offline_transaction():
            entity_repository = EntityRepository()
            total_count = await entity_repository.count()
            ids = await entity_repository.get_ids()

        batched_ids = utils.batched(ids, number_in_batch)

        worker_coroutines = utils.worker_generator(worker_function, batched_ids, total_count)

        await utils.queue_worker_functions(OfflineDatabaseManager.get_concurrency_count(), worker_coroutines)

    @classmethod
    # @timeit
    async def loader_create_text_search_index(cls, text_search_path: Path) -> None:
        log.debug("loader entity create text search index")
        if not text_search_path.exists():
            text_search_index = await cls.loader_init_text_search_index_from_database()
            cls.save_text_search_index_to_file(text_search_path, text_search_index)
        else:
            log.debug("create text search index - skipping...")

    @classmethod
    # @timeit
    async def loader_init_text_search_index_from_database(cls) -> TextSearchIndex:
        log.debug("loader entity init text search index from database")
        text_search_index = TextSearchIndex()

        async with offline_transaction():
            entity_repository = EntityRepository()
            await EntityDataAccess.init_text_search_index(
                entity_repository, text_search_index
            )
        return text_search_index

    @classmethod
    # @timeit
    def save_text_search_index_to_file(
        cls, filename: Path, text_search_index: TextSearchIndex
    ) -> None:
        log.debug(f"save text search index to file: {filename}")

        # open a file, where you ant to store the data
        with open(filename, "wb") as file:
            # dump information to that file
            # noinspection PyTypeChecker
            pickle.dump(text_search_index, file)
