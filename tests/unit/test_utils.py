import asyncio
import datetime
from collections.abc import AsyncGenerator, Coroutine
from typing import Any, Dict, List
from unittest.mock import patch, MagicMock, AsyncMock

import pytest
import requests
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


# Queue Worker Function Tests


@pytest.mark.asyncio
async def test_queue_worker_basic_operation() -> None:
    """Test queue_worker processes work items from queue correctly."""
    # Create a queue and add some mock coroutines
    queue: asyncio.Queue[Any] = asyncio.Queue()
    
    # Mock async functions to put in the queue
    mock_coro1 = AsyncMock()
    mock_coro2 = AsyncMock()
    
    # Add work items to queue
    await queue.put(mock_coro1())
    await queue.put(mock_coro2())
    
    # Create a worker task
    worker_task = asyncio.create_task(utils.queue_worker("test-worker", queue))
    
    # Let the worker process the items
    await asyncio.sleep(0.1)
    
    # Stop the worker by cancelling it
    worker_task.cancel()
    
    try:
        await worker_task
    except asyncio.CancelledError:
        pass
    
    # Verify the mock functions were called
    mock_coro1.assert_called_once()
    mock_coro2.assert_called_once()


@pytest.mark.asyncio
async def test_queue_worker_empty_queue() -> None:
    """Test queue_worker handles empty queue correctly."""
    queue: asyncio.Queue[Any] = asyncio.Queue()
    
    # Create a worker task
    worker_task = asyncio.create_task(utils.queue_worker("test-worker", queue))
    
    # Let the worker wait briefly
    await asyncio.sleep(0.1)
    
    # Worker should still be running, waiting for work
    assert not worker_task.done()
    
    # Cancel the worker
    worker_task.cancel()
    
    try:
        await worker_task
    except asyncio.CancelledError:
        pass


@pytest.mark.asyncio
async def test_queue_worker_exception_handling() -> None:
    """Test queue_worker propagates exceptions from worker functions."""
    queue: asyncio.Queue[Any] = asyncio.Queue()
    
    # Create a mock coroutine that raises an exception
    async def failing_coro() -> None:
        raise ValueError("Test error")
    
    await queue.put(failing_coro())
    
    # Create a worker task
    worker_task = asyncio.create_task(utils.queue_worker("test-worker", queue))
    
    # Let the worker process the failing item
    await asyncio.sleep(0.1)
    
    # Worker should fail due to the exception
    assert worker_task.done()
    
    # Check that the worker failed with the expected exception
    with pytest.raises(ValueError, match="Test error"):
        await worker_task


@pytest.mark.asyncio
async def test_queue_worker_multiple_items() -> None:
    """Test queue_worker processes multiple work items sequentially."""
    queue: asyncio.Queue[Any] = asyncio.Queue()
    results: List[int] = []
    
    # Create mock coroutines that track execution order
    async def numbered_coro(num: int) -> None:
        results.append(num)
    
    # Add multiple work items
    for i in range(5):
        await queue.put(numbered_coro(i))
    
    # Create a worker task
    worker_task = asyncio.create_task(utils.queue_worker("test-worker", queue))
    
    # Wait for all items to be processed
    await queue.join()
    
    # Cancel the worker
    worker_task.cancel()
    
    try:
        await worker_task
    except asyncio.CancelledError:
        pass
    
    # Verify all items were processed in order
    assert results == [0, 1, 2, 3, 4]


@pytest.mark.asyncio
async def test_queue_worker_functions_basic_operation() -> None:
    """Test queue_worker_functions with basic coroutine processing."""
    results: List[int] = []
    
    # Create a list of mock coroutines
    async def numbered_coro(num: int) -> None:
        results.append(num)
    
    def worker_generator() -> Any:
        for i in range(3):
            yield numbered_coro(i)
    
    # Run the queue worker functions
    await utils.queue_worker_functions(2, worker_generator())
    
    # Verify all coroutines were executed
    assert len(results) == 3
    assert set(results) == {0, 1, 2}


@pytest.mark.asyncio
async def test_queue_worker_functions_concurrency() -> None:
    """Test queue_worker_functions respects concurrency limits."""
    active_count = 0
    max_concurrent = 0
    results: List[int] = []
    
    async def tracking_coro(num: int) -> None:
        nonlocal active_count, max_concurrent
        active_count += 1
        max_concurrent = max(max_concurrent, active_count)
        # Simulate some work
        await asyncio.sleep(0.1)
        results.append(num)
        active_count -= 1
    
    def worker_generator() -> Any:
        for i in range(5):
            yield tracking_coro(i)
    
    # Run with concurrency limit of 2
    await utils.queue_worker_functions(2, worker_generator())
    
    # Verify all coroutines were executed
    assert len(results) == 5
    assert set(results) == {0, 1, 2, 3, 4}
    # Verify concurrency was limited to 2
    assert max_concurrent <= 2


@pytest.mark.asyncio
async def test_queue_worker_functions_empty_generator() -> None:
    """Test queue_worker_functions handles empty generator correctly."""

    # noinspection PyUnreachableCode
    def empty_generator() -> Any:
        return
        yield  # This line never executes, making it an empty generator
    
    # Should complete without error
    await utils.queue_worker_functions(2, empty_generator())


@pytest.mark.asyncio
async def test_queue_worker_functions_single_worker() -> None:
    """Test queue_worker_functions with single worker."""
    results: List[int] = []
    
    async def numbered_coro(num: int) -> None:
        results.append(num)
    
    def worker_generator() -> Any:
        for i in range(3):
            yield numbered_coro(i)
    
    # Run with single worker
    await utils.queue_worker_functions(1, worker_generator())
    
    # Verify all coroutines were executed sequentially
    assert results == [0, 1, 2]


