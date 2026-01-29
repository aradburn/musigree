"""
This module defines the offline_domain objects for representing genres in the Musigree runtime system.

It provides the `RuntimeGenre` class for handling unique genre names. These names are not official names and can be whatever the entry in the Discogs runtime_database is.

"""

__all__ = [
    "RuntimeGenre",
]

import logging

from musigree.library.domain.base import InternalDomainObject

log = logging.getLogger(__name__)


class RuntimeGenre(InternalDomainObject):
    """
    Represents a RuntimeGenre name.

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
