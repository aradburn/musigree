"""Unit tests for trellis layout."""

from musigree.library.fields.entity_id import to_entity_internal_id
from musigree.library.fields.entity_type import EntityType
from musigree.runtime.data_access_layer.relation_graph.trellis import (
    assign_clusters,
    build_trellis,
)
from musigree.runtime.data_access_layer.trellis_node import TrellisNode
from musigree.runtime.runtime_domain.runtime_entity import RuntimeEntity
from musigree.runtime.runtime_domain.runtime_relation import RuntimeRelationResult


def artist(
    entity_id: int,
    name: str,
    *,
    entities: dict[str, object] | None = None,
) -> RuntimeEntity:
    return RuntimeEntity(
        id=to_entity_internal_id(entity_id, EntityType.ARTIST),
        entity_id=entity_id,
        entity_type=EntityType.ARTIST,
        entity_name=name,
        relation_counts={},
        entity_metadata={},
        entities=entities or {},
        countries=None,
        genres=None,
        styles=None,
    )


def link(one: int, two: int) -> RuntimeRelationResult:
    return RuntimeRelationResult(
        entity_one_id=one,
        entity_one_type=EntityType.ARTIST,
        entity_two_id=two,
        entity_two_type=EntityType.ARTIST,
        releases={"1": 3},
        role="Artist",
        distance=None,
    )


def test_build_trellis_links_parent_to_child_and_measures_the_subgraph() -> None:
    center = artist(123, "Artist 1")
    other = artist(789, "Artist 2")
    nodes = {
        center.id: TrellisNode(center, 0),
        other.id: TrellisNode(other, 1),
    }
    relation = link(123, 789)

    reachable, links = build_trellis(nodes, {relation.link_key: relation}, center.id)

    assert relation.link_key in nodes[center.id].links
    assert relation.link_key in nodes[other.id].links
    assert nodes[other.id] in nodes[center.id].children
    assert nodes[center.id] in nodes[other.id].parents
    assert nodes[center.id].subgraph_size == 2
    assert set(reachable) == {center.id, other.id}
    assert set(links) == {relation.link_key}


def test_build_trellis_marks_same_distance_nodes_as_siblings() -> None:
    center = artist(1, "Center")
    left = artist(2, "Left")
    right = artist(3, "Right")
    nodes = {
        center.id: TrellisNode(center, 0),
        left.id: TrellisNode(left, 1),
        right.id: TrellisNode(right, 1),
    }
    to_left = link(1, 2)
    to_right = link(1, 3)
    between = link(2, 3)

    build_trellis(
        nodes,
        {
            to_left.link_key: to_left,
            to_right.link_key: to_right,
            between.link_key: between,
        },
        center.id,
    )

    assert nodes[right.id] in nodes[left.id].siblings
    assert nodes[left.id] in nodes[right.id].siblings


def test_build_trellis_drops_unreachable_nodes_and_orphan_links() -> None:
    center = artist(1, "Center")
    island = artist(2, "Island")
    nodes = {
        center.id: TrellisNode(center, 0),
        island.id: TrellisNode(island, 1),
    }
    orphan = link(2, 9)

    reachable, links = build_trellis(nodes, {orphan.link_key: orphan}, center.id)

    assert set(reachable) == {center.id}
    assert links == {}


def test_assign_clusters_numbers_entities_that_list_aliases() -> None:
    main = artist(123, "Main Artist", entities={"aliases": {"alias1": 456}})
    alias = artist(456, "Alias Artist")
    nodes = {
        main.id: TrellisNode(main, 0),
        alias.id: TrellisNode(alias, 1),
    }

    assign_clusters(nodes)

    assert nodes[main.id].cluster > 0
    assert nodes[alias.id].cluster == 0
