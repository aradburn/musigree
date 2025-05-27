import pytest
from musigree.runtime.runtime_domain.entity import RuntimeEntity, RuntimeEntityDB
from musigree.library.fields.entity_type import EntityType


def test_converts_runtime_entity_to_db_representation():
    entity = RuntimeEntity(
        id=1,
        entity_id=100,
        entity_type=EntityType.ARTIST,
        entity_name="Test Artist",
        relation_counts={},
        entity_metadata={},
        entities={"aliases": ["Alias1"], "groups": ["Group1"], "members": ["Member1"]},
        countries="Country1",
        genres="Genre1",
        styles="Style1",
    )
    db_entity = entity.to_db()
    assert db_entity.entity_id == 100
    assert db_entity.entity_type == EntityType.ARTIST
    assert db_entity.entity_name == "Test Artist"
    assert db_entity.aliases == ["Alias1"]
    assert db_entity.groups == ["Group1"]
    assert db_entity.members == ["Member1"]


def test_converts_runtime_entity_to_db_representation_with_empty_entities():
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


def test_converts_runtime_entity_db_to_domain_representation():
    db_entity = RuntimeEntityDB(
        id=1,
        entity_id=100,
        entity_type=EntityType.ARTIST,
        entity_name="Test Artist",
        relation_counts={},
        entity_metadata={},
        aliases=["Alias1"],
        groups=["Group1"],
        members=["Member1"],
        countries="Country1",
        genres="Genre1",
        styles="Style1",
    )
    entity = db_entity.to_domain()
    assert entity.entity_id == 100
    assert entity.entity_type == EntityType.ARTIST
    assert entity.entity_name == "Test Artist"
    assert entity.entities["aliases"] == ["Alias1"]
    assert entity.entities["groups"] == ["Group1"]
    assert entity.entities["members"] == ["Member1"]


def test_converts_runtime_entity_db_to_domain_representation_with_none_entities():
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
        countries="Country1",
        genres="Genre1",
        styles="Style1",
    )
    entity = db_entity.to_domain()
    assert "aliases" not in entity.entities
    assert "groups" not in entity.entities
    assert "members" not in entity.entities


def test_raises_value_error_for_unrecognized_entity_type():
    with pytest.raises(ValueError):
        # noinspection PyTypeChecker
        RuntimeEntity.to_json_entity_key(100, "UNKNOWN_TYPE") # type: ignore
