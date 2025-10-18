"""
Unit tests for the EntityDataAccess class.

This module contains comprehensive unit tests for the EntityDataAccess class,
which provides data access functionality for entities within the Musigree offline system.
It tests entity reference resolution, release reference resolution, entity caching,
and text search index initialization.
"""

import logging
from typing import AsyncGenerator, Any
from unittest.mock import AsyncMock, Mock, patch

import pytest

from musigree.exceptions import NotFoundError
from musigree.library.fields.entity_type import EntityType
from musigree.offline.data_access_layer.entity_data_access import EntityDataAccess
from musigree.offline.domain.entity import Entity
from musigree.offline.domain.release import Release


class TestEntityDataAccessConstants:
    """Test class for EntityDataAccess constants."""

    def test_cache_constants(self) -> None:
        """Test that cache constants are defined correctly."""
        assert EntityDataAccess.CACHE_ENTRY_IS_NULL == "___"
        assert EntityDataAccess.CACHE_KEY_SEPARATOR == "_"


class TestResolveEntityReferences:
    """Test class for resolve_entity_references method."""

    @staticmethod
    def create_test_entity(
        entity_type: EntityType, entity_id: int = 1, entities: dict | None = None
    ) -> Entity:
        """Helper method to create a test entity."""
        return Entity(
            id=entity_id,
            entity_id=entity_id,
            entity_type=entity_type,
            entity_name="Test Entity",
            relation_counts={},
            entity_metadata={},
            entities=entities or {},
            search_content="test entity content",
        )

    @pytest.fixture
    def mock_entity_repository(self) -> AsyncMock:
        """Fixture for mock entity repository."""
        return AsyncMock()

    async def test_resolve_entity_references_no_entities(
        self, mock_entity_repository: AsyncMock
    ) -> None:
        """Test resolve_entity_references with entity that has no entities dict."""
        # Create entity and manually override the entities field to None using object.__setattr__
        # to bypass Pydantic validation for testing purposes
        entity = self.create_test_entity(EntityType.ARTIST, entities={})
        object.__setattr__(entity, "entities", None)

        result = await EntityDataAccess.resolve_entity_references(mock_entity_repository, entity)

        assert result is False
        mock_entity_repository.get_id_by_entity_type_and_entity_name.assert_not_called()

    async def test_resolve_entity_references_empty_entities(
        self, mock_entity_repository: AsyncMock
    ) -> None:
        """Test resolve_entity_references with empty entities dict."""
        entity = self.create_test_entity(EntityType.ARTIST, entities={})

        result = await EntityDataAccess.resolve_entity_references(mock_entity_repository, entity)

        assert result is False
        mock_entity_repository.get_id_by_entity_type_and_entity_name.assert_not_called()

    @patch(
        "musigree.offline.data_access_layer.entity_data_access.EntityDataAccess.get_id_by_entity_type_and_entity_name"
    )
    async def test_resolve_entity_references_artist_aliases(
        self, mock_get_id: AsyncMock, mock_entity_repository: AsyncMock
    ) -> None:
        """Test resolve_entity_references for artist with aliases."""
        entities = {"aliases": {"alias1": "", "alias2": ""}}
        entity = self.create_test_entity(EntityType.ARTIST, entities=entities)

        # Mock the get_id method to return different IDs
        mock_get_id.side_effect = [123, 456]

        result = await EntityDataAccess.resolve_entity_references(mock_entity_repository, entity)

        assert result is True
        assert isinstance(entity.entities, dict)
        assert entity.entities["aliases"]["alias1"] == 123
        assert entity.entities["aliases"]["alias2"] == 456
        assert mock_get_id.call_count == 2

    @patch(
        "musigree.offline.data_access_layer.entity_data_access.EntityDataAccess.get_id_by_entity_type_and_entity_name"
    )
    async def test_resolve_entity_references_artist_groups_and_members(
        self, mock_get_id: AsyncMock, mock_entity_repository: AsyncMock
    ) -> None:
        """Test resolve_entity_references for artist with groups and members."""
        entities = {
            "groups": {"group1": "", "group2": ""},
            "members": {"member1": "", "member2": ""},
        }
        entity = self.create_test_entity(EntityType.ARTIST, entities=entities)

        # Mock the get_id method to return different IDs
        mock_get_id.side_effect = [101, 102, 201, 202]

        result = await EntityDataAccess.resolve_entity_references(mock_entity_repository, entity)

        assert result is True
        assert isinstance(entity.entities, dict)
        assert entity.entities["groups"]["group1"] == 101
        assert entity.entities["groups"]["group2"] == 102
        assert entity.entities["members"]["member1"] == 201
        assert entity.entities["members"]["member2"] == 202
        assert mock_get_id.call_count == 4

    @patch(
        "musigree.offline.data_access_layer.entity_data_access.EntityDataAccess.get_id_by_entity_type_and_entity_name"
    )
    async def test_resolve_entity_references_label_parent_and_sublabels(
        self, mock_get_id: AsyncMock, mock_entity_repository: AsyncMock
    ) -> None:
        """Test resolve_entity_references for label with parent and sublabels."""
        entities = {
            "parent_label": {"parent1": ""},
            "sublabels": {"sub1": "", "sub2": ""},
        }
        entity = self.create_test_entity(EntityType.LABEL, entities=entities)

        # Mock the get_id method to return different IDs
        mock_get_id.side_effect = [301, 401, 402]

        result = await EntityDataAccess.resolve_entity_references(mock_entity_repository, entity)

        assert result is True
        assert isinstance(entity.entities, dict)
        assert entity.entities["parent_label"]["parent1"] == 301
        assert entity.entities["sublabels"]["sub1"] == 401
        assert entity.entities["sublabels"]["sub2"] == 402
        assert mock_get_id.call_count == 3

    @patch(
        "musigree.offline.data_access_layer.entity_data_access.EntityDataAccess.get_id_by_entity_type_and_entity_name"
    )
    async def test_resolve_entity_references_no_ids_found(
        self, mock_get_id: AsyncMock, mock_entity_repository: AsyncMock
    ) -> None:
        """Test resolve_entity_references when no IDs are found."""
        entities = {"aliases": {"alias1": "", "alias2": ""}}
        entity = self.create_test_entity(EntityType.ARTIST, entities=entities)

        # Mock the get_id method to return None (not found)
        mock_get_id.return_value = None

        result = await EntityDataAccess.resolve_entity_references(mock_entity_repository, entity)

        assert result is False
        # Original values should remain unchanged
        assert isinstance(entity.entities, dict)
        assert entity.entities["aliases"]["alias1"] == ""
        assert entity.entities["aliases"]["alias2"] == ""
        assert mock_get_id.call_count == 2

    @patch(
        "musigree.offline.data_access_layer.entity_data_access.EntityDataAccess.get_id_by_entity_type_and_entity_name"
    )
    async def test_resolve_entity_references_mixed_results(
        self, mock_get_id: AsyncMock, mock_entity_repository: AsyncMock
    ) -> None:
        """Test resolve_entity_references with mixed found and not found results."""
        entities = {"aliases": {"alias1": "", "alias2": "", "alias3": ""}}
        entity = self.create_test_entity(EntityType.ARTIST, entities=entities)

        # Mock the get_id method to return mixed results
        mock_get_id.side_effect = [123, None, 456]

        result = await EntityDataAccess.resolve_entity_references(mock_entity_repository, entity)

        assert result is True  # At least one was resolved
        assert isinstance(entity.entities, dict)
        assert entity.entities["aliases"]["alias1"] == 123
        assert entity.entities["aliases"]["alias2"] == ""  # Unchanged
        assert entity.entities["aliases"]["alias3"] == 456
        assert mock_get_id.call_count == 3

    async def test_resolve_entity_references_non_dict_entities(
        self, mock_entity_repository: AsyncMock
    ) -> None:
        """Test resolve_entity_references when entities is not a dict."""
        # Create entity and manually override the entities field to string using object.__setattr__
        # to bypass Pydantic validation for testing purposes
        entity = self.create_test_entity(EntityType.ARTIST, entities={})
        object.__setattr__(entity, "entities", "not_a_dict")

        result = await EntityDataAccess.resolve_entity_references(mock_entity_repository, entity)

        assert result is False
        mock_entity_repository.get_id_by_entity_type_and_entity_name.assert_not_called()


