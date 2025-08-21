import datetime
from typing import Any, Dict, List
from unittest.mock import patch, MagicMock

import pytest
from sqlalchemy.orm import DeclarativeBase

from musigree import utils
from musigree.constants import (
    DISCOGS_ARTISTS_TYPE,
    DISCOGS_RELEASES_TYPE,
    DISCOGS_LABELS_TYPE,
    DISCOGS_MASTERS_TYPE,
)
from musigree.library.fields.entity_type import EntityType


def test_split_list_1() -> None:
    """Test split_list with evenly divisible input."""
    input_seq = [1, 2, 3, 4, 10, 11, 12, 13, 20, 21, 22, 23]
    num_chunks = 3
    result = list(utils.split_list(num_chunks, input_seq))
    expected = [[1, 2, 3, 4], [10, 11, 12, 13], [20, 21, 22, 23]]
    assert result == expected


def test_split_list_2() -> None:
    """Test split_list with remainder when dividing."""
    input_seq = [1, 2, 3, 4, 10, 11, 12, 13, 20, 21, 22, 23, 24]
    num_chunks = 3
    result = list(utils.split_list(num_chunks, input_seq))
    expected = [[1, 2, 3, 4, 10], [11, 12, 13, 20, 21], [22, 23, 24]]
    assert result == expected
    assert len(result) == num_chunks


def test_split_list_3() -> None:
    """Test split_list with single element."""
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
    assert result == expected
    assert len(result) == 1


def test_split_list_4() -> None:
    """Test split_list raises ValueError for empty sequence."""
    with pytest.raises(ValueError):
        input_seq: List[int] = []
        num_chunks = 3
        list(utils.split_list(num_chunks, input_seq))


def test_split_list_5() -> None:
    """Test split_list with zero chunks returns single chunk."""
    input_seq = [1, 2, 3, 4, 10, 11, 12, 13, 20, 21, 22, 23]
    num_chunks = 0
    result = list(utils.split_list(num_chunks, input_seq))
    expected = [
        [1, 2, 3, 4, 10, 11, 12, 13, 20, 21, 22, 23],
    ]
    assert result == expected
    assert len(result) == 1


def test_strip_input() -> None:
    """Test strip_input removes leading and trailing whitespace while preserving internal structure."""
    input_str = """
        aaa
        bbb
        ccc
    """

    actual = utils.strip_input(input_str)
    expected = "aaa\nbbb\nccc\n"
    assert actual == expected


def test_normalize_dict_01() -> None:
    """Test normalize_dict with simple dictionary containing EntityType strings."""
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
    assert actual == utils.strip_input(expected)


def test_normalize_dict_02() -> None:
    """Test normalize_dict with complex nested dictionary structure."""
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

    assert actual == utils.normalize_dict(expected)


def test_normalize_nested_dict() -> None:
    """Test normalize_dict with nested dictionary containing mixed EntityType formats."""
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
    assert actual == utils.strip_input(expected)


def test_normalize_dict_list() -> None:
    """Test normalize_dict_list with list of dictionaries."""
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
    assert actual == utils.strip_input(expected)


def test_normalize_str_list() -> None:
    """Test normalize_str_list with list of formatted strings."""
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
    assert actual == utils.strip_input(expected)


def test_strip_trailing_newline() -> None:
    """Test strip_trailing_newline removes only trailing newline."""
    input_str = "{\n    aaa\n    bbb\n    ccc\n}\n"

    actual = utils.strip_trailing_newline(input_str)
    expected = "{\n    aaa\n    bbb\n    ccc\n}"
    assert actual == expected


def test_get_discogs_url() -> None:
    """Test get_discogs_url generates correct URL format."""
    input_date = datetime.datetime(2023, 8, 1)
    result = utils.get_discogs_url(input_date, "xyz")
    expected = "https://discogs-data-dumps.s3-us-west-2.amazonaws.com/data/2023/discogs_20230801_xyz.xml.gz"
    assert result == expected


def test_get_discogs_artists_url() -> None:
    """Test get_discogs_url with artists type constant."""
    input_date = datetime.datetime(2023, 8, 1)
    result = utils.get_discogs_url(input_date, DISCOGS_ARTISTS_TYPE)
    expected = "https://discogs-data-dumps.s3-us-west-2.amazonaws.com/data/2023/discogs_20230801_artists.xml.gz"
    assert result == expected


def test_get_discogs_releases_url() -> None:
    """Test get_discogs_url with releases type constant."""
    input_date = datetime.datetime(2023, 8, 1)
    result = utils.get_discogs_url(input_date, DISCOGS_RELEASES_TYPE)
    expected = "https://discogs-data-dumps.s3-us-west-2.amazonaws.com/data/2023/discogs_20230801_releases.xml.gz"
    assert result == expected


