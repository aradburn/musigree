"""
This module defines the `TrellisNode` class, which represents a node within
a trellis data structure used for graph-based data exploration and visualization.

A `TrellisNode` encapsulates an entity within a graph, along with its
relationships to other entities (parents, children, siblings), the links
(relationships) it participates in, and various metrics used to analyze the
node's importance and connectivity within the graph.

Key functionalities include:
    - **Entity Association**: Each node holds a reference to a `RuntimeEntity`
      instance.
    - **Distance**: Represents the distance of the node from the central entity
      in the graph.
    - **Links**: Manages the links (relationships) associated with the node.
    - **Parentage**: Tracks the node's parent and ancestor nodes.
    - **Neighborhood**: Manages the sets of children, parent, and sibling
      nodes connected to the node.
    - **Cluster Membership**: Allows the node to be associated with a
      cluster ID.
    - **Missing Links**: Tracks the number of missing links (relationships)
      for the node.
    - **Subgraph Size**: Stores the size of the subgraph that the node belongs
      to.
    - **JSON Conversion**: Provides a method to convert the node to a JSON
      representation.
    - **Equality and Hashing**: Implements `__eq__` and `__hash__` for use in
      sets and dictionaries.
    - **Neighbor Retrieval**: Provides a method to retrieve all neighbors of
      the node.
    - **Parentage Retrieval**: Provides a method to retrieve all ancestors of
      the node.

The `TrellisNode` class interacts with the following components:
    - `RuntimeEntity`: The entity that this node represents.
    - `RuntimeRelationResult`: The links connected to the node.

The module utilizes
 `logging` for logging operations,
 `typing` for type hinting,
  and `frozenset`, `set`, `dict`, `hash`, `int` for data structure.
"""

from typing import Any

from musigree.library.fields.entity_type import EntityType
from musigree.runtime.runtime_domain.entity import RuntimeEntity


