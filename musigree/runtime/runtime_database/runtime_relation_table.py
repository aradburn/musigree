from sqlalchemy import (
    ForeignKey,
    Index,
    Integer,
    inspect,
)
from sqlalchemy.orm import Mapped, mapped_column

from musigree import utils
from musigree.runtime.runtime_database import RuntimeRoleTable
from musigree.runtime.runtime_database.runtime_base_table import RuntimeBase


class RuntimeRelationTable(RuntimeBase):
    """
    Represents the 'runtime_relation' table in the database.

    This table stores information about relationships between entities
    in the Musigree runtime system. Each row in the table represents
    a directed relationship between a subject entity and an object entity,
    with a specific predicate (role) defining the nature of the relationship.

    Attributes:
        __tablename__ (str): The name of the table in the database.
        id (Mapped[int]): The primary key of the table, an auto-incrementing
            integer representing the unique identifier for the relation.
        subject (Mapped[int]): The ID of the subject entity in the relation.
        predicate (Mapped[int]): The ID of the role (predicate) defining the
            relation. This is a foreign key referencing the RuntimeRoleTable.
        object (Mapped[int]): The ID of the object entity in the relation.
        __table_args__ (tuple): Additional table arguments, including indexes.
            - idx_runtime_relation_subject: A non-unique index on the subject column.
            - idx_runtime_relation_object: A non-unique index on the object column.
    """

    __tablename__ = "runtime_relation"
    """The name of the table in the database."""

    # COLUMNS

    id: Mapped[int] = mapped_column(primary_key=True)
    """
    The primary key of the table, an auto-incrementing integer representing
    the unique identifier for the relation.
    """
    subject: Mapped[int] = mapped_column(Integer)
    """The ID of the subject entity in the relation."""
    predicate: Mapped[int] = mapped_column(ForeignKey(RuntimeRoleTable.id))
    """
    The ID of the role (predicate) defining the relation. This is a foreign key
    referencing the RuntimeRoleTable.
    """
    object: Mapped[int] = mapped_column(Integer)
    """The ID of the object entity in the relation."""

    __table_args__ = (
        Index(
            "idx_runtime_relation_subject",
            subject,
            unique=False,
        ),
        Index(
            "idx_runtime_relation_object",
            object,
            unique=False,
        ),
        {},
    )
    """
    Additional table arguments, including:
        - idx_runtime_relation_subject: A non-unique index on the subject column.
        - idx_runtime_relation_object: A non-unique index on the object column.
    """

    def __init__(self, **entries):
        """
        Initializes a RuntimeRelationTable instance.

        This constructor allows for the initialization of a `RuntimeRelationTable`
        object with keyword arguments that match the table's columns. It ensures
        that only valid column names are used during initialization.

        Args:
            entries (dict): Keyword arguments corresponding to the table's
                columns and their values.
        """
        column_names = set(
            [column.name for column in inspect(RuntimeRelationTable).columns]
        )
        superentries = {
            k: entries[k] for k in column_names.intersection(entries.keys())
        }
        super().__init__(**superentries)

    def __repr__(self):
        """
        Returns a string representation of the RuntimeRelationTable instance.

        The string is a normalized dictionary representation of the object's
        data, skipping no keys.

        Returns:
            str: A normalized dictionary string representation of the object.
        """
        return utils.normalize_dict(utils.row2dict(self), skip_keys={})
