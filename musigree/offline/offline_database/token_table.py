from typing import Any

from sqlalchemy import String, inspect, Integer
from sqlalchemy.orm import Mapped, mapped_column

from musigree import utils
from musigree.offline.offline_database.base_table import OfflineBase


class TokenTable(OfflineBase):
    """
    Represents the 'token' table in the offline_database.

    This table stores information about tokens in the Musigree offline system.
    Each token is part of an entity's name. This table is
    designed for efficient lookup and management of tokens during offline operations.

    Attributes:
        __tablename__ (str): The name of the table in the offline_database.
        token (Mapped[str]): The token. This column is indexed for faster lookups.
        id (Mapped[int]): The id of the entity containign this token as part of the entity's name.
    """

    __tablename__ = "token"
    """The name of the table in the offline_database."""

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
        Initializes a TokenTable instance.

        This constructor allows for the initialization of a `TokenTable`
        object with keyword arguments that match the table's columns. It
        ensures that only valid column names are used during initialization.

        Args:
            entries (dict): Keyword arguments corresponding to the table's
                columns and their values.
        """
        column_names = set([column.name for column in inspect(TokenTable).columns])
        superentries = {k: entries[k] for k in column_names.intersection(entries.keys())}
        super().__init__(**superentries)

    def __repr__(self) -> str:
        """
        Returns a string representation of the TokenTable instance.

        The string is a normalized dictionary representation of the object's
        data, skipping no keys.

        Returns:
            str: A normalized dictionary string representation of the object.
        """
        return utils.normalize_dict(utils.table2dict(self), skip_keys=[])
