from musigree.constants import TEXT_SEARCH_DATA, TEXT_SEARCH_FILENAME
from musigree.library.full_text_search.text_search_index import TextSearchIndex
from musigree.runtime.data_access_layer.runtime_entity_search import (
    RuntimeEntitySearch,
)
from musigree.runtime.runtime_database_manager import RuntimeDatabaseManager
from tests.integration.runtime.database.runtime_database_test_case import (
    RuntimeDatabaseTestCase,
)


class TestRuntimeEntitySearch(RuntimeDatabaseTestCase):

    def test_text_search_lookup_1(self):
        text_search_path = (
            RuntimeDatabaseTestCase.runtime_config.DATA_DIR
            / TEXT_SEARCH_DATA
            / TEXT_SEARCH_FILENAME
        )
        RuntimeDatabaseManager.runtime_database_helper.text_search_index = (
            TextSearchIndex.load_text_search_index_from_file(text_search_path)
        )
        results = RuntimeEntitySearch.search_entities("Wax")

        # THEN
        expected = [
            {"key": "artist-333377", "name": "Wax (10)"},
            {"key": "artist-1163252", "name": "Wax (19)"},
            {"key": "artist-288583", "name": "Wax Tailor"},
            {"key": "artist-785", "name": "Wax Doctor"},
            {"key": "artist-46488", "name": "Wax Poetic"},
            {"key": "artist-242216", "name": "Lord Wax"},
            {"key": "artist-25723", "name": "Freshmess On Wax"},
            {"key": "artist-759", "name": "Nightmares On Wax"},
            {"key": "label-10693", "name": "Wax Magazine"},
            {"key": "label-173661", "name": "Wax Treatment"},
            {"key": "label-953", "name": "Wax Trax! Records"},
            {"key": "label-294161", "name": "Wax Trax! Records, Inc."},
            {"key": "label-111", "name": "Mo Wax"},
            {"key": "label-290481", "name": "Mo Wax Recordings"},
        ]
        self.assertEqual(14, len(results["results"]))
        self.assertEqual(expected, list(results["results"]))

    def test_text_search_lookup_2(self):
        text_search_path = (
            RuntimeDatabaseTestCase.runtime_config.DATA_DIR
            / TEXT_SEARCH_DATA
            / TEXT_SEARCH_FILENAME
        )
        RuntimeDatabaseManager.runtime_database_helper.text_search_index = (
            TextSearchIndex.load_text_search_index_from_file(text_search_path)
        )
        results = RuntimeEntitySearch.search_entities("Joker")

        # THEN
        expected = [
            {"key": "artist-622822", "name": "Joker (5)"},
            {"key": "artist-8526", "name": "Joker, The (3)"},
            {"key": "artist-129882", "name": "Joker, The (4)"},
        ]
        self.assertEqual(3, len(results["results"]))
        self.assertEqual(expected, list(results["results"]))
