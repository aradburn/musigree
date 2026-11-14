"""Unit tests for merging and storing relation links."""

from musigree.library.fields.entity_id import to_entity_internal_id
from musigree.library.fields.entity_type import EntityType
from musigree.runtime.data_access_layer.relation_graph.relations import (
    apply_cross_role_release_years,
    commit_relations,
    drop_undated_center_member_links,
    merge_database_relations,
    relation_limit_reached,
    release_year_probes,
    restrict_links_to_year_bounds,
)
from musigree.runtime.data_access_layer.trellis_node import TrellisNode
from musigree.runtime.runtime_domain.runtime_entity import RuntimeEntity
from musigree.runtime.runtime_domain.runtime_relation import RuntimeRelationResult
from tests.release_years import release_years


def relation(
    one: int,
    two: int,
    role: str,
    *,
    releases: dict[str, int | None] | None,
) -> RuntimeRelationResult:
    return RuntimeRelationResult(
        entity_one_id=one,
        entity_one_type=EntityType.ARTIST,
        entity_two_id=two,
        entity_two_type=EntityType.ARTIST,
        releases=releases,
        role=role,
        distance=None,
    )


def test_merge_database_relations_attaches_years_to_the_opposite_structural_link() -> None:
    structural = relation(123, 456, "Alias", releases=None)
    database = relation(
        456,
        123,
        "Alias",
        releases=release_years({"11": 2003, "10": 1991, "12": None}),
    )
    relations = {structural.link_key: structural}

    merge_database_relations(relations, [database], {"Alias"})

    attached = relations[structural.link_key]
    assert attached.releases == {"11": 2003, "10": 1991, "12": None}
    assert attached.as_json()["years"] == [1991, 2003]
    assert len(relations) == 1


def test_merge_database_relations_keeps_relational_links() -> None:
    database = relation(1, 2, "Producer", releases=release_years({"1": 1999}))
    relations: dict[str, RuntimeRelationResult] = {}

    merge_database_relations(relations, [database], {"Alias"})

    assert relations[database.link_key] is database


def test_commit_relations_queues_missing_ends_and_skips_self_links() -> None:
    entity = RuntimeEntity(
        id=to_entity_internal_id(1, EntityType.ARTIST),
        entity_id=1,
        entity_type=EntityType.ARTIST,
        entity_name="One",
        relation_counts={},
        entity_metadata={},
        countries=None,
        genres=None,
        styles=None,
    )
    nodes = {entity.id: TrellisNode(entity, 0)}
    outward = relation(1, 2, "Producer", releases=release_years({"1": 1999}))
    self_link = relation(1, 1, "Producer", releases=release_years({"1": 1999}))
    links: dict[str, RuntimeRelationResult] = {}

    next_ids = commit_relations(
        links,
        {outward.link_key: outward, self_link.link_key: self_link},
        nodes,
    )

    assert links == {outward.link_key: outward}
    assert next_ids == [to_entity_internal_id(2, EntityType.ARTIST)]


def test_commit_relations_keeps_release_years_already_stored() -> None:
    stored = relation(1, 2, "Producer", releases=release_years({"1": 1999}))
    replacement = relation(1, 2, "Producer", releases=None)
    links = {stored.link_key: stored}
    nodes: dict[int, TrellisNode] = {
        to_entity_internal_id(1, EntityType.ARTIST): TrellisNode(
            RuntimeEntity(
                id=to_entity_internal_id(1, EntityType.ARTIST),
                entity_id=1,
                entity_type=EntityType.ARTIST,
                entity_name="One",
                relation_counts={},
                entity_metadata={},
                countries=None,
                genres=None,
                styles=None,
            ),
            0,
        ),
        to_entity_internal_id(2, EntityType.ARTIST): TrellisNode(
            RuntimeEntity(
                id=to_entity_internal_id(2, EntityType.ARTIST),
                entity_id=2,
                entity_type=EntityType.ARTIST,
                entity_name="Two",
                relation_counts={},
                entity_metadata={},
                countries=None,
                genres=None,
                styles=None,
            ),
            1,
        ),
    }

    commit_relations(links, {replacement.link_key: replacement}, nodes)

    assert links[stored.link_key].releases == {"1": 1999}


def _node(entity_id: int, name: str, relation_counts: dict[str, int]) -> TrellisNode:
    entity = RuntimeEntity(
        id=to_entity_internal_id(entity_id, EntityType.ARTIST),
        entity_id=entity_id,
        entity_type=EntityType.ARTIST,
        entity_name=name,
        relation_counts=relation_counts,
        entity_metadata={},
        countries=None,
        genres=None,
        styles=None,
    )
    return TrellisNode(entity, 0)