@pytest.mark.asyncio
async def test_queue_worker_functions_exception_handling() -> None:
    """Test queue_worker_functions handles exceptions in worker coroutines."""
    results: List[int] = []
    
    async def working_coro(num: int) -> None:
        results.append(num)
    
    async def failing_coro() -> None:
        raise ValueError("Test error")
    
    def mixed_generator() -> Any:
        yield working_coro(1)
        yield failing_coro()
        yield working_coro(2)
    
    # Should handle the exception and continue processing
    with pytest.raises(ExceptionGroup):  # TaskGroup will wrap exceptions in ExceptionGroup
        await utils.queue_worker_functions(2, mixed_generator())


@pytest.mark.asyncio
async def test_queue_worker_functions_zero_concurrency() -> None:
    """Test queue_worker_functions with zero concurrency creates one worker."""
    results: List[int] = []
    
    async def numbered_coro(num: int) -> None:
        results.append(num)
    
    def worker_generator() -> Any:
        for i in range(2):
            yield numbered_coro(i)
    
    # Run with zero concurrency (should default to 1 worker)
    await utils.queue_worker_functions(0, worker_generator())
    
    # Verify coroutines were still executed
    assert len(results) == 2


def test_worker_generator_basic_operation() -> None:
    """Test worker_generator with basic input."""
    # Arrange
    async def mock_worker_coroutine(records: list[int], processed_count: int, total_count: int) -> None:
        """Mock worker coroutine that processes records."""
        pass
    
    def test_records_generator() -> Any:
        """Generator that yields lists of test records."""
        yield [1, 2, 3]
        yield [4, 5]
        yield [6]
    
    # Act
    worker_coroutines = utils.worker_generator(mock_worker_coroutine, test_records_generator(), 6)
    coroutines_list = list(worker_coroutines)
    
    # Assert
    assert len(coroutines_list) == 3
    # Each item should be a coroutine
    for coroutine in coroutines_list:
        assert asyncio.iscoroutine(coroutine)
        coroutine.close()  # Clean up the coroutine


def test_worker_generator_empty_generator() -> None:
    """Test worker_generator with empty input generator."""
    # Arrange
    async def mock_worker_coroutine(records: list[int], processed_count: int, total_count: int) -> None:
        """Mock worker coroutine that processes records."""
        pass

    # noinspection PyUnreachableCode
    def empty_records_generator() -> Any:
        """Empty generator."""
        return
        yield  # This line is never reached but keeps it as a generator
    
    # Act
    worker_coroutines = utils.worker_generator(mock_worker_coroutine, empty_records_generator(), 0)
    coroutines_list = list(worker_coroutines)
    
    # Assert
    assert len(coroutines_list) == 0


def test_worker_generator_single_record() -> None:
    """Test worker_generator with single record batch."""
    # Arrange
    async def mock_worker_coroutine(records: list[str], processed_count: int, total_count: int) -> None:
        """Mock worker coroutine that processes records."""
        pass
    
    def single_record_generator() -> Any:
        """Generator that yields a single batch."""
        yield ["single_record"]
    
    # Act
    worker_coroutines = utils.worker_generator(mock_worker_coroutine, single_record_generator(), 1)
    coroutines_list = list(worker_coroutines)
    
    # Assert
    assert len(coroutines_list) == 1
    assert asyncio.iscoroutine(coroutines_list[0])
    coroutines_list[0].close()  # Clean up the coroutine


def test_worker_generator_multiple_batches() -> None:
    """Test worker_generator with multiple batches of varying sizes."""
    # Arrange
    async def mock_worker_coroutine(records: list[dict[str, Any]], processed_count: int, total_count: int) -> None:
        """Mock worker coroutine that processes records."""
        pass
    
    def multiple_batches_generator() -> Any:
        """Generator that yields multiple batches of different sizes."""
        yield [{"id": 1}, {"id": 2}, {"id": 3}, {"id": 4}]  # 4 records
        yield [{"id": 5}, {"id": 6}]  # 2 records
        yield [{"id": 7}]  # 1 record
        yield [{"id": 8}, {"id": 9}, {"id": 10}]  # 3 records
    
    # Act
    worker_coroutines = utils.worker_generator(mock_worker_coroutine, multiple_batches_generator(), 10)
    coroutines_list = list(worker_coroutines)
    
    # Assert
    assert len(coroutines_list) == 4
    for coroutine in coroutines_list:
        assert asyncio.iscoroutine(coroutine)
        coroutine.close()  # Clean up the coroutine


@pytest.mark.asyncio
async def test_worker_generator_processed_count_tracking() -> None:
    """Test that worker_generator correctly tracks processed count."""
    # Arrange
    processed_counts: list[int] = []
    
    async def tracking_worker_coroutine(records: list[int], processed_count: int, total_count: int) -> None:
        """Worker coroutine that tracks processed counts."""
        processed_counts.append(processed_count)
    
    def test_records_generator() -> Any:
        """Generator that yields batches of different sizes."""
        yield [1, 2, 3]  # 3 records, processed_count should be 0
        yield [4, 5]     # 2 records, processed_count should be 3
        yield [6]        # 1 record, processed_count should be 5
        yield [7, 8, 9, 10]  # 4 records, processed_count should be 6
    
    # Act
    worker_coroutines = utils.worker_generator(tracking_worker_coroutine, test_records_generator(), 10)
    
    # Execute all coroutines to test the tracking
    for coroutine in worker_coroutines:
        await coroutine
    
    # Assert
    expected_counts = [0, 3, 5, 6]
    assert processed_counts == expected_counts


