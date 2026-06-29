from typing import AsyncGenerator

import pytest

from musigree.config import Configuration
from musigree.constants import DISCOGS_DATA, TEST_DIR
from musigree.library.fields.entity_type import EntityType
from musigree.offline.data_access_layer.offline_entity_data_access import OfflineEntityDataAccess
from musigree.offline.offline_database.entity_repository import EntityRepository
from musigree.offline.offline_database.offline_transaction import offline_transaction
from musigree.offline.offline_database.token_repository import TokenRepository
from tests import id_utils
from tests.conftest import AbstractDatabaseTest


@pytest.mark.parametrize("is_load_offline_data_required", [True], scope="class")
class TestEntityDataAccess(AbstractDatabaseTest):
    @pytest.mark.asyncio
    async def test_init_text_search_index(
        self, offline_database_setup: AsyncGenerator[None, None], is_load_offline_data_required: bool
    ) -> None:
        async with offline_transaction():
            entity_repository = EntityRepository()
            index = await OfflineEntityDataAccess.create_text_search_index(entity_repository)

        # THEN
        assert len(index.token_index.items()) == 20550
        assert len(index.documents.items()) == 6216

    @pytest.mark.asyncio
    async def test_get_id_by_entity_type_and_entity_name_1(
        self, offline_database_setup: AsyncGenerator[None, None], is_load_offline_data_required: bool
    ) -> None:
        entity_type = EntityType.ARTIST
        entity_name = "Joker, The (3)"

        async with offline_transaction():
            entity_repository = EntityRepository()
            actual = await OfflineEntityDataAccess.get_id_by_entity_type_and_entity_name(
                entity_repository, entity_type, entity_name
            )

        # THEN
        expected = 8526
        assert actual == expected

    @pytest.mark.asyncio
    async def test_get_id_by_entity_type_and_entity_name_2(
        self, offline_database_setup: AsyncGenerator[None, None], is_load_offline_data_required: bool
    ) -> None:
        entity_type = EntityType.ARTIST
        entity_name = "fall"

        async with offline_transaction():
            entity_repository = EntityRepository()
            actual = await OfflineEntityDataAccess.get_id_by_entity_type_and_entity_name(
                entity_repository, entity_type, entity_name
            )

        # THEN
        expected = None
        assert actual == expected

    @pytest.mark.asyncio
    async def test_get_id_by_entity_type_and_entity_name_3(
        self, offline_database_setup: AsyncGenerator[None, None], is_load_offline_data_required: bool
    ) -> None:
        entity_type = EntityType.ARTIST
        entity_name = "the Fall"

        async with offline_transaction():
            entity_repository = EntityRepository()
            actual = await OfflineEntityDataAccess.get_id_by_entity_type_and_entity_name(
                entity_repository, entity_type, entity_name
            )

        # THEN
        expected = None
        assert actual == expected

    @pytest.mark.asyncio
    async def test_find_entity_id_by_entity_type_and_entity_name_1(
        self, offline_database_setup: AsyncGenerator[None, None], is_load_offline_data_required: bool
    ) -> None:
        entity_type = EntityType.ARTIST
        entity_name = "Joker, The (3)"

        async with offline_transaction():
            entity_repository = EntityRepository()
            token_repository = TokenRepository()
            actual = await OfflineEntityDataAccess.find_entity_id_by_entity_type_and_entity_name(
                entity_repository, token_repository, entity_type, entity_name
            )

        # THEN
        expected = 8526
        assert actual == expected

    @pytest.mark.asyncio
    async def test_find_entity_id_by_entity_type_and_entity_name_2(
        self, offline_database_setup: AsyncGenerator[None, None], is_load_offline_data_required: bool
    ) -> None:
        entity_type = EntityType.ARTIST
        entity_name = "fall"

        async with offline_transaction():
            entity_repository = EntityRepository()
            token_repository = TokenRepository()
            actual = await OfflineEntityDataAccess.find_entity_id_by_entity_type_and_entity_name(
                entity_repository, token_repository, entity_type, entity_name
            )

        # THEN
        expected = 2228
        assert actual == expected

    @pytest.mark.asyncio
    async def test_find_entity_id_by_entity_type_and_entity_name_3(
        self, offline_database_setup: AsyncGenerator[None, None], is_load_offline_data_required: bool
    ) -> None:
        entity_type = EntityType.ARTIST
        entity_name = "the Fall"

        async with offline_transaction():
            entity_repository = EntityRepository()
            token_repository = TokenRepository()
            actual = await OfflineEntityDataAccess.find_entity_id_by_entity_type_and_entity_name(
                entity_repository, token_repository, entity_type, entity_name
            )

        # THEN
        expected = 2228
        assert actual == expected

    @pytest.mark.asyncio
    async def test_resolve_entity_references_1(
        self, offline_database_setup: AsyncGenerator[None, None], is_load_offline_data_required: bool
    ) -> None:
        # GIVEN
        discogs_data_directory = TEST_DIR / "data" / DISCOGS_DATA
        entity_id = 48
        entity_type = EntityType.ARTIST
        entity = id_utils.get_test_entity_by_id(discogs_data_directory, entity_id, entity_type)

        # WHEN
        async with offline_transaction():
            entity_repository = EntityRepository()
            token_repository = TokenRepository()
            await OfflineEntityDataAccess.resolve_entity_references(entity_repository, token_repository, entity)
            actual = entity.entities

        # THEN
        expected = {
            "aliases": {
                "Aphex Twin": 45,
                "Dice Man, The": 820,
                "Polygon Window": 2931,
                "Richard D. James": 435132,
            }
        }
        assert actual == expected

    @pytest.mark.asyncio
    async def test_resolve_entity_references_2(
        self, offline_database_setup: AsyncGenerator[None, None], is_load_offline_data_required: bool
    ) -> None:
        # GIVEN
        discogs_data_directory = TEST_DIR / "data" / DISCOGS_DATA
        entity_id = 98
        entity_type = EntityType.ARTIST
        entity = id_utils.get_test_entity_by_id(discogs_data_directory, entity_id, entity_type)

        # WHEN
        async with offline_transaction():
            entity_repository = EntityRepository()
            token_repository = TokenRepository()
            await OfflineEntityDataAccess.resolve_entity_references(entity_repository, token_repository, entity)
            actual = entity.entities

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
        assert actual == expected

    @pytest.mark.asyncio
    async def test_resolve_entity_references_3(
        self, offline_database_setup: AsyncGenerator[None, None], is_load_offline_data_required: bool
    ) -> None:
        discogs_data_directory = TEST_DIR / "data" / DISCOGS_DATA
        entity_id = 288
        entity_type = EntityType.ARTIST
        entity = id_utils.get_test_entity_by_id(discogs_data_directory, entity_id, entity_type)

        # WHEN
        async with offline_transaction():
            entity_repository = EntityRepository()
            token_repository = TokenRepository()
            await OfflineEntityDataAccess.resolve_entity_references(entity_repository, token_repository, entity)
            actual = entity.entities

        # THEN
        expected = {
            "members": {
                "Alex Banks": 10141,
                "Jay Hurren": 474638,
            },
        }
        assert actual == expected

    @pytest.mark.asyncio
    async def test_resolve_entity_references_4(
        self, offline_database_setup: AsyncGenerator[None, None], is_load_offline_data_required: bool
    ) -> None:
        # GIVEN
        discogs_data_directory = TEST_DIR / "data" / DISCOGS_DATA
        entity_id = 61
        entity_type = EntityType.LABEL
        entity = id_utils.get_test_entity_by_id(discogs_data_directory, entity_id, entity_type)

        # WHEN
        async with offline_transaction():
            entity_repository = EntityRepository()
            token_repository = TokenRepository()
            await OfflineEntityDataAccess.resolve_entity_references(entity_repository, token_repository, entity)
            actual = entity.entities

        # THEN
        expected = {
            "parent_label": {
                "Instinct Records": 1000000063,
            }
        }
        assert actual == expected

    @pytest.mark.asyncio
    async def test_resolve_release_references_1(
        self,
        offline_database_setup: AsyncGenerator[None, None],
        offline_config: Configuration, is_load_offline_data_required: bool
    ) -> None:
        # GIVEN
        release_id = 637
        discogs_data_directory = offline_config.DATA_DIR / DISCOGS_DATA
        release = id_utils.get_test_release_by_id(discogs_data_directory, release_id)

        # WHEN
        async with offline_transaction():
            entity_repository = EntityRepository()
            await OfflineEntityDataAccess.resolve_release_references(entity_repository, release)
            actual = release.labels

        # THEN
        expected = [
            {"catalog_number": "WAP100CD", "id": 1000023528, "name": "Warp Records"},
            {"catalog_number": "WAP 100CD", "id": 1000023528, "name": "Warp Records"},
        ]
        assert actual == expected

    @pytest.mark.asyncio
    async def test_resolve_release_references_2(
        self,
        offline_database_setup: AsyncGenerator[None, None],
        offline_config: Configuration, is_load_offline_data_required: bool
    ) -> None:
        # GIVEN
        release_id = 158
        discogs_data_directory = offline_config.DATA_DIR / DISCOGS_DATA
        release = id_utils.get_test_release_by_id(discogs_data_directory, release_id)

        # WHEN
        async with offline_transaction():
            entity_repository = EntityRepository()
            await OfflineEntityDataAccess.resolve_release_references(entity_repository, release)
            actual = release.companies

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
        assert actual == expected

    @pytest.mark.asyncio
    async def test_resolve_release_references_3(
        self,
        offline_database_setup: AsyncGenerator[None, None],
        offline_config: Configuration, is_load_offline_data_required: bool
    ) -> None:
        # GIVEN
        release_id = 1700
        discogs_data_directory = offline_config.DATA_DIR / DISCOGS_DATA
        release = id_utils.get_test_release_by_id(discogs_data_directory, release_id)

        # WHEN
        async with offline_transaction():
            entity_repository = EntityRepository()
            await OfflineEntityDataAccess.resolve_release_references(entity_repository, release)
            actual = release.artists

        # THEN
        expected = [{"id": 0, "name": "Various"}]
        assert actual == expected

    @pytest.mark.asyncio
    async def test_resolve_release_references_4(
        self,
        offline_database_setup: AsyncGenerator[None, None],
        offline_config: Configuration, is_load_offline_data_required: bool
    ) -> None:
        # GIVEN
        release_id = 1700
        discogs_data_directory = offline_config.DATA_DIR / DISCOGS_DATA
        release = id_utils.get_test_release_by_id(discogs_data_directory, release_id)

        # WHEN
        async with offline_transaction():
            entity_repository = EntityRepository()
            await OfflineEntityDataAccess.resolve_release_references(entity_repository, release)
            actual = release.extra_artists

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
        assert actual == expected
