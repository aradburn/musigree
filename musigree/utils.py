import enum
import itertools
import json
import logging
import math
import re
import shutil
import string
import sys
import textwrap
import time
import unicodedata
from collections.abc import Mapping, Sequence, Iterator
from datetime import datetime, date
from functools import wraps
import random
from typing import List, Any, TypeVar, Dict

import requests
from dateutil.relativedelta import relativedelta
# noinspection Mypy
from toolz import count  # type: ignore
from unidecode import unidecode

log = logging.getLogger(__name__)

URLIFY_REGEX = re.compile(r"\s+", re.MULTILINE)
# ARG_ROLES_REGEX = re.compile(r"^roles(\[\d*\])?$")
STRIP_PATTERN = re.compile(r"\(\d+\)|not on label|self[ -]released|[()&\".,]")
# STRIP_PATTERN = re.compile(r"(\(\d+\)|[^(\w\s)]+)")
# REMOVE_PUNCTUATION = re.compile(r"[^\w\s]")
WORD_PATTERN = re.compile(r"\s+")
T = TypeVar("T")


class SkipFilter:
    def __init__(self, types=None, keys=None, allow_empty=False):
        self.types = tuple(types or [])
        self.keys = set(keys or [])
        self.allow_empty = allow_empty  # if True include empty filtered structures

    def filter(self, data):
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


def parse_request_args(args) -> tuple[list[str], tuple[int, int] | int | None]:
    from musigree.library.cache.role_cache import RoleCache
    from musigree.app.fastapi_ui import UI_DEFAULT_ROLES

    year: tuple[int, int] | int | None = None
    roles = set()
    for key in args:
        if key == "year":
            year_arg = args[key]
            try:
                if "-" in year_arg:
                    start, _, stop = year_arg.partition("-")
                    start_year = int(start)
                    stop_year = int(stop)
                    if start_year <= stop_year:
                        year = (start_year, stop_year)
                    else:
                        year = (stop_year, start_year)
                else:
                    year = int(year_arg)
            except ValueError:
                log.debug("Invalid year input")
            log.debug(f"Requested year: {year}")
        elif key == "roles":
            roles_arg = args[key]
            for role_arg in roles_arg:
                # List is comma-separated, roles that contain commas are escaped by a \
                unescaped_value = role_arg.replace("\\,", "|")
                for role_escaped in unescaped_value.split(","):
                    role = role_escaped.replace("|", ",")
                    # log.debug(f"Requested role: {role}")
                    if role in RoleCache.role_category_to_role_name_lookup.keys():
                        # log.debug(f"Requested role found: {role}")
                        for role_entry in RoleCache.role_category_to_role_name_lookup[
                            role
                        ]:
                            log.debug(f"Requested role_entry: {role_entry}")
                            if (
                                role_entry
                                in RoleCache.role_name_to_role_id_lookup.keys()
                            ):
                                roles.add(role_entry)
                    elif role in RoleCache.role_name_to_role_id_lookup.keys():
                        roles.add(role)

    if len(roles) == 0:
        roles = set(UI_DEFAULT_ROLES)
    roles_list = list(sorted(roles))
    # log.debug(f"Requested roles: {roles}")
    return roles_list, year


def batched(iterable: Sequence[T], n) -> Iterator[list[T]]:
    # batched('ABCDEFG', 3) → ABC DEF G
    if n < 1:
        raise ValueError("n must be at least one")
    it = iter(iterable)
    while batch := list(itertools.islice(it, n)):
        yield batch


# def iter_in_slices(iterator, size=None):
#     while True:
#         slice_iter = itertools.islice(iterator, size)
#         # If no first object this is how StopIteration is triggered
#         try:
#             peek = next(slice_iter)
#         except StopIteration:
#             return
#         # Put the first object back and return slice
#         yield itertools.chain([peek], slice_iter)


def split_list(num_chunks: int, seq: Sequence[T]) -> Iterator[list[T]]:
    num_items = count(seq)
    num_chunks = min(num_items, num_chunks)
    num_chunks = max(1, num_chunks)
    return batched(seq, math.ceil(num_items / num_chunks))


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
    if not _string.endswith("\n"):
        _string += "\n"
    return _string