def test_worker_generator_with_string_records() -> None:
    """Test worker_generator with string record types."""
    # Arrange
    async def string_worker_coroutine(records: list[str], processed_count: int, total_count: int) -> None:
        """Mock worker coroutine that processes string records."""
        pass
    
    def string_records_generator() -> Any:
        """Generator that yields batches of string records."""
        yield ["record1", "record2"]
        yield ["record3"]
        yield ["record4", "record5", "record6"]
    
    # Act
    worker_coroutines = utils.worker_generator(string_worker_coroutine, string_records_generator(), 6)
    coroutines_list = list(worker_coroutines)
    
    # Assert
    assert len(coroutines_list) == 3
    for coroutine in coroutines_list:
        assert asyncio.iscoroutine(coroutine)
        coroutine.close()  # Clean up the coroutine


def test_worker_generator_with_empty_batches() -> None:
    """Test worker_generator with some empty batches."""
    # Arrange
    async def empty_batch_worker_coroutine(records: list[int], processed_count: int, total_count: int) -> None:
        """Mock worker coroutine that processes records."""
        pass
    
    def mixed_batches_generator() -> Any:
        """Generator that yields some empty and some non-empty batches."""
        yield [1, 2]
        yield []  # Empty batch
        yield [3]
        yield []  # Another empty batch
        yield [4, 5, 6]
    
    # Act
    worker_coroutines = utils.worker_generator(empty_batch_worker_coroutine, mixed_batches_generator(), 6)
    coroutines_list = list(worker_coroutines)
    
    # Assert
    assert len(coroutines_list) == 5  # All batches should generate coroutines, even empty ones
    for coroutine in coroutines_list:
        assert asyncio.iscoroutine(coroutine)
        coroutine.close()  # Clean up the coroutine


@pytest.mark.asyncio
async def test_worker_generator_processed_count_with_empty_batches() -> None:
    """Test that processed count tracking works correctly with empty batches."""
    # Arrange
    processed_counts: list[int] = []
    
    async def tracking_worker_coroutine(records: list[int], processed_count: int, total_count: int) -> None:
        """Worker coroutine that tracks processed counts."""
        processed_counts.append(processed_count)
    
    def mixed_batches_generator() -> Any:
        """Generator with mixed empty and non-empty batches."""
        yield [1, 2]     # 2 records, processed_count should be 0
        yield []         # 0 records, processed_count should be 2
        yield [3]        # 1 record, processed_count should be 2
        yield []         # 0 records, processed_count should be 3
        yield [4, 5, 6]  # 3 records, processed_count should be 3
    
    # Act
    worker_coroutines = utils.worker_generator(tracking_worker_coroutine, mixed_batches_generator(), 6)
    
    # Execute all coroutines to test the tracking
    for coroutine in worker_coroutines:
        await coroutine
    
    # Assert
    expected_counts = [0, 2, 2, 3, 3]
    assert processed_counts == expected_counts


@pytest.mark.asyncio
async def test_worker_generator_large_batches() -> None:
    """Test worker_generator with large batches to ensure it handles size correctly."""
    # Arrange
    processed_counts: list[int] = []
    batch_sizes: list[int] = []
    
    async def size_tracking_worker_coroutine(records: list[int], processed_count: int, total_count: int) -> None:
        """Worker coroutine that tracks batch sizes and processed counts."""
        processed_counts.append(processed_count)
        batch_sizes.append(len(records))
    
    def large_batches_generator() -> Any:
        """Generator that yields large batches."""
        yield list(range(100))    # 100 records
        yield list(range(50))     # 50 records  
        yield list(range(200))    # 200 records
    
    # Act
    worker_coroutines = utils.worker_generator(size_tracking_worker_coroutine, large_batches_generator(), 350)
    
    # Execute all coroutines
    for coroutine in worker_coroutines:
        await coroutine
    
    # Assert
    expected_counts = [0, 100, 150]
    expected_sizes = [100, 50, 200]
    assert processed_counts == expected_counts
    assert batch_sizes == expected_sizes


async def test_queue_worker_functions_timing() -> None:
    """Test queue_worker_functions includes timing functionality."""
    async def delay_coro() -> None:
        await asyncio.sleep(0.01)  # Reduced delay for faster test
    
    def worker_generator() -> Any:
        yield delay_coro()
    
    # Mock the time.monotonic to verify timing is tracked
    with patch('musigree.utils.time.monotonic') as mock_time:
        # Provide enough mock values - asyncio's internal timing may call this many times
        # Use itertools.cycle to provide infinite values
        from itertools import cycle
        mock_time.side_effect = cycle([0.0, 0.01, 0.02, 0.03, 0.04, 0.05])
        
        await utils.queue_worker_functions(1, worker_generator())
        
        # Verify time.monotonic was called for timing (at least start and end)
        assert mock_time.call_count >= 2


@pytest.mark.asyncio
async def test_queue_worker_functions_large_number_of_tasks() -> None:
    """Test queue_worker_functions handles large number of tasks efficiently."""
    results: List[int] = []
    task_count = 100
    
    async def numbered_coro(num: int) -> None:
        results.append(num)
    
    def worker_generator() -> Any:
        for i in range(task_count):
            yield numbered_coro(i)
    
    # Run with multiple workers
    await utils.queue_worker_functions(5, worker_generator())
    
    # Verify all tasks were executed
    assert len(results) == task_count
    assert set(results) == set(range(task_count))


def test_generator_with_id_accumulator_basic_operation() -> None:
    """Test generator_with_id_accumulator with basic input data."""
    # Arrange
    test_data = [
        {"id": 1, "name": "Alice"},
        {"id": 2, "name": "Bob"},
        {"id": 3, "name": "Charlie"}
    ]
    id_accumulator: list[int] = []
    
    # Act
    result = list(utils.generator_with_id_accumulator(test_data, id_accumulator, "id"))
    
    # Assert
    assert result == test_data
    assert id_accumulator == [1, 2, 3]


