"""Unit tests for merging and storing relation links."""

from musigree.library.fields.entity_id import to_entity_internal_id
from musigree.library.fields.entity_type import EntityType
from musigree.runtime.data_access_layer.relation_graph.relations import (
    commit_relations,
    merge_database_relations,
    relation_limit_reached,
)
from musigree.runtime.data_access_layer.trellis_node import TrellisNode
from musigree.runtime.runtime_domain.runtime_entity import RuntimeEntity
from musigree.runtime.runtime_domain.runtime_relation import RuntimeRelationResult


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
    database = relation(456, 123, "Alias", releases={"11": 2003, "10": 1991, "12": None})
    relations = {structural.link_key: structural}

    merge_database_relations(relations, [database], {"Alias"})

    attached = relations[structural.link_key]
    assert attached.releases == {"11": 2003, "10": 1991, "12": None}
    assert attached.as_json()["years"] == [1991, 2003]
    assert len(relations) == 1


def test_merge_database_relations_keeps_relational_links() -> None:
    database = relation(1, 2, "Producer", releases={"1": 1999})
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
    outward = relation(1, 2, "Producer", releases={"1": 1999})
    self_link = relation(1, 1, "Producer", releases={"1": 1999})
    links: dict[str, RuntimeRelationResult] = {}

    next_ids = commit_relations(
        links,
        {outward.link_key: outward, self_link.link_key: self_link},
        nodes,
    )

    assert links == {outward.link_key: outward}
    assert next_ids == [to_entity_internal_id(2, EntityType.ARTIST)]


def test_commit_relations_keeps_release_years_already_stored() -> None:
    stored = relation(1, 2, "Producer", releases={"1": 1999})
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


def test_relation_limit_reached() -> None:
    assert relation_limit_reached(distance=0, relation_count=0, max_links=20)
    assert not relation_limit_reached(distance=0, relation_count=20, max_links=20)
    assert relation_limit_reached(distance=2, relation_count=20, max_links=20)
    assert relation_limit_reached(distance=0, relation_count=60, max_links=20)
