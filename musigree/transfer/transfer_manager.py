import logging
import multiprocessing
from pathlib import Path

from musigree import utils
from musigree.constants import BULK_INSERT_BATCH_SIZE, BULK_LOAD_CHUNK_SIZE
from musigree.library.full_text_search.text_search_index import TextSearchIndex
from musigree.offline.offline_database.entity_repository import EntityRepository
from musigree.offline.offline_database.offline_transaction import offline_transaction
from musigree.offline.offline_database.relation_repository import RelationRepository
from musigree.offline.offline_database.role_repository import RoleRepository
from musigree.offline.offline_domain.entity import Entity
from musigree.offline.offline_domain.relation import RelationDB
from musigree.runtime.data_access_layer.entity_details_index import EntityDetailsIndex
from musigree.runtime.runtime_database.runtime_country_repository import RuntimeCountryRepository
from musigree.runtime.runtime_database.runtime_entity_repository import (
    RuntimeEntityRepository,
)
from musigree.runtime.runtime_database.runtime_genre_repository import RuntimeGenreRepository
from musigree.runtime.runtime_database.runtime_relation_repository import (
    RuntimeRelationRepository,
)
from musigree.runtime.runtime_database.runtime_role_repository import (
    RuntimeRoleRepository,
)
from musigree.runtime.runtime_database.runtime_style_repository import RuntimeStyleRepository
from musigree.runtime.runtime_database.runtime_token_repository import RuntimeTokenRepository
from musigree.runtime.runtime_database.runtime_transaction import runtime_transaction
from musigree.runtime.runtime_database_manager import RuntimeDatabaseManager
from musigree.runtime.runtime_domain.runtime_country import RuntimeCountry
from musigree.runtime.runtime_domain.runtime_genre import RuntimeGenre
from musigree.runtime.runtime_domain.runtime_role import RuntimeRole
from musigree.runtime.runtime_domain.runtime_style import RuntimeStyle
from musigree.runtime.runtime_domain.runtime_token import RuntimeToken
from musigree.transfer.transfer_worker_entity_inserter import (
    transfer_worker_entity_inserter,
)
from musigree.transfer.transfer_worker_relation_inserter import (
    transfer_worker_relation_inserter,
)
from musigree.transfer.transfer_worker_token_inserter import transfer_worker_token_inserter

log = logging.getLogger(__name__)