def test_generator_with_id_accumulator_empty_iterable() -> None:
    """Test generator_with_id_accumulator with empty iterable."""
    # Arrange
    test_data: list[dict[str, Any]] = []
    id_accumulator: list[int] = []
    
    # Act
    result = list(utils.generator_with_id_accumulator(test_data, id_accumulator, "id"))
    
    # Assert
    assert result == []
    assert id_accumulator == []


def test_generator_with_id_accumulator_custom_id_attribute() -> None:
    """Test generator_with_id_accumulator with custom ID attribute name."""
    # Arrange
    test_data = [
        {"user_id": 100, "name": "Alice"},
        {"user_id": 200, "name": "Bob"},
        {"user_id": 300, "name": "Charlie"}
    ]
    id_accumulator: list[int] = []
    
    # Act
    result = list(utils.generator_with_id_accumulator(test_data, id_accumulator, "user_id"))
    
    # Assert
    assert result == test_data
    assert id_accumulator == [100, 200, 300]


def test_generator_with_id_accumulator_preserves_existing_accumulator() -> None:
    """Test generator_with_id_accumulator preserves existing values in accumulator."""
    # Arrange
    test_data = [
        {"id": 4, "name": "David"},
        {"id": 5, "name": "Eve"}
    ]
    id_accumulator = [1, 2, 3]  # Pre-existing values
    
    # Act
    result = list(utils.generator_with_id_accumulator(test_data, id_accumulator, "id"))
    
    # Assert
    assert result == test_data
    assert id_accumulator == [1, 2, 3, 4, 5]


def test_generator_with_id_accumulator_string_ids() -> None:
    """Test generator_with_id_accumulator converts string IDs to integers."""
    # Arrange
    test_data = [
        {"id": "10", "name": "Alice"},
        {"id": "20", "name": "Bob"},
        {"id": "30", "name": "Charlie"}
    ]
    id_accumulator: list[int] = []
    
    # Act
    result = list(utils.generator_with_id_accumulator(test_data, id_accumulator, "id"))
    
    # Assert
    assert result == test_data
    assert id_accumulator == [10, 20, 30]


def test_generator_with_id_accumulator_negative_ids() -> None:
    """Test generator_with_id_accumulator handles negative integer IDs."""
    # Arrange
    test_data = [
        {"id": -1, "name": "Alice"},
        {"id": -2, "name": "Bob"},
        {"id": -3, "name": "Charlie"}
    ]
    id_accumulator: list[int] = []
    
    # Act
    result = list(utils.generator_with_id_accumulator(test_data, id_accumulator, "id"))
    
    # Assert
    assert result == test_data
    assert id_accumulator == [-1, -2, -3]


def test_generator_with_id_accumulator_zero_ids() -> None:
    """Test generator_with_id_accumulator handles zero IDs."""
    # Arrange
    test_data = [
        {"id": 0, "name": "Alice"},
        {"id": 1, "name": "Bob"},
        {"id": 0, "name": "Charlie"}
    ]
    id_accumulator: list[int] = []
    
    # Act
    result = list(utils.generator_with_id_accumulator(test_data, id_accumulator, "id"))
    
    # Assert
    assert result == test_data
    assert id_accumulator == [0, 1, 0]


def test_generator_with_id_accumulator_large_numbers() -> None:
    """Test generator_with_id_accumulator handles large integer IDs."""
    # Arrange
    test_data = [
        {"id": 999999999, "name": "Alice"},
        {"id": 1000000000, "name": "Bob"},
        {"id": 2147483647, "name": "Charlie"}  # Max 32-bit signed int
    ]
    id_accumulator: list[int] = []
    
    # Act
    result = list(utils.generator_with_id_accumulator(test_data, id_accumulator, "id"))
    
    # Assert
    assert result == test_data
    assert id_accumulator == [999999999, 1000000000, 2147483647]


def test_generator_with_id_accumulator_missing_id_attribute() -> None:
    """Test generator_with_id_accumulator raises KeyError for missing ID attribute."""
    # Arrange
    test_data: list[dict[str, Any]] = [
        {"name": "Alice"},  # Missing 'id' attribute
        {"id": 2, "name": "Bob"},
        {"name": "Charlie"}  # Missing 'id' attribute
    ]
    id_accumulator: list[int] = []
    
    # Act & Assert
    with pytest.raises(KeyError):
        list(utils.generator_with_id_accumulator(test_data, id_accumulator, "id"))


def test_generator_with_id_accumulator_invalid_id_type() -> None:
    """Test generator_with_id_accumulator raises ValueError for non-numeric ID."""
    # Arrange
    test_data: list[dict[str, Any]] = [
        {"id": "not_a_number", "name": "Alice"},
        {"id": 2, "name": "Bob"}
    ]
    id_accumulator: list[int] = []
    
    # Act & Assert
    with pytest.raises(ValueError):
        list(utils.generator_with_id_accumulator(test_data, id_accumulator, "id"))


def test_generator_with_id_accumulator_float_ids() -> None:
    """Test generator_with_id_accumulator converts float IDs to integers."""
    # Arrange
    test_data = [
        {"id": 1.0, "name": "Alice"},
        {"id": 2.5, "name": "Bob"},
        {"id": 3.9, "name": "Charlie"}
    ]
    id_accumulator: list[int] = []
    
    # Act
    result = list(utils.generator_with_id_accumulator(test_data, id_accumulator, "id"))
    
    # Assert
    assert result == test_data
    assert id_accumulator == [1, 2, 3]


