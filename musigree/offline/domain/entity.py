"""
This module defines the Entity domain object and related utilities.

It provides the `Entity` class, which represents entities such as artists and
labels in the Musigree system. It also includes a base class `_EntityBase`
that defines common attributes and methods for all entities.

Key functionalities include:
    - Representing entities with attributes like ID, type, name, metadata, etc.
    - Generating unique entity keys for identification.
    - Determining the size of entities (e.g., number of members for artists).
    - Converting entities between domain and database representations.
"""

__all__ = [
    "Entity",
]

import logging
from typing import Self

from musigree.library.domain.base import InternalDomainObject
from musigree.library.fields.entity_type import EntityType

log = logging.getLogger(__name__)


class _EntityBase(InternalDomainObject):
    """
    Base class for entities in the domain.

    This class defines the common attributes and methods shared by all
    entities in the Musigree system, such as artists and labels. It
    provides functionalities for generating unique entity keys, determining
    entity size, and converting between domain and database representations.

    Attributes:
        entity_id (int): The unique identifier for the entity. This is the
            external ID, from discogs.
        entity_type (EntityType): The type of the entity (e.g., ARTIST, LABEL).
        entity_name (str): The name of the entity.
        relation_counts (dict | list): The counts of relations associated with
            the entity. This might include the number of releases,
            collaborations, etc.
        entity_metadata (dict | list): Metadata associated with the entity.
            This could be any additional information not covered by other
            attributes.
        entities (dict | list): Related entities. For example, an artist might
            have a list of members, or a label might have a list of sublabels.
        search_content (str): Content used for searching the entity. This is a
            preprocessed string that can be used for full-text search operations.
    """

    entity_id: int
    entity_type: EntityType
    entity_name: str
    relation_counts: dict | list
    entity_metadata: dict | list
    entities: dict | list
    search_content: str

    @property
    def entity_key(self) -> tuple[int, EntityType]:
        """
        Returns the unique key for the entity.

        The entity key is a tuple that uniquely identifies an entity in the
        system.

        Returns:
            tuple[int, EntityType]: A tuple containing the entity ID and
                entity type.
        """
        return self.entity_id, self.entity_type

    @property
    def json_entity_key(self) -> str:
        """
        Returns the JSON representation of the entity key.

        This is a string representation of the entity key suitable for use in
        JSON data.

        Returns:
            str: The JSON entity key.
        """
        return self.to_json_entity_key(self.entity_id, self.entity_type)

    @property
    def size(self) -> int:
        """
        Returns the size of the entity based on its type.

        For artists, this is the number of members. For labels, this is the
        number of sublabels.

        Returns:
            int: The size of the entity.
        """
        members = []
        if self.entity_type == EntityType.ARTIST:
            if "members" in self.entities:
                members = self.entities["members"]
        elif self.entity_type == EntityType.LABEL:
            if "sublabels" in self.entities:
                members = self.entities["sublabels"]
        return len(members)

    @staticmethod
    def to_json_entity_key(entity_id: int, entity_type: EntityType) -> str:
        """
        Converts the entity ID and type to a JSON entity key.

        This method generates a string key that uniquely identifies an entity
        based on its ID and type.

        Args:
            entity_id (int): The unique identifier for the entity.
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
        raise ValueError(entity_id, entity_type)

    def to_domain(self) -> Self:
        """
        Converts the entity to its domain representation.

        This method is intended to be overridden in subclasses to perform
        any necessary conversions.

        Returns:
            Self: The domain representation of the entity.
        """
        return self

    def to_db(self) -> Self:
        """
        Converts the entity to its database representation.

        This method is intended to be overridden in subclasses to perform
        any necessary conversions.

        Returns:
            Self: The database representation of the entity.
        """
        return self


class Entity(_EntityBase):
    """
    Entity class that extends the base entity class.

    This class represents a specific entity in the Musigree system,
    inheriting common attributes and methods from `_EntityBase`.

    Attributes:
        id (int): The internal, unique identifier for the entity in the database.
                This is different from `entity_id` which is external id from discogs.
    """

    id: int
