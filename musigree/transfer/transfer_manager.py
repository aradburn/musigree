import logging
from pathlib import Path

from musigree.constants import (
    ENTITY_DETAILS_DATA,
    ENTITY_DETAILS_FILENAME,
    ALL_RUNTIME_DATABASE_TABLE_NAMES,
)
from musigree.exceptions import DatabaseError
from musigree.logging_config import LOGGING_TRACE
from musigree.offline.database.entity_repository import EntityRepository
from musigree.offline.database.relation_repository import RelationRepository
from musigree.offline.database.role_repository import RoleRepository
from musigree.runtime.data_access_layer.runtime_entity_data_access import (
    RuntimeEntityDataAccess,
)
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
from musigree.runtime.runtime_database_manager import RuntimeDatabaseManager
from musigree.runtime.runtime_domain.entity import RuntimeEntity
from musigree.runtime.runtime_domain.relation import (
    RuntimeRelationDB,
)
from musigree.runtime.runtime_domain.role import RuntimeRole
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
    def transfer_entity(data_directory: Path) -> None:
        log.debug(f"Running transfer_entity()")

        entity_details_path = (
            data_directory / ENTITY_DETAILS_DATA / ENTITY_DETAILS_FILENAME
        )
        entity_details_index = (
            RuntimeEntityDataAccess.load_entity_details_index_from_file(
                entity_details_path
            )
        )

        offline_entity_repository = EntityRepository()
        runtime_entity_repository = RuntimeEntityRepository()

        total_count = offline_entity_repository.count()
        with runtime_transaction():
            initial_count = runtime_entity_repository.count()
        if initial_count > 0:
            error_msg = "Error in transfer_entity, runtime_entity table not empty"
            log.exception(error_msg, exc_info=True)
            raise DatabaseError

        processed_count = 0
        bulk_records = []
        workers = []

        entities = offline_entity_repository.all()

        for entity in entities:
            countries = entity_details_index.get_countries_for_id(entity.id)
            genres = entity_details_index.get_genres_for_id(entity.id)
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
                    with runtime_transaction():
                        try:
                            runtime_entity_repository.save_all(bulk_records)
                            runtime_entity_repository.commit()
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
                with runtime_transaction():
                    try:
                        runtime_entity_repository.save_all(bulk_records)
                        runtime_entity_repository.commit()
                        log.info(f"processed: {processed_count} of {total_count}")
                        bulk_records.clear()
                    except DatabaseError:
                        log.error("Error in transfer_entity")
                        # log.exception("Error in transfer_entity", exc_info=True)
                        raise

        while len(workers) > 0:
            worker = workers.pop(0)
            TransferManager.transfer_wait_for_worker(worker)

        repository_count = runtime_entity_repository.count()
        log.debug(f"repository_count: {repository_count}")

    @staticmethod
    def transfer_relation() -> None:
        log.debug(f"Running transfer_relation()")
        offline_relation_repository = RelationRepository()
        runtime_relation_repository = RuntimeRelationRepository()

        total_count = offline_relation_repository.count()
        with runtime_transaction():
            initial_count = runtime_relation_repository.count()
        if initial_count > 0:
            error_msg = "Error in transfer_relation, runtime_relation table not empty"
            log.exception(error_msg, exc_info=True)
            raise DatabaseError

        processed_count = 0
        bulk_records = []
        workers = []

        relations = offline_relation_repository.all()

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
                    with runtime_transaction():
                        try:
                            runtime_relation_repository.save_all(bulk_records)
                            runtime_relation_repository.commit()
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
                with runtime_transaction():
                    try:
                        runtime_relation_repository.save_all(bulk_records)
                        runtime_relation_repository.commit()
                        log.info(f"processed: {processed_count} of {total_count}")
                        bulk_records.clear()
                    except DatabaseError:
                        log.error("Error in transfer_relation")
                        # log.exception("Error in transfer_relation", exc_info=True)
                        raise

        while len(workers) > 0:
            worker = workers.pop(0)
            TransferManager.transfer_wait_for_worker(worker)

        repository_count = runtime_relation_repository.count()
        log.debug(f"repository_count: {repository_count}")

    @staticmethod
    def transfer_role() -> None:
        log.debug(f"Running transfer_role()")
        roles = RoleRepository().all()
        runtime_role_repository = RuntimeRoleRepository()

        with runtime_transaction():
            for role in roles:
                runtime_role = RuntimeRole(**role.model_dump())
                runtime_role_repository.create(runtime_role)

    @staticmethod
    def transfer_all(data_directory: Path) -> None:
        log.debug(f"Running transfer_all()")

        RuntimeDatabaseManager.runtime_database_helper.drop_tables(
            ALL_RUNTIME_DATABASE_TABLE_NAMES
        )
        RuntimeDatabaseManager.runtime_database_helper.create_tables(
            ALL_RUNTIME_DATABASE_TABLE_NAMES
        )

        TransferManager.transfer_role()
        TransferManager.transfer_entity(data_directory)
        TransferManager.transfer_relation()

        log.debug(f"Transfer all done")

    @staticmethod
    def transfer_wait_for_worker(worker) -> None:
        if LOGGING_TRACE:
            log.debug(f"wait for worker {worker.name}")
        worker.join()
        worker.terminate()
        if worker.exitcode > 0:
            log.error(f"worker {worker.name} exitcode: {worker.exitcode}")
            raise RuntimeError("Error in worker process")
