from musigree.constants import DISCOGS_DATA
from musigree.library.fields.entity_type import EntityType
from musigree.offline.database.entity_repository import EntityRepository
from musigree.offline.database.offline_transaction import offline_transaction
from musigree.offline.loader.loader_utils import LoaderUtils
from musigree.offline.loader.parser_entity import ParserEntity
from tests.integration.offline.database.offline_repository_test_case import (
    OfflineRepositoryTestCase,
)


class TestRepositoryEntity(OfflineRepositoryTestCase):
    def test_create_01(self):
        # GIVEN
        discogs_data_directory = (
            OfflineRepositoryTestCase.offline_config.DATA_DIR / DISCOGS_DATA
        )
        iterator = LoaderUtils.get_iterator(
            discogs_data_directory, "artist", "testinsert"
        )
        entity_element = next(iterator)
        entity = ParserEntity().from_element(entity_element)

        # WHEN
        with offline_transaction():
            repository = EntityRepository()
            created_entity = repository.create(entity)

        # THEN
        self.assertEqual(entity, created_entity)

    def test_get_01(self):
        # GIVEN
        discogs_data_directory = (
            OfflineRepositoryTestCase.offline_config.DATA_DIR / DISCOGS_DATA
        )
        iterator = LoaderUtils.get_iterator(
            discogs_data_directory, "label", "testinsert"
        )
        entity_element = next(iterator)
        entity = ParserEntity().from_element(entity_element)

        # WHEN
        with offline_transaction():
            repository = EntityRepository()
            created_entity = repository.create(entity)

            retrieved_entity = repository.get_by_entity_id_and_entity_type(
                1, EntityType.LABEL
            )

        # THEN
        self.assertEqual(created_entity, retrieved_entity)
