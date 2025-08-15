import pytest

from musigree.constants import ROLES_DATA, INSTRUMENTS_DATA
from musigree.library.cache.role_cache import RoleCache
from musigree.offline.data_access_layer.role_data_access import RoleDataAccess
from musigree.offline.loader.loader_role import LoaderRole

from tests.conftest import AbstractDatabaseTest


@pytest.mark.parametrize("is_load_offline_data_required", [False], scope="class")
class TestLoaderRole(AbstractDatabaseTest):

    def test_load_wikipedia_instruments(self, offline_database_setup, offline_config):
        # GIVEN
        instruments_directory = offline_config.DATA_DIR / INSTRUMENTS_DATA
        # WHEN
        wikipedia_instruments = LoaderRole.load_wikipedia_instruments(
            instruments_directory
        )

        # THEN
        expected = 2186
        actual = len(wikipedia_instruments)
        assert actual == expected

    def test_load_hornbostel_sachs_instruments(self, offline_database_setup, offline_config):
        # GIVEN
        instruments_directory = offline_config.DATA_DIR / INSTRUMENTS_DATA

        # WHEN
        hornbostel_sachs_instruments = LoaderRole.load_hornbostel_sachs_instruments(
            instruments_directory
        )

        # THEN
        expected = 1865
        actual = len(hornbostel_sachs_instruments)
        assert actual == expected

    def test_load_roles_from_files(self, offline_database_setup, offline_config):
        # GIVEN
        roles_directory = offline_config.DATA_DIR / ROLES_DATA

        # WHEN
        roles_from_files = LoaderRole.load_roles_from_files(roles_directory)

        # THEN
        expected = 992
        actual = len(roles_from_files)
        assert actual == expected

    @pytest.mark.asyncio
    async def test_load_roles_from_files_from_database(self, offline_database_setup, offline_config,
                                                       reset_offline_database):
        # GIVEN
        roles_directory = offline_config.DATA_DIR / ROLES_DATA
        roles_from_files = LoaderRole.load_roles_from_files(roles_directory)

        # WHEN
        await LoaderRole.save_roles(roles_from_files)
        await RoleDataAccess.load_all_roles_into_cache()

        # THEN
        actual = len(roles_from_files)
        expected = len(RoleCache.role_name_to_role_id_lookup)
        assert expected > 0
        assert expected <= actual
        assert len(RoleCache.role_name_to_role_id_lookup) == len(RoleCache.role_id_to_role_name_lookup)

    @pytest.mark.asyncio
    async def test_load_hornbostel_sachs_instruments_from_database(self, offline_database_setup, offline_config,
                                                                   reset_offline_database):
        # GIVEN
        instruments_directory = offline_config.DATA_DIR / INSTRUMENTS_DATA
        hornbostel_sachs_roles = LoaderRole.load_hornbostel_sachs_instruments(
            instruments_directory
        )

        # WHEN
        await LoaderRole.save_roles(hornbostel_sachs_roles)
        await RoleDataAccess.load_all_roles_into_cache()

        # THEN
        actual = len(hornbostel_sachs_roles)
        expected = len(RoleCache.role_name_to_role_id_lookup)
        assert expected > 0
        assert expected <= actual
        assert len(RoleCache.role_name_to_role_id_lookup) == len(RoleCache.role_id_to_role_name_lookup)

    @pytest.mark.asyncio
    async def test_load_wikipedia_instruments_from_database(self, offline_database_setup, offline_config,
                                                            reset_offline_database):
        # GIVEN
        instruments_directory = offline_config.DATA_DIR / INSTRUMENTS_DATA
        wikipedia_instruments = LoaderRole.load_wikipedia_instruments(
            instruments_directory
        )

        # WHEN
        await LoaderRole.save_roles(wikipedia_instruments)
        await RoleDataAccess.load_all_roles_into_cache()

        # THEN
        actual = len(wikipedia_instruments)
        expected = len(RoleCache.role_name_to_role_id_lookup)
        assert expected > 0
        assert expected <= actual
        assert len(RoleCache.role_name_to_role_id_lookup) == len(RoleCache.role_id_to_role_name_lookup)
