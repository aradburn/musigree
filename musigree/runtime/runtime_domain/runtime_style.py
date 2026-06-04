"""
This module defines the offline_domain objects for representing styles in the Musigree runtime system.

It provides the `RuntimeStyle` class for handling unique style names. These names are not official names and can be whatever the entry in the Discogs runtime_database is.

"""

__all__ = [
    "RuntimeStyle",
]

import logging

from pydantic import StrictInt

from musigree.library.domain.base import InternalDomainObject

log = logging.getLogger(__name__)


class RuntimeStyle(InternalDomainObject):
    """
    Represents a RuntimeStyle name.

    This class represents an entity within the Musigree system during runtime,
    encapsulating its properties and relationships.

    Attributes:
        id (StrictInt): The unique identifier for the style.
        style_name (str): The name of the style.
    """

    id: StrictInt
    """The unique identifier for the style."""
    style_name: str
    """The name of the style."""