# def normalize_dict(obj: Dict) -> str:
#     s = normalize(json.dumps(obj, indent=4, sort_keys=True, default=str))
#     return s


def normalize_dict(obj: Any, skip_keys=None) -> str:
    preprocessor = SkipFilter(keys=skip_keys)

    def list_public_attributes(input_var):
        return {
            k: (
                list_public_attributes(preprocessor.filter(v))
                if isinstance(v, Mapping)
                else v
            )
            for k, v in input_var.items()
            if not (k.startswith("_") or callable(v))
        }

    def default(o):
        def as_dict(self):
            return {c.name: getattr(self, c.name) for c in self.__table__.columns}

        from musigree.offline.database.base_table import Base

        if isinstance(o, Base):
            return list_public_attributes(preprocessor.filter(as_dict(o)))
        elif isinstance(o, enum.Enum):
            return str(o)
        elif isinstance(o, date):
            return str(o)
        elif isinstance(o, datetime):
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


def normalize_dict_list(list_obj: List[Dict[str, Any]]) -> str:
    def sorted_itemgetter(*items):
        if len(items) == 1:
            item = items[0]

            def g(obj):
                return obj[item]

        else:

            def g(obj):
                return tuple(obj[item_] for item_ in items)

        return g

    if list_obj is None or len(list_obj) == 0:
        return "[\n" + "\n]\n"

    dict_keys = sorted(list_obj[0].keys())
    sorted_list_obj = sorted(list_obj, key=sorted_itemgetter(*dict_keys))

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
    return "[\n" + ",\n".join(textwrap.indent(_, "    ") for _ in list_obj) + "\n]\n"


def strip_input(input_str: str) -> str:
    return textwrap.dedent(input_str).replace("\n", "", 1)


def strip_trailing_newline(input_str: str) -> str:
    return input_str.removesuffix("\n")


def row2dict(row):
    return {c.name: getattr(row, c.name) for c in row.__table__.columns}


def is_latin(_string: str) -> bool:
    try:
        return all(["LATIN" in unicodedata.name(c) for c in _string])
    except ValueError:
        return False


def to_ascii(_string: str) -> str:
    if _string is None:
        return ""
    # Transliterate the unicode string into a plain ASCII string
    if is_latin(_string):
        _string = unidecode(_string, "preserve")
    return _string


def timeit(func):
    @wraps(func)
    def timeit_wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        total_time = end_time - start_time
        log.debug(f"### TIMER ### Function {func.__name__}: {total_time:.1f} seconds")
        return result

    return timeit_wrapper


def sleep_with_backoff(multiplier: int) -> None:
    time_in_secs = int(multiplier * (1.0 + random.random()))
    if time_in_secs > 60:
        time_in_secs = 60
    if time_in_secs < 1:
        time_in_secs = 1
    # log.debug(f"sleeping for {time_in_secs} secs")
    time.sleep(time_in_secs)


def download_file(input_url: str, output_file) -> None:
    with requests.get(input_url, stream=True) as response:
        response.raise_for_status()
        shutil.copyfileobj(response.raw, output_file, length=10 * 1024)
    output_file.flush()
    output_file.close()


def get_discogs_url(dump_date: date, dump_type: str) -> str:
    from musigree.constants import DISCOGS_FILE_TEMPLATE
    from musigree.constants import DISCOGS_BASE_URL

    year = dump_date.year
    base = DISCOGS_BASE_URL.format(year=year)
    path = DISCOGS_FILE_TEMPLATE.format(
        date=dump_date.strftime("%Y%m%d"), type=dump_type
    )
    return base + path


def get_discogs_dump_dates(start_date: date, end_date: date) -> list[date]:
    date_list = []
    curr_date = start_date
    while curr_date <= end_date:
        month_date = date(year=curr_date.year, month=curr_date.month, day=1)
        date_list.append(month_date)
        curr_date += relativedelta(months=1)
    return date_list


def calculate_size(obj):
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
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))
