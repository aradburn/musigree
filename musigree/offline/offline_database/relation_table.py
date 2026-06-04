from typing import Any

from sqlalchemy import (
    Index,
    Integer,
)
from sqlalchemy.orm import Mapped, mapped_column

from musigree import utils
from musigree.offline.offline_database.base_table import OfflineBase


class RelationTable(OfflineBase):
    """
    Represents the 'relation' table in the offline_database.

    This table stores information about the relationships between entities
    in the Musigree system. Each row in the table represents a directed
    relation between a subject entity and an object entity, with a specific
    predicate (role) describing the nature of the relation.

    Attributes:
        __tablename__ (str): The name of the table in the offline_database.
        id (Mapped[int]): The primary key of the table, an auto-incrementing integer.
        subject (Mapped[int]): The ID of the subject entity in the relation.
        predicate (Mapped[int]): The ID of the role (predicate) defining the relation.
            This is a foreign key referencing the RoleTable.
        object (Mapped[int]): The ID of the object entity in the relation.
        __table_args__ (tuple): Additional table arguments, including indexes.
    """

    __tablename__ = "relation"
    """The name of the table in the offline_database."""

    # COLUMNS

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    """The primary key of the table, an auto-incrementing integer."""
    subject: Mapped[int] = mapped_column(Integer, nullable=False)
    """The ID of the subject entity in the relation."""
    predicate: Mapped[int] = mapped_column(Integer, nullable=False)
    # predicate: Mapped[int] = mapped_column(ForeignKey(RoleTable.id))
    """The ID of the role (predicate) defining the relation.
       This is a foreign key referencing the RoleTable."""
    object: Mapped[int] = mapped_column(Integer, nullable=False)
    """The ID of the object entity in the relation."""
    release_id: Mapped[int] = mapped_column(Integer, nullable=False)
    """The ID of the release associated with this entry."""
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    """The year of the release."""

    __table_args__: tuple[Index, Index, dict[str, Any]] = (
        # Index(
        #     "idx_relation",
        #     subject,
        #     predicate,
        #     object,
        #     unique=False,
        # ),
        Index(
            "idx_relation_subject",
            subject,
            unique=False,
        ),
        Index(
            "idx_relation_object",
            object,
            unique=False,
        ),
        {},
    )
    """
    Additional table arguments, including:
        - idx_relation: A unique index on the subject, predicate, and object columns.
        - idx_relation_subject: A non-unique index on the subject column.
        - idx_relation_object: A non-unique index on the object column.
    """

    def __repr__(self) -> str:
        """
        Returns a string representation of the RelationTable object.

        The string is a normalized dictionary representation of the object's data,
        skipping specified keys.

        Returns:
            str: A normalized dictionary string representation of the object.
        """
        return utils.normalize_dict(utils.table2dict(self), skip_keys=[])