def test_release_year_probes_scan_the_smaller_end_of_an_undated_link() -> None:
    member = relation(1, 2, "Member Of", releases=None)
    nodes = {
        to_entity_internal_id(1, EntityType.ARTIST): _node(1, "Busy", {"Producer": 40}),
        to_entity_internal_id(2, EntityType.ARTIST): _node(2, "Quiet", {}),
    }

    probes = release_year_probes({member.link_key: member}, nodes)

    quiet = to_entity_internal_id(2, EntityType.ARTIST)
    busy = to_entity_internal_id(1, EntityType.ARTIST)
    assert probes == {quiet: {busy}}


def test_release_year_probes_skip_links_that_already_have_releases() -> None:
    dated = relation(1, 2, "Producer", releases=release_years({"9": 1994}))
    nodes = {
        to_entity_internal_id(1, EntityType.ARTIST): _node(1, "One", {}),
        to_entity_internal_id(2, EntityType.ARTIST): _node(2, "Two", {}),
    }

    assert release_year_probes({dated.link_key: dated}, nodes) == {}


def test_release_year_probes_skip_pairs_with_no_credit_rows() -> None:
    member = relation(1, 2, "Member Of", releases=None)
    nodes = {
        to_entity_internal_id(1, EntityType.ARTIST): _node(1, "One", {}),
        to_entity_internal_id(2, EntityType.ARTIST): _node(2, "Two", {}),
    }

    assert release_year_probes({member.link_key: member}, nodes) == {}


def test_release_year_probes_break_a_volume_tie_with_the_lower_id() -> None:
    member = relation(5, 3, "Member Of", releases=None)
    nodes = {
        to_entity_internal_id(5, EntityType.ARTIST): _node(5, "Five", {"Producer": 2}),
        to_entity_internal_id(3, EntityType.ARTIST): _node(3, "Three", {"Producer": 2}),
    }

    probes = release_year_probes({member.link_key: member}, nodes)

    lower = to_entity_internal_id(3, EntityType.ARTIST)
    higher = to_entity_internal_id(5, EntityType.ARTIST)
    assert probes == {lower: {higher}}


def test_apply_cross_role_release_years_fills_only_undated_links() -> None:
    member = relation(1, 2, "Member Of", releases=None)
    producer = relation(1, 2, "Producer", releases=release_years({"9": 2001}))
    links = {member.link_key: member, producer.link_key: producer}

    years_by_pair: dict[tuple[int, int], dict[str, int | None]] = {
        (1, 2): {"4": 1994, "8": 1999},
    }
    filled = apply_cross_role_release_years(links, years_by_pair)

    assert filled == 1
    assert links[member.link_key].as_json()["years"] == [1994, 1999]
    assert links[producer.link_key].releases == {"9": 2001}


def test_restrict_links_to_year_bounds_drops_a_link_whose_years_miss_the_range() -> None:
    outside = relation(1, 2, "Alias", releases=release_years({"4": 1960, "5": 2005}))
    undated = relation(1, 3, "Member Of", releases=None)
    links = {outside.link_key: outside, undated.link_key: undated}

    kept = restrict_links_to_year_bounds(links, 1970, 1979)

    assert list(kept) == [undated.link_key]


def test_restrict_links_to_year_bounds_keeps_only_years_inside_the_range() -> None:
    mixed = relation(1, 2, "Alias", releases=release_years({"4": 1975, "5": 1960, "6": None}))

    kept = restrict_links_to_year_bounds({mixed.link_key: mixed}, 1970, 1979)

    assert kept[mixed.link_key].as_json()["years"] == [1975]
    assert kept[mixed.link_key].releases == {"4": 1975, "6": None}


def test_drop_undated_center_member_links_removes_empty_memberships_in_a_year_range() -> None:
    member = relation(1, 2, "Member Of", releases=None)
    alias = relation(1, 3, "Alias", releases=None)
    dated = relation(1, 4, "Member Of", releases=release_years({"9": 1975}))
    outer = relation(2, 5, "Member Of", releases=None)
    center = _node(1, "Center", {"Producer": 1})
    center.links.update({member.link_key, alias.link_key, dated.link_key})
    nodes = {center.entity.id: center}
    links = {
        member.link_key: member,
        alias.link_key: alias,
        dated.link_key: dated,
        outer.link_key: outer,
    }

    kept = drop_undated_center_member_links(links, nodes, center.entity.id, 1970, 1979)

    assert set(kept) == {alias.link_key, dated.link_key, outer.link_key}
    assert drop_undated_center_member_links(links, nodes, center.entity.id, None, None) is links


def test_restrict_links_to_year_bounds_leaves_links_alone_when_unbounded() -> None:
    link = relation(1, 2, "Alias", releases=release_years({"4": 1960}))
    links = {link.link_key: link}

    assert restrict_links_to_year_bounds(links, None, None) is links


def test_relation_limit_reached() -> None:
    assert relation_limit_reached(distance=0, relation_count=0, max_links=20)
    assert not relation_limit_reached(distance=0, relation_count=20, max_links=20)
    assert relation_limit_reached(distance=2, relation_count=20, max_links=20)
    assert relation_limit_reached(distance=0, relation_count=60, max_links=20)
