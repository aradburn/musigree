import asyncio
import logging
from concurrent.futures import ProcessPoolExecutor, Executor, ThreadPoolExecutor
from pathlib import Path
from typing import Any

from musigree.exceptions import DatabaseError
from musigree.library.full_text_search.text_search_index import TextSearchIndex
from musigree.offline.data_access_layer.release_data_access import ReleaseDataAccess
from musigree.offline.database.entity_repository import EntityRepository
from musigree.offline.database.offline_transaction import offline_transaction
from musigree.offline.database.relation_repository import RelationRepository
from musigree.offline.database.release_repository import ReleaseRepository
from musigree.offline.database.role_repository import RoleRepository
from musigree.runtime.runtime_database.country_repository import CountryRepository
from musigree.runtime.runtime_database.genre_repository import GenreRepository
from musigree.runtime.runtime_database.runtime_entity_repository import (
    RuntimeEntityRepository,
)
from musigree.runtime.runtime_database.runtime_relation_repository import (
    RuntimeRelationRepository,
)
from musigree.runtime.runtime_database.runtime_role_repository import (
    RuntimeRoleRepository,
)
from musigree.runtime.runtime_database.runtime_transaction import runtime_transaction
from musigree.runtime.runtime_database.style_repository import StyleRepository
from musigree.runtime.runtime_database_manager import RuntimeDatabaseManager
from musigree.runtime.runtime_domain.country import Country
from musigree.runtime.runtime_domain.entity import to_runtime_entity_dict
from musigree.runtime.runtime_domain.genre import Genre
from musigree.runtime.runtime_domain.relation import (
    RuntimeRelationDB,
)
from musigree.runtime.runtime_domain.role import RuntimeRole
from musigree.runtime.runtime_domain.style import Style
from musigree.transfer.transfer_worker_entity_inserter import transfer_worker_entity_inserter
from musigree.transfer.transfer_worker_relation_inserter import transfer_worker_relation_inserter
from musigree.utils import async_chunks

log = logging.getLogger(__name__)


