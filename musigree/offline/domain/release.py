"""
This module defines the domain object for representing a music release in the Musigree system.

It provides the `Release` class, which encapsulates all the information related
to a particular music release, such as its unique identifier, artists,
companies, country of origin, genres, labels, and tracklist.

Key functionalities include:
    - Representing a music release with comprehensive details.
    - Providing a structured way to access release information.
    - Defining methods for converting between domain and database representations.
"""

__all__ = [
    "Release",
]

from datetime import date
from typing import Any, Self

from musigree.library.domain.base import InternalDomainObject


class Release(InternalDomainObject):
    """
    Represents a music release.

    This class encapsulates all the information related to a music release,
    including its unique identifier, contributing artists, associated
    companies, country of origin, and tracklist.

    Attributes:
        release_id (int): The unique identifier for the release. This is
            typically an external ID from a source like Discogs.
        artists (list[dict[str, Any]] | None): A list of artists associated
            with the release. Each item in the list is a dictionary containing
            details about an artist.
        companies (list[dict[str, Any]] | None): A list of companies associated
            with the release, such as record labels or distributors. Each item
            is a dictionary containing details about a company.
        country (str | None): The country where the release was made.
        extra_artists (list[dict[str, Any]] | None): A list of additional
            artists associated with the release, beyond the main artists. Each
            item is a dictionary with details about an extra artist.
        formats (list[dict[str, Any]] | None): A list of formats in which the
            release is available (e.g., vinyl, CD, digital). Each item is a
            dictionary describing a format.
        genres (list[str] | None): A list of genres associated with the release.
        identifiers (list[dict[str, Any]] | None): A list of identifiers for
            the release, such as catalog numbers or barcodes. Each item is a
            dictionary with identifier details.
        labels (list[dict[str, Any]] | None): A list of labels associated with
            the release. Each item is a dictionary with details about a label.
        master_id (int | None): The master ID of the release, if it is part
            of a master release.
        notes (str | None): Additional notes about the release.
        release_date (date | None): The release date.
        styles (list[str] | None): A list of styles associated with the release.
        title (str): The title of the release.
        tracklist (list[dict[str, Any]] | None): The tracklist of the release.
            Each item is a dictionary describing a track.
    """

    release_id: int
    """The unique identifier for the release."""
    artists: list[dict[str, Any]] | None = None
    """A list of artists associated with the release."""
    companies: list[dict[str, Any]] | None = None
    """A list of companies associated with the release."""
    country: str | None = None
    """The country where the release was made."""
    extra_artists: list[dict[str, Any]] | None = None
    """A list of additional artists associated with the release."""
    formats: list[dict[str, Any]] | None = None
    """A list of formats in which the release is available."""
    genres: list[str] | None = None
    """A list of genres associated with the release."""
    identifiers: list[dict[str, Any]] | None = None
    """A list of identifiers for the release."""
    labels: list[dict[str, Any]] | None = None
    """A list of labels associated with the release."""
    master_id: int | None = None
    """The master ID of the release."""
    notes: str | None = None
    """Additional notes about the release."""
    release_date: date | None = None
    """The release date."""
    styles: list[str] | None = None
    """A list of styles associated with the release."""
    title: str
    """The title of the release."""
    tracklist: list[dict[str, Any]] | None = None
    """The tracklist of the release."""

    def to_domain(self) -> Self:
        """
        Converts the release to its domain representation.

        In this implementation, the domain and database representations are
        the same, so this method returns the instance itself.

        Returns:
            Self: The domain representation of the release.
        """
        # Domain and Database entities are the same
        return self

    def to_db(self) -> Self:
        """
        Converts the release to its database representation.

        In this implementation, the domain and database representations are
        the same, so this method returns the instance itself.

        Returns:
            Self: The database representation of the release.
        """
        # Domain and Database entities are the same
        return self
