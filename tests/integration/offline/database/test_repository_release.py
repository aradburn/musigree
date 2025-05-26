from musigree.constants import DISCOGS_DATA
from musigree.offline.database.offline_transaction import offline_transaction
from musigree.offline.database.release_repository import ReleaseRepository
from musigree.offline.loader.loader_utils import LoaderUtils
from musigree.offline.loader.parser_release import ParserRelease
from tests.integration.offline.database.offline_repository_test_case import (
    OfflineRepositoryTestCase,
)


class TestRepositoryRelease(OfflineRepositoryTestCase):
    def test_create_01(self):
        # GIVEN
        discogs_data_directory = (
            OfflineRepositoryTestCase.offline_config.DATA_DIR / DISCOGS_DATA
        )
        iterator = LoaderUtils.get_iterator(
            discogs_data_directory, "release", "testinsert"
        )
        release_element = next(iterator)
        release = ParserRelease().from_element(release_element)

        # WHEN
        with offline_transaction():
            repository = ReleaseRepository()
            created_release = repository.create(release)

        # THEN
        self.assertEqual(release, created_release)

    def test_get_01(self):
        # GIVEN
        discogs_data_directory = (
            OfflineRepositoryTestCase.offline_config.DATA_DIR / DISCOGS_DATA
        )
        iterator = LoaderUtils.get_iterator(
            discogs_data_directory, "release", "testinsert"
        )
        next(iterator)
        next(iterator)
        next(iterator)
        next(iterator)
        next(iterator)
        next(iterator)
        release_element = next(iterator)
        release = ParserRelease().from_element(release_element)

        # WHEN
        with offline_transaction():
            repository = ReleaseRepository()
            created_release = repository.create(release)

            retrieved_release = repository.get(635)

        # THEN
        self.assertEqual(created_release, retrieved_release)