def test_get_discogs_labels_url() -> None:
    """Test get_discogs_url with labels type constant."""
    input_date = datetime.datetime(2023, 8, 1)
    result = utils.get_discogs_url(input_date, DISCOGS_LABELS_TYPE)
    expected = "https://discogs-data-dumps.s3-us-west-2.amazonaws.com/data/2023/discogs_20230801_labels.xml.gz"
    assert result == expected


def test_get_discogs_masters_url() -> None:
    """Test get_discogs_url with masters type constant."""
    input_date = datetime.datetime(2023, 8, 1)
    result = utils.get_discogs_url(input_date, DISCOGS_MASTERS_TYPE)
    expected = "https://discogs-data-dumps.s3-us-west-2.amazonaws.com/data/2023/discogs_20230801_masters.xml.gz"
    assert result == expected


def test_get_discogs_dump_dates() -> None:
    """Test get_discogs_dump_dates returns correct monthly date sequence."""
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
    assert result == expected


def test_batched() -> None:
    """Test batched function with normal batching scenario."""
    result = list(utils.batched([1, 2, 3, 4, 5, 6, 7], 3))
    expected = [[1, 2, 3], [4, 5, 6], [7]]
    assert result == expected


def test_batched_exact_division() -> None:
    """Test batched when sequence divides evenly."""
    result = list(utils.batched([1, 2, 3, 4, 5, 6], 2))
    expected = [[1, 2], [3, 4], [5, 6]]
    assert result == expected


def test_batched_invalid_n() -> None:
    """Test batched raises ValueError for invalid n value."""
    with pytest.raises(ValueError):
        list(utils.batched([1, 2, 3], 0))


def test_batched_empty_sequence() -> None:
    """Test batched with empty sequence."""
    result: List[List[Any]] = list(utils.batched([], 3))
    expected: List[List[Any]] = []
    assert result == expected


def test_normalize_with_indent_string() -> None:
    """Test normalize function with string indent parameter."""
    input_text = "line1\nline2\nline3"
    result = utils.normalize(input_text, indent="  ")
    expected = "  line1\n  line2\n  line3\n"
    assert result == expected


def test_normalize_with_indent_int() -> None:
    """Test normalize function with integer indent parameter."""
    input_text = "line1\nline2"
    result = utils.normalize(input_text, indent=4)
    expected = "    line1\n    line2\n"
    assert result == expected


def test_normalize_with_tabs() -> None:
    """Test normalize function removes tabs from input."""
    input_text = "\tline1\n\tline2"
    result = utils.normalize(input_text)
    expected = "line1\nline2\n"
    assert result == expected


def test_normalize_with_empty_lines() -> None:
    """Test normalize function removes empty lines."""
    input_text = "\n\nline1\nline2\n\n"
    result = utils.normalize(input_text)
    expected = "line1\nline2\n"
    assert result == expected


def test_parse_request_args_with_year_range() -> None:
    """Test parse_request_args with year range format."""
    args = {"year": "2020-2023"}
    roles, year = utils.parse_request_args(args)
    assert year == (2020, 2023)


def test_parse_request_args_with_single_year() -> None:
    """Test parse_request_args with single year format."""
    args = {"year": "2020"}
    roles, year = utils.parse_request_args(args)
    assert year == 2020


def test_parse_request_args_with_invalid_year() -> None:
    """Test parse_request_args with invalid year format."""
    args = {"year": "invalid"}
    roles, year = utils.parse_request_args(args)
    assert year is None


def test_parse_request_args_with_reversed_year_range() -> None:
    """Test parse_request_args with reversed year range."""
    args = {"year": "2023-2020"}
    roles, year = utils.parse_request_args(args)
    assert year == (2020, 2023)


def test_skip_filter_basic() -> None:
    """Test SkipFilter with basic key filtering."""
    filter_obj = utils.SkipFilter(keys=["skip_me"])
    data = {"keep": "value", "skip_me": "ignore"}
    result = filter_obj.filter(data)
    expected = {"keep": "value"}
    assert result == expected


def test_skip_filter_with_types() -> None:
    """Test SkipFilter with type filtering."""
    filter_obj = utils.SkipFilter(types=(int,))
    data = {"keep": "value", "skip": 123}
    result = filter_obj.filter(data)
    expected = {"keep": "value"}
    assert result == expected


def test_skip_filter_allow_empty() -> None:
    """Test SkipFilter with allow_empty option."""
    filter_obj = utils.SkipFilter(keys=["all"], allow_empty=True)
    data = {"all": "skip"}
    result = filter_obj.filter(data)
    expected: Dict[str, Any] = {}
    assert result == expected


