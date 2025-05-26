"""
This module defines the domain objects for representing the relationship between a relation,
a release, and a year in the Musigree system.

It provides classes for handling relation-release-year pairs, including their
representation in various stages, such as before database persistence
(`RelationReleaseYearUncommitted`), after database persistence
(`RelationReleaseYearDB`), and for public consumption (`RelationReleaseYear`).

Key functionalities include:
    - Representing a relation-release-year pair with attributes like relation ID,
      release ID, and year.
    - Providing a separate class for relation-release-year pairs before they are
      committed to the database (`RelationReleaseYearUncommitted`).
    - Managing relation-release-year pairs with an ID after they are stored in
      the database (`RelationReleaseYearDB`, `RelationReleaseYear`).
    - Converting relation-release-year pairs between different representations
      (e.g., from `RelationReleaseYearDB` to `RelationReleaseYear`).
"""

import logging

from musigree.library.domain.base import InternalDomainObject

__all__ = [
    "RelationReleaseYearUncommitted",
    "RelationReleaseYearDB",
    "RelationReleaseYear",
]

log = logging.getLogger(__name__)


class _RelationReleaseYearBase(InternalDomainObject):
    """
    Base class for relation release year entities.

    This class defines the common attributes shared by all relation-release-year
    entities in the Musigree system. It provides a structure for associating
    a relation with a release and a specific year.

    Attributes:
        relation_id (int): The ID of the relation. This is a foreign key
            referencing the `relation` table.
        release_id (int): The ID of the release. This is a foreign key
            referencing the `release` table.
        year (int | None): The release year, if available. This is the year
            in which the release was published. It can be None if the year is unknown.
    """

    relation_id: int
    """The ID of the relation."""
    release_id: int
    """The ID of the release."""
    year: int | None = None
    """The release year, if available."""


class RelationReleaseYearUncommitted(_RelationReleaseYearBase):
    """
    This schema is used for creating an instance without an id before it is persisted into the database.

    This class represents a relation-release-year pair that has not yet been
    stored in the database. It inherits attributes from `_RelationReleaseYearBase`
    and is used as a data structure for new relation-release-year entries
    before they are assigned a unique ID by the database.
    """

    pass


class RelationReleaseYearDB(_RelationReleaseYearBase):
    """
    Saved RelationReleaseYear representation, database internal representation.

    This class represents a relation-release-year pair that has been stored in
    the database. It inherits attributes from `_RelationReleaseYearBase` and
    adds a unique ID to track the entry in the database.

    Attributes:
        relation_release_year_id (int): The unique identifier for the relation release year.
            This is assigned by the database when the relation-release-year pair is stored.
    """

    relation_release_year_id: int
    """The unique identifier for the relation release year."""

    def to_domain(self) -> "RelationReleaseYear":
        """
        Converts the RelationReleaseYearDB instance to a RelationReleaseYear instance.

        This method converts the internal database representation of a
        relation-release-year pair to its public-facing domain representation.

        Returns:
            RelationReleaseYear: The domain representation of the relation release year.
        """
        relation_release_year_db_dict: dict = self.model_dump()
        return RelationReleaseYear.model_validate(relation_release_year_db_dict)


class RelationReleaseYear(_RelationReleaseYearBase):
    """
    Domain RelationReleaseYear representation, public facing.

    This class represents the public-facing domain representation of a
    relation-release-year pair. It inherits attributes from `_RelationReleaseYearBase`
    and adds a unique ID to identify the entry.

    Attributes:
        relation_release_year_id (int): The unique identifier for the relation release year.
    """

    relation_release_year_id: int
    """The unique identifier for the relation release year."""
