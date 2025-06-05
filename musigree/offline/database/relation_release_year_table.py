from sqlalchemy import (
    Index,
    Integer,
)
from sqlalchemy.orm import Mapped, mapped_column

from musigree import utils
from musigree.offline.database.base_table import Base


class RelationReleaseYearTable(Base):
    """
    Represents the 'relation_release_year' table in the database.

    This table stores information about the relationship between a relation,
    a release, and the year of that release. It's used to associate a specific
    release year with a given relation.

    Attributes:
        __tablename__ (str): The name of the table in the database.
        relation_release_year_id (Mapped[int]): The primary key of the table,
            an auto-incrementing integer.
        relation_id (Mapped[int]): The ID of the relation associated with this
            entry.
        release_id (Mapped[int]): The ID of the release associated with this
            entry.
        year (Mapped[int]): The year of the release.
        __table_args__ (tuple): Additional table arguments including indexes.
    """

    __tablename__ = "relation_release_year"
    """
    The name of the table in the database.
    """

    # COLUMNS

    relation_release_year_id: Mapped[int] = mapped_column(primary_key=True)
    """
    The primary key of the table, an auto-incrementing integer.
    """
    relation_id: Mapped[int] = mapped_column(Integer, nullable=False)
    """
    The ID of the relation associated with this entry.
    """
    release_id: Mapped[int] = mapped_column(Integer, nullable=False)
    """
    The ID of the release associated with this entry.
    """
    year: Mapped[int] = mapped_column(Integer, nullable=True)
    """
    The year of the release.
    """

    __table_args__: tuple[Index, dict]  = (
        Index(
            "idx_relation_release_year_relation_ids",
            relation_id,
            unique=False,
        ),
        {},
    )
    """
    Additional table arguments, including:
        - idx_relation_release_year_relation_ids: A non-unique index on the
          relation_id column.
    """

    def __repr__(self):
        """
        Returns a string representation of the RelationReleaseYearTable object.

        Returns:
            str: A normalized dictionary string representation of the object.
        """
        return utils.normalize_dict(utils.row2dict(self), skip_keys={})
