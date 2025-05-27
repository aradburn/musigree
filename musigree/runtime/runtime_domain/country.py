"""
This module defines the domain objects for representing countries in the Musigree runtime system.

It provides the `Country` class for handling unique country names. These names are not official names and can be whatever the entry in the Discogs database is.

"""

__all__ = [
    "Country",
]

import logging

from musigree.library.domain.base import InternalDomainObject

log = logging.getLogger(__name__)


class Country(InternalDomainObject):
    """
    Represents a Country name.

    This class represents an entity within the Musigree system during runtime,
    encapsulating its properties and relationships.

    Attributes:
        id (int): The unique identifier for the country.
        country_name (str): The name of the country.
    """

    id: int
    """The unique identifier for the country."""
    country_name: str
    """The name of the country."""
