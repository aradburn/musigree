import unittest
from sqlalchemy import inspect
from unittest.mock import Mock, patch

from musigree.library.fields.entity_type import EntityType
from musigree.runtime.runtime_database.runtime_entity_table import RuntimeEntityTable


class TestRuntimeEntityTable(unittest.TestCase):
    """Unit tests for RuntimeEntityTable class."""

    def test_init_with_valid_entries(self):
        """Test initialization with valid column entries."""
        # GIVEN
        entries = {
            "id": 1,
            "entity_id": 12345,
            "entity_type": EntityType.ARTIST,
            "entity_name": "The Beatles",
            "relation_counts": {"releases": 100, "tracks": 500},
            "entity_metadata": {"formed": "1960", "disbanded": "1970"},
            "aliases": {"alternate_names": ["Beatles", "Fab Four"]},
            "groups": {"members": ["John", "Paul", "George", "Ringo"]},
            "members": {"current": [], "former": ["John Lennon"]},
            "countries": "United Kingdom",
            "genres": "Rock, Pop",
            "styles": "Merseybeat, Pop Rock",
            "invalid_column": "should_be_ignored"
        }
        
        # WHEN
        entity_table = RuntimeEntityTable(**entries)
        
        # THEN
        self.assertEqual(entity_table.id, 1)
        self.assertEqual(entity_table.entity_id, 12345)
        self.assertEqual(entity_table.entity_type, EntityType.ARTIST)
        self.assertEqual(entity_table.entity_name, "The Beatles")
        self.assertEqual(entity_table.relation_counts, {"releases": 100, "tracks": 500})
        self.assertEqual(entity_table.entity_metadata, {"formed": "1960", "disbanded": "1970"})
        self.assertEqual(entity_table.aliases, {"alternate_names": ["Beatles", "Fab Four"]})
        self.assertEqual(entity_table.groups, {"members": ["John", "Paul", "George", "Ringo"]})
        self.assertEqual(entity_table.members, {"current": [], "former": ["John Lennon"]})
        self.assertEqual(entity_table.countries, "United Kingdom")
        self.assertEqual(entity_table.genres, "Rock, Pop")
        self.assertEqual(entity_table.styles, "Merseybeat, Pop Rock")
        self.assertFalse(hasattr(entity_table, "invalid_column"))

    def test_init_with_empty_entries(self):
        """Test initialization with empty entries dictionary."""
        # GIVEN
        entries = {}
        
        # WHEN
        entity_table = RuntimeEntityTable(**entries)
        
        # THEN
        self.assertIsInstance(entity_table, RuntimeEntityTable)

    def test_init_with_minimal_required_entries(self):
        """Test initialization with minimal required entries."""
        # GIVEN
        entries = {
            "entity_type": EntityType.LABEL,
            "entity_name": "Capitol Records",
            "entity_metadata": {"founded": "1942"}
        }
        
        # WHEN
        entity_table = RuntimeEntityTable(**entries)
        
        # THEN
        self.assertEqual(entity_table.entity_type, EntityType.LABEL)
        self.assertEqual(entity_table.entity_name, "Capitol Records")
        self.assertEqual(entity_table.entity_metadata, {"founded": "1942"})

    def test_tablename(self):
        """Test that the table name is correctly set."""
        # GIVEN/WHEN
        table_name = RuntimeEntityTable.__tablename__
        
        # THEN
        self.assertEqual(table_name, "runtime_entity")

    @patch('tests.unit.runtime.runtime_database.test_runtime_entity_table.inspect')
    def test_columns_exist(self, mock_inspect):
        """Test that expected columns exist in the table."""
        # GIVEN
        expected_columns = {
            "id", "entity_id", "entity_type", "entity_name", 
            "relation_counts", "entity_metadata", "aliases", 
            "groups", "members", "countries", "genres", "styles"
        }
        
        # Mock columns
        mock_columns = []
        for col_name in expected_columns:
            mock_col = Mock()
            mock_col.name = col_name
            mock_columns.append(mock_col)
        
        mock_inspector = Mock()
        mock_inspector.columns = mock_columns
        mock_inspect.return_value = mock_inspector
        
        # WHEN
        columns = set(column.name for column in inspect(RuntimeEntityTable).columns)
        
        # THEN
        self.assertTrue(expected_columns.issubset(columns))

    @patch('tests.unit.runtime.runtime_database.test_runtime_entity_table.inspect')
    def test_primary_key(self, mock_inspect):
        """Test that id column is the primary key."""
        # GIVEN
        mock_pk_col = Mock()
        mock_pk_col.name = "id"
        
        mock_inspector = Mock()
        mock_inspector.primary_key = [mock_pk_col]
        mock_inspect.return_value = mock_inspector
        
        # WHEN
        primary_key_columns = [col.name for col in inspect(RuntimeEntityTable).primary_key]
        
        # THEN
        self.assertEqual(primary_key_columns, ["id"])

    def test_table_args_defined(self):
        """Test that table args are properly defined."""
        # GIVEN/WHEN
        table_args = RuntimeEntityTable.__table_args__
        
        # THEN
        self.assertIsNotNone(table_args)
        self.assertIsInstance(table_args, tuple)

    def test_repr_with_data(self):
        """Test string representation of RuntimeEntityTable instance with data."""
        # GIVEN
        entity_input = {
            "id": 1,
            "entity_id": 12345,
            "entity_type": EntityType.ARTIST,
            "entity_name": "The Beatles",
            "entity_metadata": {"formed": "1960"}
        }
        entity_table = RuntimeEntityTable(**entity_input)
        
        # WHEN
        repr_str = repr(entity_table)
        
        # THEN
        self.assertIsInstance(repr_str, str)
        self.assertIn("The Beatles", repr_str)
        self.assertIn("12345", repr_str)

    def test_repr_with_minimal_data(self):
        """Test string representation with minimal data."""
        # GIVEN
        entity_input = {
            "entity_type": EntityType.LABEL,
            "entity_name": "Test Label",
            "entity_metadata": {}
        }
        entity_table = RuntimeEntityTable(**entity_input)
        
        # WHEN
        repr_str = repr(entity_table)
        
        # THEN
        self.assertIsInstance(repr_str, str)
        self.assertIn("Test Label", repr_str)

    def test_column_filtering_in_init(self):
        """Test that initialization only uses valid column names."""
        # GIVEN
        entries = {
            "entity_name": "Valid Column",
            "entity_type": EntityType.ARTIST,
            "entity_metadata": {},
            "nonexistent_column": "Should be ignored",
            "another_invalid": 123,
            "random_field": ["should", "not", "exist"]
        }
        
        # WHEN
        entity_table = RuntimeEntityTable(**entries)
        
        # THEN
        self.assertEqual(entity_table.entity_name, "Valid Column")
        self.assertEqual(entity_table.entity_type, EntityType.ARTIST)
        self.assertFalse(hasattr(entity_table, "nonexistent_column"))
        self.assertFalse(hasattr(entity_table, "another_invalid"))
        self.assertFalse(hasattr(entity_table, "random_field"))

    def test_json_fields_with_none_values(self):
        """Test JSON fields can be set to None."""
        # GIVEN
        entries = {
            "entity_type": EntityType.ARTIST,
            "entity_name": "Test Artist",
            "entity_metadata": {"info": "test"},
            "relation_counts": None,
            "aliases": None,
            "groups": None,
            "members": None
        }
        
        # WHEN
        entity_table = RuntimeEntityTable(**entries)
        
        # THEN
        self.assertIsNone(entity_table.relation_counts)
        self.assertIsNone(entity_table.aliases)
        self.assertIsNone(entity_table.groups)
        self.assertIsNone(entity_table.members)
        self.assertEqual(entity_table.entity_metadata, {"info": "test"})

    def test_string_fields_with_none_values(self):
        """Test string fields can be set to None."""
        # GIVEN
        entries = {
            "entity_type": EntityType.LABEL,
            "entity_name": "Test Label",
            "entity_metadata": {},
            "countries": None,
            "genres": None,
            "styles": None
        }
        
        # WHEN
        entity_table = RuntimeEntityTable(**entries)
        
        # THEN
        self.assertIsNone(entity_table.countries)
        self.assertIsNone(entity_table.genres)
        self.assertIsNone(entity_table.styles)


if __name__ == '__main__':
    unittest.main() 