"""
This module defines the offline_domain objects for representing countries in the Musigree runtime system.

It provides the `RuntimeCountry` class for handling unique country names. These names are not official names and can be whatever the entry in the Discogs runtime_database is.

"""

__all__ = [
    "RuntimeToken",
]

import logging

from pydantic import StrictInt

from musigree.library.domain.base import InternalDomainObject

log = logging.getLogger(__name__)


class RuntimeToken(InternalDomainObject):
    """
    Represents a token word for text searching.

    Attributes:
        token (str): The token.
        entity_id (StrictInt): The unique identifier for the corredponding entity.
    """

    token: str
    """The token."""
    entity_id: StrictInt
    """The unique identifier for the entity that has a name containing this token."""
