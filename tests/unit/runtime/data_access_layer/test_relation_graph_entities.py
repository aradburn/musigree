"""Unit tests for relation-graph entity filtering."""

from musigree.library.fields.entity_id import to_entity_internal_id
from musigree.library.fields.entity_type import EntityType
from musigree.runtime.data_access_layer.relation_graph.entities import (
    accept_entities,
    cap_frontier,
    ids_to_query,
    is_excluded_entity,
    node_limit_reached,
)
from musigree.runtime.data_access_layer.trellis_node import TrellisNode
from musigree.runtime.runtime_domain.runtime_entity import RuntimeEntity


def artist(
    entity_id: int,
    name: str,
    *,
    relation_counts: dict[str, int] | None = None,
    entities: dict[str, object] | None = None,
) -> RuntimeEntity:
    return RuntimeEntity(
        id=to_entity_internal_id(entity_id, EntityType.ARTIST),
        entity_id=entity_id,
        entity_type=EntityType.ARTIST,
        entity_name=name,
        relation_counts=relation_counts or {},
        entity_metadata={},
        entities=entities or {},
        countries=None,
        genres=None,
        styles=None,
    )


def test_is_excluded_entity_rejects_placeholders_and_compilations() -> None:
    assert is_excluded_entity(artist(1, "Various"))
    assert is_excluded_entity(artist(2, "Various Artists - Test"))
    assert is_excluded_entity(artist(3, ""))
    assert not is_excluded_entity(artist(4, "Seefeel"))


def test_cap_frontier_keeps_the_lowest_ids() -> None:
    assert cap_frontier([40, 10, 30, 20], max_nodes=2) == [10, 20]
    assert cap_frontier([3, 1], max_nodes=5) == [3, 1]


def test_accept_entities_adds_nodes_and_drops_excluded_ids() -> None:
    kept = artist(10, "Kept")
    various = artist(11, "Various")
    nodes: dict[int, TrellisNode] = {}
    frontier = [kept.id, various.id, 999]

    remaining = accept_entities([various, kept], nodes, frontier, distance=1)

    assert remaining == [kept.id, 999]
    assert nodes[kept.id].distance == 1
    assert various.id not in nodes


def test_accept_entities_does_not_reset_an_existing_distance() -> None:
    entity = artist(10, "Kept")
    nodes = {entity.id: TrellisNode(entity, 0)}

    accept_entities([entity], nodes, [entity.id], distance=2)

    assert nodes[entity.id].distance == 0


def test_node_limit_reached_only_past_the_center() -> None:
    assert not node_limit_reached(distance=0, node_count=10, max_nodes=10)
    assert node_limit_reached(distance=1, node_count=10, max_nodes=10)


def test_ids_to_query_skips_hubs_past_the_center_and_marks_small_entities() -> None:
    small = artist(2, "Small", relation_counts={"Artist": 1})
    hub = artist(3, "Hub", relation_counts={"Artist": 100})
    nodes = {
        small.id: TrellisNode(small, 1),
        hub.id: TrellisNode(hub, 1),
    }

    fetch, cacheable = ids_to_query(
        [hub.id, small.id],
        nodes,
        ["Artist"],
        distance=1,
        max_links=10,
    )

    assert fetch == [small.id]
    assert cacheable == {small.id}


def test_ids_to_query_fetches_a_hub_center_without_caching_it() -> None:
    center = artist(1, "Center", relation_counts={"Artist": 100})
    nodes = {center.id: TrellisNode(center, 0)}

    fetch, cacheable = ids_to_query(
        [center.id],
        nodes,
        ["Artist"],
        distance=0,
        max_links=10,
    )

    assert fetch == [center.id]
    assert cacheable == set()
