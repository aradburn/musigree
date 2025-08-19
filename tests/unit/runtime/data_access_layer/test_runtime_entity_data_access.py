"""
Unit tests for the RuntimeEntityDataAccess class.

This module contains comprehensive unit tests for the RuntimeEntityDataAccess class,
which provides data access functionality for runtime entities including caching,
relation counting, and structural role processing.
"""

import logging
from unittest.mock import AsyncMock, Mock, patch

import pytest

from musigree.exceptions import NotFoundError
from musigree.library.fields.entity_type import EntityType
from musigree.runtime.data_access_layer.runtime_entity_data_access import RuntimeEntityDataAccess
from musigree.runtime.runtime_domain.entity import RuntimeEntity
from musigree.runtime.runtime_domain.relation import RuntimeRelationResult


class TestRuntimeEntityDataAccessConstants:
    """Test class for RuntimeEntityDataAccess constants."""
    
    def test_cache_constants(self):
        """Test that cache constants are defined correctly."""
        assert RuntimeEntityDataAccess.CACHE_ENTRY_IS_NULL == "___"
        assert RuntimeEntityDataAccess.CACHE_KEY_SEPARATOR == "_"


class TestRolesToRelationCount:
    """Test class for roles_to_relation_count method."""
    
    def create_test_entity(self, entity_type: EntityType, entities: dict | None = None, relation_counts: dict | None = None):
        """Helper method to create a test entity."""
        return RuntimeEntity(
            id=1,
            entity_id=1,
            entity_type=entity_type,
            entity_name="Test Entity",
            entities=entities or {},
            relation_counts=relation_counts or {},
            entity_metadata={},
            countries=None,
            genres=None,
            styles=None
        )
    
    def test_roles_to_relation_count_empty_roles(self):
        """Test roles_to_relation_count with empty roles list."""
        entity = self.create_test_entity(EntityType.ARTIST)
        
        result = RuntimeEntityDataAccess.roles_to_relation_count(entity, [])
        
        assert result == 0
    
    def test_roles_to_relation_count_alias_role(self):
        """Test roles_to_relation_count with Alias role."""
        entities = {"aliases": {"alias1": 1, "alias2": 2, "alias3": 3}}
        entity = self.create_test_entity(EntityType.ARTIST, entities=entities)
        
        result = RuntimeEntityDataAccess.roles_to_relation_count(entity, ["Alias"])
        
        assert result == 3
    
    def test_roles_to_relation_count_alias_role_no_aliases(self):
        """Test roles_to_relation_count with Alias role but no aliases."""
        entity = self.create_test_entity(EntityType.ARTIST)
        
        result = RuntimeEntityDataAccess.roles_to_relation_count(entity, ["Alias"])
        
        assert result == 0
    
    def test_roles_to_relation_count_member_of_role_groups(self):
        """Test roles_to_relation_count with Member Of role and groups."""
        entities = {"groups": {"group1": 1, "group2": 2}}
        entity = self.create_test_entity(EntityType.ARTIST, entities=entities)
        
        result = RuntimeEntityDataAccess.roles_to_relation_count(entity, ["Member Of"])
        
        assert result == 2
    
    def test_roles_to_relation_count_member_of_role_members(self):
        """Test roles_to_relation_count with Member Of role and members."""
        entities = {"members": {"member1": 1, "member2": 2, "member3": 3}}
        entity = self.create_test_entity(EntityType.ARTIST, entities=entities)
        
        result = RuntimeEntityDataAccess.roles_to_relation_count(entity, ["Member Of"])
        
        assert result == 3
    
    def test_roles_to_relation_count_member_of_role_both(self):
        """Test roles_to_relation_count with Member Of role having both groups and members."""
        entities = {
            "groups": {"group1": 1, "group2": 2},
            "members": {"member1": 3, "member2": 4}
        }
        entity = self.create_test_entity(EntityType.ARTIST, entities=entities)
        
        result = RuntimeEntityDataAccess.roles_to_relation_count(entity, ["Member Of"])
        
        assert result == 4  # 2 groups + 2 members
    
    def test_roles_to_relation_count_sublabel_of_role_parent(self):
        """Test roles_to_relation_count with Sublabel Of role and parent_label."""
        entities = {"parent_label": {"parent1": 1}}
        entity = self.create_test_entity(EntityType.LABEL, entities=entities)
        
        result = RuntimeEntityDataAccess.roles_to_relation_count(entity, ["Sublabel Of"])
        
        assert result == 1
    
    def test_roles_to_relation_count_sublabel_of_role_sublabels(self):
        """Test roles_to_relation_count with Sublabel Of role and sublabels."""
        entities = {"sublabels": {"sub1": 1, "sub2": 2}}
        entity = self.create_test_entity(EntityType.LABEL, entities=entities)
        
        result = RuntimeEntityDataAccess.roles_to_relation_count(entity, ["Sublabel Of"])
        
        assert result == 2
    
    def test_roles_to_relation_count_sublabel_of_role_both(self):
        """Test roles_to_relation_count with Sublabel Of role having both parent and sublabels."""
        entities = {
            "parent_label": {"parent1": 1},
            "sublabels": {"sub1": 2, "sub2": 3}
        }
        entity = self.create_test_entity(EntityType.LABEL, entities=entities)
        
        result = RuntimeEntityDataAccess.roles_to_relation_count(entity, ["Sublabel Of"])
        
        assert result == 3  # 1 parent + 2 sublabels
    
    def test_roles_to_relation_count_other_roles(self):
        """Test roles_to_relation_count with other roles from relation_counts."""
        relation_counts = {"Producer": 5, "Engineer": 3}
        entity = self.create_test_entity(EntityType.ARTIST, relation_counts=relation_counts)
        
        result = RuntimeEntityDataAccess.roles_to_relation_count(entity, ["Producer", "Engineer"])
        
        assert result == 8  # 5 + 3
    
    def test_roles_to_relation_count_other_roles_missing(self):
        """Test roles_to_relation_count with roles not in relation_counts."""
        relation_counts = {"Producer": 5}
        entity = self.create_test_entity(EntityType.ARTIST, relation_counts=relation_counts)
        
        result = RuntimeEntityDataAccess.roles_to_relation_count(entity, ["Producer", "Nonexistent"])
        
        assert result == 5  # 5 + 0 (default)
    
    def test_roles_to_relation_count_mixed_roles(self):
        """Test roles_to_relation_count with mixed role types."""
        entities = {"aliases": {"alias1": 1, "alias2": 2}}
        relation_counts = {"Producer": 3}
        entity = self.create_test_entity(EntityType.ARTIST, entities=entities, relation_counts=relation_counts)
        
        result = RuntimeEntityDataAccess.roles_to_relation_count(entity, ["Alias", "Producer"])
        
        assert result == 5  # 2 aliases + 3 producer
    
    def test_roles_to_relation_count_none_relation_counts(self):
        """Test roles_to_relation_count when relation_counts is None."""
        entity = self.create_test_entity(EntityType.ARTIST, relation_counts=None)
        
        result = RuntimeEntityDataAccess.roles_to_relation_count(entity, ["Producer"])
        
        assert result == 0