class TransferManager:
    BULK_INSERT_BATCH_SIZE = 100000

    @staticmethod
    async def transfer_entity() -> None:
        log.debug(f"Running transfer_entity()")

        assert RuntimeDatabaseManager.runtime_database_helper is not None, (
            "runtime_database_helper must be initialized before calling initialize()"
        )

        async with runtime_transaction():
            runtime_entity_repository = RuntimeEntityRepository()
            initial_count = await runtime_entity_repository.count()
        if initial_count > 0:
            error_msg = "Error in transfer_entity, runtime_entity table not empty"
            log.exception(error_msg, exc_info=True)
            raise DatabaseError

        processed_count = 0
        concurrency_count = RuntimeDatabaseManager.get_concurrency_count()

        async with offline_transaction():
            offline_entity_repository = EntityRepository()
            total_count = await offline_entity_repository.count()
            entities = offline_entity_repository.all()

            chunked_entities = async_chunks(entities, TransferManager.BULK_INSERT_BATCH_SIZE)

            if concurrency_count > 1:
                # Use ProcessPoolExecutor for concurrent processing
                with ProcessPoolExecutor(max_workers=concurrency_count) as executor:
                    async with asyncio.TaskGroup() as task_group:
                        async for chunk in chunked_entities:
                            bulk_records = []

                            for entity in chunk:
                                runtime_entity_dict = to_runtime_entity_dict(
                                    RuntimeDatabaseManager.runtime_database_helper.entity_details_index, entity)
                                bulk_records.append(runtime_entity_dict)
                                processed_count += 1

                            future = TransferManager.run_worker_function(executor,
                                                                         concurrency_count,
                                                                         transfer_worker_entity_inserter,
                                                                         bulk_records,
                                                                         processed_count, total_count,
                                                                         )
                            task_group.create_task(future)
            else:
                # Use single-threaded execution
                async for chunk in chunked_entities:
                    bulk_records = []

                    for entity in chunk:
                        runtime_entity_dict = to_runtime_entity_dict(
                            RuntimeDatabaseManager.runtime_database_helper.entity_details_index, entity)
                        bulk_records.append(runtime_entity_dict)
                        processed_count += 1

                    with ThreadPoolExecutor(max_workers=concurrency_count) as executor:
                        async with asyncio.TaskGroup() as task_group:
                            future = TransferManager.run_worker_function(executor,
                                                                         concurrency_count,
                                                                         transfer_worker_entity_inserter,
                                                                         bulk_records,
                                                                         processed_count, total_count,
                                                                         )
                            task_group.create_task(future)

        async with runtime_transaction():
            repository_count = await runtime_entity_repository.count()
        log.debug(f"runtime entity repository count: {repository_count}")

    @staticmethod
    async def transfer_relation() -> None:
        log.debug(f"Running transfer_relation()")
        async with offline_transaction():
            offline_relation_repository = RelationRepository()
            total_count = await offline_relation_repository.count()

        async with runtime_transaction():
            runtime_relation_repository = RuntimeRelationRepository()
            initial_count = await runtime_relation_repository.count()

        if initial_count > 0:
            error_msg = "Error in transfer_relation, runtime_relation table not empty"
            log.exception(error_msg, exc_info=True)
            raise DatabaseError

        processed_count = 0
        concurrency_count = RuntimeDatabaseManager.get_concurrency_count()

        async with offline_transaction():
            relations = offline_relation_repository.all()
            chunked_relations = async_chunks(relations, TransferManager.BULK_INSERT_BATCH_SIZE)

            if concurrency_count > 1:
                # Use ProcessPoolExecutor for concurrent processing
                with ProcessPoolExecutor(max_workers=concurrency_count) as executor:
                    async with asyncio.TaskGroup() as task_group:
                        async for chunk in chunked_relations:
                            bulk_records = []

                            for relation in chunk:
                                runtime_relation = RuntimeRelationDB(**relation.model_dump())
                                bulk_records.append(runtime_relation.model_dump())
                                processed_count += 1

                            future = TransferManager.run_worker_function(executor,
                                                                         concurrency_count,
                                                                         transfer_worker_relation_inserter,
                                                                         bulk_records,
                                                                         processed_count, total_count,
                                                                         )
                            task_group.create_task(future)
            else:
                # Use single-threaded execution
                async for chunk in chunked_relations:
                    bulk_records = []

                    for relation in chunk:
                        runtime_relation = RuntimeRelationDB(**relation.model_dump())
                        bulk_records.append(runtime_relation.model_dump())
                        processed_count += 1

                    with ThreadPoolExecutor(max_workers=concurrency_count) as executor:
                        async with asyncio.TaskGroup() as task_group:
                            future = TransferManager.run_worker_function(executor,
                                                                         concurrency_count,
                                                                         transfer_worker_relation_inserter,
                                                                         bulk_records, processed_count, total_count,
                                                                         )
                            task_group.create_task(future)

        async with runtime_transaction():
            repository_count = await runtime_relation_repository.count()
        log.debug(f"runtime relation repository count: {repository_count}")

    @staticmethod
    async def transfer_role() -> None:
        log.debug(f"Running transfer_role()")
        async with offline_transaction():
            roles = RoleRepository().all()

            async with runtime_transaction():
                runtime_role_repository = RuntimeRoleRepository()
                async for role in roles:
                    runtime_role = RuntimeRole(**role.model_dump())
                    await runtime_role_repository.create(runtime_role)

    @staticmethod
    async def transfer_entity_details() -> None:
        log.debug(f"Running transfer_entity_details()")

        assert RuntimeDatabaseManager.runtime_database_helper is not None, (
            "runtime_database_helper must be initialized before calling initialize()"
        )

        # Countries
        sorted_countries = sorted(RuntimeDatabaseManager.runtime_database_helper.entity_details_index.countries_list)

        async with runtime_transaction():
            runtime_country_repository = CountryRepository()
            for _id, country_name in enumerate(sorted_countries):
                country = Country(id=_id, country_name=country_name)
                await runtime_country_repository.create(country)
                await runtime_country_repository.commit()

        # Genres
        sorted_genres = sorted(RuntimeDatabaseManager.runtime_database_helper.entity_details_index.genres_list)

        async with runtime_transaction():
            runtime_genre_repository = GenreRepository()
            for _id, genre_name in enumerate(sorted_genres):
                genre = Genre(id=_id, genre_name=genre_name)
                await runtime_genre_repository.create(genre)
                await runtime_genre_repository.commit()

        # Styles
        sorted_styles = sorted(RuntimeDatabaseManager.runtime_database_helper.entity_details_index.styles_list)

        async with runtime_transaction():
            runtime_style_repository = StyleRepository()
            for _id, style_name in enumerate(sorted_styles):
                style = Style(id=_id, style_name=style_name)
                await runtime_style_repository.create(style)
                await runtime_style_repository.commit()

    @staticmethod
    async def transfer_load_text_search_index(text_search_path: Path) -> None:
        log.debug(f"Running transfer load text search index")
        assert RuntimeDatabaseManager.runtime_database_helper is not None, (
            "runtime_database_helper must be initialized before calling initialize()"
        )
        text_search_index = TextSearchIndex.load_text_search_index_from_file(text_search_path)
        RuntimeDatabaseManager.runtime_database_helper.text_search_index = text_search_index

    @staticmethod
    async def transfer_create_entity_details_index() -> None:
        log.debug(f"Running transfer create entity details index")
        assert RuntimeDatabaseManager.runtime_database_helper is not None, (
            "runtime_database_helper must be initialized before calling initialize()"
        )
        async with offline_transaction():
            offline_release_repository = ReleaseRepository()
            RuntimeDatabaseManager.runtime_database_helper.entity_details_index = await ReleaseDataAccess.create_entity_details_index(offline_release_repository)

    @classmethod
    async def run_worker_function(cls,
                                  pool_executor: Executor,
                                  concurrency_count: int,
                                  worker_function,
                                  bulk_records: list[dict[str, Any]],
                                  current_total: int, total_count: int,
                                  ) -> None:
        """
        Performs a bulk worker_function operation.

        This method is called to run worker_function on a batch of records in the database.

        Args:
            pool_executor (ProcessPoolExecutor): The executor for running the worker function.
            concurrency_count (int): The number of concurrent operations allowed.
            worker_function (callable): The worker function to execute.
            bulk_records (list[dict[str, Any]]): The list of dicts to process.
            current_total (int): The current total number of records processed.
            total_count (int): The total number of records to process.
        """
        loop = asyncio.get_running_loop()
        executor = pool_executor if concurrency_count > 1 else None
        future = loop.run_in_executor(executor, worker_function, bulk_records, current_total, total_count)
        return await future
