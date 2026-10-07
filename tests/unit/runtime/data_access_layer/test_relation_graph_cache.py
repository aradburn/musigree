"""Unit tests for relation neighborhood caching."""

from collections.abc import Iterator

import pytest

from musigree.library.cache.cache_manager import CacheManager, SimpleCache
from musigree.library.fields.entity_id import to_entity_internal_id
from musigree.library.fields.entity_type import EntityType
from musigree.runtime.data_access_layer.relation_graph.cache import (
    CachingRelationSource,
    cached_structural_links,
    neighborhood_cache_key,
    structural_cache_key,
)
from musigree.runtime.runtime_domain.runtime_entity import RuntimeEntity
from musigree.runtime.runtime_domain.runtime_relation import RuntimeRelationResult


def artist(
    entity_id: int, name: str, *, entities: dict[str, object] | None = None
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


def relation(one: int, two: int, role: str = "Producer") -> RuntimeRelationResult:
    return RuntimeRelationResult(
        entity_one_id=one,
        entity_one_type=EntityType.ARTIST,
        entity_two_id=two,
        entity_two_type=EntityType.ARTIST,
        releases={"1": 1999},
        role=role,
        distance=None,
    )


class RecordingQuery:
    """Relation query that records each fetch and can pretend the batch was cut off."""

    def __init__(self, relations: list[RuntimeRelationResult], *, truncated: bool = False) -> None:
        self.relations = relations
        self.truncated = truncated
        self.calls: list[tuple[list[int], list[str], int]] = []

    async def fetch(
        self,
        entity_ids: list[int],
        role_names: list[str],
        limit: int,
    ) -> list[RuntimeRelationResult]:
        self.calls.append((list(entity_ids), list(role_names), limit))
        if self.truncated:
            return self.relations * limit
        return list(self.relations)


@pytest.fixture
def memory_cache() -> Iterator[SimpleCache]:
    cache = SimpleCache()
    previous = CacheManager.cache
    CacheManager.cache = cache
    try:
        yield cache
    finally:
        CacheManager.cache = previous


@pytest.mark.asyncio
async def test_neighborhood_cache_fetches_each_entity_once(memory_cache: SimpleCache) -> None:
    query = RecordingQuery([relation(1, 2)])
    source = CachingRelationSource(query)

    first = await source.load([1, 2], ["Producer"], per_entity_limit=10)
    second = await source.load([1], ["Producer"], per_entity_limit=10)

    assert len(query.calls) == 1
    assert query.calls[0][2] == 20
    assert {item.entity_two_id for item in first} == {2}
    assert second[0].link_key == first[0].link_key
    assert await memory_cache.get(neighborhood_cache_key(2, ["Producer"])) is not None


@pytest.mark.asyncio
async def test_neighborhood_cache_stores_an_empty_list(memory_cache: SimpleCache) -> None:
    query = RecordingQuery([])
    source = CachingRelationSource(query)

    await source.load([5], ["Producer"], per_entity_limit=10)
    await source.load([5], ["Producer"], per_entity_limit=10)

    assert len(query.calls) == 1
    assert await memory_cache.get(neighborhood_cache_key(5, ["Producer"])) == "[]"


@pytest.mark.asyncio
async def test_neighborhood_cache_skips_hubs_and_truncated_batches(
    memory_cache: SimpleCache,
) -> None:
    hub_query = RecordingQuery([relation(1, 2)])
    source = CachingRelationSource(hub_query)
    await source.load([1], ["Producer"], per_entity_limit=10, cacheable_ids=set())
    await source.load([1], ["Producer"], per_entity_limit=10, cacheable_ids=set())
    assert len(hub_query.calls) == 2

    truncated = RecordingQuery([relation(3, 4)], truncated=True)
    source = CachingRelationSource(truncated)
    await source.load([3], ["Producer"], per_entity_limit=2)
    await source.load([3], ["Producer"], per_entity_limit=2)
    assert len(truncated.calls) == 2
    assert await memory_cache.get(neighborhood_cache_key(3, ["Producer"])) is None


@pytest.mark.asyncio
async def test_structural_cache_is_separate_from_neighborhoods(memory_cache: SimpleCache) -> None:
    entity = artist(10, "Center", entities={"aliases": {"alias": 20}})

    first = await cached_structural_links(entity, ["Alias"])
    second = await cached_structural_links(entity, ["Alias"])

    assert set(first) == set(second)
    assert await memory_cache.get(structural_cache_key(entity.id, ["Alias"])) is not None
    assert await memory_cache.get(neighborhood_cache_key(entity.id, ["Alias"])) is None


@pytest.mark.asyncio
async def test_load_without_a_cache_still_returns_relations() -> None:
    previous = CacheManager.cache
    CacheManager.cache = None
    try:
        query = RecordingQuery([relation(1, 2)])
        found = await CachingRelationSource(query).load([1], ["Producer"], per_entity_limit=4)
    finally:
        CacheManager.cache = previous

    assert len(found) == 1
    assert query.calls[0][2] == 4