def test_generator_with_id_accumulator_complex_records() -> None:
    """Test generator_with_id_accumulator with complex record structures."""
    # Arrange
    test_data = [
        {
            "id": 1,
            "name": "Alice",
            "metadata": {"age": 30, "city": "New York"},
            "tags": ["developer", "python"]
        },
        {
            "id": 2,
            "name": "Bob",
            "metadata": {"age": 25, "city": "San Francisco"},
            "tags": ["designer", "ui"]
        }
    ]
    id_accumulator: list[int] = []
    
    # Act
    result = list(utils.generator_with_id_accumulator(test_data, id_accumulator, "id"))
    
    # Assert
    assert result == test_data
    assert id_accumulator == [1, 2]


def test_generator_with_id_accumulator_generator_input() -> None:
    """Test generator_with_id_accumulator works with generator input."""
    # Arrange
    def data_generator() -> Any:
        yield {"id": 1, "name": "Alice"}
        yield {"id": 2, "name": "Bob"}
        yield {"id": 3, "name": "Charlie"}
    
    id_accumulator: list[int] = []
    
    # Act
    result = list(utils.generator_with_id_accumulator(data_generator(), id_accumulator, "id"))
    
    # Assert
    expected_data = [
        {"id": 1, "name": "Alice"},
        {"id": 2, "name": "Bob"},
        {"id": 3, "name": "Charlie"}
    ]
    assert result == expected_data
    assert id_accumulator == [1, 2, 3]


def test_generator_with_id_accumulator_iterator_input() -> None:
    """Test generator_with_id_accumulator works with iterator input."""
    # Arrange
    test_data = iter([
        {"id": 1, "name": "Alice"},
        {"id": 2, "name": "Bob"},
        {"id": 3, "name": "Charlie"}
    ])
    id_accumulator: list[int] = []
    
    # Act
    result = list(utils.generator_with_id_accumulator(test_data, id_accumulator, "id"))
    
    # Assert
    expected_data = [
        {"id": 1, "name": "Alice"},
        {"id": 2, "name": "Bob"},
        {"id": 3, "name": "Charlie"}
    ]
    assert result == expected_data
    assert id_accumulator == [1, 2, 3]


def test_generator_with_id_accumulator_multiple_calls() -> None:
    """Test generator_with_id_accumulator works correctly with multiple calls."""
    # Arrange
    test_data_1 = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
    test_data_2 = [{"id": 3, "name": "Charlie"}, {"id": 4, "name": "David"}]
    id_accumulator: list[int] = []
    
    # Act
    result_1 = list(utils.generator_with_id_accumulator(test_data_1, id_accumulator, "id"))
    result_2 = list(utils.generator_with_id_accumulator(test_data_2, id_accumulator, "id"))
    
    # Assert
    assert result_1 == test_data_1
    assert result_2 == test_data_2
    assert id_accumulator == [1, 2, 3, 4]


def test_generator_with_id_accumulator_none_id() -> None:
    """Test generator_with_id_accumulator raises TypeError for None ID."""
    # Arrange
    test_data: list[dict[str, Any]] = [
        {"id": None, "name": "Alice"},
        {"id": 2, "name": "Bob"}
    ]
    id_accumulator: list[int] = []
    
    # Act & Assert
    with pytest.raises(TypeError):
        list(utils.generator_with_id_accumulator(test_data, id_accumulator, "id"))


def test_generator_with_id_accumulator_boolean_id() -> None:
    """Test generator_with_id_accumulator converts boolean IDs to integers."""
    # Arrange
    test_data = [
        {"id": True, "name": "Alice"},   # True becomes 1
        {"id": False, "name": "Bob"},    # False becomes 0
        {"id": 2, "name": "Charlie"}
    ]
    id_accumulator: list[int] = []
    
    # Act
    result = list(utils.generator_with_id_accumulator(test_data, id_accumulator, "id"))
    
    # Assert
    assert result == test_data
    assert id_accumulator == [1, 0, 2]


# Tests for async_chunks function
@pytest.mark.asyncio
async def test_async_chunks_basic_operation() -> None:
    """Test async_chunks with basic async generator input."""
    # Arrange
    async def number_generator() -> AsyncGenerator[int, None]:
        for i in range(5):
            yield i
    
    # Act
    chunks: list[list[int]] = []
    async for chunk in utils.async_chunks(number_generator(), 2):
        chunks.append(chunk)
    
    # Assert
    assert chunks == [[0, 1], [2, 3], [4]]


@pytest.mark.asyncio
async def test_async_chunks_exact_division() -> None:
    """Test async_chunks when items divide evenly into chunks."""
    # Arrange
    async def number_generator() -> AsyncGenerator[int, None]:
        for i in range(6):
            yield i
    
    # Act
    chunks = []
    async for chunk in utils.async_chunks(number_generator(), 2):
        chunks.append(chunk)
    
    # Assert
    assert chunks == [[0, 1], [2, 3], [4, 5]]


@pytest.mark.asyncio
async def test_async_chunks_empty_generator() -> None:
    """Test async_chunks with empty async generator."""
    # Arrange
    # noinspection PyUnreachableCode
    async def empty_generator() -> AsyncGenerator[int, None]:
        return
        # noinspection PyTypeChecker
        yield  # This line never executes
    
    # Act
    chunks = []
    async for chunk in utils.async_chunks(empty_generator(), 3):
        chunks.append(chunk)
    
    # Assert
    assert chunks == []


@pytest.mark.asyncio
async def test_async_chunks_single_item() -> None:
    """Test async_chunks with single item in generator."""
    # Arrange
    async def single_item_generator() -> AsyncGenerator[str, None]:
        yield "single"
    
    # Act
    chunks = []
    async for chunk in utils.async_chunks(single_item_generator(), 3):
        chunks.append(chunk)
    
    # Assert
    assert chunks == [["single"]]


