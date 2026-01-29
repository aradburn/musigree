from typing import AsyncGenerator

import pytest

from musigree.config import Configuration
from musigree.constants import DISCOGS_DATA
from musigree.offline.offline_database.offline_transaction import offline_transaction
from musigree.offline.offline_database.release_repository import ReleaseRepository
from musigree.offline.loader.loader_utils import LoaderUtils
from musigree.offline.loader.parser_release import ParserRelease
from tests.conftest import AbstractDatabaseTest


@pytest.mark.parametrize("is_load_offline_data_required", [False], scope="class")
class TestRepositoryRelease(AbstractDatabaseTest):
    @pytest.mark.asyncio
    async def test_create_01(
        self,
        offline_database_setup: AsyncGenerator[None, None],
        offline_config: Configuration, is_load_offline_data_required: bool
    ) -> None:
        # GIVEN
        discogs_data_directory = offline_config.DATA_DIR / DISCOGS_DATA
        iterator = LoaderUtils.get_iterator(discogs_data_directory, "release", "testinsert")
        release_element = next(iterator)
        release = ParserRelease().from_element(release_element)

        # WHEN
        async with offline_transaction():
            repository = ReleaseRepository()
            created_release = await repository.create(release)

        # THEN
        assert release == created_release

    @pytest.mark.asyncio
    async def test_get_01(
        self,
        offline_database_setup: AsyncGenerator[None, None],
        offline_config: Configuration, is_load_offline_data_required: bool
    ) -> None:
        # GIVEN
        discogs_data_directory = offline_config.DATA_DIR / DISCOGS_DATA
        iterator = LoaderUtils.get_iterator(discogs_data_directory, "release", "testinsert")
        next(iterator)
        next(iterator)
        next(iterator)
        next(iterator)
        next(iterator)
        next(iterator)
        release_element = next(iterator)
        release = ParserRelease().from_element(release_element)

        # WHEN
        async with offline_transaction():
            repository = ReleaseRepository()
            created_release = await repository.create(release)

            retrieved_release = await repository.get_by_id(635)

        # THEN
        assert created_release == retrieved_release
