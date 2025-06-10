import datetime
import unittest
from unittest.mock import patch

from musigree import utils
from musigree.constants import (
    DISCOGS_ARTISTS_TYPE,
    DISCOGS_RELEASES_TYPE,
    DISCOGS_LABELS_TYPE,
    DISCOGS_MASTERS_TYPE,
)
from musigree.library.fields.entity_type import EntityType


class TestUtils(unittest.TestCase):
    def test_split_list_1(self):
        input_seq = [1, 2, 3, 4, 10, 11, 12, 13, 20, 21, 22, 23]
        num_chunks = 3
        result = list(utils.split_list(num_chunks, input_seq))
        expected = [[1, 2, 3, 4], [10, 11, 12, 13], [20, 21, 22, 23]]
        self.assertEqual(expected, result)

    def test_split_list_2(self):
        input_seq = [1, 2, 3, 4, 10, 11, 12, 13, 20, 21, 22, 23, 24]
        num_chunks = 3
        result = list(utils.split_list(num_chunks, input_seq))
        expected = [[1, 2, 3, 4, 10], [11, 12, 13, 20, 21], [22, 23, 24]]
        self.assertEqual(expected, result)
        self.assertEqual(num_chunks, len(result))

    def test_split_list_3(self):
        input_seq = [
            1,
        ]
        num_chunks = 3
        result = list(utils.split_list(num_chunks, input_seq))
        expected = [
            [
                1,
            ],
        ]
        self.assertEqual(expected, result)
        self.assertEqual(1, len(result))

    def test_split_list_4(self):
        with self.assertRaises(ValueError):
            input_seq = []
            num_chunks = 3
            list(utils.split_list(num_chunks, input_seq))

    def test_split_list_5(self):
        input_seq = [1, 2, 3, 4, 10, 11, 12, 13, 20, 21, 22, 23]
        num_chunks = 0
        result = list(utils.split_list(num_chunks, input_seq))
        expected = [
            [1, 2, 3, 4, 10, 11, 12, 13, 20, 21, 22, 23],
        ]
        self.assertEqual(expected, result)
        self.assertEqual(1, len(result))

    def test_strip_input(self):
        input_str = """
            aaa
            bbb
            ccc
        """

        actual = utils.strip_input(input_str)
        expected = "aaa\nbbb\nccc\n"
        self.assertEqual(expected, actual)

    def test_normalize_dict_01(self):
        input_dict = {
            "entity_one_id": 430141,
            "entity_one_type": "EntityType.ARTIST",
            "entity_two_id": 307,
            "entity_two_type": "EntityType.ARTIST",
            "releases": None,
            "role": "Member Of",
        }

        actual = utils.normalize_dict(input_dict)
        expected = """
            {
                "entity_one_id": 430141,
                "entity_one_type": "EntityType.ARTIST",
                "entity_two_id": 307,
                "entity_two_type": "EntityType.ARTIST",
                "releases": null,
                "role": "Member Of"
            }
        """
        self.assertEqual(utils.strip_input(expected), actual)

    def test_normalize_dict_02(self):
        input_dict = {
            "entities": {},
            "entity_id": 264170,
            "entity_type": "EntityType.LABEL",
            "metadata": {
                "profile": "American mastering studio located in New Windsor, NY. \r\n\r\n"
                + "Formally located at 2 Engle Street, Tenafly, New Jersey, "
                + "operations were moved to New Windsor in 2005. "
                + "Operated by Chief Engineer [a=Alan Douches].\n",
                "urls": ["http://www.westwestsidemusic.com/"],
            },
            "name": "West West Side Music",
        }

        actual = utils.normalize_dict(input_dict)
        # print(f"actual: {actual}")
        expected = {
            "entities": {},
            "entity_id": 264170,
            "entity_type": "EntityType.LABEL",
            "metadata": {
                "profile": "American mastering studio located in New Windsor, NY. \r\n\r\n"
                + "Formally located at 2 Engle Street, Tenafly, New Jersey, "
                + "operations were moved to New Windsor in 2005. "
                + "Operated by Chief Engineer [a=Alan Douches].\n",
                "urls": ["http://www.westwestsidemusic.com/"],
            },
            "name": "West West Side Music",
        }

        self.assertEqual(utils.normalize_dict(expected), actual)

    def test_normalize_nested_dict(self):
        input_dict = {
            "artist-430141-member-of-artist-307": {
                "entity_one_id": 430141,
                "entity_one_type": EntityType.ARTIST,
                "entity_two_id": 307,
                "entity_two_type": EntityType.ARTIST,
                "role": "Member Of",
            },
            "artist-430141-member-of-artist-3603": {
                "entity_one_id": 430141,
                "entity_one_type": "EntityType.ARTIST",
                "entity_two_id": 3603,
                "entity_two_type": "EntityType.ARTIST",
                "role": "Member Of",
            },
        }

        actual = utils.normalize_dict(input_dict)
        expected = """
            {
                "artist-430141-member-of-artist-307": {
                    "entity_one_id": 430141,
                    "entity_one_type": "EntityType.ARTIST",
                    "entity_two_id": 307,
                    "entity_two_type": "EntityType.ARTIST",
                    "role": "Member Of"
                },
                "artist-430141-member-of-artist-3603": {
                    "entity_one_id": 430141,
                    "entity_one_type": "EntityType.ARTIST",
                    "entity_two_id": 3603,
                    "entity_two_type": "EntityType.ARTIST",
                    "role": "Member Of"
                }
            }
        """
        self.assertEqual(utils.strip_input(expected), actual)

    def test_normalize_dict_list(self):
        input_list = [
            {
                "entity_one_id": 430141,
                "entity_one_type": "EntityType.ARTIST",
                "entity_two_id": 307,
                "entity_two_type": "EntityType.ARTIST",
                "releases": None,
                "role": "Member Of",
            },
            {
                "entity_one_id": 430141,
                "entity_one_type": "EntityType.ARTIST",
                "entity_two_id": 3603,
                "entity_two_type": "EntityType.ARTIST",
                "releases": None,
                "role": "Member Of",
            },
        ]
        actual = utils.normalize_dict_list(input_list)
        expected = """
        [
            {
                "entity_one_id": 430141,
                "entity_one_type": "EntityType.ARTIST",
                "entity_two_id": 307,
                "entity_two_type": "EntityType.ARTIST",
                "releases": null,
                "role": "Member Of"
            },
            {
                "entity_one_id": 430141,
                "entity_one_type": "EntityType.ARTIST",
                "entity_two_id": 3603,
                "entity_two_type": "EntityType.ARTIST",
                "releases": null,
                "role": "Member Of"
            }
        ]
        """
        self.assertEqual(utils.strip_input(expected), actual)

    def test_normalize_str_list(self):
        input_list = [
            "{\n    aaa\n    bbb\n    ccc\n}",
            "{\n    aaa\n    bbb\n    ccc\n}",
            "{\n    aaa\n    bbb\n    ccc\n}",
        ]

        actual = utils.normalize_str_list(input_list)
        expected = """
        [
            {
                aaa
                bbb
                ccc
            },
            {
                aaa
                bbb
                ccc
            },
            {
                aaa
                bbb
                ccc
            }
        ]
        """
        self.assertEqual(utils.strip_input(expected), actual)

    def test_strip_trailing_newline(self):
        input_str = "{\n    aaa\n    bbb\n    ccc\n}\n"

        actual = utils.strip_trailing_newline(input_str)
        expected = "{\n    aaa\n    bbb\n    ccc\n}"
        self.assertEqual(expected, actual)

    def test_get_discogs_url(self):
        input_date = datetime.datetime(2023, 8, 1)
        result = utils.get_discogs_url(input_date, "xyz")
        expected = "https://discogs-data-dumps.s3-us-west-2.amazonaws.com/data/2023/discogs_20230801_xyz.xml.gz"
        self.assertEqual(expected, result)

    def test_get_discogs_artists_url(self):
        input_date = datetime.datetime(2023, 8, 1)
        result = utils.get_discogs_url(input_date, DISCOGS_ARTISTS_TYPE)
        expected = "https://discogs-data-dumps.s3-us-west-2.amazonaws.com/data/2023/discogs_20230801_artists.xml.gz"
        self.assertEqual(expected, result)

    def test_get_discogs_releases_url(self):
        input_date = datetime.datetime(2023, 8, 1)
        result = utils.get_discogs_url(input_date, DISCOGS_RELEASES_TYPE)
        expected = "https://discogs-data-dumps.s3-us-west-2.amazonaws.com/data/2023/discogs_20230801_releases.xml.gz"
        self.assertEqual(expected, result)

    def test_get_discogs_labels_url(self):
        input_date = datetime.datetime(2023, 8, 1)
        result = utils.get_discogs_url(input_date, DISCOGS_LABELS_TYPE)
        expected = "https://discogs-data-dumps.s3-us-west-2.amazonaws.com/data/2023/discogs_20230801_labels.xml.gz"
        self.assertEqual(expected, result)

    def test_get_discogs_masters_url(self):
        input_date = datetime.datetime(2023, 8, 1)
        result = utils.get_discogs_url(input_date, DISCOGS_MASTERS_TYPE)
        expected = "https://discogs-data-dumps.s3-us-west-2.amazonaws.com/data/2023/discogs_20230801_masters.xml.gz"
        self.assertEqual(expected, result)

    def test_get_discogs_dump_dates(self):
        start_date = datetime.datetime(2023, 8, 1)
        end_date = datetime.datetime(2024, 6, 13)
        result = utils.get_discogs_dump_dates(start_date, end_date)
        expected = [
            datetime.date(2023, 8, 1),
            datetime.date(2023, 9, 1),
            datetime.date(2023, 10, 1),
            datetime.date(2023, 11, 1),
            datetime.date(2023, 12, 1),
            datetime.date(2024, 1, 1),
            datetime.date(2024, 2, 1),
            datetime.date(2024, 3, 1),
            datetime.date(2024, 4, 1),
            datetime.date(2024, 5, 1),
            datetime.date(2024, 6, 1),
        ]
        self.assertEqual(expected, result)

    def test_batched(self):
        # Test normal batching
        result = list(utils.batched([1, 2, 3, 4, 5, 6, 7], 3))
        expected = [[1, 2, 3], [4, 5, 6], [7]]
        self.assertEqual(expected, result)

    def test_batched_exact_division(self):
        # Test when sequence divides evenly
        result = list(utils.batched([1, 2, 3, 4, 5, 6], 2))
        expected = [[1, 2], [3, 4], [5, 6]]
        self.assertEqual(expected, result)

    def test_batched_invalid_n(self):
        # Test with invalid n value
        with self.assertRaises(ValueError):
            list(utils.batched([1, 2, 3], 0))

    def test_batched_empty_sequence(self):
        # Test with empty sequence
        result = list(utils.batched([], 3))
        expected = []
        self.assertEqual(expected, result)

    def test_normalize_with_indent_string(self):
        input_text = "line1\nline2\nline3"
        result = utils.normalize(input_text, indent="  ")
        expected = "  line1\n  line2\n  line3\n"
        self.assertEqual(expected, result)

    def test_normalize_with_indent_int(self):
        input_text = "line1\nline2"
        result = utils.normalize(input_text, indent=4)
        expected = "    line1\n    line2\n"
        self.assertEqual(expected, result)

    def test_normalize_with_tabs(self):
        input_text = "\tline1\n\tline2"
        result = utils.normalize(input_text)
        expected = "line1\nline2\n"
        self.assertEqual(expected, result)

    def test_normalize_with_empty_lines(self):
        input_text = "\n\nline1\nline2\n\n"
        result = utils.normalize(input_text)
        expected = "line1\nline2\n"
        self.assertEqual(expected, result)

    def test_parse_request_args_with_year_range(self):
        args = {"year": "2020-2023"}
        roles, year = utils.parse_request_args(args)
        self.assertEqual((2020, 2023), year)

    def test_parse_request_args_with_single_year(self):
        args = {"year": "2020"}
        roles, year = utils.parse_request_args(args)
        self.assertEqual(2020, year)

    def test_parse_request_args_with_invalid_year(self):
        args = {"year": "invalid"}
        roles, year = utils.parse_request_args(args)
        self.assertIsNone(year)

    def test_parse_request_args_with_reversed_year_range(self):
        args = {"year": "2023-2020"}
        roles, year = utils.parse_request_args(args)
        self.assertEqual((2020, 2023), year)

    def test_skip_filter_basic(self):
        filter_obj = utils.SkipFilter(keys=["skip_me"])
        data = {"keep": "value", "skip_me": "ignore"}
        result = filter_obj.filter(data)
        expected = {"keep": "value"}
        self.assertEqual(expected, result)

    def test_skip_filter_with_types(self):
        filter_obj = utils.SkipFilter(types=(int,))
        data = {"keep": "value", "skip": 123}
        result = filter_obj.filter(data)
        expected = {"keep": "value"}
        self.assertEqual(expected, result)

    def test_skip_filter_allow_empty(self):
        filter_obj = utils.SkipFilter(keys=["all"], allow_empty=True)
        data = {"all": "skip"}
        result = filter_obj.filter(data)
        expected = {}
        self.assertEqual(expected, result)

    def test_skip_filter_non_mapping(self):
        filter_obj = utils.SkipFilter()
        data = "not a mapping"
        result = filter_obj.filter(data)
        self.assertEqual("not a mapping", result)

    def test_row2dict(self):
        # Mock a database row-like object with __table__ attribute
        class MockColumn:
            def __init__(self, name):
                self.name = name
        
        class MockTable:
            def __init__(self):
                self.columns = [MockColumn("id"), MockColumn("name")]
        
        class MockRow:
            def __init__(self):
                self.id = 1
                self.name = "test"
                self.__table__ = MockTable()
            
            @staticmethod
            def keys():
                return ["id", "name"]
            
            def __getitem__(self, key):
                return getattr(self, key)

        row = MockRow()
        result = utils.row2dict(row)
        expected = {"id": 1, "name": "test"}
        self.assertEqual(expected, result)

    def test_is_latin_true(self):
        result = utils.is_latin("Hello World")
        self.assertFalse(result)  # Space character is not in LATIN category

    def test_is_latin_false(self):
        result = utils.is_latin("Здравствуй мир")  # Russian text
        self.assertFalse(result)

    def test_is_latin_mixed(self):
        result = utils.is_latin("Hello мир")  # Mixed text
        self.assertFalse(result)

    def test_to_ascii_basic(self):
        result = utils.to_ascii("café")
        self.assertEqual("cafe", result)

    def test_to_ascii_with_accents(self):
        result = utils.to_ascii("naïve résumé")
        self.assertEqual("naïve résumé", result)  # Function preserves non-ASCII when is_latin is False

    def test_to_ascii_non_latin(self):
        result = utils.to_ascii("Здравствуй")
        self.assertEqual("Здравствуй", result)  # Function doesn't transliterate non-latin

    @patch('time.sleep')
    def test_sleep_with_backoff(self, mock_sleep):
        utils.sleep_with_backoff(2)
        mock_sleep.assert_called_once()
        # Check that it sleeps for a reasonable duration
        call_args = mock_sleep.call_args[0][0]
        self.assertGreater(call_args, 0)
        self.assertLessEqual(call_args, 20)  # 2 * 10 maximum

    # @patch('requests.get')
    # @patch('builtins.open', new_callable=mock_open)
    # def test_download_file(self, mock_file, mock_get):
    #     # Mock successful response
    #     mock_response = MagicMock()
    #     mock_response.iter_content.return_value = [b'test data']
    #     mock_response.__enter__ = MagicMock(return_value=mock_response)
    #     mock_response.__exit__ = MagicMock(return_value=None)
    #     mock_get.return_value = mock_response
    #
    #     # Mock file object
    #     mock_file_obj = MagicMock()
    #     mock_file.return_value.__enter__.return_value = mock_file_obj
    #
    #     utils.download_file("http://example.com/file", mock_file_obj)
    #
    #     mock_get.assert_called_once_with("http://example.com/file", stream=True)
    #     mock_file_obj.flush.assert_called_once()
    #     mock_file_obj.close.assert_called_once()

    def test_get_random_string(self):
        result = utils.get_random_string(10)
        self.assertEqual(10, len(result))
        # Check it only contains valid characters
        valid_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
        self.assertTrue(set(result).issubset(valid_chars))

    def test_get_random_string_different_calls(self):
        result1 = utils.get_random_string(10)
        result2 = utils.get_random_string(10)
        # Very unlikely to be the same
        self.assertNotEqual(result1, result2)

    def test_calculate_size_dict(self):
        test_dict = {"key1": "value1", "key2": "value2"}
        result = utils.calculate_size(test_dict)
        self.assertGreater(result, 0)

    def test_calculate_size_list(self):
        test_list = [1, 2, 3, 4, 5]
        result = utils.calculate_size(test_list)
        self.assertGreater(result, 0)

    def test_calculate_size_string(self):
        test_string = "Hello, World!"
        result = utils.calculate_size(test_string)
        self.assertGreater(result, 0)

    @patch('time.time')
    def test_timeit_decorator(self, mock_time):
        # Mock time to return predictable values
        mock_time.side_effect = [1.0, 2.0]  # 1 second difference
        
        @utils.timeit
        def test_function():
            return "result"
        
        with patch('musigree.utils.log') as mock_log:
            result = test_function()
            self.assertEqual("result", result)
            mock_log.debug.assert_called()
