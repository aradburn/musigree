"""Decide which entities enter the graph and which ids are queried."""

from musigree.runtime.data_access_layer.runtime_entity_data_access import (
    RuntimeEntityDataAccess,
)
from musigree.runtime.data_access_layer.trellis_node import TrellisNode
from musigree.runtime.runtime_domain.runtime_entity import RuntimeEntity

ENTITIES_TO_PRUNE: frozenset[str] = frozenset(
    {
        "Various",
        "Not On Label",
        "Self Released",
        "Self-Released",
    }
)
VARIOUS_ARTISTS_PREFIX = "Various Artists"


def is_excluded_entity(entity: RuntimeEntity) -> bool:
    """Compilation and placeholder entities are not useful graph nodes."""
    if not entity.entity_id or not entity.entity_name:
        return True
    if entity.entity_name in ENTITIES_TO_PRUNE:
        return True
    return entity.entity_name.startswith(VARIOUS_ARTISTS_PREFIX)


def cap_frontier(entity_ids: list[int], max_nodes: int) -> list[int]:
    """Keep the frontier within ``max_nodes``.

    Overflow keeps the lowest ids so the same request always drops the
    same entities.
    """
    if len(entity_ids) <= max_nodes:
        return entity_ids
    return sorted(entity_ids)[:max_nodes]


def accept_entities(
    entities: list[RuntimeEntity],
    nodes: dict[int, TrellisNode],
    frontier: list[int],
    distance: int,
) -> list[int]:
    """Add kept entities as nodes and return the frontier ids that remain.

    An id whose entity was not returned stays in the frontier. An excluded
    entity is dropped. Nodes already present keep their original distance.
    """
    by_id = {entity.id: entity for entity in entities}
    remaining: list[int] = []
    for entity_id in frontier:
        entity = by_id.get(entity_id)
        if entity is None:
            remaining.append(entity_id)
            continue
        if is_excluded_entity(entity):
            continue
        if entity.id not in nodes:
            nodes[entity.id] = TrellisNode(entity, distance)
        remaining.append(entity.id)
    return remaining


def node_limit_reached(distance: int, node_count: int, max_nodes: int) -> bool:
    """Stop expanding after this pass once the node cap is hit past the center."""
    return distance > 0 and node_count >= max_nodes


def ids_to_query(
    frontier: list[int],
    nodes: dict[int, TrellisNode],
    role_names: list[str],
    *,
    distance: int,
    max_links: int,
) -> tuple[list[int], set[int]]:
    """Return ids to fetch, and the subset small enough to cache.

    Hubs past the center are left out of the fetch. Their neighborhoods
    are larger than ``max_links`` and would dominate the graph. The center
    is still fetched, but a hub center is not cached.
    """
    fetch: list[int] = []
    cacheable: set[int] = set()
    for entity_id in frontier:
        node = nodes.get(entity_id)
        if node is None:
            continue
        relation_count = RuntimeEntityDataAccess.roles_to_relation_count(node.entity, role_names)
        if distance > 0 and max_links < relation_count:
            continue
        fetch.append(entity_id)
        if relation_count <= max_links:
            cacheable.add(entity_id)
    return sorted(fetch), cacheable
