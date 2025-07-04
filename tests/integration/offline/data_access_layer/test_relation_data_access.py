import pytest

from musigree.constants import DISCOGS_DATA
from musigree.offline.data_access_layer.entity_data_access import EntityDataAccess
from musigree.offline.data_access_layer.relation_data_access import RelationDataAccess
from musigree.offline.database.entity_repository import EntityRepository
from musigree.offline.database.offline_transaction import offline_transaction
from musigree.offline.domain.relation import RelationUncommitted
from tests import id_utils
from tests.conftest import NotATest


@pytest.mark.parametrize("is_load_offline_data_required", [True], scope="class")
class TestRelationDataAccess(NotATest):

    @pytest.mark.asyncio
    async def test_from_release(self, offline_database_setup, offline_config):
        # GIVEN
        release_id = 1700
        discogs_data_directory = offline_config.DATA_DIR / DISCOGS_DATA

        release = id_utils.get_test_release_by_id(discogs_data_directory, release_id)
        async with offline_transaction():
            entity_repository = EntityRepository()
            await EntityDataAccess().resolve_release_references(entity_repository, release)

        # WHEN
        actual = RelationDataAccess.from_release(release)

        # THEN
        expected = [
            RelationUncommitted(
                object=1000023528,
                role_name="Compiled On",
                subject=41,
            ),
            RelationUncommitted(
                object=41,
                role_name="Written By",
                subject=42,
            ),
            RelationUncommitted(
                object=1795,
                role_name="Remix",
                subject=79,
            ),
            RelationUncommitted(
                object=1795,
                role_name="Written By",
                subject=98,
            ),
            RelationUncommitted(
                object=1000023528,
                role_name="Compiled On",
                subject=201,
            ),
            RelationUncommitted(
                object=1000023528,
                role_name="Liner Notes",
                subject=391,
            ),
            RelationUncommitted(
                object=1000023528,
                role_name="Compiled On",
                subject=823,
            ),
            RelationUncommitted(
                object=1000023528,
                role_name="Compiled On",
                subject=939,
            ),
            RelationUncommitted(
                object=1000023528,
                role_name="Compiled On",
                subject=1795,
            ),
            RelationUncommitted(
                object=1000023528,
                role_name="Compiled On",
                subject=2235,
            ),
            RelationUncommitted(
                object=2235,
                role_name="Written By",
                subject=2235,
            ),
            RelationUncommitted(
                object=1000023528,
                role_name="Compiled On",
                subject=2236,
            ),
            RelationUncommitted(
                object=1000023528,
                role_name="Compiled On",
                subject=2237,
            ),
            RelationUncommitted(
                object=2235,
                role_name="Remix",
                subject=2237,
            ),
            RelationUncommitted(
                object=2237,
                role_name="Written By",
                subject=2237,
            ),
            RelationUncommitted(
                object=1000023528,
                role_name="Compiled On",
                subject=2238,
            ),
            RelationUncommitted(
                object=2238,
                role_name="Written By",
                subject=2238,
            ),
            RelationUncommitted(
                object=1000023528,
                role_name="Compiled On",
                subject=2239,
            ),
            RelationUncommitted(
                object=1795,
                role_name="Written By",
                subject=2716,
            ),
            RelationUncommitted(
                object=823,
                role_name="Written By",
                subject=4295,
            ),
            RelationUncommitted(
                object=201,
                role_name="Written By",
                subject=5025,
            ),
            RelationUncommitted(
                object=2239,
                role_name="Written By",
                subject=51674,
            ),
            RelationUncommitted(
                object=2239,
                role_name="Written By",
                subject=66803,
            ),
            RelationUncommitted(
                object=2239,
                role_name="Written By",
                subject=115880,
            ),
            RelationUncommitted(
                object=41,
                role_name="Written By",
                subject=300407,
            ),
            RelationUncommitted(
                object=1000023528,
                role_name="Artwork By",
                subject=445854,
            ),
            RelationUncommitted(
                object=2239,
                role_name="Written By",
                subject=489350,
            ),
            RelationUncommitted(
                object=939,
                role_name="Written By",
                subject=518861,
            ),
            RelationUncommitted(
                object=2236,
                role_name="Written By",
                subject=547610,
            ),
            RelationUncommitted(
                object=2236,
                role_name="Written By",
                subject=547611,
            ),
            RelationUncommitted(
                object=939,
                role_name="Written By",
                subject=605613,
            ),
            RelationUncommitted(
                object=1000023528,
                role_name="Artwork By",
                subject=1548777,
            ),
            RelationUncommitted(
                object=1000023528,
                role_name="Copyright",
                subject=1000023528,
            ),
            RelationUncommitted(
                object=1000023528,
                role_name="Phonographic Copyright",
                subject=1000023528,
            ),
        ]
        assert actual == expected

    @pytest.mark.asyncio
    async def test_get_release_setup(self, offline_database_setup, offline_config):
        # GIVEN
        release_id = 1700
        discogs_data_directory = offline_config.DATA_DIR / DISCOGS_DATA
        release = id_utils.get_test_release_by_id(discogs_data_directory, release_id)
        async with offline_transaction():
            entity_repository = EntityRepository()
            await EntityDataAccess().resolve_release_references(entity_repository, release)

        # WHEN
        actual = RelationDataAccess.from_release(release)

        # THEN
        expected = [
            RelationUncommitted(
                object=1000023528,
                role_name="Compiled On",
                subject=41,
            ),
            RelationUncommitted(
                object=41,
                role_name="Written By",
                subject=42,
            ),
            RelationUncommitted(
                object=1795,
                role_name="Remix",
                subject=79,
            ),
            RelationUncommitted(
                object=1795,
                role_name="Written By",
                subject=98,
            ),
            RelationUncommitted(
                object=1000023528,
                role_name="Compiled On",
                subject=201,
            ),
            RelationUncommitted(
                object=1000023528,
                role_name="Liner Notes",
                subject=391,
            ),
            RelationUncommitted(
                object=1000023528,
                role_name="Compiled On",
                subject=823,
            ),
            RelationUncommitted(
                object=1000023528,
                role_name="Compiled On",
                subject=939,
            ),
            RelationUncommitted(
                object=1000023528,
                role_name="Compiled On",
                subject=1795,
            ),
            RelationUncommitted(
                object=1000023528,
                role_name="Compiled On",
                subject=2235,
            ),
            RelationUncommitted(
                object=2235,
                role_name="Written By",
                subject=2235,
            ),
            RelationUncommitted(
                object=1000023528,
                role_name="Compiled On",
                subject=2236,
            ),
            RelationUncommitted(
                object=1000023528,
                role_name="Compiled On",
                subject=2237,
            ),
            RelationUncommitted(
                object=2235,
                role_name="Remix",
                subject=2237,
            ),
            RelationUncommitted(
                object=2237,
                role_name="Written By",
                subject=2237,
            ),
            RelationUncommitted(
                object=1000023528,
                role_name="Compiled On",
                subject=2238,
            ),
            RelationUncommitted(
                object=2238,
                role_name="Written By",
                subject=2238,
            ),
            RelationUncommitted(
                object=1000023528,
                role_name="Compiled On",
                subject=2239,
            ),
            RelationUncommitted(
                object=1795,
                role_name="Written By",
                subject=2716,
            ),
            RelationUncommitted(
                object=823,
                role_name="Written By",
                subject=4295,
            ),
            RelationUncommitted(
                object=201,
                role_name="Written By",
                subject=5025,
            ),
            RelationUncommitted(
                object=2239,
                role_name="Written By",
                subject=51674,
            ),
            RelationUncommitted(
                object=2239,
                role_name="Written By",
                subject=66803,
            ),
            RelationUncommitted(
                object=2239,
                role_name="Written By",
                subject=115880,
            ),
            RelationUncommitted(
                object=41,
                role_name="Written By",
                subject=300407,
            ),
            RelationUncommitted(
                object=1000023528,
                role_name="Artwork By",
                subject=445854,
            ),
            RelationUncommitted(
                object=2239,
                role_name="Written By",
                subject=489350,
            ),
            RelationUncommitted(
                object=939,
                role_name="Written By",
                subject=518861,
            ),
            RelationUncommitted(
                object=2236,
                role_name="Written By",
                subject=547610,
            ),
            RelationUncommitted(
                object=2236,
                role_name="Written By",
                subject=547611,
            ),
            RelationUncommitted(
                object=939,
                role_name="Written By",
                subject=605613,
            ),
            RelationUncommitted(
                object=1000023528,
                role_name="Artwork By",
                subject=1548777,
            ),
            RelationUncommitted(
                object=1000023528,
                role_name="Copyright",
                subject=1000023528,
            ),
            RelationUncommitted(
                object=1000023528,
                role_name="Phonographic Copyright",
                subject=1000023528,
            ),
        ]
        assert actual == expected
