from unittest.mock import patch

import pytest

from musigree.library.cache.role_cache import RoleCache
from musigree.library.fields.entity_type import EntityType
from musigree.runtime.runtime_domain.runtime_relation import (
    RuntimeRelation,
    RuntimeRelationDB,
    RuntimeRelationResult,
)


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


def test_ends_key_ignores_direction() -> None:
    forward = RuntimeRelation(
        entity_one_id=100,
        entity_one_type=EntityType.ARTIST,
        entity_two_id=200,
        entity_two_type=EntityType.LABEL,
        role="Alias",
        releases=None,
    )
    reverse = RuntimeRelation(
        entity_one_id=200,
        entity_one_type=EntityType.LABEL,
        entity_two_id=100,
        entity_two_type=EntityType.ARTIST,
        role="Alias",
        releases=None,
    )

    assert forward.ends_key == reverse.ends_key


def test_year_propagates_from_database_to_runtime_relation_result() -> None:
    with patch.dict(RoleCache.role_id_to_role_name_lookup, {3: "Producer"}):
        relation_db = RuntimeRelationDB(
            id=1,
            subject=100,
            predicate=3,
            object=200,
            release_id=12,
            year=1999,
        )
        missing_year_db = RuntimeRelationDB(
            id=2,
            subject=100,
            predicate=3,
            object=200,
            release_id=13,
            year=None,
        )

        internal = relation_db.to_domain()
        missing_year_internal = missing_year_db.to_domain()
        result = RuntimeRelationResult.from_relation_internals([internal, missing_year_internal])

    assert internal.year == 1999
    assert missing_year_internal.year is None
    assert isinstance(result, RuntimeRelationResult)
    assert result.releases == {"12": 1999, "13": None}
    assert result.to_result(distance=2).releases == {"12": 1999, "13": None}
    assert result.to_result(distance=2).distance == 2


def test_to_result_keeps_release_years() -> None:
    relation = RuntimeRelation(
        entity_one_id=100,
        entity_one_type=EntityType.ARTIST,
        entity_two_id=200,
        entity_two_type=EntityType.LABEL,
        role="Producer",
        releases={"12": 1999, "13": None},
    )

    result = relation.to_result(distance=4)

    assert isinstance(result, RuntimeRelationResult)
    assert result.releases == {"12": 1999, "13": None}
    assert result.role == "Producer"
    assert result.distance == 4


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
        "years": [],
        "distance": 5,
    }


def test_as_json_returns_years_as_an_ordered_set() -> None:
    relation_result = RuntimeRelationResult(
        entity_one_id=100,
        entity_one_type=EntityType.ARTIST,
        entity_two_id=200,
        entity_two_type=EntityType.LABEL,
        role="Producer",
        releases={"12": 2001, "13": None, "14": 1990, "15": 2001, "16": 1995},
        distance=None,
    )

    json_data = relation_result.as_json()

    assert json_data["years"] == [1990, 1995, 2001]
    assert all(isinstance(year, int) for year in json_data["years"])
