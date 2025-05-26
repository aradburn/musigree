from datetime import datetime

from sqlalchemy import String, TIMESTAMP, Integer, Index
from sqlalchemy.orm import Mapped, mapped_column

from musigree import utils
from musigree.offline.database.base_table import Base


class MetadataTable(Base):
    """
    Represents the 'metadata' table in the database.

    This table stores metadata information used by the Musigree system.
    It includes a unique key, a value, a timestamp, and a version ID for
    each metadata entry.

    Attributes:
        __tablename__ (str): The name of the table in the database.
        metadata_id (Mapped[int]): The primary key of the table, an auto-incrementing integer.
        version_id (Mapped[int]): An integer representing the version of the metadata entry.
        metadata_key (Mapped[str]): The unique key for the metadata entry.
        metadata_value (Mapped[str]): The value associated with the metadata key.
        metadata_timestamp (Mapped[datetime]): The timestamp indicating when the metadata was created or updated.
        __mapper_args__ (dict):  Version configuration for SQLAlchemy.
        __table_args__ (tuple): Additional table arguments including indexes.
    """

    __tablename__ = "metadata"

    # COLUMNS
    metadata_id: Mapped[int] = mapped_column(primary_key=True)
    """The primary key of the table, an auto-incrementing integer."""
    version_id: Mapped[int] = mapped_column(Integer, nullable=False)
    """An integer representing the version of the metadata entry."""
    metadata_key: Mapped[str] = mapped_column(String, nullable=False)
    """The unique key for the metadata entry."""
    metadata_value: Mapped[str] = mapped_column(String, nullable=False)
    """The value associated with the metadata key."""
    metadata_timestamp: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False)
    """The timestamp indicating when the metadata was created or updated."""

    __mapper_args__ = {"version_id_col": version_id}
    """
        Version configuration for SQLAlchemy.
        Specifies that `version_id` column should be used for versioning.
    """

    __table_args__ = (
        Index(
            "idx_metadata",
            metadata_key,
            unique=True,
        ),
        {},
    )
    """
    Additional table arguments, including:
        - idx_metadata: A unique index on the metadata_key column.
    """

    def __repr__(self):
        """
        Returns a string representation of the MetadataTable object.

        Returns:
            str: A normalized dictionary string representation of the object.
        """
        return utils.normalize_dict(utils.row2dict(self))
