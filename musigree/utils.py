import asyncio
import enum
import itertools
import json
import logging
import math
import random
import re
import shutil
import string
import sys
import textwrap
import time
import unicodedata
from collections.abc import Mapping, Iterator, Sequence, Iterable, AsyncIterable
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from datetime import datetime, date
from functools import partial
from io import BufferedWriter
from typing import Any, TypeVar, Generator, Callable, Protocol

import requests
from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import DeclarativeBase
from toolz import count  # type: ignore
from unidecode import unidecode

from musigree.constants import VERSION, ThreadingModel

T_read = TypeVar("T_read", covariant=True)
T_write = TypeVar("T_write", contravariant=True)


class SupportsRead(Protocol[T_read]):
    """Protocol for file-like objects that support binary reads."""

    def read(self, size: int = -1, /) -> T_read: ...


class SupportsWrite(Protocol[T_write]):
    """Protocol for file-like objects that support binary writes."""

    def write(self, data: T_write, /) -> int: ...


log = logging.getLogger(__name__)

URLIFY_REGEX = re.compile(r"\s+", re.MULTILINE)
# ARG_ROLES_REGEX = re.compile(r"^roles(\[\d*\])?$")

# Remove unwanted characters from the string.
# Any digits in round brackets are removed, and
# any "not on label" or "self-released are removed.
STRIP_PATTERN = re.compile(r"\(\d+\)|not on label|self[\s\- ]+released|[^\w \-]+|_")
# STRIP_PATTERN = re.compile(r"(\(\d+\)|[^(\w\s)]+)")
# REMOVE_PUNCTUATION = re.compile(r"[^\w\s]")
WORD_PATTERN = re.compile(r"\s+")
T = TypeVar("T")


class SkipFilter:
    def __init__(
        self,
        types: tuple[type] | None = None,
        keys: list[str] | None = None,
        allow_empty: bool = False,
    ) -> None:
        self.types = tuple(types or [])
        self.keys = set(keys or [])
        self.allow_empty = allow_empty  # if True include empty filtered structures

    def filter(self, data: Any) -> Any:
        if isinstance(data, Mapping):
            result = {}  # dict-like, use dict as a base
            for k, v in data.items():
                if k in self.keys or isinstance(v, self.types):  # skip key/type
                    continue
                try:
                    result[k] = self.filter(v)
                except ValueError:
                    pass
            if result or self.allow_empty:
                return result
        # elif isinstance(data, Sequence):
        #     result = []  # a sequence, use list as a base
        #     for v in data:
        #         if isinstance(v, self.types):  # skip type
        #             continue
        #         try:
        #             result.append(self.filter(v))
        #         except ValueError:
        #             pass
        #     if result or self.allow_empty:
        #         return result
        else:  # we don't know how to traverse this structure...
            return data  # return it as-is, hope for the best...
        raise ValueError


def batched(iterable: Iterable[T] | Sequence[T], n: int) -> Generator[list[T], None, None]:
    # batched('ABCDEFG', 3) → ABC DEF G
    if n < 1:
        raise ValueError("n must be at least one")
    if isinstance(iterable, Sequence):
        it = iter(iterable)
        while batch := list(itertools.islice(it, n)):
            yield batch
    else:
        while batch := list(itertools.islice(iterable, n)):
            yield batch


def split_list(num_chunks: int, seq: Sequence[T]) -> Iterator[list[T]]:
    num_items = count(seq)
    num_chunks = min(num_items, num_chunks)
    num_chunks = max(1, num_chunks)
    return batched(iter(seq), math.ceil(num_items / num_chunks))


def normalize(argument: str, indent: int | str | None = None) -> str:
    _string = argument.replace("\t", "    ")
    lines = _string.split("\n")
    while lines and (not lines[0] or lines[0].isspace()):
        lines.pop(0)
    while lines and (not lines[-1] or lines[-1].isspace()):
        lines.pop()
    for i, line in enumerate(lines):
        lines[i] = line.rstrip()
    _string = "\n".join(lines)
    _string = textwrap.dedent(_string)
    if indent:
        if isinstance(indent, str):
            indent_string = indent
        else:
            assert isinstance(indent, int)
            indent_string = abs(int(indent)) * " "
        lines = _string.split("\n")
        for i, line in enumerate(lines):
            if line:
                lines[i] = f"{indent_string}{line}"
        _string = "\n".join(lines)
    if _string != "" and not _string.endswith("\n"):
        _string += "\n"
    return _string


# def normalize_dict(obj: dict) -> str:
#     s = normalize(json.dumps(obj, indent=4, sort_keys=True, default=str))
#     return s


