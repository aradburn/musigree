"""
This module defines the domain objects for representing genres in the Musigree runtime system.

It provides the `Genre` class for handling unique genre names. These names are not official names and can be whatever the entry in the Discogs database is.

"""

__all__ = [
    "Genre",
]

import logging

from musigree.library.domain.base import InternalDomainObject

log = logging.getLogger(__name__)


class Genre(InternalDomainObject):
    """
    Represents a Genre name.

    This class represents an entity within the Musigree system during runtime,
    encapsulating its properties and relationships.

    Attributes:
        id (int): The unique identifier for the genre.
        genre_name (str): The name of the genre.
    """

    id: int
    """The unique identifier for the genre."""
    genre_name: str
    """The name of the genre.""" 