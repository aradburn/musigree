from typing import AsyncGenerator

import pytest

from musigree.config import Configuration
from musigree.constants import DISCOGS_DATA
from musigree.offline.data_access_layer.offline_entity_data_access import OfflineEntityDataAccess
from musigree.offline.data_access_layer.offline_relation_data_access import OfflineRelationDataAccess
from musigree.offline.offline_database.entity_repository import EntityRepository
from musigree.offline.offline_database.offline_transaction import offline_transaction
from musigree.offline.offline_domain.relation import RelationUncommitted
from tests import id_utils
from tests.conftest import AbstractDatabaseTest


@pytest.mark.parametrize("is_load_offline_data_required", [True], scope="class")
class TestRelationDataAccess(AbstractDatabaseTest):
    @pytest.mark.asyncio
    async def test_from_release(
        self,
        offline_database_setup: AsyncGenerator[None, None],
        offline_config: Configuration, is_load_offline_data_required: bool
    ) -> None:
        # GIVEN
        release_id = 1700
        discogs_data_directory = offline_config.DATA_DIR / DISCOGS_DATA

        release = id_utils.get_test_release_by_id(discogs_data_directory, release_id)
        async with offline_transaction():
            entity_repository = EntityRepository()
            await OfflineEntityDataAccess().resolve_release_references(entity_repository, release)

        # WHEN
        actual = OfflineRelationDataAccess.from_release(release)

        # THEN
        expected = [
            RelationUncommitted(
                object=1000023528,
                role_name="Compiled On",
                subject=41,
                release_id=1700,
                year=1994,
            ),
            RelationUncommitted(
                object=41,
                role_name="Written By",
                subject=42,
                release_id=1700,
                year=1994,
            ),
            RelationUncommitted(
                object=1795,
                role_name="Remix",
                subject=79,
                release_id=1700,
                year=1994,
            ),
            RelationUncommitted(
                object=1795,
                role_name="Written By",
                subject=98,
                release_id=1700,
                year=1994,
            ),
            RelationUncommitted(
                object=1000023528,
                role_name="Compiled On",
                subject=201,
                release_id=1700,
                year=1994,
            ),
            RelationUncommitted(
                object=1000023528,
                role_name="Liner Notes",
                subject=391,
                release_id=1700,
                year=1994,
            ),
            RelationUncommitted(
                object=1000023528,
                role_name="Compiled On",
                subject=823,
                release_id=1700,
                year=1994,
            ),
            RelationUncommitted(
                object=1000023528,
                role_name="Compiled On",
                subject=939,
                release_id=1700,
                year=1994,
            ),
            RelationUncommitted(
                object=1000023528,
                role_name="Compiled On",
                subject=1795,
                release_id=1700,
                year=1994,
            ),
            RelationUncommitted(
                object=1000023528,
                role_name="Compiled On",
                subject=2235,
                release_id=1700,
                year=1994,
            ),
            RelationUncommitted(
                object=2235,
                role_name="Written By",
                subject=2235,
                release_id=1700,
                year=1994,
            ),
            RelationUncommitted(
                object=1000023528,
                role_name="Compiled On",
                subject=2236,
                release_id=1700,
                year=1994,
            ),
            RelationUncommitted(
                object=1000023528,
                role_name="Compiled On",
                subject=2237,
                release_id=1700,
                year=1994,
            ),
            RelationUncommitted(
                object=2235,
                role_name="Remix",
                subject=2237,
                release_id=1700,
                year=1994,
            ),
            RelationUncommitted(
                object=2237,
                role_name="Written By",
                subject=2237,
                release_id=1700,
                year=1994,
            ),
            RelationUncommitted(
                object=1000023528,
                role_name="Compiled On",
                subject=2238,
                release_id=1700,
                year=1994,
            ),
            RelationUncommitted(
                object=2238,
                role_name="Written By",
                subject=2238,
                release_id=1700,
                year=1994,
            ),
            RelationUncommitted(
                object=1000023528,
                role_name="Compiled On",
                subject=2239,
                release_id=1700,
                year=1994,
            ),
            RelationUncommitted(
                object=1795,
                role_name="Written By",
                subject=2716,
                release_id=1700,
                year=1994,
            ),
            RelationUncommitted(
                object=823,
                role_name="Written By",
                subject=4295,
                release_id=1700,
                year=1994,
            ),
            RelationUncommitted(
                object=201,
                role_name="Written By",
                subject=5025,
                release_id=1700,
                year=1994,
            ),
            RelationUncommitted(
                object=2239,
                role_name="Written By",
                subject=51674,
                release_id=1700,
                year=1994,
            ),
            RelationUncommitted(
                object=2239,
                role_name="Written By",
                subject=66803,
                release_id=1700,
                year=1994,
            ),
            RelationUncommitted(
                object=2239,
                role_name="Written By",
                subject=115880,
                release_id=1700,
                year=1994,
            ),
            RelationUncommitted(
                object=41,
                role_name="Written By",
                subject=300407,
                release_id=1700,
                year=1994,
            ),
            RelationUncommitted(
                object=1000023528,
                role_name="Artwork By",
                subject=445854,
                release_id=1700,
                year=1994,
            ),
            RelationUncommitted(
                object=2239,
                role_name="Written By",
                subject=489350,
                release_id=1700,
                year=1994,
            ),
            RelationUncommitted(
                object=939,
                role_name="Written By",
                subject=518861,
                release_id=1700,
                year=1994,
            ),
            RelationUncommitted(
                object=2236,
                role_name="Written By",
                subject=547610,
                release_id=1700,
                year=1994,
            ),
            RelationUncommitted(
                object=2236,
                role_name="Written By",
                subject=547611,
                release_id=1700,
                year=1994,
            ),
            RelationUncommitted(
                object=939,
                role_name="Written By",
                subject=605613,
                release_id=1700,
                year=1994,
            ),
            RelationUncommitted(
                object=1000023528,
                role_name="Artwork By",
                subject=1548777,
                release_id=1700,
                year=1994,
            ),
            RelationUncommitted(
                object=1000023528,
                role_name="Copyright",
                subject=1000023528,
                release_id=1700,
                year=1994,
            ),
            RelationUncommitted(
                object=1000023528,
                role_name="Phonographic Copyright",
                subject=1000023528,
                release_id=1700,
                year=1994,
            ),
        ]
        assert actual == expected

    @pytest.mark.asyncio
    async def test_get_release_setup(
        self,
        offline_database_setup: AsyncGenerator[None, None],
        offline_config: Configuration, is_load_offline_data_required: bool
    ) -> None:
        # GIVEN
        release_id = 1700
        discogs_data_directory = offline_config.DATA_DIR / DISCOGS_DATA
        release = id_utils.get_test_release_by_id(discogs_data_directory, release_id)
        async with offline_transaction():
            entity_repository = EntityRepository()
            await OfflineEntityDataAccess().resolve_release_references(entity_repository, release)

        # WHEN
        actual = OfflineRelationDataAccess.from_release(release)

        # THEN
        expected = [
            RelationUncommitted(
                object=1000023528,
                role_name="Compiled On",
                subject=41,
                release_id=1700,
                year=1994,
            ),
            RelationUncommitted(
                object=41,
                role_name="Written By",
                subject=42,
                release_id=1700,
                year=1994,
            ),
            RelationUncommitted(
                object=1795,
                role_name="Remix",
                subject=79,
                release_id=1700,
                year=1994,
            ),
            RelationUncommitted(
                object=1795,
                role_name="Written By",
                subject=98,
                release_id=1700,
                year=1994,
            ),
            RelationUncommitted(
                object=1000023528,
                role_name="Compiled On",
                subject=201,
                release_id=1700,
                year=1994,
            ),
            RelationUncommitted(
                object=1000023528,
                role_name="Liner Notes",
                subject=391,
                release_id=1700,
                year=1994,
            ),
            RelationUncommitted(
                object=1000023528,
                role_name="Compiled On",
                subject=823,
                release_id=1700,
                year=1994,
            ),
            RelationUncommitted(
                object=1000023528,
                role_name="Compiled On",
                subject=939,
                release_id=1700,
                year=1994,
            ),
            RelationUncommitted(
                object=1000023528,
                role_name="Compiled On",
                subject=1795,
                release_id=1700,
                year=1994,
            ),
            RelationUncommitted(
                object=1000023528,
                role_name="Compiled On",
                subject=2235,
                release_id=1700,
                year=1994,
            ),
            RelationUncommitted(
                object=2235,
                role_name="Written By",
                subject=2235,
                release_id=1700,
                year=1994,
            ),
            RelationUncommitted(
                object=1000023528,
                role_name="Compiled On",
                subject=2236,
                release_id=1700,
                year=1994,
            ),
            RelationUncommitted(
                object=1000023528,
                role_name="Compiled On",
                subject=2237,
                release_id=1700,
                year=1994,
            ),
            RelationUncommitted(
                object=2235,
                role_name="Remix",
                subject=2237,
                release_id=1700,
                year=1994,
            ),
            RelationUncommitted(
                object=2237,
                role_name="Written By",
                subject=2237,
                release_id=1700,
                year=1994,
            ),
            RelationUncommitted(
                object=1000023528,
                role_name="Compiled On",
                subject=2238,
                release_id=1700,
                year=1994,
            ),
            RelationUncommitted(
                object=2238,
                role_name="Written By",
                subject=2238,
                release_id=1700,
                year=1994,
            ),
            RelationUncommitted(
                object=1000023528,
                role_name="Compiled On",
                subject=2239,
                release_id=1700,
                year=1994,
            ),
            RelationUncommitted(
                object=1795,
                role_name="Written By",
                subject=2716,
                release_id=1700,
                year=1994,
            ),
            RelationUncommitted(
                object=823,
                role_name="Written By",
                subject=4295,
                release_id=1700,
                year=1994,
            ),
            RelationUncommitted(
                object=201,
                role_name="Written By",
                subject=5025,
                release_id=1700,
                year=1994,
            ),
            RelationUncommitted(
                object=2239,
                role_name="Written By",
                subject=51674,
                release_id=1700,
                year=1994,
            ),
            RelationUncommitted(
                object=2239,
                role_name="Written By",
                subject=66803,
                release_id=1700,
                year=1994,
            ),
            RelationUncommitted(
                object=2239,
                role_name="Written By",
                subject=115880,
                release_id=1700,
                year=1994,
            ),
            RelationUncommitted(
                object=41,
                role_name="Written By",
                subject=300407,
                release_id=1700,
                year=1994,
            ),
            RelationUncommitted(
                object=1000023528,
                role_name="Artwork By",
                subject=445854,
                release_id=1700,
                year=1994,
            ),
            RelationUncommitted(
                object=2239,
                role_name="Written By",
                subject=489350,
                release_id=1700,
                year=1994,
            ),
            RelationUncommitted(
                object=939,
                role_name="Written By",
                subject=518861,
                release_id=1700,
                year=1994,
            ),
            RelationUncommitted(
                object=2236,
                role_name="Written By",
                subject=547610,
                release_id=1700,
                year=1994,
            ),
            RelationUncommitted(
                object=2236,
                role_name="Written By",
                subject=547611,
                release_id=1700,
                year=1994,
            ),
            RelationUncommitted(
                object=939,
                role_name="Written By",
                subject=605613,
                release_id=1700,
                year=1994,
            ),
            RelationUncommitted(
                object=1000023528,
                role_name="Artwork By",
                subject=1548777,
                release_id=1700,
                year=1994,
            ),
            RelationUncommitted(
                object=1000023528,
                role_name="Copyright",
                subject=1000023528,
                release_id=1700,
                year=1994,
            ),
            RelationUncommitted(
                object=1000023528,
                role_name="Phonographic Copyright",
                subject=1000023528,
                release_id=1700,
                year=1994,
            ),
        ]
        assert actual == expected
