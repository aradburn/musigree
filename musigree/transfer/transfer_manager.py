import logging
import sys
from pathlib import Path

from musigree.constants import ALL_RUNTIME_DATABASE_TABLE_NAMES
from musigree.exceptions import DatabaseError
from musigree.runtime.data_access_layer.entity_details_index import EntityDetailsIndex
from musigree.logging_config import LOGGING_TRACE
from musigree.offline.data_access_layer.release_data_access import ReleaseDataAccess
from musigree.offline.database.entity_repository import EntityRepository
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
from musigree.runtime.runtime_domain.entity import RuntimeEntity
from musigree.runtime.runtime_domain.genre import Genre
from musigree.runtime.runtime_domain.relation import (
    RuntimeRelationDB,
)
from musigree.runtime.runtime_domain.role import RuntimeRole
from musigree.runtime.runtime_domain.style import Style
from musigree.transfer.transfer_worker_entity_inserter import (
    TransferWorkerEntityInserter,
)
from musigree.transfer.transfer_worker_relation_inserter import (
    TransferWorkerRelationInserter,
)

log = logging.getLogger(__name__)


class TransferManager:
    BULK_INSERT_BATCH_SIZE = 100000

    @staticmethod
    async def transfer_entity(entity_details_index: EntityDetailsIndex) -> None:
        log.debug(f"Running transfer_entity()")

        offline_entity_repository = EntityRepository()
        runtime_entity_repository = RuntimeEntityRepository()

        total_count = offline_entity_repository.count()
        async with runtime_transaction():
            initial_count = await runtime_entity_repository.count()
        if initial_count > 0:
            error_msg = "Error in transfer_entity, runtime_entity table not empty"
            log.exception(error_msg, exc_info=True)
            raise DatabaseError

        processed_count = 0
        bulk_records = []
        workers = []

        entities = await offline_entity_repository.all()

        for entity in entities:
            # TODO get from runtime countries table
            countries = entity_details_index.get_countries_for_id(entity.id)
            # TODO get from runtime genres table
            genres = entity_details_index.get_genres_for_id(entity.id)
            # TODO get from runtime styles table
            styles = entity_details_index.get_styles_for_id(entity.id)

            runtime_entity = RuntimeEntity(
                countries=countries,
                genres=genres,
                styles=styles,
                **entity.model_dump(),
            )
            runtime_entity_db = runtime_entity.to_db()

            bulk_records.append(runtime_entity_db.model_dump())
            processed_count += 1
            if len(bulk_records) >= TransferManager.BULK_INSERT_BATCH_SIZE:
                if RuntimeDatabaseManager.get_concurrency_count() > 1:
                    # Can do multi threading
                    worker = TransferWorkerEntityInserter(
                        bulk_records,
                        processed_count,
                    )

                    worker.start()
                    workers.append(worker)
                    bulk_records.clear()
                    if len(workers) > RuntimeDatabaseManager.get_concurrency_count():
                        worker = workers.pop(0)
                        TransferManager.transfer_wait_for_worker(worker)
                else:
                    async with runtime_transaction():
                        try:
                            await runtime_entity_repository.save_all(bulk_records)
                            await runtime_entity_repository.commit()
                            log.info(f"processed: {processed_count} of {total_count}")
                            bulk_records.clear()
                        except DatabaseError:
                            log.error("Error in transfer_entity")
                            # log.exception("Error in transfer_entity", exc_info=True)
                            raise

        if len(bulk_records) > 0:
            if RuntimeDatabaseManager.get_concurrency_count() > 1:
                # Can do multi threading
                worker = TransferWorkerEntityInserter(
                    bulk_records,
                    processed_count,
                )

                worker.start()
                workers.append(worker)
                bulk_records.clear()
            else:
                async with runtime_transaction():
                    try:
                        await runtime_entity_repository.save_all(bulk_records)
                        await runtime_entity_repository.commit()
                        log.info(f"processed: {processed_count} of {total_count}")
                        bulk_records.clear()
                    except DatabaseError:
                        log.error("Error in transfer_entity")
                        # log.exception("Error in transfer_entity", exc_info=True)
                        raise

        while len(workers) > 0:
            worker = workers.pop(0)
            TransferManager.transfer_wait_for_worker(worker)

        repository_count = await runtime_entity_repository.count()
        log.debug(f"repository_count: {repository_count}")

    @staticmethod
    async def transfer_relation() -> None:
        log.debug(f"Running transfer_relation()")
        offline_relation_repository = RelationRepository()
        runtime_relation_repository = RuntimeRelationRepository()

        total_count = offline_relation_repository.count()
        async with runtime_transaction():
            initial_count = await runtime_relation_repository.count()
        if initial_count > 0:
            error_msg = "Error in transfer_relation, runtime_relation table not empty"
            log.exception(error_msg, exc_info=True)
            raise DatabaseError

        processed_count = 0
        bulk_records = []
        workers = []

        relations = await offline_relation_repository.all()

        for relation in relations:
            runtime_relation = RuntimeRelationDB(**relation.model_dump())
            bulk_records.append(runtime_relation.model_dump())
            processed_count += 1
            if len(bulk_records) >= TransferManager.BULK_INSERT_BATCH_SIZE:
                if RuntimeDatabaseManager.get_concurrency_count() > 1:
                    # Can do multi threading
                    worker = TransferWorkerRelationInserter(
                        bulk_records,
                        processed_count,
                    )

                    worker.start()
                    workers.append(worker)
                    bulk_records.clear()
                    if len(workers) > RuntimeDatabaseManager.get_concurrency_count():
                        worker = workers.pop(0)
                        TransferManager.transfer_wait_for_worker(worker)
                else:
                    async with runtime_transaction():
                        try:
                            await runtime_relation_repository.save_all(bulk_records)
                            await runtime_relation_repository.commit()
                            log.info(f"processed: {processed_count} of {total_count}")
                            bulk_records.clear()
                        except DatabaseError:
                            log.error("Error in transfer_relation")
                            # log.exception("Error in transfer_relation", exc_info=True)
                            raise

        if len(bulk_records) > 0:
            if RuntimeDatabaseManager.get_concurrency_count() > 1:
                # Can do multi threading
                worker = TransferWorkerRelationInserter(
                    bulk_records,
                    processed_count,
                )

                worker.start()
                workers.append(worker)
                bulk_records.clear()
            else:
                async with runtime_transaction():
                    try:
                        await runtime_relation_repository.save_all(bulk_records)
                        await runtime_relation_repository.commit()
                        log.info(f"processed: {processed_count} of {total_count}")
                        bulk_records.clear()
                    except DatabaseError:
                        log.error("Error in transfer_relation")
                        # log.exception("Error in transfer_relation", exc_info=True)
                        raise

        while len(workers) > 0:
            worker = workers.pop(0)
            TransferManager.transfer_wait_for_worker(worker)

        repository_count = await runtime_relation_repository.count()
        log.debug(f"repository_count: {repository_count}")

    @staticmethod
    async def transfer_role() -> None:
        log.debug(f"Running transfer_role()")
        roles = RoleRepository().all()
        runtime_role_repository = RuntimeRoleRepository()

        async with runtime_transaction():
            for role in roles:
                runtime_role = RuntimeRole(**role.model_dump())
                await runtime_role_repository.create(runtime_role)

    @staticmethod
    async def transfer_entity_details(entity_details_index: EntityDetailsIndex) -> None:
        log.debug(f"Running transfer_entity_details()")

        # Countries
        sorted_countries = sorted(entity_details_index.countries_list)
        runtime_country_repository = CountryRepository()

        for _id, country_name in enumerate(sorted_countries):
            async with runtime_transaction():
                country = Country(id=_id, country_name=country_name)
                await runtime_country_repository.create(country)
                await runtime_country_repository.commit()

        # Genres
        sorted_genres = sorted(entity_details_index.genres_list)
        runtime_genre_repository = GenreRepository()

        for _id, genre_name in enumerate(sorted_genres):
            async with runtime_transaction():
                genre = Genre(id=_id, genre_name=genre_name)
                await runtime_genre_repository.create(genre)
                await runtime_genre_repository.commit()

        # Styles
        sorted_styles = sorted(entity_details_index.styles_list)
        runtime_style_repository = StyleRepository()

        for _id, style_name in enumerate(sorted_styles):
            async with runtime_transaction():
                style = Style(id=_id, style_name=style_name)
                await runtime_style_repository.create(style)
                await runtime_style_repository.commit()

    @staticmethod
    def transfer_all(_data_directory: Path) -> None:
        log.debug(f"Running transfer_all()")
        log.error(f"BANG!!!! running transfer_all()")
        sys.exit(1)
        # RuntimeDatabaseManager.runtime_database_helper.drop_tables(
        #     ALL_RUNTIME_DATABASE_TABLE_NAMES
        # )
        # RuntimeDatabaseManager.runtime_database_helper.create_tables(
        #     ALL_RUNTIME_DATABASE_TABLE_NAMES
        # )
        #
        # offline_release_repository = ReleaseRepository()
        # entity_details_index = ReleaseDataAccess.create_entity_details_index(offline_release_repository)
        #
        # TransferManager.transfer_role()
        # TransferManager.transfer_entity_details(entity_details_index)
        # TransferManager.transfer_entity(entity_details_index)
        # TransferManager.transfer_relation()
        #
        # log.debug(f"Transfer all done")

    @staticmethod
    def transfer_wait_for_worker(worker) -> None:
        if LOGGING_TRACE:
            log.debug(f"wait for worker {worker.name}")
        worker.join()
        worker.terminate()
        if worker.exitcode > 0:
            log.error(f"worker {worker.name} exitcode: {worker.exitcode}")
            raise RuntimeError("Error in worker process")
