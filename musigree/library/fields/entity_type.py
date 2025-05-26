"""
This module defines the EntityType enum, which represents the different types of entities
in the Musigree system (currently, Artist and Label).

It also provides utility methods for working with the EntityType enum,
such as converting from a string representation to an EntityType enum value.
"""

import enum


class EntityType(enum.Enum):
    """
    Represents the type of an entity in the Musigree system.

    Currently, there are two entity types:

    - ARTIST: Represents an artist entity.
    - LABEL: Represents a label entity.

    Attributes:
        ARTIST (int): The value representing an artist entity.
        LABEL (int): The value representing a label entity.
    """

    ARTIST = 1
    LABEL = 2

    @staticmethod
    def from_str(entity_type_str: str) -> "EntityType":
        """
        Converts a string representation of an entity type to an EntityType enum value.

        Args:
            entity_type_str: The string representation of the entity type.
                             Valid values are "artist", "ARTIST", "label", and "LABEL".

        Returns:
            EntityType: The corresponding EntityType enum value.

        Raises:
            NotImplementedError: If the input string is not a valid entity type.
        """
        if entity_type_str in ("artist", "ARTIST"):
            return EntityType.ARTIST
        elif entity_type_str in ("label", "LABEL"):
            return EntityType.LABEL
        else:
            raise NotImplementedError

    def __lt__(self, other: "EntityType") -> bool:
        """
        Implements the less-than comparison operator for EntityType enum values.

        Args:
            other: The other EntityType to compare with.

        Returns:
            bool: True if the current EntityType's value is less than the other's, False otherwise.
            NotImplemented: If the other object is not an EntityType.
        """
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented

    def __repr__(self) -> str:
        """
        Returns the string representation of the EntityType (its name).

        Returns:
            str: The name of the EntityType.
        """
        return self.name
