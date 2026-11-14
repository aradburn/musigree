"""Turn collected nodes and links into a trellis rooted at the center."""

import logging
from typing import TYPE_CHECKING, Any

from musigree.library.fields.entity_id import to_entity_internal_id
from musigree.runtime.data_access_layer.runtime_entity_data_access import (
    RuntimeEntityDataAccess,
)

if TYPE_CHECKING:
    from musigree.library.fields.entity_type import EntityType
    from musigree.runtime.data_access_layer.trellis_node import TrellisNode
    from musigree.runtime.runtime_domain.runtime_entity import RuntimeEntity
    from musigree.runtime.runtime_domain.runtime_relation import RuntimeRelationResult

log = logging.getLogger(__name__)


def links_inside_nodes(
    links: dict[str, RuntimeRelationResult],
    nodes: dict[int, TrellisNode],
) -> dict[str, RuntimeRelationResult]:
    """Drop links whose ends are not both in the node map."""
    kept: dict[str, RuntimeRelationResult] = {}
    for link_key, relation in links.items():
        id_one = to_entity_internal_id(relation.entity_one_key[0], relation.entity_one_key[1])
        id_two = to_entity_internal_id(relation.entity_two_key[0], relation.entity_two_key[1])
        if id_one in nodes and id_two in nodes:
            kept[link_key] = relation
    return kept


def attach_links(
    nodes: dict[int, TrellisNode],
    links: dict[str, RuntimeRelationResult],
) -> None:
    """Record each link on its ends and classify parent, child, or sibling."""
    for link_key, relation in links.items():
        id_one = to_entity_internal_id(relation.entity_one_id, relation.entity_one_type)
        id_two = to_entity_internal_id(relation.entity_two_id, relation.entity_two_type)
        source_node = nodes[id_one]
        target_node = nodes[id_two]
        source_node.links.add(link_key)
        target_node.links.add(link_key)
        if source_node.distance == target_node.distance:
            source_node.siblings.add(target_node)
            target_node.siblings.add(source_node)
        elif source_node.distance < target_node.distance:
            source_node.children.add(target_node)
            target_node.parents.add(source_node)
        else:
            target_node.children.add(source_node)
            source_node.parents.add(target_node)


def measure_subgraphs(node: TrellisNode) -> set[tuple[int, EntityType]]:
    """Set ``subgraph_size`` for this node and its children. Returns the visited keys."""
    traversed_keys = {node.entity_key}
    for child in node.children:
        traversed_keys.update(measure_subgraphs(child))
    node.subgraph_size = len(traversed_keys)
    return traversed_keys


def build_trellis(
    nodes: dict[int, TrellisNode],
    links: dict[str, RuntimeRelationResult],
    center_id: int,
) -> tuple[dict[int, TrellisNode], dict[str, RuntimeRelationResult]]:
    """Connect links, measure the center's tree, and drop anything unreachable."""
    for node in nodes.values():
        node.clear_connections()
    links = links_inside_nodes(links, nodes)
    attach_links(nodes, links)
    measure_subgraphs(nodes[center_id])
    reachable = {entity_id: node for entity_id, node in nodes.items() if node.subgraph_size is not None}
    links = links_inside_nodes(links, reachable)
    log.debug("Built trellis: %s nodes / %s links", len(reachable), len(links))
    return reachable, links


def assign_clusters(nodes: dict[int, TrellisNode]) -> None:
    """Group entities that share an alias list under one cluster id."""
    cluster_count = 0
    cluster_map: dict[int, int] = {}
    ordered = sorted(
        nodes.values(),
        key=lambda _node: len(_node.entity.entities.get("aliases", {})),
        reverse=True,
    )
    for node in ordered:
        entity = node.entity
        aliases = entity.entities.get("aliases", {})
        if not aliases:
            continue
        if entity.entity_id not in cluster_map:
            cluster_count += 1
            cluster_map[entity.entity_id] = cluster_count
            for alias_id in aliases.values():
                cluster_map[alias_id] = cluster_count
        cluster = cluster_map[entity.entity_id]
        if cluster is not None:
            node.cluster = cluster


def assign_missing_links(nodes: dict[int, TrellisNode], roles: list[str]) -> None:
    """Record how many expected relations for ``roles`` are absent from the node."""
    for node in nodes.values():
        expected_count = RuntimeEntityDataAccess.roles_to_relation_count(node.entity, roles)
        node.missing = expected_count - len(node.links)


def network_payload(
    center_entity: RuntimeEntity,
    nodes: dict[int, TrellisNode],
    links: dict[str, RuntimeRelationResult],
) -> dict[str, Any]:
    """JSON-ready network, with nodes and links ordered by key."""
    json_links = tuple(link.as_json() for _key, link in sorted(links.items(), key=lambda item: item[0]))
    json_nodes = tuple(node.as_json() for _entity_id, node in sorted(nodes.items(), key=lambda item: item[0]))
    return {
        "center": {
            "key": center_entity.json_entity_key,
            "name": center_entity.entity_name,
        },
        "links": json_links,
        "nodes": json_nodes,
    }


def find_trellis_distance(
    trellis_nodes_by_distance: dict[int, list[TrellisNode]],
    threshold: float,
) -> int:
    """Pick a distance whose average subgraph size falls under ``threshold``."""
    log.debug("Maximum depth: %s", max(trellis_nodes_by_distance))
    log.debug("Subgraph threshold: %s", threshold)
    distancewise_average_subgraph_size = {}
    for distance, trellis_nodes in trellis_nodes_by_distance.items():
        trellis_nodes_by_distance[distance] = sorted(
            trellis_nodes,
            key=lambda _node: _node.entity_key,
        )
        # subgraph_size stays None until the node is measured. sum() only accepts numbers.
        measured_sizes: list[int] = []
        for node in trellis_nodes:
            subgraph_size = node.subgraph_size
            if subgraph_size is not None:
                measured_sizes.append(subgraph_size)
        sizes = sorted(measured_sizes)
        if not sizes:
            continue
        geometric = sum(sizes) ** (1.0 / len(sizes))
        distancewise_average_subgraph_size[distance] = geometric
        log.debug("At distance %s: %s geometric mean", distance, geometric)
    winning_distance = 0
    pairs = ((average, distance) for distance, average in distancewise_average_subgraph_size.items())
    sorted_pairs = sorted(pairs, reverse=True)
    for average, distance in sorted_pairs:
        log.debug("Testing %s @ distance %s", average, distance)
        if average < threshold:
            winning_distance = distance
            break
    log.debug("Winning distance: %s", winning_distance)
    if (winning_distance + 1) < (len(distancewise_average_subgraph_size) / 2):
        winning_distance += 1
        log.debug("Promoting winning distance: %s", winning_distance)
    return winning_distance
