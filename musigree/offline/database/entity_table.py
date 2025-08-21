from sqlalchemy import String, JSON, Index, Integer
from sqlalchemy.orm import Mapped, mapped_column

from musigree import utils
from musigree.offline.database.base_table import OfflineBase
from musigree.library.fields.entity_type import EntityType
from musigree.library.fields.int_enum import IntEnum


class EntityTable(OfflineBase):
    """
    Represents the 'entity' table in the database.

    This table stores information about entities in the Musigree system,
    including artists and labels. It contains various attributes such as
    the entity's ID, type, name, relation counts, metadata, associated entities,
    and content used for search operations.

    Attributes:
        __tablename__ (str): The name of the table in the database.
        id (Mapped[int]): The primary key of the table, an auto-incrementing integer.
        entity_id (Mapped[int]): The external ID of the entity (e.g., from Discogs).
        entity_type (Mapped[EntityType]): The type of the entity (Artist or Label).
        entity_name (Mapped[str]): The name of the entity.
        relation_counts (Mapped[dict | list]): Counts of relations to other entities.
        entity_metadata (Mapped[dict | list]): Additional metadata about the entity.
        entities (Mapped[dict | list]): Information about related entities.
        search_content (Mapped[str]): Content used for full-text search operations.
        __table_args__ (tuple): Additional table arguments including indexes.
    """

    __tablename__ = "entity"

    # COLUMNS

    id: Mapped[int] = mapped_column(primary_key=True)
    """
     The primary key of the table, an auto-incrementing integer.
    """
    entity_id: Mapped[int] = mapped_column(Integer)
    """
    The external ID of the entity (e.g., from Discogs).
    """
    entity_type: Mapped[EntityType] = mapped_column(IntEnum(EntityType), nullable=False)
    """
     The type of the entity (Artist or Label).
    """
    entity_name: Mapped[str] = mapped_column(String, index=True, nullable=False)
    """
     The name of the entity.
    """
    relation_counts: Mapped[dict | list] = mapped_column(type_=JSON, nullable=True)
    """
      Counts of relations to other entities.
    """
    entity_metadata: Mapped[dict | list] = mapped_column(type_=JSON, nullable=False)
    """
     Additional metadata about the entity.
    """
    entities: Mapped[dict | list] = mapped_column(type_=JSON, nullable=False)
    """
     Information about related entities.
    """
    search_content: Mapped[str] = mapped_column(String, nullable=False)
    """
     Content used for full-text search operations.
    """

    __table_args__: tuple[Index, Index, dict] = (
        Index(
            "idx_entity_id_and_entity_type",
            entity_id,
            entity_type,
            unique=True,
        ),
        Index(
            "idx_entity_name_and_entity_type",
            entity_name,
            entity_type,
            unique=False,
        ),
        {},
    )
    """
    Additional table arguments, including:
        - idx_entity_id_and_entity_type: A unique index on the entity_id and entity_type columns.
        - idx_entity_name_and_entity_type: A non-unique index on the entity_name and entity_type columns.
    """

    def __repr__(self) -> str:
        """
        Returns a string representation of the EntityTable object.

        The string is a normalized dictionary representation of the object's data,
        skipping specified keys.

        Returns:
            str: A normalized dictionary string representation of the object.
        """
        return utils.normalize_dict(utils.table2dict(self), skip_keys=[])
