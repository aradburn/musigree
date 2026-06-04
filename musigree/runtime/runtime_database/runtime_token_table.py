from typing import Any

from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column, class_mapper

from musigree import utils
from musigree.runtime.runtime_database.runtime_base_table import RuntimeBase


class RuntimeTokenTable(RuntimeBase):
    """
    Represents the 'token' table in the runtime_database.

    This table stores information about tokens in the Musigree runtime system.
    Each token is part of an entity's name. This table is
    designed for efficient lookup and management of tokens during runtime operations.

    Attributes:
        __tablename__ (str): The name of the table in the runtime_database.
        token (Mapped[str]): The token. This column is indexed for faster lookups.
        id (Mapped[int]): The id of the entity containign this token as part of the entity's name.
    """

    __tablename__ = "token"
    """The name of the table in the runtime_database."""

    # COLUMNS
    id: Mapped[int] = mapped_column(primary_key=True)

    token: Mapped[str] = mapped_column(String, index=True, unique=False, nullable=False)
    """
    The token. Indexed for faster lookup.
    """
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False)
    """
    The entity id.
    """

    def __init__(self, **entries: Any) -> None:
        """
        Initializes a RuntimeTokenTable instance.

        This constructor allows for the initialization of a `RuntimeTokenTable`
        object with keyword arguments that match the table's columns. It
        ensures that only valid column names are used during initialization.

        Args:
            entries (dict): Keyword arguments corresponding to the table's
                columns and their values.
        """
        column_names = set([column.name for column in class_mapper(RuntimeTokenTable).columns])
        superentries = {k: entries[k] for k in column_names.intersection(entries.keys())}
        super().__init__(**superentries)

    def __repr__(self) -> str:
        """
        Returns a string representation of the RuntimeTokenTable instance.

        The string is a normalized dictionary representation of the object's
        data, skipping no keys.

        Returns:
            str: A normalized dictionary string representation of the object.
        """
        return utils.normalize_dict(utils.table2dict(self), skip_keys=[])
