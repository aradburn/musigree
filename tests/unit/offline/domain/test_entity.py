"""Unit tests for offline entity domain model."""

import pytest

from musigree.library.fields.entity_type import EntityType
from musigree.offline.domain.entity import Entity


class TestEntity:
    """Test cases for Entity class."""

    def test_entity_init(self) -> None:
        """Test Entity initialization."""
        entity = Entity(
            id=1,
            entity_id=123,
            entity_type=EntityType.ARTIST,
            entity_name="Test Artist",
            relation_counts={},
            entity_metadata={},
            entities={},
            search_content="test artist content"
        )
        
        assert entity.id == 1
        assert entity.entity_id == 123
        assert entity.entity_type == EntityType.ARTIST
        assert entity.entity_name == "Test Artist"
        assert entity.relation_counts == {}
        assert entity.entity_metadata == {}
        assert entity.entities == {}
        assert entity.search_content == "test artist content"

    def test_entity_key_property(self) -> None:
        """Test entity_key property."""
        entity = Entity(
            id=1,
            entity_id=456,
            entity_type=EntityType.LABEL,
            entity_name="Test Label",
            relation_counts={},
            entity_metadata={},
            entities={},
            search_content="test label content"
        )
        
        assert entity.entity_key == (456, EntityType.LABEL)

    def test_json_entity_key_property(self) -> None:
        """Test json_entity_key property."""
        entity = Entity(
            id=1,
            entity_id=789,
            entity_type=EntityType.ARTIST,
            entity_name="Test Artist",
            relation_counts={},
            entity_metadata={},
            entities={},
            search_content="test artist content"
        )
        
        assert entity.json_entity_key == "artist-789"

    def test_to_json_entity_key_artist(self) -> None:
        """Test to_json_entity_key for artist."""
        result = Entity.to_json_entity_key(123, EntityType.ARTIST)
        assert result == "artist-123"

    def test_to_json_entity_key_label(self) -> None:
        """Test to_json_entity_key for label."""
        result = Entity.to_json_entity_key(456, EntityType.LABEL)
        assert result == "label-456"

    def test_to_json_entity_key_invalid_type(self) -> None:
        """Test to_json_entity_key with valid entity types only."""
        # Since only ARTIST and LABEL are supported, this test can verify the ValueError
        # is raised for an unsupported case. Let's create a mock entity type
        class MockEntityType:
            def __init__(self, value: int, name: str):
                self.value = value
                self.name = name
        
        mock_type = MockEntityType(999, "UNKNOWN")
        with pytest.raises(ValueError):
            Entity.to_json_entity_key(123, mock_type)  # type: ignore

    def test_size_property_artist_with_dict_entities(self) -> None:
        """Test size property for artist with dict entities."""
        entity = Entity(
            id=1,
            entity_id=123,
            entity_type=EntityType.ARTIST,
            entity_name="Test Artist",
            relation_counts={},
            entity_metadata={},
            entities={"members": ["Member1", "Member2", "Member3"]},
            search_content="test artist content"
        )
        
        assert entity.size == 3

    def test_size_property_artist_with_list_entities(self) -> None:
        """Test size property for artist with list entities."""
        entity = Entity(
            id=1,
            entity_id=123,
            entity_type=EntityType.ARTIST,
            entity_name="Test Artist",
            relation_counts={},
            entity_metadata={},
            entities=["Member1", "Member2"],
            search_content="test artist content"
        )
        
        assert entity.size == 2

    def test_size_property_label_with_dict_entities(self) -> None:
        """Test size property for label with dict entities."""
        entity = Entity(
            id=1,
            entity_id=456,
            entity_type=EntityType.LABEL,
            entity_name="Test Label",
            relation_counts={},
            entity_metadata={},
            entities={"sublabels": ["Sublabel1", "Sublabel2"]},
            search_content="test label content"
        )
        
        assert entity.size == 2

    def test_size_property_label_with_list_entities(self) -> None:
        """Test size property for label with list entities."""
        entity = Entity(
            id=1,
            entity_id=456,
            entity_type=EntityType.LABEL,
            entity_name="Test Label",
            relation_counts={},
            entity_metadata={},
            entities=["Sublabel1"],
            search_content="test label content"
        )
        
        assert entity.size == 1

    def test_size_property_empty_entities(self) -> None:
        """Test size property with empty entities."""
        entity = Entity(
            id=1,
            entity_id=123,
            entity_type=EntityType.ARTIST,
            entity_name="Test Artist",
            relation_counts={},
            entity_metadata={},
            entities={},
            search_content="test artist content"
        )
        
        assert entity.size == 0

    def test_to_domain_method(self) -> None:
        """Test to_domain method."""
        entity = Entity(
            id=1,
            entity_id=123,
            entity_type=EntityType.ARTIST,
            entity_name="Test Artist",
            relation_counts={},
            entity_metadata={},
            entities={},
            search_content="test artist content"
        )
        
        domain_entity = entity.to_domain()
        assert domain_entity is entity  # Should return self

    def test_to_db_method(self) -> None:
        """Test to_db method."""
        entity = Entity(
            id=1,
            entity_id=123,
            entity_type=EntityType.ARTIST,
            entity_name="Test Artist",
            relation_counts={},
            entity_metadata={},
            entities={},
            search_content="test artist content"
        )
        
        db_entity = entity.to_db()
        assert db_entity is entity  # Should return self

    def test_serialize_entity_type(self) -> None:
        """Test entity type serialization."""
        entity = Entity(
            id=1,
            entity_id=123,
            entity_type=EntityType.ARTIST,
            entity_name="Test Artist",
            relation_counts={},
            entity_metadata={},
            entities={},
            search_content="test artist content"
        )
        
        serialized_type = entity.serialize_entity_type(EntityType.ARTIST)
        assert serialized_type == "ARTIST"
