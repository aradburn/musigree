import logging
from pathlib import Path

from musigree.constants import BULK_REPORTING_SIZE
from musigree.exceptions import DatabaseError
from musigree.library.full_text_search.text_search_index import TextSearchIndex
from musigree.offline.offline_database.entity_repository import EntityRepository
from musigree.offline.offline_database.offline_transaction import offline_transaction
from musigree.offline.offline_database.relation_repository import RelationRepository
from musigree.offline.offline_database.role_repository import RoleRepository
from musigree.runtime.data_access_layer.entity_details_index import EntityDetailsIndex
from musigree.runtime.data_access_layer.runtime_entity_data_access import RuntimeEntityDataAccess
from musigree.runtime.data_access_layer.runtime_relation_data_access import (
    RuntimeRelationDataAccess,
)
from musigree.runtime.runtime_database.runtime_country_repository import RuntimeCountryRepository
from musigree.runtime.runtime_database.runtime_genre_repository import RuntimeGenreRepository
from musigree.runtime.runtime_database.runtime_entity_repository import (
    RuntimeEntityRepository,
)
from musigree.runtime.runtime_database.runtime_relation_repository import (
    RuntimeRelationRepository,
)
from musigree.runtime.runtime_database.runtime_role_repository import (
    RuntimeRoleRepository,
)
from musigree.runtime.runtime_database.runtime_token_repository import RuntimeTokenRepository
from musigree.runtime.runtime_database.runtime_transaction import runtime_transaction
from musigree.runtime.runtime_database.runtime_style_repository import RuntimeStyleRepository
from musigree.runtime.runtime_database_manager import RuntimeDatabaseManager
from musigree.runtime.runtime_domain.runtime_country import RuntimeCountry
from musigree.runtime.runtime_domain.runtime_genre import RuntimeGenre
from musigree.runtime.runtime_domain.runtime_role import RuntimeRole
from musigree.runtime.runtime_domain.runtime_style import RuntimeStyle
from musigree.runtime.runtime_domain.runtime_token import RuntimeToken
from musigree.transfer.transfer_worker_entity_inserter import (
    transfer_worker_entity_inserter_async,
)
from musigree.transfer.transfer_worker_relation_inserter import (
    transfer_worker_relation_inserter_async,
)

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
            error_msg = "Error in transfer_entity, runtime_entity table not empty"
            log.exception(error_msg, exc_info=True)
            raise DatabaseError

        async with offline_transaction():
            offline_entity_repository = EntityRepository()
            total_count = await offline_entity_repository.count()
            log.debug(f"transfering {total_count} entities...")
            entities = offline_entity_repository.all()

            inserted_count = 0
            async for entity_list in entities:
                runtime_entity_dicts_list = (
                    RuntimeEntityDataAccess.get_runtime_entity_dicts_from_entities(entity_list)
                )
                await transfer_worker_entity_inserter_async(
                    runtime_entity_dicts_list, inserted_count, total_count
                )
                inserted_count += len(entity_list)

        async with runtime_transaction():
            repository_count = await runtime_entity_repository.count()
        log.debug(f"runtime entity repository count: {repository_count}")

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
            error_msg = "Error in transfer_relation, runtime_relation table not empty"
            log.exception(error_msg, exc_info=True)
            raise DatabaseError

        async with offline_transaction():
            offline_relation_repository = RelationRepository()
            total_count = await offline_relation_repository.count()
            log.debug(f"transfering {total_count} relations...")

            relations = offline_relation_repository.all()

            inserted_count = 0
            async for relation_dbs in relations:
                runtime_relation_dicts_list = (
                    RuntimeRelationDataAccess.get_runtime_relation_dicts_from_relations(
                        relation_dbs
                    )
                )
                await transfer_worker_relation_inserter_async(
                    runtime_relation_dicts_list, inserted_count, total_count
                )
                inserted_count += len(relation_dbs)

        async with runtime_transaction():
            repository_count = await runtime_relation_repository.count()
        log.debug(f"runtime relation repository count: {repository_count}")

    @staticmethod
    async def transfer_role() -> None:
        log.debug("Running transfer_role()")
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
        text_search_index = TextSearchIndex.load_text_search_index_from_file(text_search_path)
        RuntimeDatabaseManager.runtime_database_helper.text_search_index = text_search_index

        inserted_count = 0
        total_count = 0

        for _token, entity_ids in text_search_index.token_index.items():
            total_count += len(entity_ids)

        async with runtime_transaction():
            runtime_token_repository = RuntimeTokenRepository()
            for token, entity_ids in text_search_index.token_index.items():
                for entity_id in entity_ids:
                    token_entry = RuntimeToken(token=token, entity_id=entity_id)
                    await runtime_token_repository.create(token_entry)
                    inserted_count += 1
                    if inserted_count % BULK_REPORTING_SIZE == 0:
                        """Log every BULK_REPORTING_SIZE."""
                        log.debug(f"text search processed {inserted_count} of {total_count}")

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
