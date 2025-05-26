from musigree.constants import ROLES_DATA, INSTRUMENTS_DATA
from musigree.library.cache.role_cache import RoleCache
from musigree.offline.data_access_layer.role_data_access import RoleDataAccess
from musigree.offline.loader.loader_role import LoaderRole
from tests.integration.offline.database.offline_repository_test_case import (
    OfflineRepositoryTestCase,
)


class TestLoaderRole(OfflineRepositoryTestCase):

    def setUp(self):
        super().setUp()
        self.resetDB()

    def test_load_wikipedia_instruments(self):
        # GIVEN
        instruments_directory = (
            OfflineRepositoryTestCase.offline_config.DATA_DIR / INSTRUMENTS_DATA
        )
        # WHEN
        wikipedia_instruments = LoaderRole.load_wikipedia_instruments(
            instruments_directory
        )

        # THEN
        expected = 2186
        actual = len(wikipedia_instruments)
        self.assertEqual(expected, actual)

    def test_load_hornbostel_sachs_instruments(self):
        # GIVEN
        instruments_directory = (
            OfflineRepositoryTestCase.offline_config.DATA_DIR / INSTRUMENTS_DATA
        )

        # WHEN
        hornbostel_sachs_instruments = LoaderRole.load_hornbostel_sachs_instruments(
            instruments_directory
        )

        # THEN
        expected = 1865
        actual = len(hornbostel_sachs_instruments)
        self.assertEqual(expected, actual)

    def test_load_roles_from_files(self):
        # GIVEN
        roles_directory = OfflineRepositoryTestCase.offline_config.DATA_DIR / ROLES_DATA

        # WHEN
        roles_from_files = LoaderRole.load_roles_from_files(roles_directory)

        # THEN
        expected = 992
        actual = len(roles_from_files)
        self.assertEqual(expected, actual)

    def test_load_roles_from_files_from_database(self):
        # GIVEN
        roles_directory = OfflineRepositoryTestCase.offline_config.DATA_DIR / ROLES_DATA
        roles_from_files = LoaderRole.load_roles_from_files(roles_directory)

        # WHEN
        LoaderRole.save_roles(roles_from_files)
        RoleDataAccess.load_all_roles()

        # THEN
        actual = len(roles_from_files)
        expected = len(RoleCache.role_name_to_role_id_lookup)
        self.assertTrue(expected > 0)
        self.assertTrue(expected <= actual)
        self.assertEqual(
            len(RoleCache.role_name_to_role_id_lookup),
            len(RoleCache.role_id_to_role_name_lookup),
        )

    def test_load_hornbostel_sachs_instruments_from_database(self):
        # GIVEN
        instruments_directory = (
            OfflineRepositoryTestCase.offline_config.DATA_DIR / INSTRUMENTS_DATA
        )
        hornbostel_sachs_roles = LoaderRole.load_hornbostel_sachs_instruments(
            instruments_directory
        )

        # WHEN
        LoaderRole.save_roles(hornbostel_sachs_roles)
        RoleDataAccess.load_all_roles()

        # THEN
        actual = len(hornbostel_sachs_roles)
        expected = len(RoleCache.role_name_to_role_id_lookup)
        self.assertTrue(expected > 0)
        self.assertTrue(expected <= actual)
        self.assertEqual(
            len(RoleCache.role_name_to_role_id_lookup),
            len(RoleCache.role_id_to_role_name_lookup),
        )

    def test_load_wikipedia_instruments_from_database(self):
        # GIVEN
        instruments_directory = (
            OfflineRepositoryTestCase.offline_config.DATA_DIR / INSTRUMENTS_DATA
        )
        wikipedia_instruments = LoaderRole.load_wikipedia_instruments(
            instruments_directory
        )

        # WHEN
        LoaderRole.save_roles(wikipedia_instruments)
        RoleDataAccess.load_all_roles()

        # THEN
        actual = len(wikipedia_instruments)
        expected = len(RoleCache.role_name_to_role_id_lookup)
        self.assertTrue(expected > 0)
        self.assertTrue(expected <= actual)
        self.assertEqual(
            len(RoleCache.role_name_to_role_id_lookup),
            len(RoleCache.role_id_to_role_name_lookup),
        )
