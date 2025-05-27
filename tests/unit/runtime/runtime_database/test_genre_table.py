import unittest
from sqlalchemy import inspect

from musigree.runtime.runtime_database.genre_table import GenreTable


class TestGenreTable(unittest.TestCase):
    """Unit tests for GenreTable class."""

    def test_init_with_valid_entries(self):
        """Test initialization with valid column entries."""
        # GIVEN
        entries = {
            "id": 1,
            "genre_name": "Electronic",
            "invalid_column": "should_be_ignored"
        }
        
        # WHEN
        genre_table = GenreTable(**entries)
        
        # THEN
        self.assertEqual(genre_table.id, 1)
        self.assertEqual(genre_table.genre_name, "Electronic")
        self.assertFalse(hasattr(genre_table, "invalid_column"))

    def test_init_with_empty_entries(self):
        """Test initialization with empty entries dictionary."""
        # GIVEN
        entries = {}
        
        # WHEN
        genre_table = GenreTable(**entries)
        
        # THEN
        self.assertIsInstance(genre_table, GenreTable)

    def test_tablename(self):
        """Test that the table name is correctly set."""
        # GIVEN/WHEN
        table_name = GenreTable.__tablename__
        
        # THEN
        self.assertEqual(table_name, "genre")

    def test_columns_exist(self):
        """Test that expected columns exist in the table."""
        # GIVEN
        expected_columns = {"id", "genre_name"}
        
        # WHEN
        columns = set(column.name for column in inspect(GenreTable).columns)
        
        # THEN
        self.assertTrue(expected_columns.issubset(columns))

    def test_repr(self):
        """Test string representation of GenreTable instance."""
        # GIVEN
        genre_input = {"id": 1, "genre_name": "Rock"}
        genre_table = GenreTable(**genre_input)
        
        # WHEN
        repr_str = repr(genre_table)
        
        # THEN
        self.assertIsInstance(repr_str, str)
        self.assertIn("Rock", repr_str) 