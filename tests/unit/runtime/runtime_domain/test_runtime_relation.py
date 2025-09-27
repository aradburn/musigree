import pytest
from musigree.runtime.runtime_domain.relation import (
    RuntimeRelation,
    RuntimeRelationResult,
)
from musigree.library.fields.entity_type import EntityType


def test_creates_runtime_relation_with_valid_data() -> None:
    # noinspection PyTypeChecker
    relation = RuntimeRelation(
        entity_one_id=100,
        entity_one_type=EntityType.ARTIST,
        entity_two_id=200,
        entity_two_type=EntityType.LABEL,
        role="Producer",
        releases={"release1": 1},
    )
    assert relation.entity_one_id == 100
    assert relation.entity_one_type == EntityType.ARTIST
    assert relation.entity_two_id == 200
    assert relation.entity_two_type == EntityType.LABEL
    assert relation.role == "Producer"
    assert relation.releases == {"release1": 1}


def test_raises_value_error_for_unrecognized_entity_one_type() -> None:
    with pytest.raises(ValueError):
        # noinspection PyTypeChecker
        relation = RuntimeRelation(
            entity_one_id=100,
            entity_one_type="UNKNOWN_TYPE",  # type: ignore
            entity_two_id=200,
            entity_two_type=EntityType.LABEL,
            role="Producer",
            releases=None,
        )
        _ = relation.json_entity_one_key


def test_raises_value_error_for_unrecognized_entity_two_type() -> None:
    with pytest.raises(ValueError):
        # noinspection PyTypeChecker
        relation = RuntimeRelation(
            entity_one_id=100,
            entity_one_type=EntityType.ARTIST,
            entity_two_id=200,
            entity_two_type="UNKNOWN_TYPE",  # type: ignore
            role="Producer",
            releases=None,
        )
        _ = relation.json_entity_two_key


def test_generates_correct_json_entity_one_key() -> None:
    relation = RuntimeRelation(
        entity_one_id=100,
        entity_one_type=EntityType.ARTIST,
        entity_two_id=200,
        entity_two_type=EntityType.LABEL,
        role="Producer",
        releases=None,
    )
    assert relation.json_entity_one_key == "artist-100"


def test_generates_correct_json_entity_two_key() -> None:
    relation = RuntimeRelation(
        entity_one_id=100,
        entity_one_type=EntityType.ARTIST,
        entity_two_id=200,
        entity_two_type=EntityType.LABEL,
        role="Producer",
        releases=None,
    )
    assert relation.json_entity_two_key == "label-200"


def test_generates_correct_link_key() -> None:
    relation = RuntimeRelation(
        entity_one_id=100,
        entity_one_type=EntityType.ARTIST,
        entity_two_id=200,
        entity_two_type=EntityType.LABEL,
        role="Producer",
        releases=None,
    )
    assert relation.link_key == "artist-100-producer-label-200"


def test_converts_runtime_relation_result_to_json() -> None:
    relation_result = RuntimeRelationResult(
        entity_one_id=100,
        entity_one_type=EntityType.ARTIST,
        entity_two_id=200,
        entity_two_type=EntityType.LABEL,
        role="Producer",
        releases=None,
        distance=5,
    )
    json_data = relation_result.as_json()
    assert json_data == {
        "key": "artist-100-producer-label-200",
        "role": "Producer",
        "source": "artist-100",
        "target": "label-200",
        "distance": 5,
    }
