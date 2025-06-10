import logging
import multiprocessing
from typing import List

from sqlalchemy.exc import OperationalError, IntegrityError

from musigree.exceptions import NotFoundError, DatabaseError
from musigree.library.cache.role_cache import RoleCache
from musigree.offline.data_access_layer.relation_data_access import RelationDataAccess
from musigree.offline.database.offline_database_helper import OfflineDatabaseHelper
from musigree.offline.database.relation_release_year_repository import (
    RelationReleaseYearRepository,
)
from musigree.offline.database.relation_repository import RelationRepository
from musigree.offline.database.release_repository import ReleaseRepository
from musigree.offline.database.offline_transaction import offline_transaction
from musigree.offline.domain.relation import RelationUncommitted
from musigree.offline.domain.relation_release_year import (
    RelationReleaseYearUncommitted,
)
from musigree.offline.domain.release import Release
from musigree.offline.loader.loader_base import LoaderBase
from musigree.logging_config import LOGGING_TRACE
from musigree.offline.offline_database_manager import OfflineDatabaseManager

log = logging.getLogger(__name__)


class WorkerRelationPassOne(multiprocessing.Process):
    def __init__(self, release_ids: list[int], current_total: int, total_count: int):
        super().__init__()
        self.release_ids = release_ids
        self.current_total = current_total
        self.total_count = total_count

    def run(self) -> None:
        proc_name = self.name

        relation_release_years = []

        count = self.current_total
        end_count = count + len(self.release_ids)

        if OfflineDatabaseManager.get_concurrency_count() > 1:
            OfflineDatabaseHelper.initialize()

        with offline_transaction():
            release_repository = ReleaseRepository()
            relation_repository = RelationRepository()
            relation_release_year_repository = RelationReleaseYearRepository()

            for id_ in self.release_ids:
                release: Release | None = None
                try:
                    # log.debug(f"loader_pass_one ({annotation}): {release_id}")
                    release = release_repository.get(id_)
                    relations = RelationDataAccess.from_release(release)
                    if LOGGING_TRACE:
                        log.debug(
                            f"WorkerRelationPassOne [{proc_name}]\t"
                            + f"(release_id:{release.release_id})\t[{len(relations)}] {release.title}"
                        )
                except NotFoundError:
                    log.debug(f"WorkerRelationPassOne release_id not found: {id_}")
                except DatabaseError:
                    log.error("Error in WorkerRelationPassOne worker")
                    # log.exception("Error in WorkerRelationPassOne worker", exc_info=True)
                    raise

                # relations = RelationUncommitted.from_dicts(relation_dicts)

                if len(relations) > 0 and release is not None:
                    self.create_relation_bulk(
                        relation_repository,
                        relations,
                    )

                    for relation in relations:
                        year = release.release_date.year if release.release_date is not None and release.release_date.year is not None else None
                        new_relation_release_years = self.to_relation_release_years(
                            relation_repository=relation_repository,
                            relation=relation,
                            release_id=id_,
                            year=year,
                        )
                        relation_release_years.extend(new_relation_release_years)

                        if (
                            len(relation_release_years)
                            > LoaderBase.BULK_INSERT_BATCH_SIZE
                        ):
                            self.create_relation_release_year_bulk(
                                relation_release_year_repository, relation_release_years
                            )
                            relation_release_years.clear()

                count += 1
                if (
                    count % LoaderBase.BULK_REPORTING_SIZE == 0
                    and not count == end_count
                ):
                    log.debug(f"[{proc_name}] processed {count} of {self.total_count}")

        if len(relation_release_years) > 0:
            with offline_transaction():
                relation_release_year_repository = RelationReleaseYearRepository()
                self.create_relation_release_year_bulk(
                    relation_release_year_repository, relation_release_years
                )

        log.info(f"[{proc_name}] processed {count} of {self.total_count}")

    @classmethod
    def create_relation_bulk(
        cls,
        relation_repository: RelationRepository,
        relations: list[RelationUncommitted],
    ) -> None:

        # save, do nothing if already exists
        try:
            relation_repository.create_bulk(relations, on_conflict_do_nothing=True)
            relation_repository.commit()
            # log.debug(f"inserted {len(relations)}")
        except DatabaseError:
            relation_repository.rollback()
            # log.debug(f"Roll back create")
            # log.exception(e)
        except IntegrityError:
            relation_repository.rollback()
            # log.exception("Integrity Error in bulk", exc_info=True)
            # log.debug(f"Integrity Error in bulk, roll back and try one by one...")
            for relation in relations:
                try:
                    relation_repository.create(relation, on_conflict_do_nothing=True)
                    relation_repository.commit()
                    # log.debug(f"inserted {len(relations)}")
                except DatabaseError as ex:
                    relation_repository.rollback()
                    # log.debug(f"Roll back create")
                    log.exception(ex)
                except IntegrityError:
                    relation_repository.rollback()
                    # log.exception("Integrity Error", exc_info=True)
                    # log.debug(f"Integrity Error, roll back create")
        except OperationalError as e:
            relation_repository.rollback()
            log.debug(f"OperationalError in worker process")
            raise e

    @classmethod
    def to_relation_release_years(
        cls,
        relation_repository: RelationRepository,
        relation: RelationUncommitted,
        release_id: int,
        year: int | None,
    ) -> List[RelationReleaseYearUncommitted]:
        relation_release_years = []
        try:
            role_id = RoleCache.role_name_to_role_id_lookup[relation.role_name]

            key = {
                "subject": relation.subject,
                "role_id": role_id,
                "object": relation.object,
            }
            relation_id = relation_repository.get_id_by_key(key)
            # log.debug(f"v: {relation_db.version_id}")
            relation_release_year_uncommitted = RelationReleaseYearUncommitted(
                relation_id=relation_id,
                release_id=release_id,
                year=year,
            )
            relation_release_years.append(relation_release_year_uncommitted)
        except NotFoundError:
            relation_repository.rollback()
            if LOGGING_TRACE:
                log.debug(f"Error cannot find relation")
        except DatabaseError:
            relation_repository.rollback()
            log.debug(f"Error cannot find relation")
        except OperationalError as e:
            relation_repository.rollback()
            raise e
        return relation_release_years

    @classmethod
    def create_relation_release_year_bulk(
        cls,
        relation_release_year_repository: RelationReleaseYearRepository,
        relation_release_years: List[RelationReleaseYearUncommitted],
    ) -> None:
        try:
            relation_release_year_repository.create_bulk(relation_release_years)
            relation_release_year_repository.commit()
            # log.debug(
            #     f"Created RelationReleaseYear: {relation_db.relation_id} {release_id} {year}"
            # )
        except DatabaseError:
            relation_release_year_repository.rollback()
            log.debug(f"Error cannot create RelationReleaseYear")
        except OperationalError as e:
            relation_release_year_repository.rollback()
            raise e