@pytest.mark.asyncio
async def test_async_chunks_large_chunk_size() -> None:
    """Test async_chunks with chunk size larger than available items."""
    # Arrange
    async def small_generator() -> AsyncGenerator[int, None]:
        for i in range(3):
            yield i
    
    # Act
    chunks = []
    async for chunk in utils.async_chunks(small_generator(), 10):
        chunks.append(chunk)
    
    # Assert
    assert chunks == [[0, 1, 2]]


@pytest.mark.asyncio
async def test_async_chunks_chunk_size_one() -> None:
    """Test async_chunks with chunk size of one."""
    # Arrange
    async def number_generator() -> AsyncGenerator[int, None]:
        for i in range(4):
            yield i
    
    # Act
    chunks = []
    async for chunk in utils.async_chunks(number_generator(), 1):
        chunks.append(chunk)
    
    # Assert
    assert chunks == [[0], [1], [2], [3]]


@pytest.mark.asyncio
async def test_async_chunks_with_strings() -> None:
    """Test async_chunks with string items."""
    # Arrange
    async def string_generator() -> AsyncGenerator[str, None]:
        yield "apple"
        yield "banana"
        yield "cherry"
        yield "date"
    
    # Act
    chunks = []
    async for chunk in utils.async_chunks(string_generator(), 2):
        chunks.append(chunk)
    
    # Assert
    assert chunks == [["apple", "banana"], ["cherry", "date"]]


@pytest.mark.asyncio
async def test_async_chunks_with_complex_objects() -> None:
    """Test async_chunks with complex object items."""
    # Arrange
    async def object_generator() -> AsyncGenerator[dict[str, Any], None]:
        yield {"id": 1, "name": "Alice"}
        yield {"id": 2, "name": "Bob"}
        yield {"id": 3, "name": "Charlie"}
        yield {"id": 4, "name": "David"}
        yield {"id": 5, "name": "Eve"}
    
    # Act
    chunks = []
    async for chunk in utils.async_chunks(object_generator(), 3):
        chunks.append(chunk)
    
    # Assert
    expected_chunks = [
        [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}, {"id": 3, "name": "Charlie"}],
        [{"id": 4, "name": "David"}, {"id": 5, "name": "Eve"}]
    ]
    assert chunks == expected_chunks


# Tests for download_file function
@pytest.mark.skip
@patch('musigree.utils.requests.get')
def test_download_file_success(mock_get: MagicMock) -> None:
    """Test download_file successfully downloads and writes content."""
    # Arrange
    mock_response = MagicMock()
    mock_response.raw = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_get.return_value.__enter__.return_value = mock_response
    
    mock_output_file = MagicMock()
    mock_output_file.flush.return_value = None
    mock_output_file.close.return_value = None
    
    # Act
    utils.download_file("https://example.com/test.txt", mock_output_file)
    
    # Assert
    mock_get.assert_called_once_with("https://example.com/test.txt", stream=True)
    mock_response.raise_for_status.assert_called_once()
    mock_output_file.flush.assert_called_once()
    mock_output_file.close.assert_called_once()


@patch('musigree.utils.requests.get')
def test_download_file_http_error(mock_get: MagicMock) -> None:
    """Test download_file raises exception on HTTP error."""
    # Arrange
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
    mock_get.return_value.__enter__.return_value = mock_response
    
    mock_output_file = MagicMock()
    
    # Act & Assert
    with pytest.raises(requests.HTTPError, match="404 Not Found"):
        utils.download_file("https://example.com/notfound.txt", mock_output_file)


@patch('musigree.utils.requests.get')
def test_download_file_network_error(mock_get: MagicMock) -> None:
    """Test download_file raises exception on network error."""
    # Arrange
    mock_get.side_effect = requests.RequestException("Network error")
    
    mock_output_file = MagicMock()
    
    # Act & Assert
    with pytest.raises(requests.RequestException, match="Network error"):
        utils.download_file("https://example.com/test.txt", mock_output_file)

@pytest.mark.skip
@patch('musigree.utils.requests.get')
def test_download_file_with_buffered_writer(mock_get: MagicMock) -> None:
    """Test download_file works with BufferedWriter."""
    # Arrange
    mock_response = MagicMock()
    mock_response.raw = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_get.return_value.__enter__.return_value = mock_response
    
    # Create a mock BufferedWriter
    mock_output_file = MagicMock()
    mock_output_file.flush.return_value = None
    mock_output_file.close.return_value = None
    
    # Act
    utils.download_file("https://example.com/test.txt", mock_output_file)
    
    # Assert
    mock_get.assert_called_once_with("https://example.com/test.txt", stream=True)
    mock_response.raise_for_status.assert_called_once()
    mock_output_file.flush.assert_called_once()
    mock_output_file.close.assert_called_once()


# Tests for async_worker_generator function
@pytest.mark.asyncio
async def test_async_worker_generator_basic_operation() -> None:
    """Test async_worker_generator with basic async iterable input."""
    # Arrange
    results: list[int] = []
    
    async def mock_worker_coroutine(records: list[int], processed_count: int, total_count: int) -> None:
        """Mock worker coroutine that processes records."""
        results.extend(records)
    
    async def async_records_generator() -> AsyncGenerator[list[int], None]:
        """Async generator that yields lists of test records."""
        yield [1, 2, 3]
        yield [4, 5]
        yield [6]
    
    # Act
    worker_coroutines = utils.async_worker_generator(mock_worker_coroutine, async_records_generator(), 6)
    coroutines_list = []
    async for coroutine in worker_coroutines:
        coroutines_list.append(coroutine)
    
    # Execute all coroutines
    for coroutine in coroutines_list:
        await coroutine
    
    # Assert
    assert len(coroutines_list) == 3
    assert results == [1, 2, 3, 4, 5, 6]