def normalize_dict(obj: Any, skip_keys: list[str] | None = None) -> str:
    """Normalize a dictionary into a formatted string representation, skipping specified keys and types."""
    skip_keys = skip_keys or []
    preprocessor = SkipFilter(keys=skip_keys)

    def list_public_attributes(input_var: dict[str, Any]) -> dict[str, Any]:
        return {
            k: (list_public_attributes(preprocessor.filter(v)) if isinstance(v, Mapping) else v)
            for k, v in input_var.items()
            if not (k.startswith("_") or callable(v))
        }

    def default(o: Any) -> dict[str, Any] | str:
        def as_dict(self: DeclarativeBase) -> dict[str, Any]:
            return {c.name: getattr(self, c.name) for c in self.__table__.columns}  # type: ignore

        from musigree.offline.offline_database.base_table import OfflineBase
        from musigree.runtime.runtime_database.runtime_base_table import RuntimeBase
        from musigree.library.domain.base import InternalDomainObject

        if isinstance(o, OfflineBase):
            return list_public_attributes(preprocessor.filter(as_dict(o)))
        elif isinstance(o, RuntimeBase):
            return list_public_attributes(preprocessor.filter(as_dict(o)))
        elif isinstance(o, InternalDomainObject):
            return list_public_attributes(preprocessor.filter(o.model_dump()))
        elif isinstance(o, enum.Enum):
            # noinspection PyStringConversionWithoutDunderMethod
            return str(o)
        elif isinstance(o, date):
            # noinspection PyStringConversionWithoutDunderMethod
            return str(o)
        elif isinstance(o, datetime):
            # noinspection PyStringConversionWithoutDunderMethod
            return str(o)
        else:
            return f"<<non-serializable: {type(o).__qualname__}>>"

    s = normalize(
        json.dumps(
            obj,
            indent=4,
            sort_keys=True,
            default=default,
        )
    )
    return s


def normalize_dict_list(list_obj: list[dict[str, Any]]) -> str:
    """Normalize a list of dictionaries into a formatted string representation."""

    def make_sortable_key(obj: dict[str, Any]) -> str:
        """Create a sortable key from a dictionary by converting it to a normalized JSON string."""
        try:
            # Create a normalized version for sorting by converting to JSON with sorted keys
            return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)
        except (TypeError, ValueError):
            # Fallback: convert the entire dict to string if JSON serialization fails
            return str(sorted(obj.items()))

    if list_obj is None or len(list_obj) == 0:
        return "[\n" + "\n]\n"

    # Sort the list using the normalized JSON representation as the key
    sorted_list_obj = sorted(list_obj, key=make_sortable_key)

    return (
        "[\n"
        + ",\n".join(
            textwrap.indent(
                strip_trailing_newline(
                    normalize(json.dumps(_, indent=4, sort_keys=True, default=str))
                ),
                "    ",
            )
            for _ in sorted_list_obj
        )
        + "\n]\n"
    )


def normalize_str_list(list_obj: list[str]) -> str:
    """Normalize a list of strings into a formatted string representation."""
    if list_obj is None or len(list_obj) == 0:
        return "[\n" + "\n]\n"
    return "[\n" + ",\n".join(textwrap.indent(_, "    ") for _ in list_obj) + "\n]\n"


def strip_input(input_str: str) -> str:
    """Remove leading indentation and the first newline from the input string."""
    return textwrap.dedent(input_str).replace("\n", "", 1)


def strip_trailing_newline(input_str: str) -> str:
    """Remove a trailing newline from the input string, if present."""
    return input_str.removesuffix("\n")


def table2dict(table: DeclarativeBase) -> dict[str, Any]:
    """Convert a SQLAlchemy table object to a dictionary.
    Args:
        table (DeclarativeBase): The SQLAlchemy table object.
    Returns:
        dict[str, Any]: A dictionary representation of the table object.
    """
    return {c.name: getattr(table, c.name) for c in table.__table__.columns}  # type: ignore


def is_latin(_string: str) -> bool:
    """Check if all characters in the string are Latin characters.
    Args:
        _string (str): The input string to check.
    Returns:
        bool: True if all characters are Latin, False otherwise.
    """
    if _string is None or _string == "":
        return False
    try:
        return all(["LATIN" in unicodedata.name(c) for c in _string])
    except ValueError:
        return False


def to_ascii(_string: str) -> str:
    """Convert a unicode string to a plain ASCII string.
    Args:
        _string (str): The input unicode string.
    Returns:
        str: The converted plain ASCII string.
    """
    if _string is None:
        return ""
    # Transliterate the unicode string into a plain ASCII string
    if is_latin(_string):
        _string = unidecode(_string, "preserve")
    return _string