class TestResolveReleaseReferences:
    """Test class for resolve_release_references method."""

    @staticmethod
    def create_test_release(
        release_id: int = 1, labels: list | None = None, companies: list | None = None
    ) -> Release:
        """Helper method to create a test release."""
        return Release(
            release_id=release_id,
            title="Test Release",
            artists=[],
            labels=labels or [],
            companies=companies or [],
            extra_artists=[],
            tracklist=[],
            genres=[],
            styles=[],
            release_date=None,
            country=None,
            notes=None,
            master_id=None,
            identifiers=None,
            formats=None,
        )

    @pytest.fixture
    def mock_entity_repository(self) -> AsyncMock:
        """Fixture for mock entity repository."""
        return AsyncMock()

    @patch("musigree.offline.data_access_layer.entity_data_access.to_entity_label_internal_id")
    async def test_resolve_release_references_with_labels(
        self, mock_to_internal_id: Mock, mock_entity_repository: AsyncMock
    ) -> None:
        """Test resolve_release_references with labels."""
        # Create test data
        labels = [
            {"entity_type": EntityType.LABEL, "name": "Label1"},
            {"entity_type": EntityType.LABEL, "name": "Label2"},
        ]
        release = self.create_test_release(labels=labels)

        # Mock the repository method and internal ID conversion
        mock_entity_repository.get_entity_id_by_entity_type_and_entity_name.side_effect = [
            11,
            12,
        ]
        mock_to_internal_id.side_effect = [101, 102]

        result = await EntityDataAccess.resolve_release_references(mock_entity_repository, release)

        assert result is True
        assert mock_to_internal_id.call_count == 2
        mock_to_internal_id.assert_any_call(11)
        mock_to_internal_id.assert_any_call(12)

        # Verify repository calls
        assert mock_entity_repository.get_entity_id_by_entity_type_and_entity_name.call_count == 2
        mock_entity_repository.get_entity_id_by_entity_type_and_entity_name.assert_any_call(
            EntityType.LABEL, "Label1"
        )
        mock_entity_repository.get_entity_id_by_entity_type_and_entity_name.assert_any_call(
            EntityType.LABEL, "Label2"
        )

    @patch("musigree.offline.data_access_layer.entity_data_access.to_entity_label_internal_id")
    async def test_resolve_release_references_with_companies(
        self, mock_to_internal_id: Mock, mock_entity_repository: AsyncMock
    ) -> None:
        """Test resolve_release_references with companies."""
        # Create test data
        companies = [
            {"entity_type": EntityType.LABEL, "name": "Company1"},
            {"entity_type": EntityType.LABEL, "name": "Company2"},
        ]
        release = self.create_test_release(companies=companies)

        # Mock the repository method and internal ID conversion
        mock_entity_repository.get_entity_id_by_entity_type_and_entity_name.side_effect = [
            21,
            22,
        ]
        mock_to_internal_id.side_effect = [201, 202]

        result = await EntityDataAccess.resolve_release_references(mock_entity_repository, release)

        assert result is True
        assert mock_to_internal_id.call_count == 2

    @patch("musigree.offline.data_access_layer.entity_data_access.to_entity_label_internal_id")
    async def test_resolve_release_references_no_labels_or_companies(
        self, mock_to_internal_id: Mock, mock_entity_repository: AsyncMock
    ) -> None:
        """Test resolve_release_references with no labels or companies."""
        release = self.create_test_release()

        result = await EntityDataAccess.resolve_release_references(mock_entity_repository, release)

        assert result is False
        mock_to_internal_id.assert_not_called()

    @patch("musigree.offline.data_access_layer.entity_data_access.to_entity_label_internal_id")
    async def test_resolve_release_references_with_both(
        self, mock_to_internal_id: Mock, mock_entity_repository: AsyncMock
    ) -> None:
        """Test resolve_release_references with both labels and companies."""
        labels = [{"entity_type": EntityType.LABEL, "name": "Label1"}]
        companies = [{"entity_type": EntityType.LABEL, "name": "Company1"}]
        release = self.create_test_release(labels=labels, companies=companies)

        # Mock the repository method and internal ID conversion
        mock_entity_repository.get_entity_id_by_entity_type_and_entity_name.side_effect = [
            11,
            21,
        ]
        mock_to_internal_id.side_effect = [101, 201]

        result = await EntityDataAccess.resolve_release_references(mock_entity_repository, release)

        assert result is True
        assert mock_to_internal_id.call_count == 2


