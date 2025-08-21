import asyncio
import logging
import pickle
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any, Callable

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

    @classmethod
    async def insert_bulk(
        cls,
        bulk_inserts: list[dict[str, Any]],
        inserted_count: int,
        executor: ProcessPoolExecutor,
        concurrency_count: int,
    ) -> None:
        """
        Performs a bulk insert operation for entities.

        This method is called to insert a batch of entity records in the
        database using the `insert_entities_worker` function.

        Args:
            bulk_inserts (list[dict[str, Any]]): The list of release records to update.
            inserted_count (int): The number of records processed so far.
            executor (ProcessPoolExecutor): The executor to submit the work to.
            concurrency_count (int): The number of concurrent operations allowed.
        """
        loop = asyncio.get_running_loop()
        if concurrency_count > 1:
            future = loop.run_in_executor(
                executor, insert_entities_worker, bulk_inserts, inserted_count
            )
        else:
            future = loop.run_in_executor(
                None, insert_entities_worker, bulk_inserts, inserted_count
            )
        return await future

    @classmethod
    async def update_bulk(
        cls,
        bulk_updates: list[dict[str, Any]],
        processed_count: int,
        executor: ProcessPoolExecutor,
        concurrency_count: int,
    ) -> None:
        """
        Performs a bulk update operation for entties.

        This method is called to update a batch of release records in the
        database using the `update_entities_worker` function.

        Args:
            bulk_updates (list[dict[str, Any]]): The list of entity records to update.
            processed_count (int): The number of records processed so far.
            executor (ProcessPoolExecutor): The executor to submit the work to.
            concurrency_count (int): The number of concurrent operations allowed.
        """
        loop = asyncio.get_running_loop()
        if concurrency_count > 1:
            future = loop.run_in_executor(
                executor, update_entities_worker, bulk_updates, processed_count
            )
        else:
            future = loop.run_in_executor(
                None, update_entities_worker, bulk_updates, processed_count
            )
        return await future

    @classmethod
    async def delete_bulk(
        cls,
        bulk_deletes: list[int],
        processed_count: int,
        executor: ProcessPoolExecutor,
        concurrency_count: int,
    ) -> None:
        """
        Performs a bulk delete operation for entities.

        This method is called to update a batch of entity records in the
        database using the `update_entities_worker` function.

        Args:
            bulk_deletes (list[dict[str, Any]]): The list of release records to update.
            processed_count (int): The number of records processed so far.
            executor (ProcessPoolExecutor): The executor to submit the work to.
            concurrency_count (int): The number of concurrent operations allowed.
        """
        loop = asyncio.get_running_loop()
        if concurrency_count > 1:
            future = loop.run_in_executor(
                executor, delete_entities_worker, bulk_deletes, processed_count
            )
        else:
            future = loop.run_in_executor(
                None, delete_entities_worker, bulk_deletes, processed_count
            )
        return await future

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
            batched_ids = await entity_repository.get_batched_ids(number_in_batch)

        current_total = 0
        concurrency_count = OfflineDatabaseManager.get_concurrency_count()

        if concurrency_count > 1:
            # Use ProcessPoolExecutor for concurrent processing
            with ProcessPoolExecutor(max_workers=concurrency_count) as executor:
                async with asyncio.TaskGroup() as task_group:
                    for ids in batched_ids:
                        future = cls.run_worker_function(
                            worker_function,
                            ids,
                            current_total,
                            total_count,
                            executor,
                            concurrency_count,
                        )
                        task_group.create_task(future)
                        current_total += number_in_batch
        else:
            # Use single-threaded execution
            for ids in batched_ids:
                with ProcessPoolExecutor(max_workers=concurrency_count) as executor:
                    async with asyncio.TaskGroup() as task_group:
                        future = cls.run_worker_function(
                            worker_function,
                            ids,
                            current_total,
                            total_count,
                            executor,
                            concurrency_count,
                        )
                        task_group.create_task(future)
                        current_total += number_in_batch

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
