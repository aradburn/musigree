"""
This module defines the domain objects for representing relations in the Musigree runtime system.

It provides classes for handling relations, including their representation in
various stages, such as before database persistence (`RuntimeRelationUncommitted`),
after database persistence (`RuntimeRelationDB`, `RuntimeRelationInternal`),
and for public consumption (`RuntimeRelation`, `RuntimeRelationResult`).

Key functionalities include:
    - Representing relations with attributes like subject, object, and role.
    - Providing a separate class for relations before they are committed to
      the database (`RuntimeRelationUncommitted`).
    - Managing relations with an ID after they are stored in the database
      (`RuntimeRelationDB`, `RuntimeRelationInternal`).
    - Exposing a simplified, public-facing representation of relations
      (`RuntimeRelation`) with entity IDs and types.
    - Handling search result relations with additional attributes like distance
      (`RuntimeRelationResult`).
    - Converting relations between different representations (e.g., from
      `RuntimeRelationDB` to `RuntimeRelationInternal`).
    - Generating unique link keys for relations.
    - Generating JSON-compatible entity keys.
"""

__all__ = [
    "RuntimeRelationUncommitted",
    "RuntimeRelationDB",
    "RuntimeRelation",
    "RuntimeRelationInternal",
    "RuntimeRelationResult",
    "to_runtime_relation_db_dict",
]

import logging
from typing import Any, Self

from pydantic import field_serializer
from musigree import utils
from musigree.exceptions import NotFoundError
from musigree.library.cache.role_cache import RoleCache
from musigree.library.domain.base import InternalDomainObject
from musigree.library.fields.entity_id import to_entity_external_id
from musigree.library.fields.entity_type import EntityType
from musigree.offline.domain.relation import RelationDB

log = logging.getLogger(__name__)


class _RuntimeRelationBase(InternalDomainObject):
    """
    Base class for runtime relation entities.
    """

    pass


class RuntimeRelationUncommitted(_RuntimeRelationBase):
    """
    Represents a relation before it is persisted into the database.

    This class is used to hold the data for a new relation before it is
    assigned an ID and stored in the database.

    Attributes:
        subject (int): The ID of the subject entity.
        role_name (str): The name of the role.
        object (int): The ID of the object entity.
    """

    subject: int
    """The ID of the subject entity."""
    role_name: str
    """The name of the role."""
    object: int
    """The ID of the object entity."""

    @staticmethod
    def from_dicts(
        relation_dicts: list[dict[str, Any]],
    ) -> list["RuntimeRelationUncommitted"]:
        relation_uncommitteds = []
        for relation_dict in relation_dicts:
            relation_uncommitted = RuntimeRelationUncommitted(
                subject=relation_dict["subject"],
                role_name=relation_dict["role"],
                object=relation_dict["object"],
            )
            relation_uncommitteds.append(relation_uncommitted)
        return relation_uncommitteds


class RuntimeRelationDB(_RuntimeRelationBase):
    """
    Represents a relation as stored in the database.

    This class reflects the internal representation of a relation in the
    database, with an ID, subject, predicate (role ID), and object.

    Attributes:
        id (int): The unique identifier for the relation.
        subject (int): The ID of the subject entity.
        predicate (int): The ID of the predicate entity (role ID).
        object (int): The ID of the object entity.
    """

    id: int
    """The unique identifier for the relation."""
    subject: int
    """The ID of the subject entity."""
    predicate: int
    """The ID of the predicate entity (role ID)."""
    object: int
    """The ID of the object entity."""

    def to_domain(self) -> "RuntimeRelationInternal":
        """
        Converts the RuntimeRelationDB instance to a RuntimeRelationInternal instance.

        Returns:
            RuntimeRelationInternal: The internal representation of the relation.
        """
        relation_db_dict: dict = self.model_dump()
        role_id = relation_db_dict.get("predicate")
        if role_id is None:
            raise ValueError("Role ID is None")
        role_name = RoleCache.role_id_to_role_name_lookup[role_id]
        relation_db_dict.update(role=role_name)
        return RuntimeRelationInternal.model_validate(relation_db_dict)


