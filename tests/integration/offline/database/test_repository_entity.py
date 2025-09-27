from typing import AsyncGenerator

import pytest

from musigree.config import Configuration
from musigree.constants import DISCOGS_DATA
from musigree.library.fields.entity_type import EntityType
from musigree.offline.database.entity_repository import EntityRepository
from musigree.offline.database.offline_transaction import offline_transaction
from musigree.offline.loader.loader_utils import LoaderUtils
from musigree.offline.loader.parser_entity import ParserEntity
from tests.conftest import AbstractDatabaseTest


@pytest.mark.parametrize("is_load_offline_data_required", [False], scope="class")
class TestRepositoryEntity(AbstractDatabaseTest):
    @pytest.mark.asyncio
    async def test_create_01(
        self,
        offline_database_setup: AsyncGenerator[None, None],
        offline_config: Configuration,
    ) -> None:
        # GIVEN
        discogs_data_directory = offline_config.DATA_DIR / DISCOGS_DATA
        iterator = LoaderUtils.get_iterator(
            discogs_data_directory, "artist", "testinsert"
        )
        entity_element = next(iterator)
        entity = ParserEntity().from_element(entity_element)

        # WHEN
        async with offline_transaction():
            repository = EntityRepository()
            created_entity = await repository.create(entity)

        # THEN
        assert entity == created_entity

    @pytest.mark.asyncio
    async def test_get_01(
        self,
        offline_database_setup: AsyncGenerator[None, None],
        offline_config: Configuration,
    ) -> None:
        # GIVEN
        discogs_data_directory = offline_config.DATA_DIR / DISCOGS_DATA
        iterator = LoaderUtils.get_iterator(
            discogs_data_directory, "label", "testinsert"
        )
        entity_element = next(iterator)
        entity = ParserEntity().from_element(entity_element)

        # WHEN
        async with offline_transaction():
            repository = EntityRepository()
            created_entity = await repository.create(entity)

            retrieved_entity = await repository.get_by_entity_id_and_entity_type(
                1, EntityType.LABEL
            )

        # THEN
        assert created_entity == retrieved_entity
