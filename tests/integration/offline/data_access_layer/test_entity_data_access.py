from musigree.constants import DISCOGS_DATA, TEST_DIR
from musigree.library.fields.entity_type import EntityType
from musigree.library.full_text_search.text_search_index import TextSearchIndex
from musigree.offline.data_access_layer.entity_data_access import EntityDataAccess
from musigree.offline.database.entity_repository import EntityRepository
from musigree.offline.database.offline_transaction import offline_transaction
from tests import utils
from tests.integration.offline.database.offline_database_test_case import (
    OfflineDatabaseTestCase,
)


class TestEntityDataAccess(OfflineDatabaseTestCase):

    def test_init_text_search_index(self):
        index = TextSearchIndex()

        with offline_transaction():
            entity_repository = EntityRepository()
            EntityDataAccess.init_text_search_index(entity_repository, index)

        # THEN
        self.assertEqual(7221, len(index.index.items()))
        self.assertEqual(6216, len(index.documents.items()))

    def test_get_id_by_entity_type_and_entity_name(self):
        entity_type = EntityType.ARTIST
        entity_name = "Joker, The (3)"
        with offline_transaction():
            entity_repository = EntityRepository()
            result = EntityDataAccess.get_id_by_entity_type_and_entity_name(
                entity_repository, entity_type, entity_name
            )

        # THEN
        expected = 8526
        self.assertEqual(expected, result)

    def test_resolve_entity_references_1(self):
        # GIVEN
        discogs_data_directory = TEST_DIR / "data" / DISCOGS_DATA
        entity_id = 48
        entity_type = EntityType.ARTIST
        entity = utils.get_test_entity_by_id(
            discogs_data_directory, entity_id, entity_type
        )

        # WHEN
        with offline_transaction():
            entity_repository = EntityRepository()
            EntityDataAccess.resolve_entity_references(entity_repository, entity)
            result = entity.entities

        # THEN
        expected = {
            "aliases": {
                "Aphex Twin": 45,
                "Dice Man, The": 820,
                "Polygon Window": 2931,
                "Richard D. James": 435132,
            }
        }
        self.assertEqual(expected, result)

    def test_resolve_entity_references_2(self):
        # GIVEN
        discogs_data_directory = TEST_DIR / "data" / DISCOGS_DATA
        entity_id = 98
        entity_type = EntityType.ARTIST
        entity = utils.get_test_entity_by_id(
            discogs_data_directory, entity_id, entity_type
        )

        # WHEN
        with offline_transaction():
            entity_repository = EntityRepository()
            EntityDataAccess.resolve_entity_references(entity_repository, entity)
            result = entity.entities

        # THEN
        expected = {
            "aliases": {"Cosmos": 14168},
            "groups": {
                "Chameleon": 1798,
                "Global Communication": 79,
                "Jedi Knights": 1799,
                "Link & E621": 5131,
                "Reload": 1791,
            },
        }
        self.assertEqual(expected, result)

    def test_resolve_entity_references_3(self):
        discogs_data_directory = TEST_DIR / "data" / DISCOGS_DATA
        entity_id = 288
        entity_type = EntityType.ARTIST
        entity = utils.get_test_entity_by_id(
            discogs_data_directory, entity_id, entity_type
        )

        # WHEN
        with offline_transaction():
            entity_repository = EntityRepository()
            EntityDataAccess.resolve_entity_references(entity_repository, entity)
            result = entity.entities

        # THEN
        expected = {
            "members": {
                "Alex Banks": 10141,
                "Jay Hurren": 474638,
            },
        }
        self.assertEqual(expected, result)

    def test_resolve_entity_references_4(self):
        # GIVEN
        discogs_data_directory = TEST_DIR / "data" / DISCOGS_DATA
        entity_id = 61
        entity_type = EntityType.LABEL
        entity = utils.get_test_entity_by_id(
            discogs_data_directory, entity_id, entity_type
        )

        # WHEN
        with offline_transaction():
            entity_repository = EntityRepository()
            EntityDataAccess.resolve_entity_references(entity_repository, entity)
            result = entity.entities

        # THEN
        expected = {
            "parent_label": {
                "Instinct Records": 1000000063,
            }
        }
        self.assertEqual(expected, result)

    def test_resolve_release_references_1(self):
        # GIVEN
        release_id = 637
        discogs_data_directory = (
            OfflineDatabaseTestCase.offline_config.DATA_DIR / DISCOGS_DATA
        )

        release = utils.get_test_release_by_id(discogs_data_directory, release_id)

        # WHEN
        with offline_transaction():
            entity_repository = EntityRepository()
            EntityDataAccess.resolve_release_references(entity_repository, release)
            result = release.labels

        # THEN
        expected = [
            {"catalog_number": "WAP100CD", "id": 1000023528, "name": "Warp Records"},
            {"catalog_number": "WAP 100CD", "id": 1000023528, "name": "Warp Records"},
        ]
        self.assertEqual(expected, result)

    def test_resolve_release_references_2(self):
        # GIVEN
        release_id = 158
        discogs_data_directory = (
            OfflineDatabaseTestCase.offline_config.DATA_DIR / DISCOGS_DATA
        )

        release = utils.get_test_release_by_id(discogs_data_directory, release_id)

        # WHEN
        with offline_transaction():
            entity_repository = EntityRepository()
            EntityDataAccess.resolve_release_references(entity_repository, release)
            result = release.companies

        # THEN
        expected = [
            {
                "entity_type": 13,
                "entity_type_name": "Phonographic Copyright (p)",
                "id": 1000264514,
                "name": "Warp Records Limited",
            },
            {
                "entity_type": 14,
                "entity_type_name": "Copyright (c)",
                "id": 1000264514,
                "name": "Warp Records Limited",
            },
            {
                "entity_type": 21,
                "entity_type_name": "Published By",
                "id": 1000265170,
                "name": "Warp Music",
            },
            {
                "entity_type": 21,
                "entity_type_name": "Published By",
                "id": 1000045746,
                "name": "EMI Music",
            },
            {
                "entity_type": 17,
                "entity_type_name": "Pressed By",
                "id": 1000147881,
                "name": "Mayking",
            },
        ]
        self.assertEqual(expected, result)

    def test_resolve_release_references_3(self):
        # GIVEN
        release_id = 1700
        discogs_data_directory = (
            OfflineDatabaseTestCase.offline_config.DATA_DIR / DISCOGS_DATA
        )

        release = utils.get_test_release_by_id(discogs_data_directory, release_id)

        # WHEN
        with offline_transaction():
            entity_repository = EntityRepository()
            EntityDataAccess.resolve_release_references(entity_repository, release)
            result = release.artists

        # THEN
        expected = [{"id": 0, "name": "Various"}]
        self.assertEqual(expected, result)

    def test_resolve_release_references_4(self):
        # GIVEN
        release_id = 1700
        discogs_data_directory = (
            OfflineDatabaseTestCase.offline_config.DATA_DIR / DISCOGS_DATA
        )

        release = utils.get_test_release_by_id(discogs_data_directory, release_id)

        # WHEN
        with offline_transaction():
            entity_repository = EntityRepository()
            EntityDataAccess.resolve_release_references(entity_repository, release)
            result = release.extra_artists

        # THEN
        expected = [
            {
                "id": 1548777,
                "name": "Phil Wolstenholme",
                "roles": [{"detail": "Digital Holme-grown", "name": "Artwork"}],
            },
            {
                "id": 445854,
                "name": "Designers Republic, The",
                "roles": [{"detail": "Piezoelectric Warriors", "name": "Artwork"}],
            },
            {"id": 391, "name": "David Toop", "roles": [{"name": "Liner Notes"}]},
        ]
        self.assertEqual(expected, result)
