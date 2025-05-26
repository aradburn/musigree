"""
This module defines the domain objects for handling metadata within the Musigree system.

It provides the `MetadataUncommitted` and `Metadata` classes for representing
metadata entries. The module also includes a base class `_MetadataBase` that
defines common attributes and methods for all metadata entities.

Key functionalities include:
    - Representing metadata with a key, value, and timestamp.
    - Providing a separate class for metadata before it's committed to the
      database (`MetadataUncommitted`).
    - Managing metadata with an ID and version information after it's stored
      in the database (`Metadata`).
    - Converting metadata objects between domain and database representations.
"""

__all__ = [
    "MetadataUncommitted",
    "Metadata",
]

import logging
from datetime import datetime
from typing import Self

from musigree.library.domain.base import InternalDomainObject

log = logging.getLogger(__name__)


class _MetadataBase(InternalDomainObject):
    """
    Base class for metadata entities.

    This class defines the common attributes shared by all metadata entities
    in the Musigree system. It provides a structure for metadata entries
    with a key, value, and timestamp.

    Attributes:
        metadata_key (str): The key of the metadata. This is used to uniquely
            identify the metadata entry.
        metadata_value (str): The value of the metadata. This is the data
            associated with the metadata key.
        metadata_timestamp (datetime): The timestamp when the metadata was
            created or updated. This records the time of the metadata event.
    """

    metadata_key: str
    """The key of the metadata."""
    metadata_value: str
    """The value of the metadata."""
    metadata_timestamp: datetime
    """The timestamp when the metadata was created or updated."""


class MetadataUncommitted(_MetadataBase):
    """
    Schema used for creating an instance without an ID before it is persisted into the database.

    This class represents metadata that has not yet been stored in the database.
    It inherits attributes from `_MetadataBase` and is used as a data structure
    for new metadata entries before they are assigned a unique ID by the database.
    """

    pass


class Metadata(_MetadataBase):
    """
    Metadata entity that includes an ID and version information.

    This class represents metadata that has been stored in the database. It
    inherits attributes from `_MetadataBase` and adds a unique ID and version
    information to track the metadata entry in the database.

    Attributes:
        metadata_id (int): The unique identifier for the metadata. This is
            assigned by the database when the metadata is stored.
        version_id (int): The version of the metadata, default is 1. This
            can be used to track updates to the metadata over time.
    """

    metadata_id: int
    """The unique identifier for the metadata."""
    version_id: int = 1
    """The version of the metadata, default is 1."""

    def to_domain(self) -> Self:
        """
        Converts the metadata to its domain representation.

        This method currently returns itself, indicating that the database
        representation is the same as the domain representation. It could be
        overridden in the future if a more complex conversion is needed.

        Returns:
            Self: The domain representation of the metadata.
        """
        return self

    def to_db(self) -> Self:
        """
        Converts the metadata to its database representation.

        This method currently returns itself, indicating that the domain
        representation is the same as the database representation. It could
        be overridden in the future if a more complex conversion is needed.

        Returns:
            Self: The database representation of the metadata.
        """
        return self
