import datetime
import unittest

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