class TestGetIdByEntityTypeAndEntityName:
    """Test class for get_id_by_entity_type_and_entity_name method."""

    @pytest.fixture
    def mock_entity_repository(self) -> AsyncMock:
        """Fixture for mock entity repository."""
        return AsyncMock()

    @pytest.fixture
    def mock_cache(self) -> Mock:
        """Fixture for mock cache."""
        return Mock()

    @patch("musigree.offline.data_access_layer.entity_data_access.CacheManager.get_cache")
    async def test_get_id_cache_hit(
        self, mock_get_cache: Mock, mock_cache: Mock, mock_entity_repository: AsyncMock
    ) -> None:
        """Test get_id_by_entity_type_and_entity_name with cache hit."""
        # Setup
        mock_get_cache.return_value = mock_cache
        mock_cache.get.return_value = 123

        # Test
        result = await EntityDataAccess.get_id_by_entity_type_and_entity_name(
            mock_entity_repository, EntityType.ARTIST, "Test Artist"
        )

        # Assertions
        assert result == 123
        mock_cache.get.assert_called_once_with("Test Artist_EntityType.ARTIST")
        mock_entity_repository.get_id_by_entity_type_and_entity_name.assert_not_called()

    @patch("musigree.offline.data_access_layer.entity_data_access.CacheManager.get_cache")
    async def test_get_id_cache_null_entry(
        self, mock_get_cache: Mock, mock_cache: Mock, mock_entity_repository: AsyncMock
    ) -> None:
        """Test get_id_by_entity_type_and_entity_name with cache null entry."""
        # Setup
        mock_get_cache.return_value = mock_cache
        mock_cache.get.return_value = EntityDataAccess.CACHE_ENTRY_IS_NULL

        # Test
        result = await EntityDataAccess.get_id_by_entity_type_and_entity_name(
            mock_entity_repository, EntityType.ARTIST, "Test Artist"
        )

        # Assertions
        assert result is None
        mock_cache.get.assert_called_once_with("Test Artist_EntityType.ARTIST")
        mock_entity_repository.get_id_by_entity_type_and_entity_name.assert_not_called()

    @patch("musigree.offline.data_access_layer.entity_data_access.CacheManager.get_cache")
    async def test_get_id_cache_miss_db_hit(
        self, mock_get_cache: Mock, mock_cache: Mock, mock_entity_repository: AsyncMock
    ) -> None:
        """Test get_id_by_entity_type_and_entity_name with cache miss but database hit."""
        # Setup
        mock_get_cache.return_value = mock_cache
        mock_cache.get.return_value = None
        mock_entity_repository.get_id_by_entity_type_and_entity_name.return_value = 456

        # Test
        result = await EntityDataAccess.get_id_by_entity_type_and_entity_name(
            mock_entity_repository, EntityType.LABEL, "Test Label"
        )

        # Assertions
        assert result == 456
        mock_cache.get.assert_called_once_with("Test Label_EntityType.LABEL")
        mock_entity_repository.get_id_by_entity_type_and_entity_name.assert_called_once_with(
            EntityType.LABEL, "Test Label"
        )
        mock_cache.set.assert_called_once_with("Test Label_EntityType.LABEL", 456)

    @patch("musigree.offline.data_access_layer.entity_data_access.CacheManager.get_cache")
    async def test_get_id_cache_miss_db_miss(
        self, mock_get_cache: Mock, mock_cache: Mock, mock_entity_repository: AsyncMock
    ) -> None:
        """Test get_id_by_entity_type_and_entity_name with both cache and database miss."""
        # Setup
        mock_get_cache.return_value = mock_cache
        mock_cache.get.return_value = None
        mock_entity_repository.get_id_by_entity_type_and_entity_name.side_effect = NotFoundError(
            message="Entity not found"
        )

        # Test
        result = await EntityDataAccess.get_id_by_entity_type_and_entity_name(
            mock_entity_repository, EntityType.ARTIST, "Nonexistent Artist"
        )

        # Assertions
        assert result is None
        mock_cache.get.assert_called_once_with("Nonexistent Artist_EntityType.ARTIST")
        mock_entity_repository.get_id_by_entity_type_and_entity_name.assert_called_once_with(
            EntityType.ARTIST, "Nonexistent Artist"
        )
        mock_cache.set.assert_called_once_with(
            "Nonexistent Artist_EntityType.ARTIST", EntityDataAccess.CACHE_ENTRY_IS_NULL
        )

    @patch("musigree.offline.data_access_layer.entity_data_access.CacheManager.get_cache")
    @patch("musigree.offline.data_access_layer.entity_data_access.LOGGING_TRACE", True)
    @patch("musigree.offline.data_access_layer.entity_data_access.log")
    async def test_get_id_cache_miss_db_miss_with_logging(
        self,
        mock_log: Mock,
        mock_get_cache: Mock,
        mock_cache: Mock,
        mock_entity_repository: AsyncMock,
    ) -> None:
        """Test get_id_by_entity_type_and_entity_name with logging enabled for not found."""
        # Setup
        mock_get_cache.return_value = mock_cache
        mock_cache.get.return_value = None
        mock_entity_repository.get_id_by_entity_type_and_entity_name.side_effect = NotFoundError(
            message="Entity not found"
        )

        # Test
        result = await EntityDataAccess.get_id_by_entity_type_and_entity_name(
            mock_entity_repository, EntityType.ARTIST, "Nonexistent Artist"
        )

        # Assertions
        assert result is None
        mock_log.debug.assert_called_once_with(
            "get_id_from_entity_type_and_entity_name key not found: Nonexistent Artist_EntityType.ARTIST"
        )