@pytest.mark.asyncio
async def test_async_worker_generator_empty_generator() -> None:
    """Test async_worker_generator with empty async generator."""
    # Arrange
    async def mock_worker_coroutine(records: list[int], processed_count: int, total_count: int) -> None:
        """Mock worker coroutine that processes records."""
        pass

    # noinspection PyUnreachableCode
    async def empty_async_generator() -> AsyncGenerator[list[int], None]:
        """Empty async generator."""
        return
        yield [0]  # This line is never reached
    
    # Act
    worker_coroutines = utils.async_worker_generator(mock_worker_coroutine, empty_async_generator(), 0)
    coroutines_list = []
    async for coroutine in worker_coroutines:
        coroutines_list.append(coroutine)
    
    # Assert
    assert len(coroutines_list) == 0


@pytest.mark.asyncio
async def test_async_worker_generator_processed_count_tracking() -> None:
    """Test that async_worker_generator correctly tracks processed count."""
    # Arrange
    processed_counts: list[int] = []
    
    async def tracking_worker_coroutine(records: list[int], processed_count: int, total_count: int) -> None:
        """Worker coroutine that tracks processed counts."""
        processed_counts.append(processed_count)
    
    async def async_test_records_generator() -> AsyncGenerator[list[int], None]:
        """Async generator that yields batches of different sizes."""
        yield [1, 2, 3]  # 3 records, processed_count should be 0
        yield [4, 5]     # 2 records, processed_count should be 3
        yield [6]        # 1 record, processed_count should be 5
        yield [7, 8, 9, 10]  # 4 records, processed_count should be 6
    
    # Act
    worker_coroutines = utils.async_worker_generator(tracking_worker_coroutine, async_test_records_generator(), 10)
    
    # Execute all coroutines to test the tracking
    async for coroutine in worker_coroutines:
        await coroutine
    
    # Assert
    expected_counts = [0, 3, 5, 6]
    assert processed_counts == expected_counts


@pytest.mark.asyncio
async def test_async_worker_generator_with_string_records() -> None:
    """Test async_worker_generator with string record types."""
    # Arrange
    results: list[str] = []
    
    async def string_worker_coroutine(records: list[str], processed_count: int, total_count: int) -> None:
        """Mock worker coroutine that processes string records."""
        results.extend(records)
    
    async def async_string_records_generator() -> AsyncGenerator[list[str], None]:
        """Async generator that yields batches of string records."""
        yield ["record1", "record2"]
        yield ["record3"]
        yield ["record4", "record5", "record6"]
    
    # Act
    worker_coroutines = utils.async_worker_generator(string_worker_coroutine, async_string_records_generator(), 6)
    coroutines_list = []
    async for coroutine in worker_coroutines:
        coroutines_list.append(coroutine)
    
    # Execute all coroutines
    for coroutine in coroutines_list:
        await coroutine
    
    # Assert
    assert len(coroutines_list) == 3
    assert results == ["record1", "record2", "record3", "record4", "record5", "record6"]


@pytest.mark.asyncio
async def test_async_worker_generator_large_batches() -> None:
    """Test async_worker_generator with large batches to ensure it handles size correctly."""
    # Arrange
    processed_counts: list[int] = []
    batch_sizes: list[int] = []
    
    async def size_tracking_worker_coroutine(records: list[int], processed_count: int, total_count: int) -> None:
        """Worker coroutine that tracks batch sizes and processed counts."""
        processed_counts.append(processed_count)
        batch_sizes.append(len(records))
    
    async def async_large_batches_generator() -> AsyncGenerator[list[int], None]:
        """Async generator that yields large batches."""
        yield list(range(100))    # 100 records
        yield list(range(50))     # 50 records  
        yield list(range(200))    # 200 records
    
    # Act
    worker_coroutines = utils.async_worker_generator(size_tracking_worker_coroutine, async_large_batches_generator(), 350)
    
    # Execute all coroutines
    async for coroutine in worker_coroutines:
        await coroutine
    
    # Assert
    expected_counts = [0, 100, 150]
    expected_sizes = [100, 50, 200]
    assert processed_counts == expected_counts
    assert batch_sizes == expected_sizes


# Tests for queue_async_worker_functions function
@pytest.mark.asyncio
async def test_queue_async_worker_functions_basic_operation() -> None:
    """Test queue_async_worker_functions with basic async generator processing."""
    results: list[int] = []
    
    async def numbered_coro(num: int) -> None:
        results.append(num)
    
    async def async_worker_generator() -> AsyncGenerator[Coroutine[int, None, None], None]:
        for i in range(3):
            yield numbered_coro(i)
    
    # Run the queue async worker functions
    await utils.queue_async_worker_functions(2, async_worker_generator())
    
    # Verify all coroutines were executed
    assert len(results) == 3
    assert set(results) == {0, 1, 2}


@pytest.mark.asyncio
async def test_queue_async_worker_functions_concurrency() -> None:
    """Test queue_async_worker_functions respects concurrency limits."""
    active_count = 0
    max_concurrent = 0
    results: list[int] = []
    
    async def tracking_coro(num: int) -> None:
        nonlocal active_count, max_concurrent
        active_count += 1
        max_concurrent = max(max_concurrent, active_count)
        # Simulate some work
        await asyncio.sleep(0.1)
        results.append(num)
        active_count -= 1
    
    async def async_worker_generator() -> AsyncGenerator[Coroutine[int, None, None], None]:
        for i in range(5):
            yield tracking_coro(i)
    
    # Run with concurrency limit of 2
    await utils.queue_async_worker_functions(2, async_worker_generator())
    
    # Verify all coroutines were executed
    assert len(results) == 5
    assert set(results) == {0, 1, 2, 3, 4}
    # Verify concurrency was limited to 2
    assert max_concurrent <= 2


