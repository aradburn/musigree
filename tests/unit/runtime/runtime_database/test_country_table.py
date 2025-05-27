import unittest
from sqlalchemy import inspect

from musigree.runtime.runtime_database.country_table import CountryTable


class TestCountryTable(unittest.TestCase):
    """Unit tests for CountryTable class."""

    def test_init_with_valid_entries(self):
        """Test initialization with valid column entries."""
        # GIVEN
        entries = {
            "id": 1,
            "country_name": "United States",
            "invalid_column": "should_be_ignored"
        }
        
        # WHEN
        country_table = CountryTable(**entries)
        
        # THEN
        self.assertEqual(country_table.id, 1)
        self.assertEqual(country_table.country_name, "United States")
        self.assertFalse(hasattr(country_table, "invalid_column"))

    def test_init_with_empty_entries(self):
        """Test initialization with empty entries dictionary."""
        # GIVEN
        entries = {}
        
        # WHEN
        country_table = CountryTable(**entries)
        
        # THEN
        self.assertIsInstance(country_table, CountryTable)

    def test_tablename(self):
        """Test that the table name is correctly set."""
        # GIVEN/WHEN
        table_name = CountryTable.__tablename__
        
        # THEN
        self.assertEqual(table_name, "country")

    def test_columns_exist(self):
        """Test that expected columns exist in the table."""
        # GIVEN
        expected_columns = {"id", "country_name"}
        
        # WHEN
        columns = set(column.name for column in inspect(CountryTable).columns)
        
        # THEN
        self.assertTrue(expected_columns.issubset(columns))

    def test_repr(self):
        """Test string representation of CountryTable instance."""
        # GIVEN
        country_input = {"id": 1, "country_name": "United Kingdom"}
        country_table = CountryTable(**country_input)
        
        # WHEN
        repr_str = repr(country_table)
        
        # THEN
        self.assertIsInstance(repr_str, str)
        self.assertIn("United Kingdom", repr_str) 