class TrellisNode:
    """
    Represents a node within a trellis data structure.

    This class encapsulates an entity along with its relationships to other
    entities in a graph, providing a structure for graph-based data
    exploration.
    """

    __slots__ = (
        "_children",
        "_cluster",
        "_distance",
        "_links",
        "_missing",
        "_missing_by_page",
        "_entity",
        "_parentage",
        "_parents",
        "_siblings",
        "_subgraph_size",
    )
    """
        Specifies the allowed attributes of the `TrellisNode` class,
        limiting dynamic attribute creation for efficiency.
    """

    def __init__(self, entity: RuntimeEntity, distance: int = 0):
        """
        Initializes a TrellisNode instance.

        Args:
            entity (RuntimeEntity): The entity that this node represents.
            distance (int, optional): The distance of this node from the
                central entity in the graph. Defaults to 0.
        """
        self._children: set["TrellisNode"] = set()
        """Set of child nodes."""
        self._cluster: int = 0
        """Cluster ID for the node."""
        self._distance: int = distance
        """Distance of the node from the center entity."""
        self._links: set[str] = set()
        """Set of links (relationships) associated with the node."""
        self._missing: int = 0
        """Number of missing links for the node."""
        self._missing_by_page: dict = {}
        """Missing links by page."""
        self._entity: RuntimeEntity = entity
        """The entity associated with this node."""
        self._parentage: frozenset["TrellisNode"] | None = None
        """Frozen set of ancestor nodes."""
        self._parents: set["TrellisNode"] = set()
        """Set of parent nodes."""
        self._siblings: set["TrellisNode"] = set()
        """Set of sibling nodes."""
        self._subgraph_size: int | None = None
        """The size of the subgraph that the node is part of."""

    # SPECIAL METHODS

    def __eq__(self, other: object) -> bool:
        """
        Checks if two TrellisNode instances are equal.

        Args:
            other (object): The other object to compare.

        Returns:
            bool: True if the instances are equal, False otherwise.
        """
        if isinstance(other, TrellisNode):
            return self.entity_key == other.entity_key
        return False

    def __hash__(self) -> int:
        """
        Returns the hash value of the TrellisNode instance.

        Returns:
            int: The hash value of the instance.
        """
        return hash((type(self), self.entity_key))

    # PUBLIC METHODS

    def as_json(self) -> dict[str, Any]:
        """
        Converts the TrellisNode to a JSON-compatible dictionary.

        Returns:
            dict: A JSON-compatible dictionary representing the node.
        """
        data: dict[str, Any] = {
            "distance": self.distance,
            "id": self.entity.entity_id,
            "key": self.entity.json_entity_key,
            "links": tuple(sorted(self.links)),
            "missing": self.missing,
            "name": self.entity.entity_name,
            "size": self.entity.size,
            "type": self.entity.json_entity_key.split("-")[0],
        }
        if self.cluster:
            data["cluster"] = self.cluster
        if self.missing_by_page:
            data["missingByPage"] = self.missing_by_page
        return data

    def get_neighbors(self) -> set["TrellisNode"]:
        """
        Gets the set of all neighboring nodes.

        Returns:
            Set[TrellisNode]: A set of all neighboring nodes.
        """
        neighbors = set()
        """Set to store the neighbors."""
        neighbors.update(self.parents)
        """Add the parents."""
        neighbors.update(self.siblings)
        """Add the siblings."""
        neighbors.update(self.children)
        """Add the children."""
        return neighbors

    def get_parentage(self) -> frozenset["TrellisNode"]:
        """
        Gets the set of all parent and ancestor nodes.

        Returns:
            frozenset[TrellisNode]: A frozenset of all parent and ancestor
                nodes.
        """
        if self._parentage is not None:
            """If the parentage is already computed, return it."""
            return self._parentage
        # noinspection PySetFunctionToLiteral
        parentage: set["TrellisNode"] = set([self])
        """Set to store the parentage."""
        parents: set["TrellisNode"] = self.parents
        """Set with the parent of the current node."""
        while parents:
            """While there are parents to process."""
            parentage.update(parents)
            """Add all the parents to the parentage."""
            new_parents: set["TrellisNode"] = set()
            """Set to store the parents of the current parents."""
            for parent in parents:
                """Iterate over the current parents."""
                new_parents.update(parent.parents)
                """Update the new parents with the parents of the current parents."""
            parents = new_parents
            """Update the parents to the new parents."""
        """Convert the parentage to a frozenset."""
        self._parentage = frozenset(parentage)
        """Update the parentage."""
        return self._parentage

    # PUBLIC PROPERTIES

    @property
    def children(self) -> set["TrellisNode"]:
        """
        Gets the set of child nodes.

        Returns:
            Set[TrellisNode]: The set of child nodes.
        """
        return self._children

    @property
    def cluster(self) -> int:
        """
        Gets the cluster ID of the node.

        Returns:
            int: The cluster ID.
        """
        return self._cluster

    @cluster.setter
    def cluster(self, expr: int):
        """
        Sets the cluster ID of the node.

        Args:
            expr (int): The cluster ID to set.
        """
        self._cluster = int(expr)

    @property
    def distance(self) -> int:
        """
        Gets the distance of the node from the center entity.

        Returns:
            int: The distance.
        """
        return self._distance

    @property
    def entity(self) -> RuntimeEntity:
        """
        Gets the entity associated with this node.

        Returns:
            RuntimeEntity: The associated entity.
        """
        return self._entity

    @property
    def entity_key(self) -> tuple[int, EntityType]:
        """
        Gets the key of the entity associated with this node.

        Returns:
            tuple[int, EntityType]: The key of the associated entity.
        """
        return self._entity.entity_key

    @property
    def links(self) -> set[str]:
        """
        Gets the set of link keys associated with this node.

        Returns:
            Set[str]: The set of link keys.
        """
        return self._links

    @property
    def missing(self) -> int:
        """
        Gets the number of missing links for this node.

        Returns:
            int: The number of missing links.
        """
        return self._missing

    @missing.setter
    def missing(self, expr: int):
        """
        Sets the number of missing links for this node.

        Args:
            expr (int): The number of missing links to set.
        """
        self._missing = int(expr)

    @property
    def missing_by_page(self) -> dict:
        """
        Gets the missing links by page for this node.

        Returns:
            dict: The missing links by page.
        """
        return self._missing_by_page

    @property
    def parents(self) -> set["TrellisNode"]:
        """
        Gets the set of parent nodes.

        Returns:
            Set[TrellisNode]: The set of parent nodes.
        """
        return self._parents

    @property
    def siblings(self) -> set["TrellisNode"]:
        """
        Gets the set of sibling nodes.

        Returns:
            Set[TrellisNode]: The set of sibling nodes.
        """
        return self._siblings

    @property
    def size(self) -> int:
        """
        Gets the size of the entity associated with this node.

        Returns:
            int: The size of the entity.
        """
        return self._entity.size

    @property
    def subgraph_size(self) -> int | None:
        """
        Gets the size of the subgraph that the node is part of.

        Returns:
            int | None: The size of the subgraph, or None if it has not
                been computed.
        """
        return self._subgraph_size

    @subgraph_size.setter
    def subgraph_size(self, expr: int):
        """
        Sets the size of the subgraph that the node is part of.

        Args:
            expr (int): The size of the subgraph to set.
        """
        self._subgraph_size = int(expr)
