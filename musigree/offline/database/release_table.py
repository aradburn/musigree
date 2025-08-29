from sqlalchemy import String, Integer, Date, JSON
from sqlalchemy.orm import Mapped, mapped_column

from musigree import utils
from musigree.offline.database.base_table import OfflineBase


class ReleaseTable(OfflineBase):
    """
    Represents the 'release' table in the database.

    This table stores information about music releases, including details
    such as artists, companies, country of origin, extra artists, formats,
    genres, identifiers, labels, master ID, notes, release date, styles, title,
    and tracklist.

    Attributes:
        __tablename__ (str): The name of the table in the database.
        release_id (Mapped[int]): The primary key of the table, representing the
            unique identifier for the release.
        artists (Mapped[dict | list]): Information about the artists involved
            in the release. Stored as a JSON object.
        companies (Mapped[dict | list]): Information about the companies involved
            in the release (e.g., record labels, distributors). Stored as a JSON
            object.
        country (Mapped[str]): The country where the release originated.
        extra_artists (Mapped[dict | list]): Information about additional artists
            involved in the release. Stored as a JSON object.
        formats (Mapped[dict | list]): Information about the formats of the
            release (e.g., vinyl, CD, digital). Stored as a JSON object.
        genres (Mapped[dict | list]): The musical genres associated with the
            release. Stored as a JSON object.
        identifiers (Mapped[dict | list]): Various identifiers associated with
            the release (e.g., catalog numbers). Stored as a JSON object.
        labels (Mapped[dict | list]): Information about the record labels
            associated with the release. Stored as a JSON object.
        master_id (Mapped[int]): The ID of the master release this release is
            associated with, if applicable.
        notes (Mapped[str]): Additional notes about the release.
        release_date (Mapped[Date]): The date the release was published.
        styles (Mapped[dict | list]): The musical styles associated with the
            release. Stored as a JSON object.
        title (Mapped[str]): The title of the release.
        tracklist (Mapped[dict | list]): Information about the tracks included
            in the release. Stored as a JSON object.
    """

    __tablename__ = "release"
    """The name of the table in the database."""

    # COLUMNS

    release_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    """
    The primary key of the table, representing the unique identifier for the release.
    """
    artists: Mapped[dict | list] = mapped_column(type_=JSON, nullable=True)
    """
    Information about the artists involved in the release. Stored as a JSON object.
    """
    companies: Mapped[dict | list] = mapped_column(type_=JSON, nullable=True)
    """
    Information about the companies involved in the release. Stored as a JSON object.
    """
    country: Mapped[str] = mapped_column(String, nullable=True)
    """The country where the release originated."""
    extra_artists: Mapped[dict | list] = mapped_column(type_=JSON, nullable=True)
    """
    Information about additional artists involved in the release. Stored as a JSON object.
    """
    formats: Mapped[dict | list] = mapped_column(type_=JSON, nullable=True)
    """
    Information about the formats of the release. Stored as a JSON object.
    """
    genres: Mapped[dict | list] = mapped_column(type_=JSON, nullable=True)
    """The musical genres associated with the release. Stored as a JSON object."""
    identifiers: Mapped[dict | list] = mapped_column(type_=JSON, nullable=True)
    """
    Various identifiers associated with the release. Stored as a JSON object.
    """
    labels: Mapped[dict | list] = mapped_column(type_=JSON, nullable=True)
    """
    Information about the record labels associated with the release. Stored as a JSON object.
    """
    master_id: Mapped[int] = mapped_column(Integer, nullable=True)
    """
    The ID of the master release this release is associated with.
    """
    notes: Mapped[str] = mapped_column(String, nullable=True)
    """Additional notes about the release."""
    release_date: Mapped[Date] = mapped_column(Date, nullable=True)
    """The date the release was published."""
    styles: Mapped[dict | list] = mapped_column(type_=JSON, nullable=True)
    """
    The musical styles associated with the release. Stored as a JSON object.
    """
    title: Mapped[str] = mapped_column(String, nullable=True)
    """The title of the release."""
    tracklist: Mapped[dict | list] = mapped_column(type_=JSON, nullable=True)
    """
    Information about the tracks included in the release. Stored as a JSON object.
    """

    def __repr__(self) -> str:
        """
        Returns a string representation of the ReleaseTable object.

        The string is a normalized dictionary representation of the object's data,
        skipping no keys.

        Returns:
            str: A normalized dictionary string representation of the object.
        """
        return utils.normalize_dict(utils.table2dict(self), skip_keys=[])