class RuntimeRelation(_RuntimeRelationBase):
    """
    Represents a relation in the domain, exposed publicly.

    This class is used for public-facing representations of relations. It
    provides entity IDs and types for both ends of the relation, along with
    the role and associated releases.

    Attributes:
        id (int): The unique identifier for the relation.
        entity_one_id (int): The ID of the first entity.
        entity_one_type (EntityType): The type of the first entity.
        entity_two_id (int): The ID of the second entity.
        entity_two_type (EntityType): The type of the second entity.
        role (str): The role of the relation.
        releases (dict[str, int | None] | None): The releases associated with the relation.
    """

    id: int
    """The unique identifier for the relation."""
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

    @field_serializer("entity_one_type", "entity_two_type", when_used="json")
    def serialize_entity_types(self, entity_type: EntityType) -> str:
        """Serialize EntityType to its name for JSON compatibility."""
        return entity_type.name

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

    def to_db(self) -> "RuntimeRelationDB":
        """
        Converts the runtime relation to its database representation.

        This method prepares the `RuntimeRelation` instance for storage in the
        database by transforming its attributes into the format expected by
        the database schema (`RuntimeRelationDB`).

        Returns:
            RuntimeRelationDB: The database representation of the runtime relation.
        """
        relation_dict: dict = self.model_dump()
        return RuntimeRelationDB.model_validate(relation_dict)


class RuntimeRelationResult(RuntimeRelation):
    """
    Represents a relation as a search result.

    This class extends the `RuntimeRelation` class to include additional
    attributes relevant to search results, such as distance.

    Attributes:
        id (int): The unique identifier for the relation.
        role (str): The role of the relation.
        distance (int | None): The distance of the relation, if available.
    """

    id: int
    """The unique identifier for the relation."""
    role: str
    """The role of the relation."""
    distance: int | None = None
    """The distance of the relation, if available."""

    def as_json(self) -> dict[str, Any]:
        """
        Converts the relation result to a JSON representation.

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


class RuntimeRelationInternal(_RuntimeRelationBase):
    """
    Represents a relation internally, after retrieval from the database.

    This class is used for internal representations of relations. It
    includes subject, role, and object IDs.

    Attributes:
        id (int): The unique identifier for the relation.
        subject (int): The ID of the subject entity.
        role (str): The role of the relation.
        object (int): The ID of the object entity.
    """

    id: int
    """The unique identifier for the relation."""
    subject: int
    """The ID of the subject entity."""
    role: str
    """The role of the relation."""
    object: int
    """The ID of the object entity."""

    def to_relation(self) -> RuntimeRelation | None:
        """
        Converts the RelationInternal instance to a Relation instance.

        Returns:
            Relation | None: The public facing representation of the relation,
                or None if not found.
        """
        try:
            entity_one_id, entity_one_type = to_entity_external_id(self.subject)
            entity_two_id, entity_two_type = to_entity_external_id(self.object)
            return RuntimeRelation(
                id=self.id,
                entity_one_id=entity_one_id,
                entity_one_type=entity_one_type,
                entity_two_id=entity_two_id,
                entity_two_type=entity_two_type,
                role=self.role,
                releases=None,
            )
        except NotFoundError:
            return None

    @classmethod
    def to_relations(
        cls,
        relation_internals: list[Self],
    ) -> list[RuntimeRelation]:
        """
        Converts a list of RelationInternal instances to a list of Relation
        instances.

        Args:
            relation_internals (list[Self]): A list of RelationInternal
                instances.

        Returns:
            list[Relation]: A list of public facing Relation instances.
        """
        relations = []
        for relation_internal in relation_internals:
            relation = relation_internal.to_relation()
            if relation:
                relations.append(relation)
        return relations


def to_runtime_relation_db_dict(relation_db: RelationDB) -> dict[str, Any]:
    """
    Converts a Relation instance to a dictionary suitable for RuntimeRelationDB.
    Args:
        relation_db (RelationDB): The RelationDB instance to convert.
    Returns:
        dict[str, Any]: The dictionary representation of the RuntimeRelationDB.
    """
    runtime_relation_db = RuntimeRelationDB(**relation_db.model_dump())
    return runtime_relation_db.model_dump()