class TestStructuralRolesToRelations:
    """Test class for structural_roles_to_relations method."""
    
    def create_test_entity(self, entity_type: EntityType, entity_id: int = 1, entities: dict | None = None):
        """Helper method to create a test entity."""
        return RuntimeEntity(
            id=entity_id,
            entity_id=entity_id,
            entity_type=entity_type,
            entity_name="Test Entity",
            entities=entities or {},
            relation_counts={},
            entity_metadata={},
            countries=None,
            genres=None,
            styles=None
        )
    
    def test_structural_roles_to_relations_empty_roles(self):
        """Test structural_roles_to_relations with empty roles."""
        entity = self.create_test_entity(EntityType.ARTIST)
        
        result = RuntimeEntityDataAccess.structural_roles_to_relations(entity, [])
        
        assert result == {}
    
    def test_structural_roles_to_relations_artist_alias(self):
        """Test structural_roles_to_relations for artist with aliases."""
        entities = {"aliases": {"alias1": 2, "alias2": 3}}
        entity = self.create_test_entity(EntityType.ARTIST, entity_id=1, entities=entities)
        
        result = RuntimeEntityDataAccess.structural_roles_to_relations(entity, ["Alias"])
        
        assert len(result) == 2
        
        # Check that relations are created correctly
        for relation in result.values():
            assert isinstance(relation, RuntimeRelationResult)
            assert relation.role == "Alias"
            assert relation.entity_one_type == EntityType.ARTIST
            assert relation.entity_two_type == EntityType.ARTIST
            assert relation.releases is None
            assert relation.distance is None
            assert relation.id == 0
    
    def test_structural_roles_to_relations_artist_alias_empty_values(self):
        """Test structural_roles_to_relations for artist with empty alias values."""
        entities = {"aliases": {"alias1": None, "alias2": 0, "alias3": 3}}
        entity = self.create_test_entity(EntityType.ARTIST, entity_id=1, entities=entities)
        
        result = RuntimeEntityDataAccess.structural_roles_to_relations(entity, ["Alias"])
        
        # Should only create relation for alias3 (non-empty value)
        assert len(result) == 1
    
    def test_structural_roles_to_relations_artist_member_of_groups(self):
        """Test structural_roles_to_relations for artist member of groups."""
        entities = {"groups": {"group1": 2, "group2": 3}}
        entity = self.create_test_entity(EntityType.ARTIST, entity_id=1, entities=entities)
        
        result = RuntimeEntityDataAccess.structural_roles_to_relations(entity, ["Member Of"])
        
        assert len(result) == 2
        
        for relation in result.values():
            assert relation.role == "Member Of"
            assert relation.entity_one_id == 1  # entity is member
            assert relation.entity_two_id in [2, 3]  # of these groups
    
    def test_structural_roles_to_relations_artist_member_of_members(self):
        """Test structural_roles_to_relations for artist with members."""
        entities = {"members": {"member1": 2, "member2": 3}}
        entity = self.create_test_entity(EntityType.ARTIST, entity_id=1, entities=entities)
        
        result = RuntimeEntityDataAccess.structural_roles_to_relations(entity, ["Member Of"])
        
        assert len(result) == 2
        
        for relation in result.values():
            assert relation.role == "Member Of"
            assert relation.entity_one_id in [2, 3]  # these entities are members
            assert relation.entity_two_id == 1  # of this entity
    
    def test_structural_roles_to_relations_artist_member_of_both(self):
        """Test structural_roles_to_relations for artist with both groups and members."""
        entities = {
            "groups": {"group1": 2},
            "members": {"member1": 3, "member2": 4}
        }
        entity = self.create_test_entity(EntityType.ARTIST, entity_id=1, entities=entities)
        
        result = RuntimeEntityDataAccess.structural_roles_to_relations(entity, ["Member Of"])
        
        assert len(result) == 3  # 1 group + 2 members
    
    def test_structural_roles_to_relations_label_sublabel_of_parent(self):
        """Test structural_roles_to_relations for label with parent."""
        entities = {"parent_label": {"parent1": 2}}
        entity = self.create_test_entity(EntityType.LABEL, entity_id=1, entities=entities)
        
        result = RuntimeEntityDataAccess.structural_roles_to_relations(entity, ["Sublabel Of"])
        
        assert len(result) == 1
        
        relation = list(result.values())[0]
        assert relation.role == "Sublabel Of"
        assert relation.entity_one_id == 1  # this entity is sublabel
        assert relation.entity_two_id == 2  # of parent
    
    def test_structural_roles_to_relations_label_sublabel_of_sublabels(self):
        """Test structural_roles_to_relations for label with sublabels."""
        entities = {"sublabels": {"sub1": 2, "sub2": 3}}
        entity = self.create_test_entity(EntityType.LABEL, entity_id=1, entities=entities)
        
        result = RuntimeEntityDataAccess.structural_roles_to_relations(entity, ["Sublabel Of"])
        
        assert len(result) == 2
        
        for relation in result.values():
            assert relation.role == "Sublabel Of"
            assert relation.entity_one_id in [2, 3]  # these entities are sublabels
            assert relation.entity_two_id == 1  # of this entity
    
    def test_structural_roles_to_relations_non_matching_entity_type(self):
        """Test structural_roles_to_relations with non-matching entity type."""
        # Create a mock entity with a type that doesn't have special handling
        # We'll use LABEL but test with roles that don't apply to labels
        entity = self.create_test_entity(EntityType.LABEL)
        
        # Test with roles that only apply to artists
        result = RuntimeEntityDataAccess.structural_roles_to_relations(entity, ["Alias", "Member Of"])
        
        assert result == {}
    
    def test_structural_roles_to_relations_artist_without_matching_roles(self):
        """Test structural_roles_to_relations for artist without matching roles."""
        entities = {"aliases": {"alias1": 2}}
        entity = self.create_test_entity(EntityType.ARTIST, entities=entities)
        
        result = RuntimeEntityDataAccess.structural_roles_to_relations(entity, ["Sublabel Of"])  # Wrong role for artist
        
        assert result == {}
    
    def test_structural_roles_to_relations_label_without_matching_roles(self):
        """Test structural_roles_to_relations for label without matching roles."""
        entities = {"parent_label": {"parent1": 2}}
        entity = self.create_test_entity(EntityType.LABEL, entities=entities)
        
        result = RuntimeEntityDataAccess.structural_roles_to_relations(entity, ["Alias"])  # Wrong role for label
        
        assert result == {}


