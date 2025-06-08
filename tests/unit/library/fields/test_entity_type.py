import unittest

from musigree.library.fields.entity_type import EntityType


class TestEntityType(unittest.TestCase):
    """Test cases for the EntityType enum."""

    def test_entity_type_values(self):
        """Test that EntityType enum has correct values."""
        self.assertEqual(1, EntityType.ARTIST.value)
        self.assertEqual(2, EntityType.LABEL.value)

    def test_entity_type_names(self):
        """Test that EntityType enum has correct names."""
        self.assertEqual("ARTIST", EntityType.ARTIST.name)
        self.assertEqual("LABEL", EntityType.LABEL.name)

    def test_from_str_artist_lowercase(self):
        """Test from_str with lowercase 'artist'."""
        result = EntityType.from_str("artist")
        self.assertEqual(EntityType.ARTIST, result)

    def test_from_str_artist_uppercase(self):
        """Test from_str with uppercase 'ARTIST'."""
        result = EntityType.from_str("ARTIST")
        self.assertEqual(EntityType.ARTIST, result)

    def test_from_str_label_lowercase(self):
        """Test from_str with lowercase 'label'."""
        result = EntityType.from_str("label")
        self.assertEqual(EntityType.LABEL, result)

    def test_from_str_label_uppercase(self):
        """Test from_str with uppercase 'LABEL'."""
        result = EntityType.from_str("LABEL")
        self.assertEqual(EntityType.LABEL, result)

    def test_from_str_invalid_input(self):
        """Test from_str with invalid input raises NotImplementedError."""
        with self.assertRaises(NotImplementedError):
            EntityType.from_str("invalid")

    def test_from_str_empty_string(self):
        """Test from_str with empty string raises NotImplementedError."""
        with self.assertRaises(NotImplementedError):
            EntityType.from_str("")

    def test_from_str_none(self):
        """Test from_str with None raises NotImplementedError."""
        with self.assertRaises(NotImplementedError):
            EntityType.from_str(None)  # type: ignore

    def test_from_str_mixed_case(self):
        """Test from_str with mixed case raises NotImplementedError."""
        with self.assertRaises(NotImplementedError):
            EntityType.from_str("Artist")
        
        with self.assertRaises(NotImplementedError):
            EntityType.from_str("Label")

    def test_less_than_comparison_artist_label(self):
        """Test less-than comparison between ARTIST and LABEL."""
        self.assertTrue(EntityType.ARTIST < EntityType.LABEL)
        self.assertFalse(EntityType.LABEL < EntityType.ARTIST)

    def test_less_than_comparison_same_types(self):
        """Test less-than comparison between same types."""
        self.assertFalse(EntityType.ARTIST < EntityType.ARTIST)
        self.assertFalse(EntityType.LABEL < EntityType.LABEL)

    def test_less_than_comparison_with_non_entity_type(self):
        """Test less-than comparison with non-EntityType returns NotImplemented."""
        result = EntityType.ARTIST.__lt__("not an entity type")  # type: ignore
        self.assertEqual(NotImplemented, result)

    def test_repr_method(self):
        """Test string representation (__repr__) of EntityType."""
        self.assertEqual("ARTIST", repr(EntityType.ARTIST))
        self.assertEqual("LABEL", repr(EntityType.LABEL))

    def test_str_method(self):
        """Test string conversion (__str__) of EntityType."""
        self.assertEqual("EntityType.ARTIST", str(EntityType.ARTIST))
        self.assertEqual("EntityType.LABEL", str(EntityType.LABEL))

    def test_equality_comparison(self):
        """Test equality comparison between EntityType values."""
        self.assertEqual(EntityType.ARTIST, EntityType.ARTIST)
        self.assertEqual(EntityType.LABEL, EntityType.LABEL)
        self.assertNotEqual(EntityType.ARTIST, EntityType.LABEL)

    def test_hash_consistency(self):
        """Test that EntityType values are hashable and consistent."""
        # Should be able to use as dictionary keys
        test_dict = {
            EntityType.ARTIST: "artist_value",
            EntityType.LABEL: "label_value"
        }
        
        self.assertEqual("artist_value", test_dict[EntityType.ARTIST])
        self.assertEqual("label_value", test_dict[EntityType.LABEL])

    def test_enum_iteration(self):
        """Test iteration over EntityType enum values."""
        entity_types = list(EntityType)
        self.assertEqual(2, len(entity_types))
        self.assertIn(EntityType.ARTIST, entity_types)
        self.assertIn(EntityType.LABEL, entity_types)

    def test_enum_membership(self):
        """Test membership testing for EntityType enum."""
        self.assertIn(EntityType.ARTIST, EntityType)
        self.assertIn(EntityType.LABEL, EntityType)


if __name__ == "__main__":
    unittest.main() 