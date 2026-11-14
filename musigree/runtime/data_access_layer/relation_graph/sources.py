"""Load entities and relations from the runtime repositories."""

from typing import TYPE_CHECKING, Protocol, cast

from musigree.runtime.data_access_layer.runtime_relation_data_access import (
    RuntimeRelationDataAccess,
)

if TYPE_CHECKING:
    from musigree.runtime.runtime_database.runtime_entity_repository import (
        RuntimeEntityRepository,
    )
    from musigree.runtime.runtime_database.runtime_relation_repository import (
        RuntimeRelationRepository,
    )
    from musigree.runtime.runtime_domain.runtime_entity import RuntimeEntity
    from musigree.runtime.runtime_domain.runtime_relation import RuntimeRelationResult

# One IN-list this size stays within a single query for the usual node cap.
ENTITY_LOOKUP_BATCH_SIZE = 1000


class EntitySource(Protocol):
    """Loads entities by internal id."""

    async def load(self, entity_ids: list[int]) -> list[RuntimeEntity]:
        """Return the entities that exist for these ids."""
        ...


class RelationQuery(Protocol):
    """Fetches relation rows for a set of entities. The result may be truncated."""

    async def fetch(
        self,
        entity_ids: list[int],
        role_names: list[str],
        limit: int,
    ) -> list[RuntimeRelationResult]:
        """Return up to ``limit`` relations touching ``entity_ids``."""
        ...


class ProbeReleaseLookup(Protocol):
    """Release years for specific entity pairs, across every role."""

    async def release_years_for_probes(
        self,
        probes: dict[int, set[int]],
    ) -> dict[tuple[int, int], dict[str, int | None]]:
        """Return release id to year for each probed pair that has a dated release."""
        ...


def supports_probe_release_lookup(source: object) -> bool:
    """True when this object's class implements the pair year lookup.

    Checking the class avoids treating a mock as a lookup. A mock answers
    ``hasattr`` for every name.
    """
    return callable(getattr(type(source), "release_years_for_probes", None))


def as_probe_release_lookup(source: object) -> ProbeReleaseLookup | None:
    """Return the source when its class implements the pair year lookup.

    ``RelationSource`` and ``ProbeReleaseLookup`` do not share a base. The
    cast is from ``object``, after the class method has been checked.
    """
    if not supports_probe_release_lookup(source):
        return None
    return cast("ProbeReleaseLookup", source)


class RelationSource(Protocol):
    """Relations for a frontier, optionally remembering the small neighborhoods."""

    async def load(
        self,
        entity_ids: list[int],
        role_names: list[str],
        per_entity_limit: int,
        *,
        cacheable_ids: set[int] | None = None,
    ) -> list[RuntimeRelationResult]:
        """Return relations for ``entity_ids`` in ``role_names``."""
        ...


class RepositoryEntitySource:
    """Entity loader backed by ``RuntimeEntityRepository.search_multi``."""

    def __init__(self, repository: RuntimeEntityRepository) -> None:
        self._repository = repository

    async def load(self, entity_ids: list[int]) -> list[RuntimeEntity]:
        if not entity_ids:
            return []
        entities: list[RuntimeEntity] = []
        stop = len(entity_ids)
        for start in range(0, stop, ENTITY_LOOKUP_BATCH_SIZE):
            found = await self._repository.search_multi(entity_ids[start : start + ENTITY_LOOKUP_BATCH_SIZE])
            entities.extend(found)
        return entities


class DatabaseRelationQuery:
    """One relation query for the ids that were not already cached."""

    def __init__(
        self,
        repository: RuntimeRelationRepository,
        *,
        min_year: int | None = None,
        max_year: int | None = None,
    ) -> None:
        self._repository = repository
        self._min_year = min_year
        self._max_year = max_year

    async def fetch(
        self,
        entity_ids: list[int],
        role_names: list[str],
        limit: int,
    ) -> list[RuntimeRelationResult]:
        if not entity_ids or not role_names or limit <= 0:
            return []
        return await RuntimeRelationDataAccess.search_multi(
            relation_repository=self._repository,
            ids=entity_ids,
            role_names=role_names,
            limit=limit,
            min_year=self._min_year,
            max_year=self._max_year,
        )

    async def release_years_for_probes(
        self,
        probes: dict[int, set[int]],
    ) -> dict[tuple[int, int], dict[str, int | None]]:
        # Every dated year is returned. The graph then drops a link whose
        # years all miss the request bounds, and trims the years it keeps.
        return await self._repository.find_release_years_for_probes(probes)