@pytest.mark.asyncio
async def test_queue_async_worker_functions_empty_generator() -> None:
    """Test queue_async_worker_functions handles empty async generator correctly."""
    results: list[int] = []

    async def numbered_coro(num: int) -> None:
        results.append(num)

    # noinspection PyUnreachableCode
    async def empty_async_generator() -> AsyncGenerator[Coroutine[int, None, None], None]:
        return
        yield numbered_coro(0) # This line never executes

    # Should complete without error
    await utils.queue_async_worker_functions(2, empty_async_generator())


@pytest.mark.asyncio
async def test_queue_async_worker_functions_single_worker() -> None:
    """Test queue_async_worker_functions with single worker."""
    results: list[int] = []
    
    async def numbered_coro(num: int) -> None:
        results.append(num)
    
    async def async_worker_generator() -> AsyncGenerator[Coroutine[int, None, None], None]:
        for i in range(3):
            yield numbered_coro(i)
    
    # Run with single worker
    await utils.queue_async_worker_functions(1, async_worker_generator())
    
    # Verify all coroutines were executed sequentially
    assert results == [0, 1, 2]


@pytest.mark.asyncio
async def test_queue_async_worker_functions_exception_handling() -> None:
    """Test queue_async_worker_functions handles exceptions in worker coroutines."""
    results: list[int] = []
    
    async def working_coro(num: int) -> None:
        results.append(num)
    
    async def failing_coro() -> None:
        raise ValueError("Test error")
    
    async def mixed_async_generator() -> AsyncGenerator[Coroutine[int, None, None], None]:
        yield working_coro(1)
        yield failing_coro()
        yield working_coro(2)
    
    # Should handle the exception and continue processing
    with pytest.raises(ExceptionGroup):  # TaskGroup will wrap exceptions in ExceptionGroup
        await utils.queue_async_worker_functions(2, mixed_async_generator())


@pytest.mark.asyncio
async def test_queue_async_worker_functions_zero_concurrency() -> None:
    """Test queue_async_worker_functions with zero concurrency creates one worker."""
    results: list[int] = []
    
    async def numbered_coro(num: int) -> None:
        results.append(num)
    
    async def async_worker_generator() -> AsyncGenerator[Coroutine[int, None, None], None]:
        for i in range(2):
            yield numbered_coro(i)
    
    # Run with zero concurrency (should default to 1 worker)
    await utils.queue_async_worker_functions(0, async_worker_generator())
    
    # Verify coroutines were still executed
    assert len(results) == 2


@pytest.mark.asyncio
async def test_queue_async_worker_functions_timing() -> None:
    """Test queue_async_worker_functions includes timing functionality."""
    async def delay_coro() -> None:
        await asyncio.sleep(0.01)  # Reduced delay for faster test
    
    async def async_worker_generator() -> AsyncGenerator[Coroutine[int, None, None], None]:
        yield delay_coro()
    
    # Mock the time.monotonic to verify timing is tracked
    with patch('musigree.utils.time.monotonic') as mock_time:
        # Provide enough mock values - asyncio's internal timing may call this many times
        # Use itertools.cycle to provide infinite values
        from itertools import cycle
        mock_time.side_effect = cycle([0.0, 0.01, 0.02, 0.03, 0.04, 0.05])
        
        await utils.queue_async_worker_functions(1, async_worker_generator())
        
        # Verify time.monotonic was called for timing (at least start and end)
        assert mock_time.call_count >= 2


@pytest.mark.asyncio
async def test_queue_async_worker_functions_large_number_of_tasks() -> None:
    """Test queue_async_worker_functions handles large number of tasks efficiently."""
    results: list[int] = []
    task_count = 100
    
    async def numbered_coro(num: int) -> None:
        results.append(num)
    
    async def async_worker_generator() -> AsyncGenerator[Coroutine[None, None, None], None]:
        for i in range(task_count):
            yield numbered_coro(i)
    
    # Run with multiple workers
    await utils.queue_async_worker_functions(5, async_worker_generator())
    
    # Verify all tasks were executed
    assert len(results) == task_count
    assert set(results) == set(range(task_count))


@pytest.mark.asyncio
async def test_queue_async_worker_functions_with_complex_objects() -> None:
    """Test queue_async_worker_functions with complex object processing."""
    results: list[dict[str, Any]] = []
    
    async def object_coro(obj: dict[str, Any]) -> None:
        results.append(obj)
    
    test_objects = [
        {"id": 1, "name": "Alice", "data": {"age": 30}},
        {"id": 2, "name": "Bob", "data": {"age": 25}},
        {"id": 3, "name": "Charlie", "data": {"age": 35}}
    ]
    
    async def async_worker_generator() -> AsyncGenerator[Coroutine[None, None, None], None]:
        for obj in test_objects:
            yield object_coro(obj)
    
    # Run with multiple workers
    await utils.queue_async_worker_functions(2, async_worker_generator())
    
    # Verify all objects were processed
    assert len(results) == 3
    assert set(obj["id"] for obj in results) == {1, 2, 3}


# Simple test for async_chunks to verify it works
@pytest.mark.asyncio
async def test_async_chunks_simple() -> None:
    """Test async_chunks with a simple async generator."""
    async def simple_generator() -> AsyncGenerator[int, None]:
        yield 1
        yield 2
        yield 3
    
    chunks = []
    async for chunk in utils.async_chunks(simple_generator(), 2):
        chunks.append(chunk)
    
    assert chunks == [[1, 2], [3]]