def sleep_with_backoff(multiplier: int) -> None:
    """Sleep for a random amount of time based on the given multiplier.
    The sleep time is calculated as a random value between 1 and the multiplier,
    capped at a maximum of 60 seconds.
    Args:
        multiplier (int): The maximum multiplier for the sleep time.
    """
    if multiplier < 1:
        multiplier = 1
    time_in_secs = int(multiplier * (1.0 + random.random()))
    if time_in_secs > 60:
        time_in_secs = 60
    if time_in_secs < 1:
        time_in_secs = 1
    # log.debug(f"sleeping for {time_in_secs} secs")
    time.sleep(time_in_secs)


def copyfile(s: SupportsRead[bytes], t: SupportsWrite[bytes], length: int) -> None:
    shutil.copyfileobj(s, t, length=length)


def download_file(input_url: str, output_file: BufferedWriter) -> None:
    """Download a file from a URL and write it to the provided output file-like object.
    Args:
        input_url (str): The URL of the file to download.
        output_file (SupportsWrite | BufferedWriter): A file-like object to write the downloaded content to.
    """
    with requests.get(input_url, stream=True) as response:
        response.raise_for_status()
        copyfile(response.raw, output_file, length=10 * 1024)
    output_file.flush()
    output_file.close()


def get_discogs_url(dump_date: date, dump_type: str) -> str:
    """Construct the URL for a Discogs data dump based on the date and type.
    Args:
        dump_date (date): The date of the dump.
        dump_type (str): The type of dump (e.g., "artists", "releases").
    Returns:
        str: The constructed URL for the Discogs data dump.
    """
    from musigree.constants import DISCOGS_FILE_TEMPLATE
    from musigree.constants import DISCOGS_BASE_URL

    year = dump_date.year
    base = DISCOGS_BASE_URL.format(year=year)
    path = DISCOGS_FILE_TEMPLATE.format(date=dump_date.strftime("%Y%m%d"), type=dump_type)
    return base + path


def get_discogs_dump_dates(start_date: date, end_date: date) -> list[date]:
    """Generate a list of dates representing the first day of each month between start_date and end_date.
    Args:
        start_date (date): The start date of the range.
        end_date (date): The end date of the range.
    Returns:
        list[date]: A list of dates representing the first day of each month in the range.
    """
    date_list = []
    curr_date = start_date
    while curr_date <= end_date:
        month_date = date(year=curr_date.year, month=curr_date.month, day=1)
        date_list.append(month_date)
        curr_date += relativedelta(months=1)
    return date_list


def calculate_size(obj: Any) -> int:
    """Recursively calculates the memory size of an object and its contents.
    Args:
        obj (Any): The object to calculate the size of.
    Returns:
        int: The total memory size of the object in bytes.
    """
    size = sys.getsizeof(obj)
    if isinstance(obj, dict):
        size += sum(calculate_size(v) for v in obj.values())
        size += sum(calculate_size(k) for k in obj.keys())
    elif isinstance(obj, (list, tuple, set)):
        size += sum(calculate_size(v) for v in obj)
    elif isinstance(obj, bytes):
        size += len(obj)
    elif isinstance(obj, str):
        size += len(obj.encode("utf-8"))
    elif isinstance(obj, type(None)):
        size += 0
    elif isinstance(obj, (int, float)):
        size += sys.getsizeof(obj)
    else:
        size += sum(
            calculate_size(getattr(obj, attr))
            for attr in dir(obj)
            if not callable(getattr(obj, attr)) and not attr.startswith("__")
        )
    return size


def get_random_string(length: int) -> str:
    """Generate a random string of fixed length.
    Args:
        length (int): The length of the random string to generate.
    Returns:
        str: A random string of the specified length.
    """
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))


def worker_generator(
    worker_function: Callable[[list[T], int, int], None],
    records: Iterable[list[T]],
    total_count: int,
) -> Generator[partial, None, None]:
    """A generator that yields worker functions for processing records.
    Args:
        worker_function (Callable[[list[T], int, int], None]): The worker function to be called for each batch of records.
        records (Iterable[list[T]]): An iterable of lists of records to be processed.
        total_count (int): The total number of records to be processed.
    Yields:
        Callable[..., None]: A partial that processes a batch of records.
    """
    processed_count: int = 0
    for record in records:
        yield partial(worker_function, record, processed_count, total_count)
        processed_count += len(record)


async def async_worker_generator(
    worker_function: Callable[[list[T], int, int], None],
    records: AsyncIterable[list[T]],
    total_count: int,
) -> list[partial]:
    """A generator that yields worker functions for processing records.
    Args:
        worker_function (Callable[[list[T], int, int], None]): The worker function to be called for each batch of records.
        records (Iterable[list[T]]): An iterable of lists of records to be processed.
        total_count (int): The total number of records to be processed.
    Yields:
        Callable[..., None]: A partial that processes a batch of records.
    """
    partials: list[partial] = []
    processed_count: int = 0
    async for record in records:
        partials.append(partial(worker_function, record, processed_count, total_count))
        processed_count += len(record)
    return partials