class TestCreateTextSearchIndex:
    """Test class for create_text_search_index method."""

    @pytest.fixture
    def mock_entity_repository(self) -> AsyncMock:
        """Fixture for mock entity repository."""
        return AsyncMock()

    @pytest.fixture
    def mock_loader_base(self) -> Mock:
        """Fixture for mock loader base."""
        return Mock()

    @pytest.fixture
    def mock_text_search_index(self) -> Mock:
        """Fixture for mock text search index."""
        return Mock()

    @patch("musigree.offline.data_access_layer.entity_data_access.TextSearchIndex")
    async def test_create_text_search_index_success(
        self,
        mock_text_search_index_class: Mock,
        mock_entity_repository: AsyncMock,
        mock_loader_base: Mock,
    ) -> None:
        """Test create_text_search_index with successful execution."""
        # Setup
        mock_id_name_pairs = [
            (1, "Artist 1"),
            (2, "Artist 2"),
            (3, "Label 1"),
        ]

        async def mock_all_ids_and_names() -> AsyncGenerator[list[tuple[int, str]], None]:
            yield mock_id_name_pairs

        mock_entity_repository.all_ids_and_names = mock_all_ids_and_names

        # Mock the TextSearchIndex instance
        mock_index = Mock()
        mock_text_search_index_class.return_value = mock_index

        # Test
        result = await EntityDataAccess.create_text_search_index(mock_entity_repository)

        # Assertions - verify text search index was populated
        assert result == mock_index
        assert mock_index.index_entry.call_count == 3
        mock_index.index_entry.assert_any_call(1, "Artist 1")
        mock_index.index_entry.assert_any_call(2, "Artist 2")
        mock_index.index_entry.assert_any_call(3, "Label 1")
        mock_index.reduce_list_to_set.assert_called_once()
        mock_index.print_sizes.assert_called_once()

    @patch("musigree.offline.data_access_layer.entity_data_access.TextSearchIndex")
    async def test_create_text_search_index_empty_entities(
        self,
        mock_text_search_index_class: Mock,
        mock_entity_repository: AsyncMock,
        mock_loader_base: Mock,
    ) -> None:
        """Test create_text_search_index with no entities."""

        # Setup
        # noinspection PyUnreachableCode
        async def mock_all_ids_and_names() -> AsyncGenerator[list[tuple[int, str]], None]:
            # Empty async generator - yield nothing
            return
            # noinspection PyTypeChecker
            yield  # Never reached, but makes this a generator function

        mock_entity_repository.all_ids_and_names = mock_all_ids_and_names

        # Mock the TextSearchIndex instance
        mock_index = Mock()
        mock_text_search_index_class.return_value = mock_index

        # Test
        result = await EntityDataAccess.create_text_search_index(mock_entity_repository)

        # Assertions - verify no entries were added to index
        assert result == mock_index
        mock_index.index_entry.assert_not_called()
        mock_index.reduce_list_to_set.assert_called_once()
        mock_index.print_sizes.assert_called_once()


