from typing import AsyncGenerator

import pytest

from musigree.config import Configuration
from musigree.constants import DISCOGS_DATA
from musigree.offline.offline_database.master_repository import MasterRepository
from musigree.offline.offline_database.offline_transaction import offline_transaction
from musigree.offline.loader.loader_utils import LoaderUtils
from musigree.offline.loader.parser_master import ParserMaster
from tests.conftest import AbstractDatabaseTest


@pytest.mark.parametrize("is_load_offline_data_required", [False], scope="class")
class TestRepositoryMaster(AbstractDatabaseTest):
    @pytest.mark.asyncio
    async def test_create_01(
        self,
        offline_database_setup: AsyncGenerator[None, None],
        offline_config: Configuration, is_load_offline_data_required: bool
    ) -> None:
        # GIVEN
        discogs_data_directory = offline_config.DATA_DIR / DISCOGS_DATA
        iterator = LoaderUtils.get_iterator(discogs_data_directory, "master", "testinsert")
        master_element = next(iterator)
        master = ParserMaster().from_element(master_element)

        # WHEN
        async with offline_transaction():
            repository = MasterRepository()
            created_master = await repository.create(master)

        # THEN
        assert master == created_master

    @pytest.mark.asyncio
    async def test_get_01(
        self,
        offline_database_setup: AsyncGenerator[None, None],
        offline_config: Configuration, is_load_offline_data_required: bool
    ) -> None:
        # GIVEN
        discogs_data_directory = offline_config.DATA_DIR / DISCOGS_DATA
        iterator = LoaderUtils.get_iterator(discogs_data_directory, "master", "testinsert")
        next(iterator)
        next(iterator)
        next(iterator)
        next(iterator)
        next(iterator)
        next(iterator)
        master_element = next(iterator)
        master = ParserMaster().from_element(master_element)

        # WHEN
        async with offline_transaction():
            repository = MasterRepository()
            created_master = await repository.create(master)

            retrieved_master = await repository.get_by_id(18041)

        # THEN
        assert created_master == retrieved_master
