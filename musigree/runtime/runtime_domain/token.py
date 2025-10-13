"""
This module defines the domain objects for representing countries in the Musigree runtime system.

It provides the `Country` class for handling unique country names. These names are not official names and can be whatever the entry in the Discogs database is.

"""

__all__ = [
    "Token",
]

import logging

from musigree.library.domain.base import InternalDomainObject

log = logging.getLogger(__name__)


class Token(InternalDomainObject):
    """
    Represents a token word for text searching.

    Attributes:
        token (str): The token.
        entity_id (int): The unique identifier for the corredponding entity.
    """

    token: str
    """The token."""
    entity_id: int
    """The unique identifier for the entity that has a name containing this token."""
