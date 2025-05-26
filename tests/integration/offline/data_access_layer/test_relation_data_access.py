from musigree.constants import DISCOGS_DATA
from musigree.offline.data_access_layer.entity_data_access import EntityDataAccess
from musigree.offline.data_access_layer.relation_data_access import RelationDataAccess
from musigree.offline.database.entity_repository import EntityRepository
from musigree.offline.database.offline_transaction import offline_transaction
from tests import utils
from tests.integration.offline.database.offline_database_test_case import (
    OfflineDatabaseTestCase,
)


class TestRelationDataAccess(OfflineDatabaseTestCase):

    def test_from_release(self):
        # GIVEN
        release_id = 1700
        discogs_data_directory = (
            OfflineDatabaseTestCase.offline_config.DATA_DIR / DISCOGS_DATA
        )

        release = utils.get_test_release_by_id(discogs_data_directory, release_id)
        with offline_transaction():
            entity_repository = EntityRepository()
            EntityDataAccess().resolve_release_references(entity_repository, release)

        # WHEN
        result = RelationDataAccess.from_release(release)

        # THEN
        expected = [
            {
                "object": 1000023528,
                "release_id": 1700,
                "role": "Compiled On",
                "subject": 41,
                "year": 1994,
            },
            {
                "object": 41,
                "release_id": 1700,
                "role": "Written By",
                "subject": 42,
                "year": 1994,
            },
            {
                "object": 1795,
                "release_id": 1700,
                "role": "Remix",
                "subject": 79,
                "year": 1994,
            },
            {
                "object": 1795,
                "release_id": 1700,
                "role": "Written By",
                "subject": 98,
                "year": 1994,
            },
            {
                "object": 1000023528,
                "release_id": 1700,
                "role": "Compiled On",
                "subject": 201,
                "year": 1994,
            },
            {
                "object": 1000023528,
                "release_id": 1700,
                "role": "Liner Notes",
                "subject": 391,
                "year": 1994,
            },
            {
                "object": 1000023528,
                "release_id": 1700,
                "role": "Compiled On",
                "subject": 823,
                "year": 1994,
            },
            {
                "object": 1000023528,
                "release_id": 1700,
                "role": "Compiled On",
                "subject": 939,
                "year": 1994,
            },
            {
                "object": 1000023528,
                "release_id": 1700,
                "role": "Compiled On",
                "subject": 1795,
                "year": 1994,
            },
            {
                "object": 1000023528,
                "release_id": 1700,
                "role": "Compiled On",
                "subject": 2235,
                "year": 1994,
            },
            {
                "object": 2235,
                "release_id": 1700,
                "role": "Written By",
                "subject": 2235,
                "year": 1994,
            },
            {
                "object": 1000023528,
                "release_id": 1700,
                "role": "Compiled On",
                "subject": 2236,
                "year": 1994,
            },
            {
                "object": 1000023528,
                "release_id": 1700,
                "role": "Compiled On",
                "subject": 2237,
                "year": 1994,
            },
            {
                "object": 2235,
                "release_id": 1700,
                "role": "Remix",
                "subject": 2237,
                "year": 1994,
            },
            {
                "object": 2237,
                "release_id": 1700,
                "role": "Written By",
                "subject": 2237,
                "year": 1994,
            },
            {
                "object": 1000023528,
                "release_id": 1700,
                "role": "Compiled On",
                "subject": 2238,
                "year": 1994,
            },
            {
                "object": 2238,
                "release_id": 1700,
                "role": "Written By",
                "subject": 2238,
                "year": 1994,
            },
            {
                "object": 1000023528,
                "release_id": 1700,
                "role": "Compiled On",
                "subject": 2239,
                "year": 1994,
            },
            {
                "object": 1795,
                "release_id": 1700,
                "role": "Written By",
                "subject": 2716,
                "year": 1994,
            },
            {
                "object": 823,
                "release_id": 1700,
                "role": "Written By",
                "subject": 4295,
                "year": 1994,
            },
            {
                "object": 201,
                "release_id": 1700,
                "role": "Written By",
                "subject": 5025,
                "year": 1994,
            },
            {
                "object": 2239,
                "release_id": 1700,
                "role": "Written By",
                "subject": 51674,
                "year": 1994,
            },
            {
                "object": 2239,
                "release_id": 1700,
                "role": "Written By",
                "subject": 66803,
                "year": 1994,
            },
            {
                "object": 2239,
                "release_id": 1700,
                "role": "Written By",
                "subject": 115880,
                "year": 1994,
            },
            {
                "object": 41,
                "release_id": 1700,
                "role": "Written By",
                "subject": 300407,
                "year": 1994,
            },
            {
                "object": 1000023528,
                "release_id": 1700,
                "role": "Artwork By",
                "subject": 445854,
                "year": 1994,
            },
            {
                "object": 2239,
                "release_id": 1700,
                "role": "Written By",
                "subject": 489350,
                "year": 1994,
            },
            {
                "object": 939,
                "release_id": 1700,
                "role": "Written By",
                "subject": 518861,
                "year": 1994,
            },
            {
                "object": 2236,
                "release_id": 1700,
                "role": "Written By",
                "subject": 547610,
                "year": 1994,
            },
            {
                "object": 2236,
                "release_id": 1700,
                "role": "Written By",
                "subject": 547611,
                "year": 1994,
            },
            {
                "object": 939,
                "release_id": 1700,
                "role": "Written By",
                "subject": 605613,
                "year": 1994,
            },
            {
                "object": 1000023528,
                "release_id": 1700,
                "role": "Artwork By",
                "subject": 1548777,
                "year": 1994,
            },
            {
                "object": 1000023528,
                "release_id": 1700,
                "role": "Copyright",
                "subject": 1000023528,
                "year": 1994,
            },
            {
                "object": 1000023528,
                "release_id": 1700,
                "role": "Phonographic Copyright",
                "subject": 1000023528,
                "year": 1994,
            },
        ]
        self.assertEqual(expected, result)

    def test_get_release_setup(self):
        # GIVEN
        release_id = 1700
        discogs_data_directory = (
            OfflineDatabaseTestCase.offline_config.DATA_DIR / DISCOGS_DATA
        )

        release = utils.get_test_release_by_id(discogs_data_directory, release_id)
        with offline_transaction():
            entity_repository = EntityRepository()
            EntityDataAccess().resolve_release_references(entity_repository, release)

        # WHEN
        result = RelationDataAccess.from_release(release)

        # THEN
        expected = [
            {
                "object": 1000023528,
                "release_id": 1700,
                "role": "Compiled On",
                "subject": 41,
                "year": 1994,
            },
            {
                "object": 41,
                "release_id": 1700,
                "role": "Written By",
                "subject": 42,
                "year": 1994,
            },
            {
                "object": 1795,
                "release_id": 1700,
                "role": "Remix",
                "subject": 79,
                "year": 1994,
            },
            {
                "object": 1795,
                "release_id": 1700,
                "role": "Written By",
                "subject": 98,
                "year": 1994,
            },
            {
                "object": 1000023528,
                "release_id": 1700,
                "role": "Compiled On",
                "subject": 201,
                "year": 1994,
            },
            {
                "object": 1000023528,
                "release_id": 1700,
                "role": "Liner Notes",
                "subject": 391,
                "year": 1994,
            },
            {
                "object": 1000023528,
                "release_id": 1700,
                "role": "Compiled On",
                "subject": 823,
                "year": 1994,
            },
            {
                "object": 1000023528,
                "release_id": 1700,
                "role": "Compiled On",
                "subject": 939,
                "year": 1994,
            },
            {
                "object": 1000023528,
                "release_id": 1700,
                "role": "Compiled On",
                "subject": 1795,
                "year": 1994,
            },
            {
                "object": 1000023528,
                "release_id": 1700,
                "role": "Compiled On",
                "subject": 2235,
                "year": 1994,
            },
            {
                "object": 2235,
                "release_id": 1700,
                "role": "Written By",
                "subject": 2235,
                "year": 1994,
            },
            {
                "object": 1000023528,
                "release_id": 1700,
                "role": "Compiled On",
                "subject": 2236,
                "year": 1994,
            },
            {
                "object": 1000023528,
                "release_id": 1700,
                "role": "Compiled On",
                "subject": 2237,
                "year": 1994,
            },
            {
                "object": 2235,
                "release_id": 1700,
                "role": "Remix",
                "subject": 2237,
                "year": 1994,
            },
            {
                "object": 2237,
                "release_id": 1700,
                "role": "Written By",
                "subject": 2237,
                "year": 1994,
            },
            {
                "object": 1000023528,
                "release_id": 1700,
                "role": "Compiled On",
                "subject": 2238,
                "year": 1994,
            },
            {
                "object": 2238,
                "release_id": 1700,
                "role": "Written By",
                "subject": 2238,
                "year": 1994,
            },
            {
                "object": 1000023528,
                "release_id": 1700,
                "role": "Compiled On",
                "subject": 2239,
                "year": 1994,
            },
            {
                "object": 1795,
                "release_id": 1700,
                "role": "Written By",
                "subject": 2716,
                "year": 1994,
            },
            {
                "object": 823,
                "release_id": 1700,
                "role": "Written By",
                "subject": 4295,
                "year": 1994,
            },
            {
                "object": 201,
                "release_id": 1700,
                "role": "Written By",
                "subject": 5025,
                "year": 1994,
            },
            {
                "object": 2239,
                "release_id": 1700,
                "role": "Written By",
                "subject": 51674,
                "year": 1994,
            },
            {
                "object": 2239,
                "release_id": 1700,
                "role": "Written By",
                "subject": 66803,
                "year": 1994,
            },
            {
                "object": 2239,
                "release_id": 1700,
                "role": "Written By",
                "subject": 115880,
                "year": 1994,
            },
            {
                "object": 41,
                "release_id": 1700,
                "role": "Written By",
                "subject": 300407,
                "year": 1994,
            },
            {
                "object": 1000023528,
                "release_id": 1700,
                "role": "Artwork By",
                "subject": 445854,
                "year": 1994,
            },
            {
                "object": 2239,
                "release_id": 1700,
                "role": "Written By",
                "subject": 489350,
                "year": 1994,
            },
            {
                "object": 939,
                "release_id": 1700,
                "role": "Written By",
                "subject": 518861,
                "year": 1994,
            },
            {
                "object": 2236,
                "release_id": 1700,
                "role": "Written By",
                "subject": 547610,
                "year": 1994,
            },
            {
                "object": 2236,
                "release_id": 1700,
                "role": "Written By",
                "subject": 547611,
                "year": 1994,
            },
            {
                "object": 939,
                "release_id": 1700,
                "role": "Written By",
                "subject": 605613,
                "year": 1994,
            },
            {
                "object": 1000023528,
                "release_id": 1700,
                "role": "Artwork By",
                "subject": 1548777,
                "year": 1994,
            },
            {
                "object": 1000023528,
                "release_id": 1700,
                "role": "Copyright",
                "subject": 1000023528,
                "year": 1994,
            },
            {
                "object": 1000023528,
                "release_id": 1700,
                "role": "Phonographic Copyright",
                "subject": 1000023528,
                "year": 1994,
            },
        ]
        self.assertEqual(expected, result)
