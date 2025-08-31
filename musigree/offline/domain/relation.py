"""
This module defines the domain objects for representing relationships between entities in the Musigree system.

It provides classes for handling relations, including their representation in
various stages, such as before database persistence (`RelationUncommitted`),
after database persistence (`RelationDB`, `RelationInternal`), and for public
consumption (`Relation`, `RelationResult`).

Key functionalities include:
    - Representing relations with attributes like subject, object, and role.
    - Providing a separate class for relations before they are committed to
      the database (`RelationUncommitted`).
    - Managing relations with an ID after they are stored in the database
      (`RelationDB`, `RelationInternal`).
    - Exposing a simplified, public-facing representation of relations
      (`Relation`) with entity IDs and types.
    - Handling search result relations with additional attributes like distance
      (`RelationResult`).
    - Converting relations between different representations (e.g., from
      `RelationDB` to `RelationInternal` to `Relation`).
    - Generating unique link keys for relations.
    - Generating JSON-compatible entity keys.
"""

__all__ = [
    "RelationUncommitted",
    "RelationDB",
    "Relation",
    "RelationInternal",
    "RelationResult",
]

import logging
from typing import Any

from musigree import utils
from musigree.library.cache.role_cache import RoleCache
from musigree.library.domain.base import InternalDomainObject
from musigree.library.fields.entity_id import to_entity_external_id
from musigree.library.fields.entity_type import EntityType

log = logging.getLogger(__name__)


class _RelationBase(InternalDomainObject):
    """Base class for relation entities."""

    pass


class RelationUncommitted(_RelationBase):
    """
    Represents a relation before it is persisted into the database.

    This class is used to hold the data for a new relation before it is
    assigned an ID and stored in the database.

    Attributes:
        subject (int): The subject entity ID.
        role_name (str): The name of the role.
        object (int): The object entity ID.
        release_id (int): The release ID.
        year (int): The release year.
    """

    subject: int
    """The subject entity ID."""
    role_name: str
    """The name of the role."""
    object: int
    """The object entity ID."""
    release_id: int
    """The ID of the release."""
    year: int | None = None
    """The release year, if available."""

    @staticmethod
    def from_dicts(relation_dicts: list[dict[str, Any]]) -> list["RelationUncommitted"]:
        relation_uncommitteds = []
        for relation_dict in relation_dicts:
            relation_uncommitted = RelationUncommitted(
                subject=relation_dict["subject"],
                role_name=relation_dict["role"],
                object=relation_dict["object"],
                release_id=relation_dict["release_id"],
                year=relation_dict["year"],
            )
            relation_uncommitteds.append(relation_uncommitted)
        return relation_uncommitteds


class RelationDB(_RelationBase):
    """
    Represents a relation as stored in the database.

    This class reflects the internal representation of a relation in the
    database, with an ID, subject, predicate (role ID), and object.

    Attributes:
        id (int): The unique identifier for the relation.
        subject (int): The subject entity ID.
        predicate (int): The predicate (role) ID.
        object (int): The object entity ID.
        release_id (int): The release ID.
        year (int): The release year.
    """

    id: int
    """The unique identifier for the relation."""
    subject: int
    """The subject entity ID."""
    predicate: int
    """The predicate (role) ID."""
    object: int
    """The object entity ID."""
    release_id: int
    """The ID of the release."""
    year: int | None = None
    """The release year, if available."""

    def to_domain(self) -> "RelationInternal":
        """
        Converts the RelationDB instance to a RelationInternal instance.

        Returns:
            RelationInternal: The internal representation of the relation.
        """
        relation_db_dict: dict[str, Any] = self.model_dump()
        _role_id = relation_db_dict.get("predicate")
        role_id: int = (
            _role_id if _role_id is not None and isinstance(_role_id, int) else 0
        )
        role_name = RoleCache.role_id_to_role_name_lookup[role_id]
        relation_db_dict.update(role=role_name)
        return RelationInternal.model_validate(relation_db_dict)


