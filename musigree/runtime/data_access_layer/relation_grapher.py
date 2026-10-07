"""Public entry point for building a relation network around one entity."""

import logging
from typing import Any

from musigree.runtime.data_access_layer.relation_graph.assemble import (
    assemble_network,
    repository_sources,
)
from musigree.runtime.data_access_layer.relation_graph.limits import (
    GraphLimits,
    resolve_limits,
)
from musigree.runtime.data_access_layer.relation_graph.roles import (
    RolePartition,
    partition_roles,
)
from musigree.runtime.data_access_layer.relation_graph.sources import (
    EntitySource,
    RelationSource,
)
from musigree.runtime.runtime_database.runtime_entity_repository import (
    RuntimeEntityRepository,
)
from musigree.runtime.runtime_database.runtime_relation_repository import (
    RuntimeRelationRepository,
)
from musigree.runtime.runtime_domain.runtime_entity import RuntimeEntity

log = logging.getLogger(__name__)


class RelationGrapher:
    """Build the network of entities around ``center_entity``.

    Pass ``entity_source`` and ``relation_source`` to run the search
    against fakes in tests. A request leaves them empty and the grapher
    reads the repositories, caching small neighborhoods on the way.
    """

    __slots__ = (
        "_center_entity",
        "_entity_source",
        "_limits",
        "_relation_source",
        "_roles",
    )

    def __init__(
        self,
        center_entity: RuntimeEntity,
        degree: int,
        link_ratio: int | None,
        max_nodes: int | None,
        role_names: list[str],
        *,
        entity_source: EntitySource | None = None,
        relation_source: RelationSource | None = None,
    ) -> None:
        log.debug("RelationGrapher for %s-%s", center_entity.entity_type, center_entity.entity_name)
        self._center_entity = center_entity
        self._limits = resolve_limits(degree, max_nodes, link_ratio)
        self._roles = partition_roles(role_names)
        self._entity_source = entity_source
        self._relation_source = relation_source

    async def get_relation_graph(
        self,
        entity_repository: RuntimeEntityRepository,
        relation_repository: RuntimeRelationRepository,
    ) -> dict[str, Any]:
        """
        Generate a relation graph for the center entity.

        Breadth-first search walks relationships out to ``degree``. The
        result has ``center``, ``nodes``, and ``links``.
        """
        entity_source = self._entity_source
        relation_source = self._relation_source
        if entity_source is None or relation_source is None:
            default_entities, default_relations = repository_sources(
                entity_repository, relation_repository
            )
            if entity_source is None:
                entity_source = default_entities
            if relation_source is None:
                relation_source = default_relations
        return await assemble_network(
            center_entity=self._center_entity,
            limits=self._limits,
            roles=self._roles,
            entity_source=entity_source,
            relation_source=relation_source,
        )

    @property
    def all_roles(self) -> list[str]:
        return self._roles.all_roles

    @property
    def center_entity(self) -> RuntimeEntity:
        return self._center_entity

    @property
    def degree(self) -> int:
        return self._limits.degree

    @property
    def limits(self) -> GraphLimits:
        return self._limits

    @property
    def link_ratio(self) -> int:
        return self._limits.link_ratio

    @property
    def max_links(self) -> int:
        return self._limits.max_links

    @property
    def max_nodes(self) -> int:
        return self._limits.max_nodes

    @property
    def relational_role_names(self) -> list[str]:
        return list(self._roles.relational)

    @property
    def roles(self) -> RolePartition:
        return self._roles

    @property
    def structural_role_names(self) -> list[str]:
        return list(self._roles.structural)
