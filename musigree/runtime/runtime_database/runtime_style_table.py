from typing import Any

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, class_mapper

from musigree import utils
from musigree.runtime.runtime_database.runtime_base_table import RuntimeBase


class RuntimeStyleTable(RuntimeBase):
    """
    Represents the 'style' table in the runtime_database.

    This table stores information about styles in the Musigree runtime system.
    Each style has a name. This table is
    designed for efficient lookup and management of styles during runtime
    operations.

    Attributes:
        __tablename__ (str): The name of the table in the runtime_database.
        id (Mapped[int]): The primary key of the table, an auto-incrementing
            integer representing the unique identifier for the runtime style.
        style_name (Mapped[str]): The name of the style (e.g., 'Electronic', 'Rock'). This column is indexed for faster lookups.
    """

    __tablename__ = "style"
    """The name of the table in the runtime_database."""

    # COLUMNS

    id: Mapped[int] = mapped_column(primary_key=True)
    """
    The primary key of the table, an auto-incrementing integer representing
    the unique identifier for the runtime style.
    """
    style_name: Mapped[str] = mapped_column(String, index=True, unique=True, nullable=False)
    """
    The name of the style (e.g., 'Electronic', 'Rock'). Indexed for faster lookup.
    """

    def __init__(self, **entries: Any) -> None:
        """
        Initializes a RuntimeStyleTable instance.

        This constructor allows for the initialization of a `RuntimeStyleTable`
        object with keyword arguments that match the table's columns. It
        ensures that only valid column names are used during initialization.

        Args:
            entries (dict): Keyword arguments corresponding to the table's
                columns and their values.
        """
        column_names = set([column.name for column in class_mapper(RuntimeStyleTable).columns])
        superentries = {k: entries[k] for k in column_names.intersection(entries.keys())}
        super().__init__(**superentries)

    def __repr__(self) -> str:
        """
        Returns a string representation of the RuntimeStyleTable instance.

        The string is a normalized dictionary representation of the object's
        data, skipping no keys.

        Returns:
            str: A normalized dictionary string representation of the object.
        """
        return utils.normalize_dict(utils.table2dict(self), skip_keys=[])
