"""
This module defines the domain objects for representing entities in the Musigree runtime system.

It provides the `RuntimeEntity` and `RuntimeEntityDB` classes for handling
entities, their attributes, and their representation in different stages, such
as before and after database persistence.

Key functionalities include:
    - Representing entities with attributes like ID, external ID, type, name,
      relation counts, metadata, and related entities.
    - Providing a separate class for the database representation of entities
      (`RuntimeEntityDB`).
    - Managing entity attributes like aliases, groups, members, countries,
      genres, and styles.
    - Converting entities between domain and database representations
      (`RuntimeEntity.to_db`, `RuntimeEntityDB.to_domain`).
    - Generating JSON-compatible entity keys.
    - Calculating entity size based on related members or sublabels.
"""

__all__ = [
    "RuntimeEntity",
    "RuntimeEntityDB",
    "to_runtime_entity_dict",
]

import logging
from typing import Any

from pydantic import Field, field_serializer

from musigree.library.domain.base import InternalDomainObject
from musigree.library.fields.entity_type import EntityType
from musigree.offline.domain.entity import Entity
from musigree.runtime.data_access_layer.entity_details_index import EntityDetailsIndex

log = logging.getLogger(__name__)


class RuntimeEntity(InternalDomainObject):
    """
    Represents a runtime entity.

    This class represents an entity within the Musigree system during runtime,
    encapsulating its properties and relationships.

    Attributes:
        id (int): The unique identifier for the runtime entity.
        entity_id (int): The ID of the entity, typically an external ID
            from a source like Discogs.
        entity_type (EntityType): The type of the entity (e.g., ARTIST, LABEL).
        entity_name (str): The name of the entity.
        relation_counts (dict[str, int]): The relation counts of the entity.
            This is a dictionary of relation names and their counts.
        entity_metadata (dict[str, Any]): The metadata of the entity, stored as
            a dictionary of metadata entries.
        entities (dict[str, Any]): The entities related to this entity, such as
            aliases, groups, members, or sublabels.
        countries (str | None): The countries associated with the entity.
        genres (str | None): The genres associated with the entity.
        styles (str | None): The styles associated with the entity.
    """

    id: int
    """The unique identifier for the runtime entity."""
    entity_id: int
    """The ID of the entity."""
    entity_type: EntityType
    """The type of the entity."""
    entity_name: str
    """The name of the entity."""
    relation_counts: dict[str, int]
    """The relation counts of the entity."""
    entity_metadata: dict[str, Any]
    """The metadata of the entity."""
    entities: dict[str, Any] = Field(default_factory=dict)
    """The entities related to this entity."""
    countries: str | None
    """The countries associated with the entity."""
    genres: str | None
    """The genres associated with the entity."""
    styles: str | None
    """The styles associated with the entity."""

    @field_serializer("entity_type", when_used="json")
    def serialize_entity_type(self, entity_type: EntityType) -> str:
        """Serialize EntityType to its name for JSON compatibility."""
        return entity_type.name

    @property
    def entity_key(self) -> tuple[int, EntityType]:
        """
        Returns the key for the entity.

        The entity key is a tuple consisting of the entity ID and entity type.

        Returns:
            tuple[int, EntityType]: The key for the entity.
        """
        return self.entity_id, self.entity_type

    @property
    def json_entity_key(self) -> str:
        """
        Returns the JSON representation of the entity key.

        This is a string representation of the entity key, suitable for use
        in JSON-formatted data.

        Returns:
            str: The JSON entity key for the entity.
        """
        return self.to_json_entity_key(self.entity_id, self.entity_type)

    @property
    def size(self) -> int:
        """
        Returns the size of the entity.

        The size is determined by the number of members (for artists) or
        sublabels (for labels) associated with the entity.

        Returns:
            int: The size of the entity.
        """
        members = []
        if isinstance(self.entities, dict):
            if self.entity_type == EntityType.ARTIST:
                members = self.entities.get("members", [])
            elif self.entity_type == EntityType.LABEL:
                members = self.entities.get("sublabels", [])
        return len(members)

    @staticmethod
    def to_json_entity_key(entity_id: int, entity_type: EntityType) -> str:
        """
        Converts the entity ID and type to a JSON entity key.

        Args:
            entity_id (int): The ID of the entity.
            entity_type (EntityType): The type of the entity.

        Returns:
            str: The JSON entity key.

        Raises:
            ValueError: If the entity type is not recognized.
        """
        if entity_type == EntityType.ARTIST:
            return f"artist-{entity_id}"
        elif entity_type == EntityType.LABEL:
            return f"label-{entity_id}"
        # noinspection PyUnreachableCode
        raise ValueError(entity_id, entity_type)

    def to_db(self) -> "RuntimeEntityDB":
        """
        Converts the runtime entity to its database representation.

        This method prepares the `RuntimeEntity` instance for storage in the
        database by transforming its attributes into the format expected by
        the database schema (`RuntimeEntityDB`).

        Returns:
            RuntimeEntityDB: The database representation of the runtime entity.
        """
        entity_dict: dict = self.model_dump()
        entities: dict = entity_dict.get("entities", {})
        # noinspection PyUnreachableCode
        aliases: dict | None = entities.get("aliases", None) if isinstance(entities, dict) else None
        # noinspection PyUnreachableCode
        groups: dict | None = entities.get("groups", None) if isinstance(entities, dict) else None
        # noinspection PyUnreachableCode
        members: dict | None = entities.get("members", None) if isinstance(entities, dict) else None
        # noinspection PyUnreachableCode
        parent_label: dict | None = (
            entities.get("parent_label", None) if isinstance(entities, dict) else None
        )
        if aliases is not None and len(aliases) == 0:
            aliases = None
        if groups is not None and len(groups) == 0:
            groups = None
        if members is not None and len(members) == 0:
            members = None
        if parent_label is not None and len(parent_label) == 0:
            parent_label = None
        entity_dict.update(
            aliases=aliases, groups=groups, members=members, parent_label=parent_label
        )
        return RuntimeEntityDB.model_validate(entity_dict)


