import pytest

from musigree.library.fields.entity_id import (
    to_entity_internal_id,
    to_entity_external_id,
    to_entity_label_internal_id,
    LABEL_ENTITY_ID_OFFSET,
    MISSING_LABEL_ENTITY,
)
from musigree.library.fields.entity_type import EntityType


class TestEntityId:
    """Test cases for entity ID conversion functions."""

    def test_to_entity_internal_id_artist(self) -> None:
        """Test converting artist external ID to internal ID."""
        # Artist IDs should remain unchanged
        result = to_entity_internal_id(12345, EntityType.ARTIST)
        assert 12345 == result

    def test_to_entity_internal_id_artist_zero(self) -> None:
        """Test converting artist ID of zero."""
        result = to_entity_internal_id(0, EntityType.ARTIST)
        assert 0 == result

    def test_to_entity_internal_id_label_small(self) -> None:
        """Test converting small label external ID to internal ID."""
        # Small label IDs get offset added
        result = to_entity_internal_id(12345, EntityType.LABEL)
        expected = 12345 + LABEL_ENTITY_ID_OFFSET
        assert expected == result

    def test_to_entity_internal_id_label_already_offset(self) -> None:
        """Test converting label ID that's already offset."""
        # If label ID is already >= LABEL_ENTITY_ID_OFFSET, it remains unchanged
        large_id = LABEL_ENTITY_ID_OFFSET + 12345
        result = to_entity_internal_id(large_id, EntityType.LABEL)
        assert large_id == result

    def test_to_entity_internal_id_label_missing(self) -> None:
        """Test converting missing label entity ID."""
        result = to_entity_internal_id(MISSING_LABEL_ENTITY, EntityType.LABEL)
        assert MISSING_LABEL_ENTITY == result

    def test_to_entity_internal_id_artist_invalid_missing_label(self) -> None:
        """Test that artist cannot have missing label entity ID."""
        with pytest.raises(AssertionError):
            to_entity_internal_id(MISSING_LABEL_ENTITY, EntityType.ARTIST)

    def test_to_entity_internal_id_artist_invalid_large_id(self) -> None:
        """Test that artist cannot have ID >= LABEL_ENTITY_ID_OFFSET."""
        with pytest.raises(AssertionError):
            to_entity_internal_id(LABEL_ENTITY_ID_OFFSET, EntityType.ARTIST)

    def test_to_entity_external_id_artist(self) -> None:
        """Test converting artist internal ID to external ID."""
        result = to_entity_external_id(12345)
        expected = (12345, EntityType.ARTIST)
        assert expected == result

    def test_to_entity_external_id_artist_zero(self) -> None:
        """Test converting artist internal ID of zero."""
        result = to_entity_external_id(0)
        expected = (0, EntityType.ARTIST)
        assert expected == result

    def test_to_entity_external_id_label(self) -> None:
        """Test converting label internal ID to external ID."""
        internal_id = LABEL_ENTITY_ID_OFFSET + 12345
        result = to_entity_external_id(internal_id)
        expected = (12345, EntityType.LABEL)
        assert expected == result

    def test_to_entity_external_id_label_exact_offset(self) -> None:
        """Test converting label internal ID that's exactly the offset."""
        result = to_entity_external_id(LABEL_ENTITY_ID_OFFSET)
        expected = (0, EntityType.LABEL)
        assert expected == result

    def test_to_entity_external_id_missing_label(self) -> None:
        """Test converting missing label entity internal ID."""
        result = to_entity_external_id(MISSING_LABEL_ENTITY)
        expected = (-1, EntityType.LABEL)
        assert expected == result

    def test_to_entity_label_internal_id_valid(self) -> None:
        """Test converting valid label external ID to internal ID."""
        result = to_entity_label_internal_id(12345)
        expected = 12345 + LABEL_ENTITY_ID_OFFSET
        assert expected == result

    def test_to_entity_label_internal_id_zero(self) -> None:
        """Test converting zero label ID to internal ID."""
        result = to_entity_label_internal_id(0)
        expected = MISSING_LABEL_ENTITY  # 0 is falsy, so it's treated as None/missing
        assert expected == result

    def test_to_entity_label_internal_id_none(self) -> None:
        """Test converting None label ID (missing label)."""
        result = to_entity_label_internal_id(None)
        assert MISSING_LABEL_ENTITY == result

    def test_round_trip_artist(self) -> None:
        """Test round trip conversion for artist IDs."""
        original_id = 12345
        entity_type = EntityType.ARTIST

        # Convert to internal and back
        internal_id = to_entity_internal_id(original_id, entity_type)
        external_id, result_type = to_entity_external_id(internal_id)

        assert original_id == external_id
        assert entity_type == result_type

    def test_round_trip_label(self) -> None:
        """Test round trip conversion for label IDs."""
        original_id = 12345
        entity_type = EntityType.LABEL

        # Convert to internal and back
        internal_id = to_entity_internal_id(original_id, entity_type)
        external_id, result_type = to_entity_external_id(internal_id)

        assert original_id == external_id
        assert entity_type == result_type

    def test_round_trip_missing_label(self) -> None:
        """Test round trip conversion for missing label."""
        # Convert to internal and back
        internal_id = to_entity_internal_id(MISSING_LABEL_ENTITY, EntityType.LABEL)
        external_id, result_type = to_entity_external_id(internal_id)

        assert -1 == external_id
        assert EntityType.LABEL == result_type

    def test_round_trip_label_none(self) -> None:
        """Test round trip conversion for None label ID."""
        # Convert None to internal and back
        internal_id = to_entity_label_internal_id(None)
        external_id, result_type = to_entity_external_id(internal_id)

        assert -1 == external_id
        assert EntityType.LABEL == result_type

    def test_constants_values(self) -> None:
        """Test that constants have expected values."""
        assert 1000000000 == LABEL_ENTITY_ID_OFFSET
        assert -2000000000 == MISSING_LABEL_ENTITY

    def test_id_ranges_do_not_overlap(self) -> None:
        """Test that artist and label ID ranges don't overlap."""
        # Artists should be < LABEL_ENTITY_ID_OFFSET
        max_artist_id = LABEL_ENTITY_ID_OFFSET - 1
        artist_internal = to_entity_internal_id(max_artist_id, EntityType.ARTIST)
        assert max_artist_id == artist_internal

        # Labels should be >= LABEL_ENTITY_ID_OFFSET
        min_label_internal = LABEL_ENTITY_ID_OFFSET
        label_external, label_type = to_entity_external_id(min_label_internal)
        assert 0 == label_external
        assert EntityType.LABEL == label_type

    def test_edge_cases_boundary_values(self) -> None:
        """Test edge cases with boundary values."""
        # Test maximum valid artist ID
        max_artist = LABEL_ENTITY_ID_OFFSET - 1
        result = to_entity_internal_id(max_artist, EntityType.ARTIST)
        assert max_artist == result

        # Test minimum label ID that gets offset
        min_label = 1
        result = to_entity_internal_id(min_label, EntityType.LABEL)
        assert min_label + LABEL_ENTITY_ID_OFFSET == result

