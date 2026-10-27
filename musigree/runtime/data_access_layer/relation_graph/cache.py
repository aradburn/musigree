"""Cache structural links and small relational neighborhoods."""

import json
import logging
from typing import Any

from pydantic import ValidationError

from musigree.library.cache.cache_manager import BaseCache, CacheManager
from musigree.library.fields.entity_id import to_entity_internal_id
from musigree.runtime.data_access_layer.relation_graph.sources import RelationQuery
from musigree.runtime.data_access_layer.runtime_entity_data_access import (
    RuntimeEntityDataAccess,
)
from musigree.runtime.runtime_domain.runtime_entity import RuntimeEntity
from musigree.runtime.runtime_domain.runtime_relation import RuntimeRelationResult

log = logging.getLogger(__name__)


def structural_cache_key(entity_id: int, role_names: list[str]) -> str:
    roles = ",".join(sorted(role_names))
    return f"relation:structural:{entity_id}:{roles}"


def neighborhood_cache_key(
    entity_id: int,
    role_names: list[str],
    min_year: int | None = None,
    max_year: int | None = None,
) -> str:
    """Identify a cached neighborhood by entity, roles, and year bounds.

    Missing bounds use ``*`` so an unfiltered neighborhood cannot be reused
    for a filtered request.
    """
    roles = ",".join(sorted(role_names))
    lower = "*" if min_year is None else str(min_year)
    upper = "*" if max_year is None else str(max_year)
    return f"relation:neighborhood:{entity_id}:{roles}:min={lower}:max={upper}"


def active_cache() -> BaseCache | None:
    """Return the process cache when one is configured."""
    cache = CacheManager.cache
    if isinstance(cache, BaseCache):
        return cache
    return None


def relation_to_payload(relation: RuntimeRelationResult) -> dict[str, Any]:
    payload = relation.model_dump(mode="json")
    payload["entity_one_type"] = relation.entity_one_type.value
    payload["entity_two_type"] = relation.entity_two_type.value
    return payload


def relations_from_payload(raw: str) -> list[RuntimeRelationResult] | None:
    try:
        payload = json.loads(raw)
        return [RuntimeRelationResult.model_validate(item) for item in payload]
    except json.JSONDecodeError, ValidationError, TypeError:
        return None


async def read_cached_relations(cache: BaseCache, key: str) -> list[RuntimeRelationResult] | None:
    raw = await cache.get(key)
    if raw is None:
        return None
    return relations_from_payload(raw)


async def write_cached_relations(
    cache: BaseCache,
    key: str,
    relations: list[RuntimeRelationResult],
) -> None:
    payload = json.dumps([relation_to_payload(relation) for relation in relations])
    await cache.set(key, payload)


def group_by_endpoint(
    relations: list[RuntimeRelationResult],
    entity_ids: set[int],
) -> dict[int, list[RuntimeRelationResult]]:
    """Index relations by each requested end, so one row can fill two caches."""
    grouped: dict[int, list[RuntimeRelationResult]] = {entity_id: [] for entity_id in entity_ids}
    for relation in relations:
        id_one = to_entity_internal_id(relation.entity_one_id, relation.entity_one_type)
        id_two = to_entity_internal_id(relation.entity_two_id, relation.entity_two_type)
        if id_one in grouped:
            grouped[id_one].append(relation)
        if id_two in grouped and id_two != id_one:
            grouped[id_two].append(relation)
    return grouped


async def cached_structural_links(
    entity: RuntimeEntity,
    role_names: list[str],
) -> dict[str, RuntimeRelationResult]:
    """Structural links for one entity, reused across searches until the cache is cleared."""
    cache = active_cache()
    if cache is not None and role_names:
        cached = await read_cached_relations(cache, structural_cache_key(entity.id, role_names))
        if cached is not None:
            return {relation.link_key: relation for relation in cached}
    fresh = RuntimeEntityDataAccess.structural_roles_to_relations(entity, role_names)
    if cache is not None and role_names:
        await write_cached_relations(
            cache,
            structural_cache_key(entity.id, role_names),
            list(fresh.values()),
        )
    return fresh


class CachingRelationSource:
    """Relation source that remembers per-entity neighborhoods.

    A batch is cached only when the query did not hit its limit. Hitting
    the limit means some rows were dropped, so the per-entity lists would
    be incomplete. Hubs are omitted from ``cacheable_ids`` by the caller.
    """

    def __init__(
        self,
        query: RelationQuery,
        *,
        min_year: int | None = None,
        max_year: int | None = None,
    ) -> None:
        self._query = query
        self._min_year = min_year
        self._max_year = max_year

    async def load(
        self,
        entity_ids: list[int],
        role_names: list[str],
        per_entity_limit: int,
        *,
        cacheable_ids: set[int] | None = None,
    ) -> list[RuntimeRelationResult]:
        if not entity_ids or not role_names or per_entity_limit <= 0:
            return []
        cache = active_cache()
        if cache is None:
            limit = len(entity_ids) * per_entity_limit
            return await self._query.fetch(entity_ids, role_names, limit)

        hits: list[RuntimeRelationResult] = []
        misses: list[int] = []
        for entity_id in entity_ids:
            cached = await read_cached_relations(
                cache,
                neighborhood_cache_key(
                    entity_id,
                    role_names,
                    self._min_year,
                    self._max_year,
                ),
            )
            if cached is None:
                misses.append(entity_id)
            else:
                hits.extend(cached)
        if not misses:
            return hits

        limit = len(misses) * per_entity_limit
        fresh = await self._query.fetch(misses, role_names, limit)
        truncated = len(fresh) == limit
        if not truncated:
            allowed = set(misses) if cacheable_ids is None else cacheable_ids
            grouped = group_by_endpoint(fresh, set(misses))
            for entity_id, relations in grouped.items():
                if entity_id not in allowed:
                    continue
                await write_cached_relations(
                    cache,
                    neighborhood_cache_key(
                        entity_id,
                        role_names,
                        self._min_year,
                        self._max_year,
                    ),
                    relations,
                )
        return hits + fresh