class RuntimeEntityDB(InternalDomainObject):
    """
    Represents a runtime entity in the database.

    This class represents an entity as it is stored in the runtime database,
    including its attributes and relationships.

    Attributes:
        id (int): The unique identifier for the runtime entity.
        entity_id (int): The ID of the entity.
        entity_type (EntityType): The type of the entity.
        entity_name (str): The name of the entity.
        relation_counts (dict | list): The relation counts of the entity.
        entity_metadata (dict | list): The metadata of the entity.
        aliases (dict | list | None): The aliases of the entity.
        groups (dict | list | None): The groups associated with the entity.
        members (dict | list | None): The members associated with the entity.
        countries (str | None): The countries associated with the entity.
        genres (str | None): The genres associated with the entity.
        styles (str | None): The styles associated with the entity.
    """

    id: int
    """The unique identifier for the runtime entity."""
    entity_id: int
    """The ID of the entity."""
    entity_type: EntityType
    """The type of the entity."""
    entity_name: str
    """The name of the entity."""
    relation_counts: dict | list
    """The relation counts of the entity."""
    entity_metadata: dict | list
    """The metadata of the entity."""
    aliases: dict | list | None
    """The aliases of the entity."""
    groups: dict | list | None
    """The groups associated with the entity."""
    members: dict | list | None
    """The members associated with the entity."""
    parent_label: dict | list | None
    """The parent label associated with the entity if it is a label."""
    countries: str | None
    """The countries associated with the entity."""
    genres: str | None
    """The genres associated with the entity."""
    styles: str | None
    """The styles associated with the entity."""

    @field_serializer("entity_type", when_used="json")
    def serialize_entity_type(self, entity_type: EntityType) -> str:
        """Serialize EntityType to its name for JSON compatibility."""
        return entity_type.name

    def to_domain(self) -> RuntimeEntity:
        """
        Converts the runtime entity from its database representation to its domain representation.

        This method transforms the `RuntimeEntityDB` instance into a
        `RuntimeEntity` instance, making it suitable for use within the
        application's domain logic.

        Returns:
            RuntimeEntity: The domain representation of the runtime entity.
        """
        entity_dict: dict = self.model_dump()
        aliases: dict = entity_dict.pop("aliases", {})
        groups: dict = entity_dict.pop("groups", {})
        members: dict = entity_dict.pop("members", {})
        parent_label: dict = entity_dict.pop("parent_label", {})
        entities: dict[str, Any] = {}
        if aliases is not None and len(aliases) > 0:
            entities.update(aliases=aliases)
        if groups is not None and len(groups) > 0:
            entities.update(groups=groups)
        if members is not None and len(members) > 0:
            entities.update(members=members)
        if parent_label is not None and len(parent_label) > 0:
            entities.update(parent_label=parent_label)
        entity_dict.update(entities=entities)
        return RuntimeEntity.model_validate(entity_dict)


def to_runtime_entity_dict(
    entity_details_index: EntityDetailsIndex, entity: Entity
) -> dict[str, Any]:
    # TODO get from runtime countries table
    countries = entity_details_index.get_countries_for_id(entity.id)
    # TODO get from runtime genres table
    genres = entity_details_index.get_genres_for_id(entity.id)
    # TODO get from runtime styles table
    styles = entity_details_index.get_styles_for_id(entity.id)

    runtime_entity = RuntimeEntity(
        countries=countries,
        genres=genres,
        styles=styles,
        **entity.model_dump(),
    )
    runtime_entity_db = runtime_entity.to_db()
    return runtime_entity_db.model_dump()
