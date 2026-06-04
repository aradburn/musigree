from typing import Any

from sqlalchemy import String, Index, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, class_mapper

from musigree import utils
from musigree.library.fields.entity_type import EntityType
from musigree.library.fields.int_enum import IntEnum
from musigree.runtime.runtime_database.runtime_base_table import RuntimeBase


class RuntimeEntityTable(RuntimeBase):
    """
    Represents the 'runtime_entity' table in the runtime_database.

    This table stores information about entities within the Musigree system,
    such as artists and labels, optimized for runtime operations. It includes
    various attributes for describing and categorizing entities, along with
    relationships to other entities.

    Attributes:
        __tablename__ (str): The name of the table in the runtime_database.
        id (Mapped[int]): The primary key, a unique identifier for the runtime entity.
        entity_id (Mapped[int]): The external ID of the entity (e.g., from Discogs).
        entity_type (Mapped[EntityType]): The type of the entity (e.g., ARTIST, LABEL).
        entity_name (Mapped[str]): The name of the entity.
        relation_counts (Mapped[dict | list]): A dictionary or list representing
            the counts of various relationships the entity has. Stored as JSON.
        entity_metadata (Mapped[dict | list]): Metadata associated with the entity.
             Stored as JSON.
        aliases (Mapped[dict | list]): Alternative names or aliases for the entity.
             Stored as JSON.
        groups (Mapped[dict | list]): Groups the entity is part of. Stored as JSON.
        members (Mapped[dict | list]): Members associated with the entity (e.g.,
            members of a band). Stored as JSON.
        countries (Mapped[str]): Countries associated with the entity.
        genres (Mapped[str]): Genres associated with the entity.
        styles (Mapped[str]): Styles associated with the entity.
        __table_args__ (tuple): Additional table arguments, including indexes.
    """

    __tablename__ = "runtime_entity"
    """The name of the table in the runtime_database."""

    # COLUMNS

    id: Mapped[int] = mapped_column(primary_key=True)
    """The primary key, a unique identifier for the runtime entity."""
    entity_id: Mapped[int] = mapped_column(Integer)
    """The external ID of the entity (e.g., from Discogs)."""
    entity_type: Mapped[EntityType] = mapped_column(IntEnum(EntityType), nullable=False)
    """The type of the entity (e.g., ARTIST, LABEL)."""
    entity_name: Mapped[str] = mapped_column(String, nullable=False)
    """The name of the entity."""
    relation_counts: Mapped[dict[str, Any]] = mapped_column(type_=JSON, nullable=True)
    """
    A dictionary representing the counts of various relationships the entity has.
    Stored as JSON.
    """
    entity_metadata: Mapped[dict[str, Any]] = mapped_column(type_=JSON, nullable=False)
    """Metadata associated with the entity. Stored as JSON."""
    aliases: Mapped[dict[str, Any]] = mapped_column(type_=JSON, nullable=True)
    """Alternative names or aliases for the entity. Stored as JSON."""
    groups: Mapped[dict[str, Any]] = mapped_column(type_=JSON, nullable=True)
    """Groups the entity is part of. Stored as JSON."""
    members: Mapped[dict[str, Any]] = mapped_column(type_=JSON, nullable=True)
    """Members associated with the entity (e.g., members of a band). Stored as JSON."""
    parent_label: Mapped[dict[str, Any]] = mapped_column(type_=JSON, nullable=True)
    """Parent label associated with the entity. Stored as JSON."""
    countries: Mapped[str] = mapped_column(String, nullable=True)
    """Countries associated with the entity."""
    genres: Mapped[str] = mapped_column(String, nullable=True)
    """Genres associated with the entity."""
    styles: Mapped[str] = mapped_column(String, nullable=True)
    """Styles associated with the entity."""

    __table_args__: tuple[Index, dict] = (
        Index(
            "idx_runtime_entity_id_and_entity_type",
            entity_id,
            entity_type,
            unique=True,
        ),
        {},
    )
    """
    Additional table arguments, including:
        - idx_runtime_entity_id_and_entity_type: A unique index on the entity_id and
          entity_type columns.
    """

    def __init__(self, **entries: Any) -> None:
        """
        Initializes a RuntimeEntityTable instance.

        This constructor allows for the initialization of a `RuntimeEntityTable`
        object with keyword arguments that match the table's columns. It
        ensures that only valid column names are used during initialization.

        Args:
            entries (dict): Keyword arguments corresponding to the table's
                columns and their values.
        """
        column_names = set([column.name for column in class_mapper(RuntimeEntityTable).columns])
        superentries = {k: entries[k] for k in column_names.intersection(entries.keys())}
        super().__init__(**superentries)

    def __repr__(self) -> str:
        """
        Returns a string representation of the RuntimeEntityTable instance.

        The string is a normalized dictionary representation of the object's
        data, skipping no keys.

        Returns:
            str: A normalized dictionary string representation of the object.
        """
        return utils.normalize_dict(utils.table2dict(self), skip_keys=[])
