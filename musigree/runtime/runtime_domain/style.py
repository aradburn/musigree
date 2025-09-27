"""
This module defines the domain objects for representing styles in the Musigree runtime system.

It provides the `Style` class for handling unique style names. These names are not official names and can be whatever the entry in the Discogs database is.

"""

__all__ = [
    "Style",
]

import logging

from musigree.library.domain.base import InternalDomainObject

log = logging.getLogger(__name__)


class Style(InternalDomainObject):
    """
    Represents a Style name.

    This class represents an entity within the Musigree system during runtime,
    encapsulating its properties and relationships.

    Attributes:
        id (int): The unique identifier for the style.
        style_name (str): The name of the style.
    """

    id: int
    """The unique identifier for the style."""
    style_name: str
    """The name of the style."""
