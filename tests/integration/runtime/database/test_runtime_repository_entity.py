from typing import AsyncGenerator

import pytest
import pydantic

from musigree.config import Configuration
from musigree.constants import DISCOGS_DATA
from musigree.library.fields.entity_type import EntityType
from musigree.offline.loader.loader_utils import LoaderUtils
from musigree.offline.loader.parser_entity import ParserEntity
from musigree.runtime.runtime_database.runtime_entity_repository import (
    RuntimeEntityRepository,
)
from musigree.runtime.runtime_database.runtime_transaction import runtime_transaction
from musigree.runtime.runtime_domain.entity import RuntimeEntity
from tests.conftest import AbstractDatabaseTest


@pytest.mark.parametrize("is_load_runtime_data_required", [False], scope="class")
class TestRuntimeRepositoryEntity(AbstractDatabaseTest):
    @pytest.mark.asyncio
    async def test_create_01(
        self,
        runtime_database_setup: AsyncGenerator[None, None],
        runtime_config: Configuration,
    ) -> None:
        """Test creating a runtime entity."""
        # GIVEN
        discogs_data_directory = runtime_config.DATA_DIR / DISCOGS_DATA
        iterator = LoaderUtils.get_iterator(discogs_data_directory, "artist", "testinsert")
        entity_element = next(iterator)
        entity = ParserEntity().from_element(entity_element)

        countries = "UK"
        genres = "Rock"
        styles = "Psychedelic"
        runtime_entity = RuntimeEntity(
            countries=countries,
            genres=genres,
            styles=styles,
            **entity.model_dump(),
        )

        # WHEN
        async with runtime_transaction():
            repository = RuntimeEntityRepository()
            created_entity = await repository.create(runtime_entity)

        # THEN
        assert runtime_entity == created_entity

    @pytest.mark.asyncio
    async def test_get_01(
        self,
        runtime_database_setup: AsyncGenerator[None, None],
        runtime_config: Configuration,
    ) -> None:
        """Test retrieving a runtime entity by ID and type."""
        # GIVEN
        discogs_data_directory = runtime_config.DATA_DIR / DISCOGS_DATA
        iterator = LoaderUtils.get_iterator(discogs_data_directory, "label", "testinsert")
        entity_element = next(iterator)
        entity = ParserEntity().from_element(entity_element)
        countries = "US"
        genres = "Electronic"
        styles = "Psy-trance"
        runtime_entity = RuntimeEntity(
            countries=countries,
            genres=genres,
            styles=styles,
            **entity.model_dump(),
        )

        # WHEN
        async with runtime_transaction():
            repository = RuntimeEntityRepository()
            try:
                created_entity = await repository.create(runtime_entity)
            except pydantic.ValidationError as validation_error:
                print(f"{validation_error.errors()}")

            retrieved_entity = await repository.get_by_entity_id_and_entity_type(
                1, EntityType.LABEL
            )

        # THEN
        assert created_entity == retrieved_entity

    @pytest.mark.asyncio
    async def test_create_02(
        self,
        runtime_database_setup: AsyncGenerator[None, None],
        runtime_config: Configuration,
    ) -> None:
        """Test creating a more complex runtime entity with members."""
        # GIVEN
        discogs_data_directory = runtime_config.DATA_DIR / DISCOGS_DATA
        iterator = LoaderUtils.get_iterator(discogs_data_directory, "artist", "testinsert")
        # Skip to the 9th element
        for _ in range(8):
            next(iterator)
        entity_element = next(iterator)
        entity = ParserEntity().from_element(entity_element)

        countries = "UK"
        genres = "Rock"
        styles = "Psychedelic"
        runtime_entity = RuntimeEntity(
            countries=countries,
            genres=genres,
            styles=styles,
            **entity.model_dump(),
        )

        # WHEN
        async with runtime_transaction():
            repository = RuntimeEntityRepository()
            created_entity = await repository.create(runtime_entity)

        # THEN
        assert runtime_entity == created_entity
        expected_members = {"Chris Duckenfield": 8783, "Richard Brown": 11454}
        assert expected_members == created_entity.entities.get("members")
        assert countries == created_entity.countries
        assert genres == created_entity.genres
        assert styles == created_entity.styles
