import unittest
from sqlalchemy import inspect

from musigree.runtime.runtime_database.runtime_relation_table import RuntimeRelationTable


class TestRuntimeRelationTable(unittest.TestCase):
    """Unit tests for RuntimeRelationTable class."""

    def test_init_with_valid_entries(self):
        """Test initialization with valid column entries."""
        # GIVEN
        entries = {
            "id": 1,
            "subject": 12345,
            "predicate": 3,
            "object": 67890,
            "invalid_column": "should_be_ignored"
        }
        
        # WHEN
        relation_table = RuntimeRelationTable(**entries)
        
        # THEN
        self.assertEqual(relation_table.id, 1)
        self.assertEqual(relation_table.subject, 12345)
        self.assertEqual(relation_table.predicate, 3)
        self.assertEqual(relation_table.object, 67890)
        self.assertFalse(hasattr(relation_table, "invalid_column"))

    def test_init_with_empty_entries(self):
        """Test initialization with empty entries dictionary."""
        # GIVEN
        entries = {}
        
        # WHEN
        relation_table = RuntimeRelationTable(**entries)
        
        # THEN
        self.assertIsInstance(relation_table, RuntimeRelationTable)

    def test_init_with_minimal_required_entries(self):
        """Test initialization with minimal required entries."""
        # GIVEN
        entries = {
            "subject": 123,
            "predicate": 456,
            "object": 789
        }
        
        # WHEN
        relation_table = RuntimeRelationTable(**entries)
        
        # THEN
        self.assertEqual(relation_table.subject, 123)
        self.assertEqual(relation_table.predicate, 456)
        self.assertEqual(relation_table.object, 789)

    def test_tablename(self):
        """Test that the table name is correctly set."""
        # GIVEN/WHEN
        table_name = RuntimeRelationTable.__tablename__
        
        # THEN
        self.assertEqual(table_name, "runtime_relation")

    def test_columns_exist(self):
        """Test that expected columns exist in the table."""
        # GIVEN
        expected_columns = {"id", "subject", "predicate", "object"}
        
        # WHEN
        columns = set(column.name for column in inspect(RuntimeRelationTable).columns)
        
        # THEN
        self.assertTrue(expected_columns.issubset(columns))

    def test_primary_key(self):
        """Test that id column is the primary key."""
        # GIVEN/WHEN
        primary_key_columns = [col.name for col in inspect(RuntimeRelationTable).primary_key]
        
        # THEN
        self.assertEqual(primary_key_columns, ["id"])

    def test_table_args_defined(self):
        """Test that table args are properly defined."""
        # GIVEN/WHEN
        table_args = RuntimeRelationTable.__table_args__
        
        # THEN
        self.assertIsNotNone(table_args)
        self.assertIsInstance(table_args, tuple)

    def test_repr_with_data(self):
        """Test string representation of RuntimeRelationTable instance with data."""
        # GIVEN
        relation_input = {
            "id": 1,
            "subject": 12345,
            "predicate": 3,
            "object": 67890
        }
        relation_table = RuntimeRelationTable(**relation_input)
        
        # WHEN
        repr_str = repr(relation_table)
        
        # THEN
        self.assertIsInstance(repr_str, str)
        self.assertIn("12345", repr_str)
        self.assertIn("67890", repr_str)

    def test_repr_with_minimal_data(self):
        """Test string representation with minimal data."""
        # GIVEN
        relation_input = {
            "subject": 111,
            "predicate": 222,
            "object": 333
        }
        relation_table = RuntimeRelationTable(**relation_input)
        
        # WHEN
        repr_str = repr(relation_table)
        
        # THEN
        self.assertIsInstance(repr_str, str)
        self.assertIn("111", repr_str)
        self.assertIn("333", repr_str)

    def test_column_filtering_in_init(self):
        """Test that initialization only uses valid column names."""
        # GIVEN
        entries = {
            "subject": 100,
            "predicate": 200,
            "object": 300,
            "nonexistent_column": "Should be ignored",
            "another_invalid": 123,
            "random_field": ["should", "not", "exist"]
        }
        
        # WHEN
        relation_table = RuntimeRelationTable(**entries)
        
        # THEN
        self.assertEqual(relation_table.subject, 100)
        self.assertEqual(relation_table.predicate, 200)
        self.assertEqual(relation_table.object, 300)
        self.assertFalse(hasattr(relation_table, "nonexistent_column"))
        self.assertFalse(hasattr(relation_table, "another_invalid"))
        self.assertFalse(hasattr(relation_table, "random_field"))

    def test_foreign_key_relationship(self):
        """Test that predicate column has foreign key constraint."""
        # GIVEN/WHEN
        predicate_column = inspect(RuntimeRelationTable).columns['predicate']
        
        # THEN
        self.assertTrue(len(predicate_column.foreign_keys) > 0)


if __name__ == '__main__':
    unittest.main() 