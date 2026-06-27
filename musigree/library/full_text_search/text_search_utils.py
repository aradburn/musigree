"""
This module provides utility functions for full-text search operations,
specifically for normalizing text content before indexing or searching.
"""

import logging
import re

from musigree import utils

log = logging.getLogger(__name__)

SEARCH_STOP_WORDS: set[str] = {
    "the",
    "and",
    "a",
    "of",
    "studio",
    "studios",
    "productions",
    "music",
    "records",
    "recordings",
    "entertainment",
}
"""Common tokens ignored during full-text indexing and search."""


def normalise_search_content(string: str) -> str:
    """
    Normalizes a string for full-text search indexing or querying.

    This function performs the following operations:
    1. Converts the input string to lowercase.
    2. Removes all characters matching the `SEARCH_STRIP_PATTERN` from the `utils` module.
    3. Removes leading and trailing whitespace.

    Args:
        string: The string to normalize.

    Returns:
        str: The normalized string.
    """
    string = string.lower()
    string = utils.SEARCH_STRIP_PATTERN.sub("", string)
    string = re.sub(", ", " ", string)
    # No trailing commas
    string = re.sub(",\\s*$", "", string)
    # string = re.sub("-", " ", string) # DO NOT REPLACE HYPHENS
    string = re.sub(" +", " ", string)
    string = string.strip()
    return string


def remove_stop_words(input_string: str) -> str:
    """
    Remove stop words from a whitespace-delimited string.

    Each token is compared against ``SEARCH_STOP_WORDS``. Matching
    tokens are dropped; remaining tokens are joined with a single space.
    Comparison is case-sensitive, so callers should normalise text first when
    needed.

    Args:
        input_string: Space-separated tokens to filter.

    Returns:
        str: Tokens with stop words removed, or an empty string when none remain.
    """
    output_words = []
    for word in input_string.split():
        if word not in SEARCH_STOP_WORDS:
            output_words.append(word)
    return " ".join(output_words)
