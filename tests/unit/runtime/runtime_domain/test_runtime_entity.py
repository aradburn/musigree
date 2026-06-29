from unittest.mock import MagicMock

import pytest

from musigree.library.fields.entity_type import EntityType
from musigree.offline.offline_domain.entity import Entity
from musigree.runtime.runtime_domain.runtime_entity import (
    RuntimeEntity,
    RuntimeEntityDB,
    to_runtime_entity_dict,
)


def test_converts_runtime_entity_to_db_representation() -> None:
    entity = RuntimeEntity(
        id=1,
        entity_id=100,
        entity_type=EntityType.ARTIST,
        entity_name="Test Artist",
        relation_counts={},
        entity_metadata={},
        entities={"aliases": {"Alias1": 123}, "groups": {"Group1": 456}, "members": {"Member1": 789}},
        countries="Country1",
        genres="Genre1",
        styles="Style1",
    )
    db_entity = entity.to_db()
    assert db_entity.entity_id == 100
    assert db_entity.entity_type == EntityType.ARTIST
    assert db_entity.entity_name == "Test Artist"
    assert db_entity.aliases == {"Alias1": 123}
    assert db_entity.groups == {"Group1": 456}
    assert db_entity.members == {"Member1": 789}


def test_converts_runtime_entity_to_db_representation_with_empty_entities() -> None:
    entity = RuntimeEntity(
        id=1,
        entity_id=100,
        entity_type=EntityType.ARTIST,
        entity_name="Test Artist",
        relation_counts={},
        entity_metadata={},
        entities={"aliases": [], "groups": [], "members": []},
        countries="Country1",
        genres="Genre1",
        styles="Style1",
    )
    db_entity = entity.to_db()
    assert db_entity.aliases is None
    assert db_entity.groups is None
    assert db_entity.members is None


def test_converts_runtime_entity_db_to_domain_representation() -> None:
    db_entity = RuntimeEntityDB(
        id=1,
        entity_id=100,
        entity_type=EntityType.ARTIST,
        entity_name="Test Artist",
        relation_counts={},
        entity_metadata={},
        aliases={"Alias1": 123},
        groups={"Group1": 456},
        members={"Member1": 789},
        parent_label={"Parent1": 543},
        countries="Country1",
        genres="Genre1",
        styles="Style1",
    )
    entity = db_entity.to_domain()
    assert entity.entity_id == 100
    assert entity.entity_type == EntityType.ARTIST
    assert entity.entity_name == "Test Artist"
    assert entity.entities["aliases"] == {"Alias1": 123}
    assert entity.entities["groups"] == {"Group1": 456}
    assert entity.entities["members"] == {"Member1": 789}
    assert entity.entities["parent_label"] == {"Parent1": 543}


def test_converts_runtime_entity_db_to_domain_representation_with_none_entities() -> None:
    db_entity = RuntimeEntityDB(
        id=1,
        entity_id=100,
        entity_type=EntityType.ARTIST,
        entity_name="Test Artist",
        relation_counts={},
        entity_metadata={},
        aliases=None,
        groups=None,
        members=None,
        parent_label=None,
        countries="Country1",
        genres="Genre1",
        styles="Style1",
    )
    entity = db_entity.to_domain()
    assert "aliases" not in entity.entities
    assert "groups" not in entity.entities
    assert "members" not in entity.entities
    assert "parent_label" not in entity.entities


def test_raises_value_error_for_unrecognized_entity_type() -> None:
    with pytest.raises(ValueError):
        # noinspection PyTypeChecker
        RuntimeEntity.to_json_entity_key(100, "UNKNOWN_TYPE")  # type: ignore


def test_serialize_entity_type_in_json_mode() -> None:
    """Test entity_type is serialized to name when dumping to JSON."""
    entity = RuntimeEntity(
        id=1,
        entity_id=100,
        entity_type=EntityType.ARTIST,
        entity_name="Test Artist",
        relation_counts={},
        entity_metadata={},
        entities={},
        countries="US",
        genres="Rock",
        styles="Alternative",
    )
    data = entity.model_dump(mode="json")
    assert data["entity_type"] == "ARTIST"


def test_to_runtime_entity_dict() -> None:
    """Test to_runtime_entity_dict builds dict with countries, genres, styles from index."""
    offline_entity = Entity(
        id=1,
        entity_id=200,
        entity_type=EntityType.LABEL,
        entity_name="Test Label",
        relation_counts={},
        entity_metadata={},
        entities={},
    )
    mock_index = MagicMock()
    mock_index.get_countries_for_id = MagicMock(return_value="US, UK")
    mock_index.get_genres_for_id = MagicMock(return_value="Jazz, Rock")
    mock_index.get_styles_for_id = MagicMock(return_value="Bebop")

    result = to_runtime_entity_dict(mock_index, offline_entity)

    assert result["entity_id"] == 200
    assert result["entity_type"] == EntityType.LABEL
    assert result["entity_name"] == "Test Label"
    assert result["countries"] == "US, UK"
    assert result["genres"] == "Jazz, Rock"
    assert result["styles"] == "Bebop"
    mock_index.get_countries_for_id.assert_called_once_with(1)
    mock_index.get_genres_for_id.assert_called_once_with(1)
    mock_index.get_styles_for_id.assert_called_once_with(1)