class TransferManager:
    @staticmethod
    async def transfer_entity() -> None:
        log.debug("Running transfer_entity()")

        assert RuntimeDatabaseManager.runtime_database_helper is not None, (
            "runtime_database_helper must be initialized before calling initialize()"
        )

        async with runtime_transaction():
            runtime_entity_repository = RuntimeEntityRepository()
            initial_count = await runtime_entity_repository.count()
        if initial_count > 0:
            log.info("Runtime entity table not empty, skip loading")
            log.debug(f"Runtime entity repository count: {initial_count}")
            return

        worker = transfer_worker_entity_inserter

        async def flush(chunk: list[Entity], processed: int) -> None:
            batch_relations = utils.batched(chunk, BULK_INSERT_BATCH_SIZE)
            worker_coroutines = utils.worker_generator(worker, batch_relations, total_count)
            await utils.queue_worker_functions(multiprocessing.cpu_count(), worker_coroutines)
            log.info(f"transferred {processed} of {total_count} entities")

        async with offline_transaction():
            offline_entity_repository = EntityRepository()
            total_count = await offline_entity_repository.count()
            log.debug(f"transfering {total_count} entities...")

            entities: list[Entity] = []
            processed_count = 0
            async for entity_list in offline_entity_repository.all():
                log.debug(f"read {len(entity_list)} entities...")
                entities.extend(entity_list)
                if len(entities) >= BULK_LOAD_CHUNK_SIZE:
                    processed_count += len(entities)
                    await flush(entities, processed_count)
                    entities.clear()

            if entities:
                processed_count += len(entities)
                await flush(entities, processed_count)

        async with runtime_transaction():
            repository_count = await runtime_entity_repository.count()
        log.debug(f"Runtime entity repository count: {repository_count}")

    @staticmethod
    async def transfer_relation() -> None:
        log.debug("Running transfer_relation()")

        assert RuntimeDatabaseManager.runtime_database_helper is not None, (
            "runtime_database_helper must be initialized before calling initialize()"
        )

        async with runtime_transaction():
            runtime_relation_repository = RuntimeRelationRepository()
            initial_count = await runtime_relation_repository.count()

        if initial_count > 0:
            log.info("Runtime relation table not empty, skip loading")
            log.debug(f"Runtime relation repository count: {initial_count}")
            return

        worker = transfer_worker_relation_inserter

        # The relation table can hold hundreds of millions of rows, far more
        # than fits in memory. Stream the DB partitions into a bounded buffer
        # and flush roughly BULK_LOAD_CHUNK_SIZE rows at a time to a saturated
        # process pool. This keeps memory bounded while still feeding each pool
        # enough batches to keep all worker processes busy (instead of spinning
        # up a pool per small DB partition).
        async def flush(chunk: list[RelationDB], processed: int) -> None:
            batch_relations = utils.batched(chunk, BULK_INSERT_BATCH_SIZE)
            worker_coroutines = utils.worker_generator(worker, batch_relations, total_count)
            await utils.queue_worker_functions(multiprocessing.cpu_count(), worker_coroutines)
            log.info(f"transferred {processed} of {total_count} relations")

        async with offline_transaction():
            offline_relation_repository = RelationRepository()
            total_count = await offline_relation_repository.count()
            log.debug(f"transfering {total_count} relations...")

            relations: list[RelationDB] = []
            processed_count = 0
            async for relation_list in offline_relation_repository.all():
                log.debug(f"read {len(relation_list)} relations...")
                relations.extend(relation_list)
                if len(relations) >= BULK_LOAD_CHUNK_SIZE:
                    processed_count += len(relations)
                    await flush(relations, processed_count)
                    relations.clear()

            if relations:
                processed_count += len(relations)
                await flush(relations, processed_count)

        async with runtime_transaction():
            repository_count = await runtime_relation_repository.count()
        log.debug(f"runtime relation repository count: {repository_count}")

        # Create indexes
        # log.debug("runtime relation create indexes...")
        # # Create relation subject predicate index
        # index_sp = Index("idx_runtime_relation_subject_predicate", RuntimeRelationTable.subject,
        #                  RuntimeRelationTable.predicate)
        # index_op = Index("idx_runtime_relation_object_predicate", RuntimeRelationTable.object,
        #                  RuntimeRelationTable.predicate)
        # RuntimeDatabaseManager.runtime_database_helper.extra_indexes.add(index_sp)
        # RuntimeDatabaseManager.runtime_database_helper.extra_indexes.add(index_op)

        # DDL is synchronous, so run it through an async connection via run_sync.
        # async_engine = RuntimeDatabaseManager.runtime_database_helper.runtime_async_engine
        # assert async_engine is not None, (
        #     "runtime_async_engine must be initialized before creating indexes"
        # )
        # async with async_engine.begin() as conn:
        #     try:
        #         await conn.run_sync(index_sp.drop, checkfirst=True)
        #     except ProgrammingError:
        #         log.debug(f"runtime relation index {index_sp.name} cant drop")
        #     except OperationalError:
        #         log.debug(f"runtime relation index {index_sp.name} cant drop")
        # async with async_engine.begin() as conn:
        #     try:
        #         await conn.run_sync(index_sp.create, checkfirst=True)
        #     except ProgrammingError:
        #         log.debug(f"runtime relation index {index_sp.name} already exists")
        #     except OperationalError:
        #         log.debug(f"runtime relation index {index_sp.name} already exists")
        # async with async_engine.begin() as conn:
        #     try:
        #         await conn.run_sync(index_op.drop, checkfirst=True)
        #     except ProgrammingError:
        #         log.debug(f"runtime relation index {index_op.name} cant drop")
        #     except OperationalError:
        #         log.debug(f"runtime relation index {index_op.name} cant drop")
        # async with async_engine.begin() as conn:
        #     try:
        #         await conn.run_sync(index_op.create, checkfirst=True)
        #     except ProgrammingError:
        #         log.debug(f"runtime relation index {index_op.name} already exists")
        #     except OperationalError:
        #         log.debug(f"runtime relation index {index_op.name} already exists")
        #
        # log.debug("runtime relation created indexes")

    @staticmethod
    async def transfer_role() -> None:
        log.debug("Running transfer_role()")

        async with runtime_transaction():
            runtime_role_repository = RuntimeRoleRepository()
            initial_count = await runtime_role_repository.count()
        if initial_count > 0:
            log.info("Runtime role table not empty, skip loading")
            log.debug(f"Runtime role repository count: {initial_count}")
            return

        async with offline_transaction():
            roles = RoleRepository().all()

            async with runtime_transaction():
                runtime_role_repository = RuntimeRoleRepository()
                async for role in roles:
                    runtime_role = RuntimeRole(**role.model_dump())
                    await runtime_role_repository.create(runtime_role)

    @staticmethod
    async def transfer_entity_details() -> None:
        log.debug("Running transfer_entity_details()")

        assert RuntimeDatabaseManager.runtime_database_helper is not None, (
            "runtime_database_helper must be initialized before calling initialize()"
        )

        async with runtime_transaction():
            runtime_country_repository = RuntimeCountryRepository()
            initial_count = await runtime_country_repository.count()
        if initial_count > 0:
            log.info("Runtime country table not empty, skip loading")
            log.debug(f"Runtime country repository count: {initial_count}")
        else:
            # Countries
            log.debug("Running transfer_entity_details: countries")
            sorted_countries = sorted(
                RuntimeDatabaseManager.runtime_database_helper.entity_details_index.countries_list
            )

            async with runtime_transaction():
                runtime_country_repository = RuntimeCountryRepository()
                for _id, country_name in enumerate(sorted_countries):
                    country = RuntimeCountry(id=_id, country_name=country_name)
                    await runtime_country_repository.create(country)
                    await runtime_country_repository.commit()

        # Genres
        async with runtime_transaction():
            runtime_genre_repository = RuntimeGenreRepository()
            initial_count = await runtime_genre_repository.count()
        if initial_count > 0:
            log.info("Runtime genre table not empty, skip loading")
            log.debug(f"Runtime genre repository count: {initial_count}")
        else:
            log.debug("Running transfer_entity_details: genres")
            sorted_genres = sorted(
                RuntimeDatabaseManager.runtime_database_helper.entity_details_index.genres_list
            )

            async with runtime_transaction():
                runtime_genre_repository = RuntimeGenreRepository()
                for _id, genre_name in enumerate(sorted_genres):
                    genre = RuntimeGenre(id=_id, genre_name=genre_name)
                    await runtime_genre_repository.create(genre)
                    await runtime_genre_repository.commit()

        # Styles
        async with runtime_transaction():
            runtime_style_repository = RuntimeStyleRepository()
            initial_count = await runtime_style_repository.count()
        if initial_count > 0:
            log.info("Runtime style table not empty, skip loading")
            log.debug(f"Runtime style repository count: {initial_count}")
        else:
            log.debug("Running transfer_entity_details: styles")
            sorted_styles = sorted(
                RuntimeDatabaseManager.runtime_database_helper.entity_details_index.styles_list
            )

            async with runtime_transaction():
                runtime_style_repository = RuntimeStyleRepository()
                for _id, style_name in enumerate(sorted_styles):
                    style = RuntimeStyle(id=_id, style_name=style_name)
                    await runtime_style_repository.create(style)
                    await runtime_style_repository.commit()

    @staticmethod
    async def transfer_load_text_search_index(text_search_path: Path) -> None:
        log.debug("Running transfer load text search index")
        assert RuntimeDatabaseManager.runtime_database_helper is not None, (
            "runtime_database_helper must be initialized before calling initialize()"
        )

        async with runtime_transaction():
            runtime_token_repository = RuntimeTokenRepository()
            initial_count = await runtime_token_repository.count()
        if initial_count > 0:
            log.info("Runtime token table not empty, skip loading")
            log.debug(f"Runtime token repository count: {initial_count}")
            return

        text_search_index = TextSearchIndex.load_text_search_index_from_file(text_search_path)
        RuntimeDatabaseManager.runtime_database_helper.text_search_index = text_search_index

        worker = transfer_worker_token_inserter

        async def flush(chunk: list[RuntimeToken], processed: int) -> None:
            batch_tokens = utils.batched(chunk, BULK_INSERT_BATCH_SIZE)
            worker_coroutines = utils.worker_generator(worker, batch_tokens, total_count)
            await utils.queue_worker_functions(multiprocessing.cpu_count(), worker_coroutines)
            log.info(f"transferred {processed} of {total_count} tokens")

        tokens: list[RuntimeToken] = []
        processed_count = 0

        total_count = 0

        for _token, entity_ids in text_search_index.token_index.items():
            total_count += len(entity_ids)
        log.debug(f"transfering {total_count} tokens...")

        for token, entity_ids in text_search_index.token_index.items():
            for entity_id in entity_ids:
                token_entry = RuntimeToken(token=token, entity_id=entity_id)
                tokens.append(token_entry)

                if len(tokens) >= BULK_LOAD_CHUNK_SIZE:
                    processed_count += len(tokens)
                    await flush(tokens, processed_count)
                    tokens.clear()

        if tokens:
            processed_count += len(tokens)
            await flush(tokens, processed_count)

        async with runtime_transaction():
            repository_count = await runtime_token_repository.count()
        log.debug(f"runtime token repository count: {repository_count}")

    @staticmethod
    async def transfer_load_entity_details_index(entity_details_path: Path) -> None:
        log.debug("Running transfer load entity details index")
        assert RuntimeDatabaseManager.runtime_database_helper is not None, (
            "runtime_database_helper must be initialized before calling initialize()"
        )
        entity_details_index = EntityDetailsIndex.load_entity_details_index_from_file(
            entity_details_path
        )
        RuntimeDatabaseManager.runtime_database_helper.entity_details_index = entity_details_index

    @staticmethod
    async def transfer_optimize() -> None:
        assert RuntimeDatabaseManager.runtime_database_helper is not None, (
            "RuntimeDatabaseManager.runtime_database_helper must be initialized before calling transfer_optimize()"
        )
        assert RuntimeDatabaseManager.runtime_database_helper.runtime_async_engine is not None, (
            "RuntimeDatabaseManager.runtime_database_helper.runtime_async_engine must be initialized before calling transfer_optimize()"
        )

        return await RuntimeDatabaseManager.runtime_database_helper.optimize(
            None,
            RuntimeDatabaseManager.runtime_database_helper.runtime_async_engine,
        )
