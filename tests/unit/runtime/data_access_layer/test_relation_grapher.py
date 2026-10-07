"""Unit tests for RelationGrapher."""

from unittest.mock import AsyncMock

import pytest

from musigree.library.cache.role_cache import RoleCache
from musigree.library.fields.entity_id import to_entity_internal_id
from musigree.library.fields.entity_type import EntityType
from musigree.runtime.data_access_layer.relation_graph.assemble import assemble_network
from musigree.runtime.data_access_layer.relation_graph.limits import GraphLimits
from musigree.runtime.data_access_layer.relation_graph.roles import RolePartition
from musigree.runtime.data_access_layer.relation_grapher import RelationGrapher
from musigree.runtime.runtime_domain.runtime_entity import RuntimeEntity
from musigree.runtime.runtime_domain.runtime_relation import RuntimeRelationResult

ROLE_LOOKUP = {
    "Artist": 1,
    "Alias": 3,
    "Member Of": 4,
    "Sublabel Of": 5,
    "Producer": 6,
    "Released On": 7,
}


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


def label(entity_id: int, name: str) -> RuntimeEntity:
    return RuntimeEntity(
        id=to_entity_internal_id(entity_id, EntityType.LABEL),
        entity_id=entity_id,
        entity_type=EntityType.LABEL,
        entity_name=name,
        relation_counts={},
        entity_metadata={},
        countries=None,
        genres=None,
        styles=None,
    )


class MemoryEntitySource:
    def __init__(self, entities: dict[int, RuntimeEntity]) -> None:
        self.entities = entities
        self.calls: list[list[int]] = []

    async def load(self, entity_ids: list[int]) -> list[RuntimeEntity]:
        self.calls.append(list(entity_ids))
        return [self.entities[entity_id] for entity_id in entity_ids if entity_id in self.entities]


class MemoryRelationSource:
    def __init__(self, by_entity: dict[int, list[RuntimeRelationResult]]) -> None:
        self.by_entity = by_entity
        self.calls: list[list[int]] = []

    async def load(
        self,
        entity_ids: list[int],
        role_names: list[str],
        per_entity_limit: int,
        *,
        cacheable_ids: set[int] | None = None,
    ) -> list[RuntimeRelationResult]:
        del role_names, per_entity_limit, cacheable_ids
        self.calls.append(list(entity_ids))
        found: dict[str, RuntimeRelationResult] = {}
        for entity_id in entity_ids:
            for relation in self.by_entity.get(entity_id, []):
                found[relation.link_key] = relation
        return list(found.values())


@pytest.fixture
def role_lookup(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(RoleCache, "role_name_to_role_id_lookup", ROLE_LOOKUP)


def test_constructor_splits_roles_and_limits(role_lookup: None) -> None:
    center = artist(123, "Test Artist")

    grapher = RelationGrapher(
        center_entity=center,
        degree=2,
        link_ratio=15,
        max_nodes=200,
        role_names=["Artist", "Alias"],
    )

    assert grapher.center_entity == center
    assert grapher.degree == 2
    assert grapher.link_ratio == 15
    assert grapher.max_nodes == 200
    assert grapher.max_links == 3000
    assert grapher.structural_role_names == ["Alias"]
    assert grapher.relational_role_names == ["Artist"]
    assert grapher.all_roles == ["Alias", "Artist"]


def test_constructor_uses_helper_defaults_when_bounds_are_omitted(
    role_lookup: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "musigree.runtime.runtime_database.runtime_database_helper.RuntimeDatabaseHelper.MAX_NODES",
        1000,
        raising=False,
    )
    monkeypatch.setattr(
        "musigree.runtime.runtime_database.runtime_database_helper.RuntimeDatabaseHelper.LINK_RATIO",
        20,
        raising=False,
    )

    grapher = RelationGrapher(
        center_entity=artist(123, "Test Artist"),
        degree=1,
        link_ratio=None,
        max_nodes=None,
        role_names=["Artist", "Alias", "Member Of"],
    )

    assert grapher.max_nodes == 1000
    assert grapher.link_ratio == 20
    assert grapher.structural_role_names == ["Alias", "Member Of"]
    assert grapher.relational_role_names == ["Artist"]


def test_constructor_rejects_a_non_positive_degree(role_lookup: None) -> None:
    with pytest.raises(ValueError, match="degree"):
        RelationGrapher(
            center_entity=artist(123, "Test Artist"),
            degree=0,
            link_ratio=10,
            max_nodes=100,
            role_names=["Artist"],
        )


def test_constructor_rejects_unknown_roles(role_lookup: None) -> None:
    with pytest.raises(ValueError, match="Unknown roles"):
        RelationGrapher(
            center_entity=artist(123, "Test Artist"),
            degree=1,
            link_ratio=10,
            max_nodes=100,
            role_names=["InvalidRole"],
        )


@pytest.mark.asyncio
async def test_assemble_network_walks_structural_and_relational_links() -> None:
    alias_internal_id = to_entity_internal_id(20, EntityType.ARTIST)
    center = artist(
        10,
        "Center",
        relation_counts={"Producer": 1},
        entities={"aliases": {"stage": alias_internal_id}},
    )
    alias = artist(20, "Stage Name")
    imprint = label(30, "Imprint")
    produced = RuntimeRelationResult(
        entity_one_id=10,
        entity_one_type=EntityType.ARTIST,
        entity_two_id=30,
        entity_two_type=EntityType.LABEL,
        releases={"9": 2001},
        role="Producer",
        distance=None,
    )
    alias_years = RuntimeRelationResult(
        entity_one_id=20,
        entity_one_type=EntityType.ARTIST,
        entity_two_id=10,
        entity_two_type=EntityType.ARTIST,
        releases={"4": 1994, "5": None},
        role="Alias",
        distance=None,
    )
    entities = MemoryEntitySource({center.id: center, alias.id: alias, imprint.id: imprint})
    relations = MemoryRelationSource({center.id: [produced, alias_years]})

    network = await assemble_network(
        center_entity=center,
        limits=GraphLimits(degree=1, max_nodes=100, link_ratio=10),
        roles=RolePartition(("Alias",), ("Producer",)),
        entity_source=entities,
        relation_source=relations,
    )

    assert network["center"] == {"key": "artist-10", "name": "Center"}
    nodes = {node["name"]: node for node in network["nodes"]}
    assert set(nodes) == {"Center", "Stage Name", "Imprint"}
    assert nodes["Center"]["distance"] == 0
    assert nodes["Stage Name"]["distance"] == 1
    assert nodes["Center"]["cluster"] > 0
    links = {link["role"]: link for link in network["links"]}
    assert set(links) == {"Alias", "Producer"}
    assert links["Alias"]["years"] == [1994]
    assert links["Producer"]["years"] == [2001]
    assert relations.calls == [[center.id]]


@pytest.mark.asyncio
async def test_get_relation_graph_uses_injected_sources(role_lookup: None) -> None:
    center = artist(10, "Center")
    entities = MemoryEntitySource({center.id: center})
    relations = MemoryRelationSource({})
    grapher = RelationGrapher(
        center_entity=center,
        degree=1,
        link_ratio=10,
        max_nodes=20,
        role_names=["Artist"],
        entity_source=entities,
        relation_source=relations,
    )

    network = await grapher.get_relation_graph(AsyncMock(), AsyncMock())

    assert network["center"]["name"] == "Center"
    assert [node["name"] for node in network["nodes"]] == ["Center"]
    assert entities.calls[0] == [center.id]
    assert relations.calls == [[center.id]]
