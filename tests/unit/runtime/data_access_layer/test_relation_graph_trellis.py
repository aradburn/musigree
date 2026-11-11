"""Unit tests for trellis layout."""

from typing import overload

from musigree.library.fields.entity_id import to_entity_internal_id
from musigree.library.fields.entity_type import EntityType
from musigree.runtime.data_access_layer.relation_graph.trellis import (
    assign_clusters,
    build_trellis,
    find_trellis_distance,
)
from musigree.runtime.data_access_layer.trellis_node import TrellisNode
from musigree.runtime.runtime_domain.runtime_entity import RuntimeEntity
from musigree.runtime.runtime_domain.runtime_relation import RuntimeRelationResult
from tests.release_years import release_years


@overload
def artist(
    entity_id: int,
    name: str,
    *,
    entities: dict[str, object] = ...,
) -> RuntimeEntity: ...


@overload
def artist(
    entity_id: int,
    name: str,
    *,
    entities: None = None,
) -> RuntimeEntity: ...


def artist(
    entity_id: int,
    name: str,
    *,
    entities: dict[str, object] | None = None,
) -> RuntimeEntity:
    # Callers that pass a dict match the overload above, so literal keys are
    # widened. None is the runtime default and is not a shared mutable value.
    return RuntimeEntity(
        id=to_entity_internal_id(entity_id, EntityType.ARTIST),
        entity_id=entity_id,
        entity_type=EntityType.ARTIST,
        entity_name=name,
        relation_counts={},
        entity_metadata={},
        entities=dict(entities or {}),
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
        releases=release_years({"1": 3}),
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


def test_find_trellis_distance_chooses_the_largest_mean_under_the_threshold() -> None:
    """Means are sum(sizes) ** (1/n). The highest mean still below the threshold wins."""
    center = TrellisNode(artist(1, "Center"), 0)
    near = TrellisNode(artist(2, "Near"), 1)
    far = TrellisNode(artist(3, "Far"), 2)
    center.subgraph_size = 1
    near.subgraph_size = 4
    far.subgraph_size = 9

    winning_distance = find_trellis_distance({0: [center], 1: [near], 2: [far]}, 5)

    assert winning_distance == 1


def test_find_trellis_distance_promotes_a_shallow_winner() -> None:
    """A winner in the first half of the distances is moved one step deeper."""
    center = TrellisNode(artist(1, "Center"), 0)
    middle = TrellisNode(artist(2, "Middle"), 1)
    far = TrellisNode(artist(3, "Far"), 2)
    center.subgraph_size = 1
    middle.subgraph_size = 100
    far.subgraph_size = 100

    winning_distance = find_trellis_distance({0: [center], 1: [middle], 2: [far]}, 10)

    assert winning_distance == 1


def test_find_trellis_distance_ignores_unmeasured_nodes_and_sorts_by_entity_key() -> None:
    """Nodes without a subgraph size are left out of the mean. The distance list is sorted."""
    later = TrellisNode(artist(9, "Later"), 1)
    earlier = TrellisNode(artist(2, "Earlier"), 1)
    unmeasured = TrellisNode(artist(4, "Unmeasured"), 1)
    later.subgraph_size = 4
    earlier.subgraph_size = 4
    by_distance = {1: [later, unmeasured, earlier]}

    winning_distance = find_trellis_distance(by_distance, 10)

    assert winning_distance == 1
    assert by_distance[1] == [earlier, unmeasured, later]
