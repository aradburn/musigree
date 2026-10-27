"""Breadth-first search that assembles one relation network."""

import logging
from typing import Any

from musigree.library.fields.entity_type import EntityType
from musigree.runtime.data_access_layer.relation_graph.cache import (
    CachingRelationSource,
    cached_structural_links,
)
from musigree.runtime.data_access_layer.relation_graph.entities import (
    accept_entities,
    cap_frontier,
    ids_to_query,
    node_limit_reached,
)
from musigree.runtime.data_access_layer.relation_graph.limits import GraphLimits
from musigree.runtime.data_access_layer.relation_graph.relations import (
    commit_relations,
    merge_database_relations,
    relation_limit_reached,
)
from musigree.runtime.data_access_layer.relation_graph.roles import (
    RolePartition,
    prune_roles,
    roles_for_database,
    structural_roles_for_distance,
)
from musigree.runtime.data_access_layer.relation_graph.sources import (
    DatabaseRelationQuery,
    EntitySource,
    RelationSource,
    RepositoryEntitySource,
)
from musigree.runtime.data_access_layer.relation_graph.trellis import (
    assign_clusters,
    assign_missing_links,
    build_trellis,
    network_payload,
)
from musigree.runtime.data_access_layer.trellis_node import TrellisNode
from musigree.runtime.runtime_database.runtime_entity_repository import (
    RuntimeEntityRepository,
)
from musigree.runtime.runtime_database.runtime_relation_repository import (
    RuntimeRelationRepository,
)
from musigree.runtime.runtime_domain.runtime_entity import RuntimeEntity
from musigree.runtime.runtime_domain.runtime_relation import RuntimeRelationResult

log = logging.getLogger(__name__)


async def _structural_links(
    nodes: dict[int, TrellisNode],
    frontier: list[int],
    role_names: list[str],
) -> dict[str, RuntimeRelationResult]:
    collected: dict[str, RuntimeRelationResult] = {}
    for entity_id in frontier:
        node = nodes.get(entity_id)
        if node is None:
            continue
        collected.update(await cached_structural_links(node.entity, role_names))
    return collected


async def _collect_relations(
    *,
    nodes: dict[int, TrellisNode],
    frontier: list[int],
    distance: int,
    limits: GraphLimits,
    roles: RolePartition,
    active_roles: list[str],
    relation_source: RelationSource,
) -> dict[str, RuntimeRelationResult]:
    relations: dict[str, RuntimeRelationResult] = {}
    visible_structural = structural_roles_for_distance(roles.structural, distance)
    if visible_structural:
        relations.update(await _structural_links(nodes, frontier, visible_structural))
    if distance >= limits.degree:
        return relations
    roles_to_load = roles_for_database(active_roles, roles.structural)
    if not roles_to_load:
        return relations
    fetch_ids, cacheable_ids = ids_to_query(
        frontier,
        nodes,
        active_roles,
        distance=distance,
        max_links=limits.max_links,
    )
    if not fetch_ids:
        return relations
    database_relations = await relation_source.load(
        fetch_ids,
        roles_to_load,
        limits.max_links,
        cacheable_ids=cacheable_ids,
    )
    merge_database_relations(relations, database_relations, set(roles.structural))
    return relations


async def assemble_network(
    *,
    center_entity: RuntimeEntity,
    limits: GraphLimits,
    roles: RolePartition,
    entity_source: EntitySource,
    relation_source: RelationSource,
) -> dict[str, Any]:
    """Search outward from ``center_entity`` and return the network payload."""
    nodes: dict[int, TrellisNode] = {}
    links: dict[str, RuntimeRelationResult] = {}
    frontier = [center_entity.id]
    active_roles = list(roles.relational)
    stop_after_this_pass = False

    log.debug(
        "Searching around %s (max nodes %s, max links %s)",
        center_entity.entity_name,
        limits.max_nodes,
        limits.max_links,
    )
    for distance in range(limits.degree + 1):
        frontier = cap_frontier(frontier, limits.max_nodes)
        entities = await entity_source.load(frontier)
        frontier = accept_entities(entities, nodes, frontier, distance)
        if not frontier or stop_after_this_pass or len(entities) > limits.max_nodes:
            break
        if node_limit_reached(distance, len(nodes), limits.max_nodes):
            stop_after_this_pass = True
        active_roles = prune_roles(
            active_roles,
            distance=distance,
            node_count=len(nodes),
            max_nodes=limits.max_nodes,
            center_is_artist=center_entity.entity_type == EntityType.ARTIST,
        )
        relations: dict[str, RuntimeRelationResult] = {}
        if not stop_after_this_pass:
            relations = await _collect_relations(
                nodes=nodes,
                frontier=frontier,
                distance=distance,
                limits=limits,
                roles=roles,
                active_roles=active_roles,
                relation_source=relation_source,
            )
        if relation_limit_reached(distance, len(relations), limits.max_links):
            stop_after_this_pass = True
        frontier = commit_relations(links, relations, nodes)

    nodes, links = build_trellis(nodes, links, center_entity.id)
    assign_clusters(nodes)
    assign_missing_links(nodes, roles.all_roles)
    log.debug("number of links: %s", len(links))
    log.debug("number of nodes: %s", len(nodes))
    return network_payload(center_entity, nodes, links)


def repository_sources(
    entity_repository: RuntimeEntityRepository,
    relation_repository: RuntimeRelationRepository,
    *,
    min_year: int | None = None,
    max_year: int | None = None,
) -> tuple[EntitySource, RelationSource]:
    """Sources used by a request that did not inject its own."""
    query = DatabaseRelationQuery(
        relation_repository,
        min_year=min_year,
        max_year=max_year,
    )
    return (
        RepositoryEntitySource(entity_repository),
        CachingRelationSource(query, min_year=min_year, max_year=max_year),
    )
