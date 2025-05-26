from musigree.offline.database.entity_repository import EntityRepository
from tests.integration.offline.database.offline_database_test_case import (
    OfflineDatabaseTestCase,
)


class TestLoaderEntityDetails(OfflineDatabaseTestCase):
    def test_loader_entity_details(self):
        # GIVEN

        # WHEN
        actual = EntityRepository().count()

        # THEN
        expected = 6216
        self.assertEqual(expected, actual)
