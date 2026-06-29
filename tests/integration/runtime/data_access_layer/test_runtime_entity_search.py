from typing import AsyncGenerator

import pytest

from musigree.config import Configuration
from musigree.constants import TEXT_SEARCH_DATA, TEXT_SEARCH_FILENAME
from musigree.library.full_text_search.text_search_index import TextSearchIndex
from musigree.runtime.data_access_layer.runtime_entity_search import (
    RuntimeEntitySearch,
)
from musigree.runtime.runtime_database.runtime_entity_repository import RuntimeEntityRepository
from musigree.runtime.runtime_database.runtime_token_repository import RuntimeTokenRepository
from musigree.runtime.runtime_database.runtime_transaction import runtime_transaction
from musigree.runtime.runtime_database_manager import RuntimeDatabaseManager
from tests.conftest import AbstractDatabaseTest


@pytest.mark.parametrize("is_load_offline_data_required", [True], scope="class")
@pytest.mark.parametrize("is_load_runtime_data_required", [True], scope="class")
class TestRuntimeEntitySearch(AbstractDatabaseTest):
    @pytest.mark.asyncio
    async def test_text_search_lookup_1(
        self,
        runtime_config: Configuration,
        offline_database_setup: AsyncGenerator[None, None],
        runtime_database_setup: AsyncGenerator[None, None], is_load_offline_data_required: bool,
        is_load_runtime_data_required: bool
    ) -> None:
        """Test text search functionality for 'Wax' query."""
        text_search_path = runtime_config.DATA_DIR / TEXT_SEARCH_DATA / TEXT_SEARCH_FILENAME

        assert RuntimeDatabaseManager.runtime_database_helper is not None
        RuntimeDatabaseManager.runtime_database_helper.text_search_index = (
            TextSearchIndex.load_text_search_index_from_file(text_search_path)
        )
        async with runtime_transaction():
            runtime_entity_repository = RuntimeEntityRepository()
            token_repository = RuntimeTokenRepository()

            results = await RuntimeEntitySearch.search_entities(
                runtime_entity_repository, token_repository, "Wax"
            )

        # THEN
        expected = [
            {"key": "artist-333377", "name": "Wax (10)"},
            {"key": "artist-1163252", "name": "Wax (19)"},
            {"key": "artist-288583", "name": "Wax Tailor"},
            {"key": "artist-785", "name": "Wax Doctor"},
            {"key": "artist-46488", "name": "Wax Poetic"},
            {"key": "artist-242216", "name": "Lord Wax"},
            {"key": "artist-4009", "name": "Microbots"},
            {"key": "artist-25723", "name": "Freshmess On Wax"},
            {"key": "artist-759", "name": "Nightmares On Wax"},
            {"key": "label-10693", "name": "Wax Magazine"},
            {"key": "label-173661", "name": "Wax Treatment"},
            {"key": "label-953", "name": "Wax Trax! Records"},
            {"key": "label-294161", "name": "Wax Trax! Records, Inc."},
            {"key": "label-111", "name": "Mo Wax"},
            {"key": "label-290481", "name": "Mo Wax Recordings"},
        ]
        assert len(results["results"]) == 15
        assert list(results["results"]) == expected

    @pytest.mark.asyncio
    async def test_text_search_lookup_2(
        self,
        runtime_config: Configuration,
        offline_database_setup: AsyncGenerator[None, None],
        runtime_database_setup: AsyncGenerator[None, None], is_load_offline_data_required: bool,
        is_load_runtime_data_required: bool
    ) -> None:
        """Test text search functionality for 'Joker' query."""
        text_search_path = runtime_config.DATA_DIR / TEXT_SEARCH_DATA / TEXT_SEARCH_FILENAME
        assert RuntimeDatabaseManager.runtime_database_helper is not None

        RuntimeDatabaseManager.runtime_database_helper.text_search_index = (
            TextSearchIndex.load_text_search_index_from_file(text_search_path)
        )
        async with runtime_transaction():
            runtime_entity_repository = RuntimeEntityRepository()
            token_repository = RuntimeTokenRepository()

            results = await RuntimeEntitySearch.search_entities(
                runtime_entity_repository, token_repository, "Joker"
            )

        # THEN
        expected = [
            {"key": "artist-622822", "name": "Joker (5)"},
            {"key": "artist-8526", "name": "Joker, The (3)"},
            {"key": "artist-129882", "name": "Joker, The (4)"},
        ]
        assert len(results["results"]) == 3
        assert list(results["results"]) == expected
