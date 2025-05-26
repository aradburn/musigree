"""
This module provides utility functions for full-text search operations,
specifically for normalizing text content before indexing or searching.
"""

import logging

from musigree import utils

log = logging.getLogger(__name__)


def normalise_search_content(string: str) -> str:
    """
    Normalizes a string for full-text search indexing or querying.

    This function performs the following operations:
    1. Converts the input string to lowercase.
    2. Removes all characters matching the `STRIP_PATTERN` from the `utils` module.
    3. Removes leading and trailing whitespace.

    Args:
        string: The string to normalize.

    Returns:
        str: The normalized string.
    """
    string = string.lower()
    string = utils.STRIP_PATTERN.sub("", string)
    string = string.strip()
    return string
