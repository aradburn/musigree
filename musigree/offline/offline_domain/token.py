"""
This module defines the offline_domain objects for representing countries in the Musigree offline system.

It provides the `Token` class for handling unique country names. These names are not official names and can be whatever the entry in the Discogs offline_database is.

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
        entity_id (int): The unique identifier for the corresponding entity.
    """

    token: str
    """The token."""
    entity_id: int
    """The unique identifier for the entity that has a name containing this token."""
