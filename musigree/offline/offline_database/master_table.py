from sqlalchemy import String, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column

from musigree import utils
from musigree.offline.offline_database.base_table import OfflineBase


class MasterTable(OfflineBase):
    """
    Represents the 'master' table in the runtime_database.

    This table stores information about music masters, including details
    such as the unique identifier, title, year, main release, data quality,
    artists, genres, styles, videos, and images.

    Attributes:
        __tablename__ (str): The name of the table in the runtime_database.
        master_id (Mapped[int]): The primary key of the table, representing the
            unique identifier for the master.
        title (Mapped[str]): The title of the master.
        year (Mapped[int]): The year the master was released.
        main_release (Mapped[str]): The main release ID associated with this master.
        data_quality (Mapped[str]): The data quality indicator for this master.
        artists (Mapped[dict | list]): Information about the artists involved
            in the master. Stored as a JSON object.
        genres (Mapped[dict | list]): The musical genres associated with the
            master. Stored as a JSON object.
        styles (Mapped[dict | list]): The musical styles associated with the
            master. Stored as a JSON object.
        videos (Mapped[dict | list]): Information about videos associated with
            the master. Stored as a JSON object.
        images (Mapped[dict | list]): Information about images associated with
            the master. Stored as a JSON object.
    """

    __tablename__ = "master"
    """The name of the table in the runtime_database."""

    # COLUMNS

    master_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    """
    The primary key of the table, representing the unique identifier for the master.
    """
    title: Mapped[str] = mapped_column(String, nullable=False)
    """The title of the master."""
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    """The year the master was released."""
    main_release: Mapped[str] = mapped_column(String, nullable=False)
    """The main release ID associated with this master."""
    data_quality: Mapped[str] = mapped_column(String, nullable=False)
    """The data quality indicator for this master."""
    artists: Mapped[dict | list] = mapped_column(type_=JSON, nullable=True)
    """
    Information about the artists involved in the master. Stored as a JSON object.

    Each artist dictionary contains:
        - id (int): The artist ID
        - name (str): The artist name
        - anv (str | None): Artist name variation
        - join (str | None): Join string (e.g., ", ", " & ")
        - position (int | None): Optional position/order
        - role (str | None): Optional role
    """
    genres: Mapped[dict | list] = mapped_column(type_=JSON, nullable=True)
    """
    The musical genres associated with the master. Stored as a JSON array of strings.
    """
    styles: Mapped[dict | list] = mapped_column(type_=JSON, nullable=True)
    """
    The musical styles associated with the master. Stored as a JSON array of strings.
    """
    videos: Mapped[dict | list] = mapped_column(type_=JSON, nullable=True)
    """
    Information about videos associated with the master. Stored as a JSON object.

    Each video dictionary contains:
        - src (str): The video URI/URL
        - duration (int): Duration in seconds
        - embed (bool): Whether the video can be embedded
        - title (str): Video title
        - description (str | None): Video description
    """
    images: Mapped[dict | list] = mapped_column(type_=JSON, nullable=True)
    """
    Information about images associated with the master. Stored as a JSON object.

    Each image dictionary contains:
        - type (str): Image type
        - width (int): Image width in pixels
        - height (int): Image height in pixels
    """

    def __repr__(self) -> str:
        """
        Returns a string representation of the masterTable object.

        The string is a normalized dictionary representation of the object's data,
        skipping no keys.

        Returns:
            str: A normalized dictionary string representation of the object.
        """
        return utils.normalize_dict(utils.table2dict(self), skip_keys=[])
