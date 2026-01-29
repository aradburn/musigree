from typing import AsyncGenerator

import pytest

from musigree.config import Configuration
from musigree.constants import ENTITY_DETAILS_DATA, ENTITY_DETAILS_FILENAME
from musigree.offline.data_access_layer.offline_release_data_access import OfflineReleaseDataAccess
from musigree.offline.offline_database.offline_transaction import offline_transaction
from musigree.offline.offline_database.relation_repository import RelationRepository
from musigree.offline.offline_database.release_repository import ReleaseRepository
from musigree.offline.offline_database.role_repository import RoleRepository
from musigree.runtime.runtime_database.runtime_country_repository import RuntimeCountryRepository
from musigree.runtime.runtime_database.runtime_entity_repository import (
    RuntimeEntityRepository,
)
from musigree.runtime.runtime_database.runtime_genre_repository import RuntimeGenreRepository
from musigree.runtime.runtime_database.runtime_relation_repository import (
    RuntimeRelationRepository,
)
from musigree.runtime.runtime_database.runtime_role_repository import (
    RuntimeRoleRepository,
)
from musigree.runtime.runtime_database.runtime_style_repository import RuntimeStyleRepository
from musigree.runtime.runtime_database.runtime_transaction import runtime_transaction
from musigree.transfer.transfer_manager import TransferManager
from tests.conftest import AbstractDatabaseTest


@pytest.mark.parametrize("is_load_offline_data_required", [True], scope="class")
@pytest.mark.parametrize("is_load_runtime_data_required", [False], scope="class")
class TestTransfer(AbstractDatabaseTest):
    @pytest.mark.asyncio
    async def test_transfer_roles(
        self,
        offline_database_setup: AsyncGenerator[None, None],
        runtime_database_setup: AsyncGenerator[None, None], is_load_offline_data_required: bool,
        is_load_runtime_data_required: bool
    ) -> None:
        # GIVEN
        async with offline_transaction():
            offline_role_repository = RoleRepository()
            expected_count = await offline_role_repository.count()

        # WHEN
        await TransferManager.transfer_role()

        # THEN
        async with runtime_transaction():
            runtime_role_repository = RuntimeRoleRepository()
            actual_count = await runtime_role_repository.count()

        assert actual_count == expected_count

    @pytest.mark.asyncio
    async def test_transfer_entities(
        self,
        runtime_config: Configuration,
        offline_database_setup: AsyncGenerator[None, None],
        runtime_database_setup: AsyncGenerator[None, None], is_load_offline_data_required: bool,
        is_load_runtime_data_required: bool
    ) -> None:
        # GIVEN
        entity_details_path = (
            runtime_config.DATA_DIR / ENTITY_DETAILS_DATA / ENTITY_DETAILS_FILENAME
        )
        await TransferManager.transfer_load_entity_details_index(entity_details_path)

        # WHEN
        await TransferManager.transfer_entity()

        # THEN
        async with runtime_transaction():
            runtime_entity_repository = RuntimeEntityRepository()
            actual_count = await runtime_entity_repository.count()

        expected_count = 6216
        assert actual_count == expected_count

    @pytest.mark.asyncio
    async def test_transfer_relations(
        self,
        offline_database_setup: AsyncGenerator[None, None],
        runtime_database_setup: AsyncGenerator[None, None], is_load_offline_data_required: bool,
        is_load_runtime_data_required: bool
    ) -> None:
        # GIVEN
        async with offline_transaction():
            offline_relation_repository = RelationRepository()
            expected_count = await offline_relation_repository.count()

        # WHEN
        await TransferManager.transfer_relation()

        # THEN
        async with runtime_transaction():
            runtime_relation_repository = RuntimeRelationRepository()
            actual_count = await runtime_relation_repository.count()

        assert actual_count == expected_count

    @pytest.mark.asyncio
    async def test_transfer_entity_details(
        self,
        offline_database_setup: AsyncGenerator[None, None],
        runtime_database_setup: AsyncGenerator[None, None], is_load_offline_data_required: bool,
        is_load_runtime_data_required: bool
    ) -> None:
        # GIVEN
        async with runtime_transaction():
            runtime_country_repository = RuntimeCountryRepository()
            runtime_genre_repository = RuntimeGenreRepository()
            runtime_style_repository = RuntimeStyleRepository()

            actual_country_count = await runtime_country_repository.count()
            actual_genre_count = await runtime_genre_repository.count()
            actual_style_count = await runtime_style_repository.count()
            assert actual_country_count == 0
            assert actual_genre_count == 0
            assert actual_style_count == 0

        async with offline_transaction():
            offline_release_repository = ReleaseRepository()
            await OfflineReleaseDataAccess.create_entity_details_index(offline_release_repository)

        # WHEN
        await TransferManager.transfer_entity_details()

        # THEN
        async with runtime_transaction():
            actual_country_count = await runtime_country_repository.count()
            actual_genre_count = await runtime_genre_repository.count()
            actual_style_count = await runtime_style_repository.count()

        expected_country_count = 30
        expected_genre_count = 16
        expected_style_count = 122

        assert actual_country_count == expected_country_count
        assert actual_genre_count == expected_genre_count
        assert actual_style_count == expected_style_count
