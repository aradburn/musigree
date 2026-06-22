"""
Unit tests for RuntimeRelationDataAccess class.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from musigree.library.fields.entity_id import to_entity_internal_id
from musigree.library.fields.entity_type import EntityType
from musigree.offline.offline_domain.relation import RelationDB
from musigree.runtime.data_access_layer.runtime_relation_data_access import (
    RuntimeRelationDataAccess,
)
from musigree.runtime.runtime_domain.runtime_relation import (
    RuntimeRelation,
    RuntimeRelationInternal,
)


class TestGetRuntimeRelationDictsFromRelations:
    """Test get_runtime_relation_dicts_from_relations static method."""

    @patch("musigree.runtime.runtime_database_manager.RuntimeDatabaseManager.runtime_database_helper", MagicMock())
    def test_returns_list_of_dicts(self) -> None:
        """Test that relation_dbs are converted to runtime relation dicts."""
        relation_dbs = [
            RelationDB(
                id=1,
                subject=100,
                predicate=1,
                object=200,
                release_id=10,
                year=2020,
            ),
        ]
        result = RuntimeRelationDataAccess.get_runtime_relation_dicts_from_relations(
            relation_dbs
        )
        assert len(result) == 1
        assert isinstance(result[0], dict)
        assert result[0]["id"] == 1
        assert result[0]["subject"] == 100
        assert result[0]["object"] == 200
        assert result[0]["release_id"] == 10
        assert result[0]["year"] == 2020

    @patch("musigree.runtime.runtime_database_manager.RuntimeDatabaseManager.runtime_database_helper", MagicMock())
    def test_empty_list_returns_empty_list(self) -> None:
        """Test empty relation_dbs returns empty list."""
        result = RuntimeRelationDataAccess.get_runtime_relation_dicts_from_relations([])
        assert result == []


class TestSearchMulti:
    """Test search_multi class method."""

    @pytest.mark.asyncio
    @patch("musigree.runtime.data_access_layer.runtime_relation_data_access.RoleCache")
    async def test_search_multi_returns_relations_from_repository(
        self, mock_role_cache: MagicMock
    ) -> None:
        """Test search_multi aggregates relations from repository and groups by link_key."""
        mock_role_cache.role_name_to_role_id_lookup = {"Alias": 1}

        mock_repo = MagicMock()
        internal_id = to_entity_internal_id(1, EntityType.ARTIST)
        internal = RuntimeRelationInternal(
            id=1,
            subject=internal_id,
            role="Alias",
            object=200,
            release_id=10,
            year=2020,
        )
        mock_repo.find_by_entity_and_roles = AsyncMock(return_value=[internal])

        result = await RuntimeRelationDataAccess.search_multi(
            relation_repository=mock_repo,
            ids=[internal_id],
            role_names=["Alias"],
        )

        assert len(result) == 1
        assert isinstance(result[0], RuntimeRelation)
        mock_repo.find_by_entity_and_roles.assert_called_once_with(internal_id, [1])

    @pytest.mark.asyncio
    async def test_search_multi_empty_ids_asserts(self) -> None:
        """Test search_multi with empty ids raises AssertionError."""
        mock_repo = MagicMock()
        with pytest.raises(AssertionError):
            await RuntimeRelationDataAccess.search_multi(
                relation_repository=mock_repo,
                ids=[],
                role_names=["Alias"],
            )

    @pytest.mark.asyncio
    async def test_search_multi_empty_role_names_asserts(self) -> None:
        """Test search_multi with empty role_names raises AssertionError."""
        mock_repo = MagicMock()
        with pytest.raises(AssertionError):
            await RuntimeRelationDataAccess.search_multi(
                relation_repository=mock_repo,
                ids=[to_entity_internal_id(1, EntityType.ARTIST)],
                role_names=[],
            )
