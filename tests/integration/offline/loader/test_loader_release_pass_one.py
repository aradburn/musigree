from musigree.offline.database.release_repository import ReleaseRepository
from tests.integration.offline.database.offline_database_test_case import (
    OfflineDatabaseTestCase,
)


class TestLoaderReleasePassOne(OfflineDatabaseTestCase):
    def test_loader_release_pass_one(self):
        # GIVEN

        # WHEN
        actual = ReleaseRepository().count()

        # THEN
        expected = 1700
        self.assertEqual(expected, actual)
