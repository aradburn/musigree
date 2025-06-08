import unittest

from musigree.library.fields.entity_id import (
    to_entity_internal_id,
    to_entity_external_id,
    to_entity_label_internal_id,
    LABEL_ENTITY_ID_OFFSET,
    MISSING_LABEL_ENTITY,
)
from musigree.library.fields.entity_type import EntityType


class TestEntityId(unittest.TestCase):
    """Test cases for entity ID conversion functions."""

    def test_to_entity_internal_id_artist(self):
        """Test converting artist external ID to internal ID."""
        # Artist IDs should remain unchanged
        result = to_entity_internal_id(12345, EntityType.ARTIST)
        self.assertEqual(12345, result)

    def test_to_entity_internal_id_artist_zero(self):
        """Test converting artist ID of zero."""
        result = to_entity_internal_id(0, EntityType.ARTIST)
        self.assertEqual(0, result)

    def test_to_entity_internal_id_label_small(self):
        """Test converting small label external ID to internal ID."""
        # Small label IDs get offset added
        result = to_entity_internal_id(12345, EntityType.LABEL)
        expected = 12345 + LABEL_ENTITY_ID_OFFSET
        self.assertEqual(expected, result)

    def test_to_entity_internal_id_label_already_offset(self):
        """Test converting label ID that's already offset."""
        # If label ID is already >= LABEL_ENTITY_ID_OFFSET, it remains unchanged
        large_id = LABEL_ENTITY_ID_OFFSET + 12345
        result = to_entity_internal_id(large_id, EntityType.LABEL)
        self.assertEqual(large_id, result)

    def test_to_entity_internal_id_label_missing(self):
        """Test converting missing label entity ID."""
        result = to_entity_internal_id(MISSING_LABEL_ENTITY, EntityType.LABEL)
        self.assertEqual(MISSING_LABEL_ENTITY, result)

    def test_to_entity_internal_id_artist_invalid_missing_label(self):
        """Test that artist cannot have missing label entity ID."""
        with self.assertRaises(AssertionError):
            to_entity_internal_id(MISSING_LABEL_ENTITY, EntityType.ARTIST)

    def test_to_entity_internal_id_artist_invalid_large_id(self):
        """Test that artist cannot have ID >= LABEL_ENTITY_ID_OFFSET."""
        with self.assertRaises(AssertionError):
            to_entity_internal_id(LABEL_ENTITY_ID_OFFSET, EntityType.ARTIST)

    def test_to_entity_external_id_artist(self):
        """Test converting artist internal ID to external ID."""
        result = to_entity_external_id(12345)
        expected = (12345, EntityType.ARTIST)
        self.assertEqual(expected, result)

    def test_to_entity_external_id_artist_zero(self):
        """Test converting artist internal ID of zero."""
        result = to_entity_external_id(0)
        expected = (0, EntityType.ARTIST)
        self.assertEqual(expected, result)

    def test_to_entity_external_id_label(self):
        """Test converting label internal ID to external ID."""
        internal_id = LABEL_ENTITY_ID_OFFSET + 12345
        result = to_entity_external_id(internal_id)
        expected = (12345, EntityType.LABEL)
        self.assertEqual(expected, result)

    def test_to_entity_external_id_label_exact_offset(self):
        """Test converting label internal ID that's exactly the offset."""
        result = to_entity_external_id(LABEL_ENTITY_ID_OFFSET)
        expected = (0, EntityType.LABEL)
        self.assertEqual(expected, result)

    def test_to_entity_external_id_missing_label(self):
        """Test converting missing label entity internal ID."""
        result = to_entity_external_id(MISSING_LABEL_ENTITY)
        expected = (-1, EntityType.LABEL)
        self.assertEqual(expected, result)

    def test_to_entity_label_internal_id_valid(self):
        """Test converting valid label external ID to internal ID."""
        result = to_entity_label_internal_id(12345)
        expected = 12345 + LABEL_ENTITY_ID_OFFSET
        self.assertEqual(expected, result)

    def test_to_entity_label_internal_id_zero(self):
        """Test converting zero label ID to internal ID."""
        result = to_entity_label_internal_id(0)
        expected = MISSING_LABEL_ENTITY  # 0 is falsy, so it's treated as None/missing
        self.assertEqual(expected, result)

    def test_to_entity_label_internal_id_none(self):
        """Test converting None label ID (missing label)."""
        result = to_entity_label_internal_id(None)
        self.assertEqual(MISSING_LABEL_ENTITY, result)

    def test_round_trip_artist(self):
        """Test round trip conversion for artist IDs."""
        original_id = 12345
        entity_type = EntityType.ARTIST
        
        # Convert to internal and back
        internal_id = to_entity_internal_id(original_id, entity_type)
        external_id, result_type = to_entity_external_id(internal_id)
        
        self.assertEqual(original_id, external_id)
        self.assertEqual(entity_type, result_type)

    def test_round_trip_label(self):
        """Test round trip conversion for label IDs."""
        original_id = 12345
        entity_type = EntityType.LABEL
        
        # Convert to internal and back
        internal_id = to_entity_internal_id(original_id, entity_type)
        external_id, result_type = to_entity_external_id(internal_id)
        
        self.assertEqual(original_id, external_id)
        self.assertEqual(entity_type, result_type)

    def test_round_trip_missing_label(self):
        """Test round trip conversion for missing label."""
        # Convert to internal and back
        internal_id = to_entity_internal_id(MISSING_LABEL_ENTITY, EntityType.LABEL)
        external_id, result_type = to_entity_external_id(internal_id)
        
        self.assertEqual(-1, external_id)
        self.assertEqual(EntityType.LABEL, result_type)

    def test_round_trip_label_none(self):
        """Test round trip conversion for None label ID."""
        # Convert None to internal and back
        internal_id = to_entity_label_internal_id(None)
        external_id, result_type = to_entity_external_id(internal_id)
        
        self.assertEqual(-1, external_id)
        self.assertEqual(EntityType.LABEL, result_type)

    def test_constants_values(self):
        """Test that constants have expected values."""
        self.assertEqual(1000000000, LABEL_ENTITY_ID_OFFSET)
        self.assertEqual(-2000000000, MISSING_LABEL_ENTITY)

    def test_id_ranges_do_not_overlap(self):
        """Test that artist and label ID ranges don't overlap."""
        # Artists should be < LABEL_ENTITY_ID_OFFSET
        max_artist_id = LABEL_ENTITY_ID_OFFSET - 1
        artist_internal = to_entity_internal_id(max_artist_id, EntityType.ARTIST)
        self.assertEqual(max_artist_id, artist_internal)
        
        # Labels should be >= LABEL_ENTITY_ID_OFFSET
        min_label_internal = LABEL_ENTITY_ID_OFFSET
        label_external, label_type = to_entity_external_id(min_label_internal)
        self.assertEqual(0, label_external)
        self.assertEqual(EntityType.LABEL, label_type)

    def test_edge_cases_boundary_values(self):
        """Test edge cases with boundary values."""
        # Test maximum valid artist ID
        max_artist = LABEL_ENTITY_ID_OFFSET - 1
        result = to_entity_internal_id(max_artist, EntityType.ARTIST)
        self.assertEqual(max_artist, result)
        
        # Test minimum label ID that gets offset
        min_label = 1
        result = to_entity_internal_id(min_label, EntityType.LABEL)
        self.assertEqual(min_label + LABEL_ENTITY_ID_OFFSET, result)


if __name__ == "__main__":
    unittest.main() 