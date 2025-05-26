"""
This module provides functions for converting between external and internal entity IDs,
and for handling special cases like missing label entities.

It defines constants for label entity ID offsets and missing label entity values,
and provides functions to perform the conversions and handle these special cases.
"""

from musigree.library.fields.entity_type import EntityType

#: The offset added to external label entity IDs to generate internal label entity IDs.
LABEL_ENTITY_ID_OFFSET = 1000000000
#: A special internal entity ID representing a missing label entity.
MISSING_LABEL_ENTITY = -2000000000


def to_entity_internal_id(entity_id: int, entity_type: EntityType) -> int:
    """
    Converts an external entity ID and its type to an internal entity ID.

    Internal entity IDs for artists are the same as their external IDs.
    Internal entity IDs for labels are offset by `LABEL_ENTITY_ID_OFFSET`.
    The `MISSING_LABEL_ENTITY` constant is used to represent a missing label entity.

    Args:
        entity_id: The external entity ID.
        entity_type: The type of the entity (Artist or Label).

    Returns:
        The internal entity ID.

    Raises:
        AssertionError: If the entity ID is invalid for the given entity type.
                         Specifically, for artists, if the ID is `MISSING_LABEL_ENTITY`
                         or if it's greater than or equal to `LABEL_ENTITY_ID_OFFSET`.
    """
    if entity_type == EntityType.ARTIST:
        assert entity_id != MISSING_LABEL_ENTITY
        assert entity_id < LABEL_ENTITY_ID_OFFSET
        return entity_id
    else:
        if entity_id != MISSING_LABEL_ENTITY:
            if entity_id < LABEL_ENTITY_ID_OFFSET:
                return entity_id + LABEL_ENTITY_ID_OFFSET
            else:
                return entity_id
        else:
            return MISSING_LABEL_ENTITY


def to_entity_external_id(id_: int) -> tuple[int, EntityType]:
    """
    Converts an internal entity ID to an external entity ID and its type.

    Internal artist IDs are the same as their external IDs.
    Internal label IDs have `LABEL_ENTITY_ID_OFFSET` subtracted from them to get the
    external ID. `MISSING_LABEL_ENTITY` is converted to an external ID of -1.

    Args:
        id_: The internal entity ID.

    Returns:
        A tuple containing the external entity ID and its type.

    """
    if id_ == MISSING_LABEL_ENTITY:
        entity_id = -1
        entity_type = EntityType.LABEL
    elif id_ >= LABEL_ENTITY_ID_OFFSET:
        entity_id = id_ - LABEL_ENTITY_ID_OFFSET
        entity_type = EntityType.LABEL
    else:
        entity_id = id_
        entity_type = EntityType.ARTIST
    return entity_id, entity_type


def to_entity_label_internal_id(entity_id: int | None) -> int:
    """
    Converts an external label entity ID to an internal label entity ID,
    handling the case where the entity ID is None.

    If the entity ID is None, it's treated as a missing label and returns
    `MISSING_LABEL_ENTITY`. Otherwise, it converts the given ID to an internal
    label ID using `to_entity_internal_id`.

    Args:
        entity_id: The external label entity ID, or None if it's missing.

    Returns:
        The internal label entity ID.
    """
    if entity_id:
        return to_entity_internal_id(entity_id, EntityType.LABEL)
    else:
        return MISSING_LABEL_ENTITY