class Relation(_RelationBase):
    """
    Represents a relation in the domain, exposed publicly.

    This class is used for public-facing representations of relations. It
    provides entity IDs and types for both ends of the relation, along with
    the role and associated releases.

    Attributes:
        entity_one_id (int): The ID of the first entity.
        entity_one_type (EntityType): The type of the first entity.
        entity_two_id (int): The ID of the second entity.
        entity_two_type (EntityType): The type of the second entity.
        role (str): The role of the relation.
        releases (dict[str, int | None] | None): The releases associated with
            the relation.
    """

    entity_one_id: int
    """The ID of the first entity."""
    entity_one_type: EntityType
    """The type of the first entity."""
    entity_two_id: int
    """The ID of the second entity."""
    entity_two_type: EntityType
    """The type of the second entity."""
    role: str
    """The role of the relation."""
    releases: dict[str, int | None] | None
    """The releases associated with the relation."""

    @property
    def entity_one_key(self) -> tuple[int, EntityType]:
        """
        Returns the key for the first entity.

        Returns:
            tuple[int, EntityType]: The key for the first entity.
        """
        return self.entity_one_id, self.entity_one_type

    @property
    def entity_two_key(self) -> tuple[int, EntityType]:
        """
        Returns the key for the second entity.

        Returns:
            tuple[int, EntityType]: The key for the second entity.
        """
        return self.entity_two_id, self.entity_two_type

    @property
    def json_entity_one_key(self) -> str:
        """
        Returns the JSON representation of the first entity key.

        Returns:
            str: The JSON entity key for the first entity.

        Raises:
            ValueError: If the entity type is not recognized.
        """
        if self.entity_one_type == EntityType.ARTIST:
            return f"artist-{self.entity_one_id}"
        elif self.entity_one_type == EntityType.LABEL:
            return f"label-{self.entity_one_id}"
        # noinspection PyUnreachableCode
        raise ValueError(self.entity_one_key)

    @property
    def json_entity_two_key(self) -> str:
        """
        Returns the JSON representation of the second entity key.

        Returns:
            str: The JSON entity key for the second entity.

        Raises:
            ValueError: If the entity type is not recognized.
        """
        if self.entity_two_type == EntityType.ARTIST:
            return f"artist-{self.entity_two_id}"
        elif self.entity_two_type == EntityType.LABEL:
            return f"label-{self.entity_two_id}"
        # noinspection PyUnreachableCode
        raise ValueError(self.entity_two_key)

    @property
    def link_key(self) -> str:
        """
        Returns the link key for the relation.

        The link key is a string representation of the relation, suitable for
        use as a unique identifier in various contexts.

        Returns:
            str: The link key for the relation.
        """
        source = self.json_entity_one_key
        target = self.json_entity_two_key
        role = utils.WORD_PATTERN.sub("-", str(self.role)).lower()
        pieces = [
            source,
            role,
            target,
        ]
        return "-".join(str(_) for _ in pieces)

    @staticmethod
    def from_relation_internals(relation_internals: list["RelationInternal"]) -> "Relation":
        releases: dict[str, int | None] = {}
        subjects: set[int] = set()
        roles: set[str] = set()
        objects: set[int] = set()
        for relation_internal in relation_internals:
            releases.update({str(relation_internal.release_id): relation_internal.year})
            subjects.add(relation_internal.subject)
            roles.add(relation_internal.role)
            objects.add(relation_internal.object)
        assert len(subjects) == 1, "relations_internals must all have the same subject"
        assert len(roles) == 1, "relations_internals must all have the same roles"
        assert len(objects) == 1, "relations_internals must all have the same object"
        [_subject] = subjects
        [_role] = roles
        [_object] = objects
        entity_one_id, entity_one_type = to_entity_external_id(_subject)
        entity_two_id, entity_two_type = to_entity_external_id(_object)
        return Relation(
            entity_one_id=entity_one_id,
            entity_one_type=entity_one_type,
            entity_two_id=entity_two_id,
            entity_two_type=entity_two_type,
            role=_role,
            releases=releases,
        )


class RelationInternal(_RelationBase):
    """
    Represents a relation internally, after retrieval from the database.

    This class is used for internal representations of relations. It
    includes subject, role, and object IDs, and provides methods to convert
    to the public-facing `Relation` class.

    Attributes:
        id (int): The unique identifier for the relation.
        subject (int): The subject entity ID.
        role (str): The role of the relation.
        object (int): The object entity ID.
        release_id (int): The release ID.
        year (int): The year.
    """

    id: int
    """The unique identifier for the relation."""
    subject: int
    """The subject entity ID."""
    role: str
    """The role of the relation."""
    object: int
    """The object entity ID."""
    release_id: int
    """The ID of the release."""
    year: int | None
    """The release year, if available."""


class RelationResult(Relation):
    """
    Represents a relation as a search result.

    This class extends the `Relation` class to include additional attributes
    relevant to search results, such as distance.

    Attributes:
        id (int): The unique identifier for the relation.
        role (str): The role of the relation.
        distance (int | None): The distance of the relation, if applicable.
    """

    id: int
    """The unique identifier for the relation."""
    role: str
    """The role of the relation."""
    distance: int | None = None
    """The distance of the relation, if applicable."""

    def as_json(self) -> dict[str, Any]:
        """
        Returns the JSON representation of the relation result.

        Returns:
            dict[str, Any]: The JSON representation of the relation result.
        """
        data: dict[str, Any] = {
            "key": self.link_key,
            "role": self.role,
            "source": self.json_entity_one_key,
            "target": self.json_entity_two_key,
        }
        if hasattr(self, "distance") and self.distance is not None:
            data["distance"] = int(self.distance)
        return data
