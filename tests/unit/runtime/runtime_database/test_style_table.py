import unittest
from sqlalchemy import inspect

from musigree.runtime.runtime_database.style_table import StyleTable


class TestStyleTable(unittest.TestCase):
    """Unit tests for StyleTable class."""

    def test_init_with_valid_entries(self):
        """Test initialization with valid column entries."""
        # GIVEN
        entries = {
            "id": 1,
            "style_name": "Electronic",
            "invalid_column": "should_be_ignored"
        }
        
        # WHEN
        style_table = StyleTable(**entries)
        
        # THEN
        self.assertEqual(style_table.id, 1)
        self.assertEqual(style_table.style_name, "Electronic")
        self.assertFalse(hasattr(style_table, "invalid_column"))

    def test_init_with_empty_entries(self):
        """Test initialization with empty entries dictionary."""
        # GIVEN
        entries = {}
        
        # WHEN
        style_table = StyleTable(**entries)
        
        # THEN
        self.assertIsInstance(style_table, StyleTable)

    def test_tablename(self):
        """Test that the table name is correctly set."""
        # GIVEN/WHEN
        table_name = StyleTable.__tablename__
        
        # THEN
        self.assertEqual(table_name, "style")

    def test_columns_exist(self):
        """Test that expected columns exist in the table."""
        # GIVEN
        expected_columns = {"id", "style_name"}
        
        # WHEN
        columns = set(column.name for column in inspect(StyleTable).columns)
        
        # THEN
        self.assertTrue(expected_columns.issubset(columns))

    def test_repr(self):
        """Test string representation of StyleTable instance."""
        # GIVEN
        style_input = {"id": 1, "style_name": "Rock"}
        style_table = StyleTable(**style_input)
        
        # WHEN
        repr_str = repr(style_table)
        
        # THEN
        self.assertIsInstance(repr_str, str)
        self.assertIn("Rock", repr_str) 