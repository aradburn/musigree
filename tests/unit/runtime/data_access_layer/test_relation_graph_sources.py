"""Unit tests for repository-backed graph sources."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from musigree.runtime.data_access_layer.relation_graph.sources import (
    ENTITY_LOOKUP_BATCH_SIZE,
    DatabaseRelationQuery,
    RepositoryEntitySource,
    as_probe_release_lookup,
)
from tests.type_helpers import as_object


@pytest.mark.asyncio
async def test_repository_entity_source_chunks_large_id_lists() -> None:
    repository = AsyncMock()
    repository.search_multi.side_effect = [["first"], ["second"]]
    entity_ids = list(range(ENTITY_LOOKUP_BATCH_SIZE + 1))

    found = await RepositoryEntitySource(repository).load(entity_ids)

    assert as_object(found) == ["first", "second"]
    assert repository.search_multi.await_count == 2
    assert len(repository.search_multi.await_args_list[0].args[0]) == ENTITY_LOOKUP_BATCH_SIZE
    assert repository.search_multi.await_args_list[1].args[0] == [ENTITY_LOOKUP_BATCH_SIZE]


@pytest.mark.asyncio
async def test_database_relation_query_passes_the_limit_through() -> None:
    with patch(
        "musigree.runtime.data_access_layer.relation_graph.sources.RuntimeRelationDataAccess.search_multi",
        new_callable=AsyncMock,
        return_value=[],
    ) as search_multi:
        await DatabaseRelationQuery(AsyncMock()).fetch([10, 11], ["Artist"], 40)

    assert search_multi.await_args is not None
    assert search_multi.await_args.kwargs["ids"] == [10, 11]
    assert search_multi.await_args.kwargs["role_names"] == ["Artist"]
    assert search_multi.await_args.kwargs["limit"] == 40


@pytest.mark.asyncio
async def test_database_relation_query_loads_every_dated_year_for_probes() -> None:
    """Link membership is decided later, so the probe lookup is not pre-filtered."""
    repository = AsyncMock()
    years_by_pair: dict[tuple[int, int], dict[str, int | None]] = {
        (1, 2): {"9": 1994, "10": 1960},
    }
    repository.find_release_years_for_probes.return_value = years_by_pair
    query = DatabaseRelationQuery(repository, min_year=1990, max_year=1999)

    found = await query.release_years_for_probes({1: {2}})

    assert found == {(1, 2): {"9": 1994, "10": 1960}}
    repository.find_release_years_for_probes.assert_awaited_once_with({1: {2}})


def test_as_probe_release_lookup_accepts_only_classes_that_define_the_method() -> None:
    """A mock answers hasattr for every name, so only a real class method counts."""

    class Lookup:
        @staticmethod
        async def release_years_for_probes(
            _probes: dict[int, set[int]],
        ) -> dict[tuple[int, int], dict[str, int | None]]:
            return {}

    class Plain:
        pass

    lookup = Lookup()
    query = DatabaseRelationQuery(AsyncMock())

    assert as_probe_release_lookup(lookup) is lookup
    assert as_probe_release_lookup(query) is query
    assert as_probe_release_lookup(Plain()) is None
    assert as_probe_release_lookup(MagicMock()) is None
