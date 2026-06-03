"""
This module defines the offline_domain object for representing a master record of releases in the Musigree system.

It provides the `Master` class, which encapsulates all the information related
to multiple music releases, such as its unique identifier, artists, genres,
styles, videos, and images.

Key functionalities include:
    - Representing a music master record with comprehensive details.
    - Providing a structured way to access master information.
    - Defining methods for converting between offline_domain and runtime_database representations.
"""

__all__ = [
    "Master",
]

from typing import Any, Self

from pydantic import StrictInt

from musigree.library.domain.base import InternalDomainObject


class Master(InternalDomainObject):
    """
    Represents a music master record.

    This class encapsulates all the information related to multiple music releases,
    including its unique identifier, contributing artists, genres, styles, videos,
    and images.

    Attributes:
        master_id (StrictInt): The unique identifier for this master record. This is
            typically an external ID from a source like Discogs.
        title (str): The title of the master record.
        year (int): The year the master record was released.
        main_release (str): The main release ID associated with this master.
        data_quality (str): The data quality indicator for this master record.
        artists (list[dict[str, Any]] | None): A list of artists associated
            with the master. Each item contains id, name, anv (artist name
            variation), join (join string), and optionally position and role.
        genres (list[str] | None): A list of genres associated with the master.
        styles (list[str] | None): A list of styles associated with the master.
        videos (list[dict[str, Any]] | None): A list of videos associated with
            the master. Each item contains src (URI), duration, embed (boolean),
            title, and description.
        images (list[dict[str, Any]] | None): A list of images associated with
            the master. Each item contains type, width, and height.
    """

    # 'master': 'id title year main_release data_quality',
    # 'master_artist': 'master_id artist_id artist_name anv position join_string role',
    # 'master_video': 'master_id duration title description uri',
    # 'master_genre': 'master_id genre',
    # 'master_style': 'master_id style',
    # 'master_image': 'master_id type width height',

    master_id: StrictInt
    """The unique identifier for the master record."""
    title: str
    """The title of the master record."""
    year: StrictInt
    """The year the master record was released."""
    main_release: str
    """The main release ID associated with this master."""
    data_quality: str
    """The data quality indicator for this master record."""
    artists: list[dict[str, Any]] | None = None
    """
    A list of artists associated with the master.

    Each artist dictionary contains:
        - id (int): The artist ID
        - name (str): The artist name
        - anv (str | None): Artist name variation
        - join (str | None): Join string (e.g., ", ", " & ")
        - position (int | None): Optional position/order
        - role (str | None): Optional role
    """
    genres: list[str] | None = None
    """A list of genres associated with the master."""
    styles: list[str] | None = None
    """A list of styles associated with the master."""
    videos: list[dict[str, Any]] | None = None
    """
    A list of videos associated with the master.

    Each video dictionary contains:
        - src (str): The video URI/URL
        - duration (int): Duration in seconds
        - embed (bool): Whether the video can be embedded
        - title (str): Video title
        - description (str | None): Video description
    """
    images: list[dict[str, Any]] | None = None
    """
    A list of images associated with the master.

    Each image dictionary contains:
        - type (str): Image type
        - width (int): Image width in pixels
        - height (int): Image height in pixels
    """

    def to_domain(self) -> Self:
        """
        Converts the master to its offline_domain representation.

        In this implementation, the offline_domain and runtime_database representations are
        the same, so this method returns the instance itself.

        Returns:
            Self: The offline_domain representation of the master.
        """
        # Domain and Database entities are the same
        return self

    def to_db(self) -> Self:
        """
        Converts the master to its runtime_database representation.

        In this implementation, the offline_domain and runtime_database representations are
        the same, so this method returns the instance itself.

        Returns:
            Self: The runtime_database representation of the master.
        """
        # Domain and Database entities are the same
        return self