async def queue_worker_functions(
    max_concurrent: int,
    worker_partials: Generator[partial, None, None] | list[partial],
    threading_model: ThreadingModel = ThreadingModel.THREAD,
) -> Any:
    """Run worker coroutines with a maximum number of concurrent workers.
    Args:
        max_concurrent (int): The maximum number of concurrent workers.
        worker_partials (Generator[Callable[..., None], None, None]): A generator of worker coroutines.
        threading_model: (ThreadingModel)
    """
    if max_concurrent < 1:
        max_concurrent = 1
    if max_concurrent > 8:
        max_concurrent = 8
    started_at = time.monotonic()

    tasks = []
    loop = asyncio.get_running_loop()
    if threading_model == ThreadingModel.PROCESS:
        # loop.set_debug(True)
        with ProcessPoolExecutor(max_workers=max_concurrent) as process_executor:
            for worker_partial in worker_partials:
                # log.debug("Get next worker_partial")
                # Create max_concurrent worker tasks to process the queue concurrently.
                future = loop.run_in_executor(
                    process_executor, worker_partial.func, *worker_partial.args
                )
                # log.debug("Got next worker_partial future")
                tasks.append(future)

                if len(tasks) >= max_concurrent:
                    task = tasks.pop(0)
                    # log.debug("awaiting future")
                    for completed_future in asyncio.as_completed([task]):
                        await completed_future
                    # await asyncio.wait([task])
                    # log.debug("completed future")
                    await asyncio.sleep(0.1)
            # log.debug("Done all worker_partials")

            for completed_future in asyncio.as_completed(tasks):
                # log.debug(f"Get as_completed on future: {completed_future}")
                await completed_future
    else:
        with ThreadPoolExecutor(max_workers=max_concurrent) as thread_executor:
            for worker_partial in worker_partials:
                # log.debug("Get next worker_partial")
                # Create max_concurrent worker tasks to process the queue concurrently.
                future = loop.run_in_executor(
                    thread_executor, worker_partial.func, *worker_partial.args
                )
                # log.debug("Got next worker_partial future")
                tasks.append(future)

                if len(tasks) >= max_concurrent:
                    task = tasks.pop(0)
                    # log.debug("awaiting future")
                    for completed_future in asyncio.as_completed([task]):
                        await completed_future
                    # await asyncio.wait([task])
                    # log.debug("completed future")
                    await asyncio.sleep(0.1)
            # log.debug("Done all worker_partials")

            for completed_future in asyncio.as_completed(tasks):
                # log.debug(f"Get as_completed on future: {completed_future}")
                await completed_future
        # for worker_partial in worker_partials:
        #     # Create a worker tasks to process the queue one by one.
        #     future = loop.run_in_executor(None, worker_partial.func, *worker_partial.args)
        #     await future

    total_processing_time = time.monotonic() - started_at
    log.debug(f"total processing time: {total_processing_time:.2f} seconds")


def generator_with_id_accumulator(
    records: Iterable[dict[str, Any]], id_accumulator: list[int], id_attr: str
) -> Generator[dict[str, Any], None, None]:
    """A generator that yields records and accumulates their IDs.
    Args:
        records (Iterable[dict[str, Any]]): An iterable of records (dictionaries).
        id_accumulator (list[int]): A list to accumulate the IDs.
        id_attr (str): The attribute name in the record that contains the ID.
    Yields:
        dict[str, Any]: The next record from the input iterable.
    """
    for record in records:
        _id = int(record[id_attr])
        id_accumulator.append(_id)
        yield record


def log_banner() -> None:
    log.info("")
    log.info("")
    log.info("##     ## ##     ##  ######  ####  ######   ########  ######## ########")
    log.info("###   ### ##     ## ##    ##  ##  ##    ##  ##     ## ##       ##      ")
    log.info("#### #### ##     ## ##        ##  ##        ##     ## ##       ##      ")
    log.info("## ### ## ##     ##  ######   ##  ##   #### ########  ######   ######  ")
    log.info("##     ## ##     ##       ##  ##  ##    ##  ##   ##   ##       ##      ")
    log.info("##     ## ##     ## ##    ##  ##  ##    ##  ##    ##  ##       ##      ")
    log.info("##     ##  #######   ######  ####  ######   ##     ## ######## ########")
    log.info("")
    log.info("")
    log.info(f"Version: {VERSION}")
    log.info("")