def test_skip_filter_non_mapping() -> None:
    """Test SkipFilter with non-mapping input."""
    filter_obj = utils.SkipFilter()
    data = "not a mapping"
    result = filter_obj.filter(data)
    assert result == "not a mapping"


def test_table2dict() -> None:
    """Test table2dict converts database table object to dictionary."""

    # Mock a database row-like object with __table__ attribute
    class MockColumn:
        def __init__(self, name: str) -> None:
            self.name = name

    class MockTableDef:
        def __init__(self) -> None:
            self.columns = [MockColumn("id"), MockColumn("name"), MockColumn("value")]

    class MockTable(DeclarativeBase):
        def __init__(self, **kw: Any) -> None:
            super().__init__(**kw)
            self.id: int = 1
            self.name: str = "test"
            self.value: float = 3.14
            # Override the __table__ attribute after initialization
            object.__setattr__(self, "__table__", MockTableDef())

    table = MockTable()
    result = utils.table2dict(table)
    expected: dict[str, Any] = {"id": 1, "name": "test", "value": 3.14}
    assert result == expected


def test_is_latin_true() -> None:
    """Test is_latin function with string containing non-latin characters."""
    result = utils.is_latin("Hello World")
    assert result is False  # Space character is not in LATIN category


def test_is_latin_false() -> None:
    """Test is_latin function with non-latin text."""
    result = utils.is_latin("Здравствуй мир")  # Russian text
    assert result is False


def test_is_latin_mixed() -> None:
    """Test is_latin function with mixed latin and non-latin text."""
    result = utils.is_latin("Hello мир")  # Mixed text
    assert result is False


def test_to_ascii_basic() -> None:
    """Test to_ascii function with accented characters."""
    result = utils.to_ascii("café")
    assert result == "cafe"


def test_to_ascii_with_accents() -> None:
    """Test to_ascii function preserves non-ASCII when is_latin is False."""
    result = utils.to_ascii("naïve résumé")
    assert (
        result == "naïve résumé"
    )  # Function preserves non-ASCII when is_latin is False


def test_to_ascii_non_latin() -> None:
    """Test to_ascii function doesn't transliterate non-latin characters."""
    result = utils.to_ascii("Здравствуй")
    assert result == "Здравствуй"  # Function doesn't transliterate non-latin


@patch("time.sleep")
def test_sleep_with_backoff(mock_sleep: MagicMock) -> None:
    """Test sleep_with_backoff function calls sleep with appropriate duration."""
    utils.sleep_with_backoff(2)
    mock_sleep.assert_called_once()
    # Check that it sleeps for a reasonable duration
    call_args = mock_sleep.call_args[0][0]
    assert call_args > 0
    assert call_args <= 20  # 2 * 10 maximum


def test_get_random_string() -> None:
    """Test get_random_string returns string of correct length with valid characters."""
    result = utils.get_random_string(10)
    assert len(result) == 10
    # Check it only contains valid characters
    valid_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
    assert set(result).issubset(valid_chars)


def test_get_random_string_different_calls() -> None:
    """Test get_random_string returns different values on subsequent calls."""
    result1 = utils.get_random_string(10)
    result2 = utils.get_random_string(10)
    # Very unlikely to be the same
    assert result1 != result2


def test_calculate_size_dict() -> None:
    """Test calculate_size function with dictionary input."""
    test_dict = {"key1": "value1", "key2": "value2"}
    result = utils.calculate_size(test_dict)
    assert result > 0


def test_calculate_size_list() -> None:
    """Test calculate_size function with list input."""
    test_list = [1, 2, 3, 4, 5]
    result = utils.calculate_size(test_list)
    assert result > 0


def test_calculate_size_string() -> None:
    """Test calculate_size function with string input."""
    test_string = "Hello, World!"
    result = utils.calculate_size(test_string)
    assert result > 0


# Additional tests for better coverage
def test_batched_single_element() -> None:
    """Test batched with single element per batch."""
    result = list(utils.batched([1, 2, 3], 1))
    expected = [[1], [2], [3]]
    assert result == expected


def test_parse_request_args_no_year() -> None:
    """Test parse_request_args with no year argument."""
    args: Dict[str, str] = {}
    roles, year = utils.parse_request_args(args)
    assert year is None


def test_get_random_string_zero_length() -> None:
    """Test get_random_string with zero length."""
    result = utils.get_random_string(0)
    assert result == ""


def test_normalize_empty_string() -> None:
    """Test normalize function with empty string."""
    result = utils.normalize("")
    expected = ""
    assert result == expected
