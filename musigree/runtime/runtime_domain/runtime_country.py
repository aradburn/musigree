"""
This module defines the offline_domain objects for representing countries in the Musigree runtime system.

It provides the `RuntimeCountry` class for handling unique country names. These names are not official names and can be whatever the entry in the Discogs runtime_database is.

"""

__all__ = [
    "RuntimeCountry",
]

import logging

from pydantic import StrictInt

from musigree.library.domain.base import InternalDomainObject

log = logging.getLogger(__name__)


class RuntimeCountry(InternalDomainObject):
    """
    Represents a RuntimeCountry name.

    This class represents an entity within the Musigree system during runtime,
    encapsulating its properties and relationships.

    Attributes:
        id (int): The unique identifier for the country.
        country_name (str): The name of the country.
    """

    id: StrictInt
    """The unique identifier for the country."""
    country_name: str
    """The name of the country."""
