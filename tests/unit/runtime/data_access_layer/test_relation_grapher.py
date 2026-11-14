"""Unit tests for RelationGrapher."""

from typing import overload
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
from tests.release_years import release_years

ROLE_LOOKUP = {
    "Artist": 1,
    "Alias": 3,
    "Member Of": 4,
    "Sublabel Of": 5,
    "Producer": 6,
    "Released On": 7,
}


@overload
def artist(
    entity_id: int,
    name: str,
    *,
    relation_counts: dict[str, int] = ...,
    entities: dict[str, object] = ...,
) -> RuntimeEntity: ...


@overload
def artist(
    entity_id: int,
    name: str,
    *,
    relation_counts: None = None,
    entities: None = None,
) -> RuntimeEntity: ...


def artist(
    entity_id: int,
    name: str,
    *,
    relation_counts: dict[str, int] | None = None,
    entities: dict[str, object] | None = None,
) -> RuntimeEntity:
    # Callers that pass a dict match the overload above, so literal keys are
    # widened. None is the runtime default and is not a shared mutable value.
    return RuntimeEntity(
        id=to_entity_internal_id(entity_id, EntityType.ARTIST),
        entity_id=entity_id,
        entity_type=EntityType.ARTIST,
        entity_name=name,
        relation_counts=dict(relation_counts or {}),
        entity_metadata={},
        entities=dict(entities or {}),
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
        releases=release_years({"9": 2001}),
        role="Producer",
        distance=None,
    )
    alias_years = RuntimeRelationResult(
        entity_one_id=20,
        entity_one_type=EntityType.ARTIST,
        entity_two_id=10,
        entity_two_type=EntityType.ARTIST,
        releases=release_years({"4": 1994, "5": None}),
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
async def test_assemble_network_fills_structural_years_from_other_roles() -> None:
    alias_internal_id = to_entity_internal_id(20, EntityType.ARTIST)
    center = artist(
        10,
        "Center",
        relation_counts={"Producer": 50},
        entities={"aliases": {"stage": alias_internal_id}},
    )
    alias = artist(20, "Stage Name")
    entities = MemoryEntitySource({center.id: center, alias.id: alias})

    class YearLookup(MemoryRelationSource):
        def __init__(self) -> None:
            super().__init__({})
            self.probes: dict[int, set[int]] | None = None

        async def release_years_for_probes(
            self,
            probes: dict[int, set[int]],
        ) -> dict[tuple[int, int], dict[str, int | None]]:
            self.probes = {probe: set(partners) for probe, partners in probes.items()}
            years: dict[tuple[int, int], dict[str, int | None]] = {
                (10, 20): {"4": 1994, "5": None},
            }
            return years

    relations = YearLookup()
    network = await assemble_network(
        center_entity=center,
        limits=GraphLimits(degree=1, max_nodes=100, link_ratio=10),
        roles=RolePartition(("Alias",), ()),
        entity_source=entities,
        relation_source=relations,
    )

    links = {link["role"]: link for link in network["links"]}
    assert links["Alias"]["years"] == [1994]
    assert relations.probes == {alias.id: {center.id}}


@pytest.mark.asyncio
async def test_assemble_network_looks_up_years_only_for_links_touching_the_center() -> None:
    alias_internal_id = to_entity_internal_id(20, EntityType.ARTIST)
    group_internal_id = to_entity_internal_id(30, EntityType.ARTIST)
    center = artist(
        10,
        "Center",
        relation_counts={"Producer": 50},
        entities={"aliases": {"stage": alias_internal_id}},
    )
    alias = artist(
        20,
        "Stage Name",
        entities={"groups": {"band": group_internal_id}},
    )
    group = artist(30, "Band", relation_counts={"Producer": 10})
    entities = MemoryEntitySource({center.id: center, alias.id: alias, group.id: group})

    class YearLookup(MemoryRelationSource):
        def __init__(self) -> None:
            super().__init__({})
            self.probes: dict[int, set[int]] | None = None

        async def release_years_for_probes(
            self,
            probes: dict[int, set[int]],
        ) -> dict[tuple[int, int], dict[str, int | None]]:
            self.probes = {probe: set(partners) for probe, partners in probes.items()}
            available: dict[tuple[int, int], dict[str, int | None]] = {
                (10, 20): {"4": 1994},
                (20, 30): {"8": 2001},
            }
            found: dict[tuple[int, int], dict[str, int | None]] = {}
            for probe, partners in probes.items():
                for partner in partners:
                    pair = (probe, partner) if probe < partner else (partner, probe)
                    years = available.get(pair)
                    if years is not None:
                        found[pair] = years
            return found

    relations = YearLookup()
    network = await assemble_network(
        center_entity=center,
        limits=GraphLimits(degree=2, max_nodes=100, link_ratio=10),
        roles=RolePartition(("Alias", "Member Of"), ()),
        entity_source=entities,
        relation_source=relations,
    )

    links = {link["key"]: link for link in network["links"]}
    assert links["artist-10-alias-artist-20"]["years"] == [1994]
    assert links["artist-20-member-of-artist-30"]["years"] == []
    assert relations.probes == {alias.id: {center.id}}


@pytest.mark.asyncio
async def test_assemble_network_drops_links_outside_the_year_bounds() -> None:
    alias_internal_id = to_entity_internal_id(20, EntityType.ARTIST)
    kept_internal_id = to_entity_internal_id(30, EntityType.ARTIST)
    center = artist(
        10,
        "Center",
        relation_counts={"Producer": 50},
        entities={"aliases": {"early": alias_internal_id, "later": kept_internal_id}},
    )
    early = artist(20, "Early Alias")
    later = artist(30, "Later Alias")
    entities = MemoryEntitySource({center.id: center, early.id: early, later.id: later})

    class YearLookup(MemoryRelationSource):
        @staticmethod
        async def release_years_for_probes(
            probes: dict[int, set[int]],
        ) -> dict[tuple[int, int], dict[str, int | None]]:
            del probes
            years: dict[tuple[int, int], dict[str, int | None]] = {
                (10, 20): {"1": 1960},
                (10, 30): {"2": 1975, "3": 2001},
            }
            return years

    network = await assemble_network(
        center_entity=center,
        limits=GraphLimits(degree=1, max_nodes=100, link_ratio=10),
        roles=RolePartition(("Alias",), ()),
        entity_source=entities,
        relation_source=YearLookup({}),
        min_year=1970,
        max_year=1979,
    )

    assert [node["name"] for node in network["nodes"]] == ["Center", "Later Alias"]
    links = {link["role"]: link for link in network["links"]}
    assert list(links) == ["Alias"]
    assert links["Alias"]["years"] == [1975]
    assert links["Alias"]["target"] == "artist-30"


@pytest.mark.asyncio
async def test_assemble_network_drops_undated_center_memberships_in_a_year_range() -> None:
    alias_internal_id = to_entity_internal_id(20, EntityType.ARTIST)
    group_internal_id = to_entity_internal_id(30, EntityType.ARTIST)
    center = artist(
        10,
        "Center",
        relation_counts={"Producer": 5},
        entities={
            "aliases": {"stage": alias_internal_id},
            "groups": {"band": group_internal_id},
        },
    )
    alias = artist(20, "Stage Name")
    group = artist(30, "Band")
    entities = MemoryEntitySource({center.id: center, alias.id: alias, group.id: group})

    class YearLookup(MemoryRelationSource):
        @staticmethod
        async def release_years_for_probes(
            probes: dict[int, set[int]],
        ) -> dict[tuple[int, int], dict[str, int | None]]:
            del probes
            return {}

    network = await assemble_network(
        center_entity=center,
        limits=GraphLimits(degree=1, max_nodes=100, link_ratio=10),
        roles=RolePartition(("Alias", "Member Of"), ()),
        entity_source=entities,
        relation_source=YearLookup({}),
        min_year=1970,
        max_year=1979,
    )

    assert [node["name"] for node in network["nodes"]] == ["Center", "Stage Name"]
    assert [link["role"] for link in network["links"]] == ["Alias"]


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
