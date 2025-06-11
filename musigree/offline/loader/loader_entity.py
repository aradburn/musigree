import logging
import pickle
from pathlib import Path
from typing import Any

from sortedcontainers import SortedSet

from musigree.offline.data_access_layer.entity_data_access import EntityDataAccess
from musigree.offline.database.entity_repository import EntityRepository
from musigree.offline.database.entity_table import EntityTable
from musigree.offline.database.offline_transaction import offline_transaction
from musigree.library.full_text_search.text_search_index import TextSearchIndex
from musigree.offline.loader.loader_base import LoaderBase
from musigree.offline.loader.parser_entity import ParserEntity
from musigree.offline.loader.worker_entity_deleter import WorkerEntityDeleter
from musigree.offline.loader.worker_entity_inserter import WorkerEntityInserter
from musigree.offline.loader.worker_entity_pass_three import WorkerEntityPassThree
from musigree.offline.loader.worker_entity_pass_two import WorkerEntityPassTwo
from musigree.offline.loader.worker_entity_updater import WorkerEntityUpdater
from musigree.offline.offline_database_manager import OfflineDatabaseManager
from musigree.utils import timeit

log = logging.getLogger(__name__)


class LoaderEntity(LoaderBase):
    # CLASS METHODS

    @classmethod
    @timeit
    def loader_entity_pass_one(
        cls, discogs_data_directory: Path, data_date: str, is_bulk_inserts=False
    ) -> int:
        log.debug(f"loader entity pass one - artist - date: {data_date}")
        with offline_transaction():
            entity_repository = EntityRepository()
            entity_parser = ParserEntity()
            artists_loaded = cls.loader_pass_one_manager(
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
        with offline_transaction():
            entity_repository = EntityRepository()
            entity_parser = ParserEntity()
            labels_loaded = cls.loader_pass_one_manager(
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
    def insert_bulk(cls, bulk_inserts: list[dict[str, Any]], inserted_count: int):
        worker = WorkerEntityInserter(
            bulk_inserts=bulk_inserts,
            inserted_count=inserted_count,
        )
        return worker

    @classmethod
    def update_bulk(cls, bulk_updates: list[dict[str, Any]], processed_count: int):
        worker = WorkerEntityUpdater(
            bulk_updates=bulk_updates,
            processed_count=processed_count,
        )
        return worker

    @classmethod
    def delete_bulk(cls, bulk_deletes: list[int], processed_count: int):
        worker = WorkerEntityDeleter(
            bulk_deletes=bulk_deletes,
            processed_count=processed_count,
        )
        return worker

    @classmethod
    def get_set_of_ids(cls, entity_type):
        with offline_transaction():
            entity_repository = EntityRepository()
            ids = entity_repository.get_ids_by_type(entity_type)
        set_of_entity_ids = SortedSet(ids)
        return set_of_entity_ids

    @classmethod
    @timeit
    def loader_entity_pass_two(cls) -> None:
        log.debug("loader entity pass two")
        cls.loader_start_workers(WorkerEntityPassTwo)

    @classmethod
    @timeit
    def loader_entity_pass_three(cls):
        log.debug("loader entity pass three")
        cls.loader_start_workers(WorkerEntityPassThree)

    @classmethod
    def loader_start_workers(cls, worker_class) -> None:
        number_in_batch = int(LoaderBase.BULK_INSERT_BATCH_SIZE)

        with offline_transaction():
            entity_repository = EntityRepository()
            total_count = entity_repository.count()
            batched_ids = entity_repository.get_batched_ids(number_in_batch)

        current_total = 0

        workers = []
        for ids in batched_ids:
            # log.debug(f"batched ids: {ids}")
            worker = worker_class(ids, current_total, total_count)
            worker.start()
            workers.append(worker)
            current_total += number_in_batch

            if len(workers) > OfflineDatabaseManager.get_concurrency_count():
                worker = workers.pop(0)
                cls.loader_wait_for_worker(worker)

        while len(workers) > 0:
            worker = workers.pop(0)
            cls.loader_wait_for_worker(worker)

    @classmethod
    @timeit
    def loader_create_text_search_index(cls, text_search_path: Path) -> None:
        log.debug(f"loader entity create text search index")
        if not text_search_path.exists():
            text_search_index = cls.loader_init_text_search_index_from_database()
            cls.save_text_search_index_to_file(text_search_path, text_search_index)
        else:
            log.debug("create text search index - skipping...")

    @classmethod
    @timeit
    def loader_init_text_search_index_from_database(cls) -> TextSearchIndex:
        log.debug(f"loader entity init text search index from database")
        text_search_index = TextSearchIndex()

        with offline_transaction():
            entity_repository = EntityRepository()
            EntityDataAccess.init_text_search_index(
                entity_repository, text_search_index
            )
        return text_search_index

    @classmethod
    @timeit
    def save_text_search_index_to_file(
        cls, filename: Path, text_search_index: TextSearchIndex
    ) -> None:
        log.debug(f"save text search index to file: {filename}")

        # open a file, where you ant to store the data
        with open(filename, "wb") as file:
            # dump information to that file
            # noinspection PyTypeChecker
            pickle.dump(text_search_index, file)
