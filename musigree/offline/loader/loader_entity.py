import logging
import multiprocessing
from pathlib import Path
from typing import Callable, Any

from musigree import utils
from musigree.constants import BULK_INSERT_BATCH_SIZE, BULK_LOAD_CHUNK_SIZE
from musigree.library.fields.entity_type import EntityType
from musigree.library.full_text_search.text_search_index import TextSearchIndex
from musigree.offline.data_access_layer.offline_entity_data_access import OfflineEntityDataAccess
from musigree.offline.data_access_layer.offline_release_data_access import OfflineReleaseDataAccess
from musigree.offline.loader.loader_base import LoaderBase
from musigree.offline.loader.parser_entity import ParserEntity
from musigree.offline.loader.worker_entity_deleter import delete_entities_worker
from musigree.offline.loader.worker_entity_inserter import insert_entities_worker
from musigree.offline.loader.worker_entity_pass_four import process_entity_pass_four_worker
from musigree.offline.loader.worker_entity_pass_three import (
    process_entity_pass_three_worker,
)
from musigree.offline.loader.worker_entity_pass_two import (
    process_entity_pass_two_worker,
)
from musigree.offline.loader.worker_entity_updater import update_entities_worker
from musigree.offline.loader.worker_token_inserter import worker_token_inserter
from musigree.offline.offline_database.entity_repository import EntityRepository
from musigree.offline.offline_database.entity_table import EntityTable
from musigree.offline.offline_database.offline_transaction import offline_transaction
from musigree.offline.offline_database.release_repository import ReleaseRepository
from musigree.offline.offline_database.token_repository import TokenRepository
from musigree.offline.offline_database_manager import OfflineDatabaseManager
from musigree.offline.offline_domain.token import Token
from musigree.runtime.data_access_layer.entity_details_index import EntityDetailsIndex

log = logging.getLogger(__name__)


class LoaderEntity(LoaderBase):
    # CLASS METHODS

    @classmethod
    # @timeit
    async def loader_entity_pass_one(
        cls, discogs_data_directory: Path, data_date: str, is_bulk_inserts: bool = False
    ) -> None:
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
        log.info(f"Artists loaded: {artists_loaded}")

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
        log.info(f"Labels loaded : {labels_loaded}")

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
    # @timeit
    async def loader_entity_pass_four(cls) -> None:
        log.debug("loader entity pass four")
        await cls.loader_start_workers(process_entity_pass_four_worker)

    @classmethod
    async def loader_start_workers(cls, worker_function: Callable) -> None:
        async with offline_transaction():
            entity_repository = EntityRepository()
            total_count = await entity_repository.count()
            ids = await entity_repository.get_ids()

        batched_ids = utils.batched(ids, BULK_INSERT_BATCH_SIZE)

        worker_coroutines = utils.worker_generator(worker_function, batched_ids, total_count)

        assert OfflineDatabaseManager.offline_config is not None

        await utils.queue_worker_functions(
            OfflineDatabaseManager.get_concurrency_count(),
            worker_coroutines,
            OfflineDatabaseManager.offline_config.THREADING_MODEL,
        )

    @classmethod
    # @timeit
    async def loader_create_text_search_index(cls, text_search_path: Path) -> None:
        log.debug("loader entity create text search index")
        if not text_search_path.exists():
            text_search_index = await cls.loader_init_text_search_index_from_database()
            text_search_index.save_text_search_index_to_file(text_search_path)
        else:
            log.debug("create text search index - skipping...")

    @classmethod
    # @timeit
    async def loader_init_text_search_index_from_database(cls) -> TextSearchIndex:
        log.debug("loader entity init text search index from database")

        async with offline_transaction():
            entity_repository = EntityRepository()
            text_search_index = await OfflineEntityDataAccess.create_text_search_index(
                entity_repository
            )
        return text_search_index

    @classmethod
    # @timeit
    async def loader_create_entity_details_index(cls, entity_details_path: Path) -> None:
        log.debug("loader entity create entity details index")
        if not entity_details_path.exists():
            entity_details_index = await cls.loader_init_entity_details_index_from_database()
            entity_details_index.save_entity_details_index_to_file(entity_details_path)
        else:
            log.debug("create entity details index - skipping...")

    @classmethod
    async def loader_init_entity_details_index_from_database(cls) -> EntityDetailsIndex:
        log.debug("Running loader create entity details index")
        async with offline_transaction():
            offline_release_repository = ReleaseRepository()
            entity_details_index = await OfflineReleaseDataAccess.create_entity_details_index(
                offline_release_repository
            )

        return entity_details_index

    @classmethod
    async def loader_create_text_search_tokens(cls, text_search_path: Path) -> None:
        log.debug("loader entity create text search tokens")

        assert OfflineDatabaseManager.offline_database_helper is not None, (
            "offline_database_helper must be initialized before calling initialize()"
        )

        async with offline_transaction():
            offline_token_repository = TokenRepository()
            initial_count = await offline_token_repository.count()
        if initial_count > 0:
            log.info("Offline token table not empty, skip loading")
            log.debug(f"Offline token repository count: {initial_count}")
            return

        text_search_index = TextSearchIndex.load_text_search_index_from_file(text_search_path)
        # OfflineDatabaseManager.offline_database_helper.text_search_index = text_search_index

        worker = worker_token_inserter

        async def flush(chunk: list[Token], processed: int) -> None:
            batch_tokens = utils.batched(chunk, BULK_INSERT_BATCH_SIZE)
            worker_coroutines = utils.worker_generator(worker, batch_tokens, total_count)
            assert OfflineDatabaseManager._threading_model is not None, (
                "OfflineDatabaseManager _threading_model must be initialized"
            )
            await utils.queue_worker_functions(
                multiprocessing.cpu_count(),
                worker_coroutines,
                OfflineDatabaseManager._threading_model,
            )
            log.info(f"transferred {processed} of {total_count} tokens")

        tokens: list[Token] = []
        processed_count = 0

        total_count = 0

        for _token, entity_ids in text_search_index.token_index.items():
            total_count += len(entity_ids)
        log.debug(f"loading {total_count} tokens...")

        for token, entity_ids in text_search_index.token_index.items():
            for entity_id in entity_ids:
                token_entry = Token(token=token, entity_id=entity_id)
                tokens.append(token_entry)

                if len(tokens) >= BULK_LOAD_CHUNK_SIZE:
                    processed_count += len(tokens)
                    await flush(tokens, processed_count)
                    tokens.clear()

        if tokens:
            processed_count += len(tokens)
            await flush(tokens, processed_count)

        async with offline_transaction():
            repository_count = await offline_token_repository.count()
        log.debug(f"offline token repository count: {repository_count}")
