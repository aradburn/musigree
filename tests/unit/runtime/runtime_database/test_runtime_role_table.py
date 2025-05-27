import unittest
from sqlalchemy import inspect

from musigree.library.fields.role_type import RoleType
from musigree.runtime.runtime_database.runtime_role_table import RuntimeRoleTable


class TestRuntimeRoleTable(unittest.TestCase):
    """Unit tests for RuntimeRoleTable class."""

    def test_init_with_valid_entries(self):
        """Test initialization with valid column entries."""
        # GIVEN
        entries = {
            "id": 1,
            "role_name": "Producer",
            "role_category": RoleType.Category.PRODUCTION,
            "role_subcategory": RoleType.Subcategory.NONE,
            "role_category_name": "Production",
            "role_subcategory_name": "None",
            "invalid_column": "should_be_ignored"
        }
        
        # WHEN
        role_table = RuntimeRoleTable(**entries)
        
        # THEN
        self.assertEqual(role_table.id, 1)
        self.assertEqual(role_table.role_name, "Producer")
        self.assertEqual(role_table.role_category, RoleType.Category.PRODUCTION)
        self.assertEqual(role_table.role_subcategory, RoleType.Subcategory.NONE)
        self.assertEqual(role_table.role_category_name, "Production")
        self.assertEqual(role_table.role_subcategory_name, "None")
        self.assertFalse(hasattr(role_table, "invalid_column"))

    def test_init_with_empty_entries(self):
        """Test initialization with empty entries dictionary."""
        # GIVEN
        entries = {}
        
        # WHEN
        role_table = RuntimeRoleTable(**entries)
        
        # THEN
        self.assertIsInstance(role_table, RuntimeRoleTable)

    def test_init_with_minimal_required_entries(self):
        """Test initialization with minimal required entries."""
        # GIVEN
        entries = {
            "role_name": "Vocalist",
            "role_category": RoleType.Category.VOCAL,
            "role_subcategory": RoleType.Subcategory.NONE
        }
        
        # WHEN
        role_table = RuntimeRoleTable(**entries)
        
        # THEN
        self.assertEqual(role_table.role_name, "Vocalist")
        self.assertEqual(role_table.role_category, RoleType.Category.VOCAL)
        self.assertEqual(role_table.role_subcategory, RoleType.Subcategory.NONE)

    def test_init_with_instruments_category(self):
        """Test initialization with instruments category and subcategory."""
        # GIVEN
        entries = {
            "role_name": "Guitarist",
            "role_category": RoleType.Category.INSTRUMENTS,
            "role_subcategory": RoleType.Subcategory.STRINGED_INSTRUMENTS,
            "role_category_name": "Instruments",
            "role_subcategory_name": "String Instruments"
        }
        
        # WHEN
        role_table = RuntimeRoleTable(**entries)
        
        # THEN
        self.assertEqual(role_table.role_name, "Guitarist")
        self.assertEqual(role_table.role_category, RoleType.Category.INSTRUMENTS)
        self.assertEqual(role_table.role_subcategory, RoleType.Subcategory.STRINGED_INSTRUMENTS)
        self.assertEqual(role_table.role_category_name, "Instruments")
        self.assertEqual(role_table.role_subcategory_name, "String Instruments")

    def test_tablename(self):
        """Test that the table name is correctly set."""
        # GIVEN/WHEN
        table_name = RuntimeRoleTable.__tablename__
        
        # THEN
        self.assertEqual(table_name, "runtime_role")

    def test_columns_exist(self):
        """Test that expected columns exist in the table."""
        # GIVEN
        expected_columns = {
            "id", "role_name", "role_category", "role_subcategory",
            "role_category_name", "role_subcategory_name"
        }
        
        # WHEN
        columns = set(column.name for column in inspect(RuntimeRoleTable).columns)
        
        # THEN
        self.assertTrue(expected_columns.issubset(columns))

    def test_primary_key(self):
        """Test that id column is the primary key."""
        # GIVEN/WHEN
        primary_key_columns = [col.name for col in inspect(RuntimeRoleTable).primary_key]
        
        # THEN
        self.assertEqual(primary_key_columns, ["id"])

    def test_role_name_indexed(self):
        """Test that role_name column has index."""
        # GIVEN/WHEN
        role_name_column = inspect(RuntimeRoleTable).columns['role_name']
        
        # THEN
        self.assertTrue(role_name_column.index)

    def test_repr_with_data(self):
        """Test string representation of RuntimeRoleTable instance with data."""
        # GIVEN
        role_input = {
            "id": 1,
            "role_name": "Producer",
            "role_category": RoleType.Category.PRODUCTION,
            "role_subcategory": RoleType.Subcategory.NONE,
            "role_category_name": "Production",
            "role_subcategory_name": "None"
        }
        role_table = RuntimeRoleTable(**role_input)
        
        # WHEN
        repr_str = repr(role_table)
        
        # THEN
        self.assertIsInstance(repr_str, str)
        self.assertIn("Producer", repr_str)
        self.assertIn("Production", repr_str)

    def test_repr_with_minimal_data(self):
        """Test string representation with minimal data."""
        # GIVEN
        role_input = {
            "role_name": "Test Role",
            "role_category": RoleType.Category.TECHNICAL,
            "role_subcategory": RoleType.Subcategory.TECHNICAL_MUSICAL
        }
        role_table = RuntimeRoleTable(**role_input)
        
        # WHEN
        repr_str = repr(role_table)
        
        # THEN
        self.assertIsInstance(repr_str, str)
        self.assertIn("Test Role", repr_str)

    def test_column_filtering_in_init(self):
        """Test that initialization only uses valid column names."""
        # GIVEN
        entries = {
            "role_name": "Valid Role",
            "role_category": RoleType.Category.MANAGEMENT,
            "role_subcategory": RoleType.Subcategory.NONE,
            "nonexistent_column": "Should be ignored",
            "another_invalid": 123,
            "random_field": ["should", "not", "exist"]
        }
        
        # WHEN
        role_table = RuntimeRoleTable(**entries)
        
        # THEN
        self.assertEqual(role_table.role_name, "Valid Role")
        self.assertEqual(role_table.role_category, RoleType.Category.MANAGEMENT)
        self.assertEqual(role_table.role_subcategory, RoleType.Subcategory.NONE)
        self.assertFalse(hasattr(role_table, "nonexistent_column"))
        self.assertFalse(hasattr(role_table, "another_invalid"))
        self.assertFalse(hasattr(role_table, "random_field"))

    def test_enum_values_assignment(self):
        """Test that enum values are properly assigned."""
        # GIVEN
        entries = {
            "role_name": "Drummer",
            "role_category": RoleType.Category.INSTRUMENTS,
            "role_subcategory": RoleType.Subcategory.DRUMS_AND_PERCUSSION
        }
        
        # WHEN
        role_table = RuntimeRoleTable(**entries)
        
        # THEN
        self.assertIsInstance(role_table.role_category, RoleType.Category)
        self.assertIsInstance(role_table.role_subcategory, RoleType.Subcategory)
        self.assertEqual(role_table.role_category.value, 6)  # INSTRUMENTS = 6
        self.assertEqual(role_table.role_subcategory.value, 1)  # DRUMS_AND_PERCUSSION = 1


if __name__ == '__main__':
    unittest.main() 