class TestGetIdByEntityTypeAndEntityName:
    """Test class for get_id_by_entity_type_and_entity_name method."""
    
    @pytest.fixture
    def mock_cache(self):
        """Fixture for mock cache."""
        return Mock()
    
    @pytest.fixture
    def mock_entity_repository(self):
        """Fixture for mock entity repository."""
        return AsyncMock()
    
    @patch('musigree.runtime.data_access_layer.runtime_entity_data_access.CacheManager.get_cache')
    async def test_get_id_cache_hit(self, mock_get_cache, mock_cache, mock_entity_repository):
        """Test get_id_by_entity_type_and_entity_name with cache hit."""
        # Setup
        mock_get_cache.return_value = mock_cache
        mock_cache.get.return_value = 123
        
        # Test
        result = await RuntimeEntityDataAccess.get_id_by_entity_type_and_entity_name(
            mock_entity_repository, EntityType.ARTIST, "Test Artist"
        )
        
        # Assertions
        assert result == 123
        mock_cache.get.assert_called_once_with("Test Artist_EntityType.ARTIST")
        mock_entity_repository.get_id_by_entity_type_and_entity_name.assert_not_called()
    
    @patch('musigree.runtime.data_access_layer.runtime_entity_data_access.CacheManager.get_cache')
    async def test_get_id_cache_null_entry(self, mock_get_cache, mock_cache, mock_entity_repository):
        """Test get_id_by_entity_type_and_entity_name with cache null entry."""
        # Setup
        mock_get_cache.return_value = mock_cache
        mock_cache.get.return_value = RuntimeEntityDataAccess.CACHE_ENTRY_IS_NULL
        
        # Test
        result = await RuntimeEntityDataAccess.get_id_by_entity_type_and_entity_name(
            mock_entity_repository, EntityType.ARTIST, "Test Artist"
        )
        
        # Assertions
        assert result is None
        mock_cache.get.assert_called_once_with("Test Artist_EntityType.ARTIST")
        mock_entity_repository.get_id_by_entity_type_and_entity_name.assert_not_called()
    
    @patch('musigree.runtime.data_access_layer.runtime_entity_data_access.CacheManager.get_cache')
    async def test_get_id_cache_miss_db_hit(self, mock_get_cache, mock_cache, mock_entity_repository):
        """Test get_id_by_entity_type_and_entity_name with cache miss but database hit."""
        # Setup
        mock_get_cache.return_value = mock_cache
        mock_cache.get.return_value = None
        mock_entity_repository.get_id_by_entity_type_and_entity_name.return_value = 456
        
        # Test
        result = await RuntimeEntityDataAccess.get_id_by_entity_type_and_entity_name(
            mock_entity_repository, EntityType.LABEL, "Test Label"
        )
        
        # Assertions
        assert result == 456
        mock_cache.get.assert_called_once_with("Test Label_EntityType.LABEL")
        mock_entity_repository.get_id_by_entity_type_and_entity_name.assert_called_once_with(
            EntityType.LABEL, "Test Label"
        )
        mock_cache.set.assert_called_once_with("Test Label_EntityType.LABEL", 456)
    
    @patch('musigree.runtime.data_access_layer.runtime_entity_data_access.CacheManager.get_cache')
    async def test_get_id_cache_miss_db_miss(self, mock_get_cache, mock_cache, mock_entity_repository):
        """Test get_id_by_entity_type_and_entity_name with both cache and database miss."""
        # Setup
        mock_get_cache.return_value = mock_cache
        mock_cache.get.return_value = None
        mock_entity_repository.get_id_by_entity_type_and_entity_name.side_effect = NotFoundError("Entity not found")
        
        # Test
        result = await RuntimeEntityDataAccess.get_id_by_entity_type_and_entity_name(
            mock_entity_repository, EntityType.LABEL, "Test Label"
        )
        
        # Assertions
        assert result is None
        mock_cache.get.assert_called_once_with("Test Label_EntityType.LABEL")
        mock_entity_repository.get_id_by_entity_type_and_entity_name.assert_called_once_with(
            EntityType.LABEL, "Test Label"
        )
        mock_cache.set.assert_called_once_with("Test Label_EntityType.LABEL", RuntimeEntityDataAccess.CACHE_ENTRY_IS_NULL)
    
    @patch('musigree.runtime.data_access_layer.runtime_entity_data_access.CacheManager.get_cache')
    @patch('musigree.runtime.data_access_layer.runtime_entity_data_access.LOGGING_TRACE', True)
    @patch('musigree.runtime.data_access_layer.runtime_entity_data_access.log')
    async def test_get_id_cache_miss_db_miss_with_logging(self, mock_log, mock_get_cache, mock_cache, mock_entity_repository):
        """Test get_id_by_entity_type_and_entity_name with logging enabled for not found."""
        # Setup
        mock_get_cache.return_value = mock_cache
        mock_cache.get.return_value = None
        mock_entity_repository.get_id_by_entity_type_and_entity_name.side_effect = NotFoundError("Entity not found")
        
        # Test
        result = await RuntimeEntityDataAccess.get_id_by_entity_type_and_entity_name(
            mock_entity_repository, EntityType.ARTIST, "Nonexistent Artist"
        )
        
        # Assertions
        assert result is None
        mock_log.debug.assert_called_once_with(
            "get_id_from_entity_type_and_entity_name key not found: Nonexistent Artist_EntityType.ARTIST"
        )
    
    def test_cache_key_format(self):
        """Test that cache key is formatted correctly."""
        # This is implicit in the other tests, but let's be explicit
        entity_name = "Test Entity"
        entity_type = EntityType.ARTIST
        expected_key = f"{entity_name}{RuntimeEntityDataAccess.CACHE_KEY_SEPARATOR}{entity_type}"
        
        assert expected_key == "Test Entity_EntityType.ARTIST"


class TestLogging:
    """Test class for logging behavior."""
    
    def test_logger_exists(self):
        """Test that the module logger is properly configured."""
        from musigree.runtime.data_access_layer.runtime_entity_data_access import log
        
        assert isinstance(log, logging.Logger)
        assert log.name == "musigree.runtime.data_access_layer.runtime_entity_data_access"