class TestAdditionalEdgeCases:
    """Test class for additional edge cases."""

    @pytest.fixture
    def mock_entity_repository(self) -> AsyncMock:
        """Fixture for mock entity repository."""
        return AsyncMock()

    @patch(
        "musigree.offline.data_access_layer.entity_data_access.EntityDataAccess.get_id_by_entity_type_and_entity_name"
    )
    async def test_resolve_entity_references_with_empty_alias_value(
        self, mock_get_id: AsyncMock, mock_entity_repository: AsyncMock
    ) -> None:
        """Test resolve_entity_references with empty alias values."""
        entities = {"aliases": {"": "some_value", "valid_alias": ""}}
        entity = TestResolveEntityReferences.create_test_entity(
            EntityType.ARTIST, entities=entities
        )

        # Mock get_id to return None for empty values
        mock_get_id.return_value = None

        result = await EntityDataAccess.resolve_entity_references(mock_entity_repository, entity)

        # Should return False since no valid processing occurred
        assert result is False

    async def test_resolve_entity_references_with_nested_empty_dict(
        self, mock_entity_repository: AsyncMock
    ) -> None:
        """Test resolve_entity_references with nested empty dictionaries."""
        entities: dict[str, Any] = {"aliases": {}, "groups": {}, "members": {}}
        entity = TestResolveEntityReferences.create_test_entity(
            EntityType.ARTIST, entities=entities
        )

        result = await EntityDataAccess.resolve_entity_references(mock_entity_repository, entity)

        assert result is False

    @patch(
        "musigree.offline.data_access_layer.entity_data_access.EntityDataAccess.get_id_by_entity_type_and_entity_name"
    )
    async def test_resolve_entity_references_with_exception(
        self, mock_get_id: AsyncMock, mock_entity_repository: AsyncMock
    ) -> None:
        """Test resolve_entity_references when get_id raises an exception."""
        entities = {"aliases": {"alias1": ""}}
        entity = TestResolveEntityReferences.create_test_entity(
            EntityType.ARTIST, entities=entities
        )

        # Mock the get_id method to raise an exception
        mock_get_id.side_effect = Exception("Database error")

        # Exception should propagate since it's not handled in the implementation
        with pytest.raises(Exception, match="Database error"):
            await EntityDataAccess.resolve_entity_references(mock_entity_repository, entity)


class TestLogging:
    """Test class for logging behavior."""

    def test_logger_exists(self) -> None:
        """Test that the module logger is properly configured."""
        from musigree.offline.data_access_layer.entity_data_access import log

        assert isinstance(log, logging.Logger)
        assert log.name == "musigree.offline.data_access_layer.entity_data_access"
