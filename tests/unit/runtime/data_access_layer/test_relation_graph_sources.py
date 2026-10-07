"""Unit tests for repository-backed graph sources."""

from unittest.mock import AsyncMock, patch

import pytest

from musigree.runtime.data_access_layer.relation_graph.sources import (
    ENTITY_LOOKUP_BATCH_SIZE,
    DatabaseRelationQuery,
    RepositoryEntitySource,
)


@pytest.mark.asyncio
async def test_repository_entity_source_chunks_large_id_lists() -> None:
    repository = AsyncMock()
    repository.search_multi.side_effect = [["first"], ["second"]]
    entity_ids = list(range(ENTITY_LOOKUP_BATCH_SIZE + 1))

    found = await RepositoryEntitySource(repository).load(entity_ids)

    assert found == ["first", "second"]
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
