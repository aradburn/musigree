"""
Unit tests for musigree.library.cache.role_cache module.
"""
import json
from unittest.mock import patch

import pytest

from musigree.library.cache.role_cache import RoleCache
from musigree.library.fields.role_type import RoleType
from musigree.runtime.runtime_domain.role import (
    RuntimeRoleJSTree,
    RuntimeRoleJSTreeWrapper,
)


class TestRoleCache:
    """Test cases for RoleCache class."""

    @staticmethod
    def setup_method():
        """Set up test fixtures before each test method."""
        # Clear all class variables to ensure clean state
        RoleCache.role_name_to_role_id_lookup.clear()
        RoleCache.role_name_set.clear()
        RoleCache.role_id_to_role_category_lookup.clear()
        RoleCache.role_id_to_role_name_lookup.clear()
        RoleCache.role_jstree = RuntimeRoleJSTree()
        RoleCache.role_category_to_role_name_lookup.clear()

    def test_class_variables_initialization(self):
        """Test that class variables are properly initialized."""
        # Assert
        assert isinstance(RoleCache.role_name_to_role_id_lookup, dict)
        assert isinstance(RoleCache.role_name_set, set)
        assert isinstance(RoleCache.role_id_to_role_category_lookup, dict)
        assert isinstance(RoleCache.role_id_to_role_name_lookup, dict)
        assert isinstance(RoleCache.role_jstree, RuntimeRoleJSTree)
        assert isinstance(RoleCache.role_category_to_role_name_lookup, dict)

    def test_get_all_roles_empty(self):
        """Test get_all_roles with empty cache."""
        # Act
        result = RoleCache.get_all_roles()

        # Assert
        assert result == {"roles": []}

    def test_get_all_roles_with_data(self):
        """Test get_all_roles with populated cache."""
        # Arrange
        RoleCache.role_id_to_role_name_lookup[1] = "Vocalist"
        RoleCache.role_id_to_role_name_lookup[2] = "Guitarist"
        RoleCache.role_id_to_role_category_lookup[1] = RoleType.Category.VOCAL
        RoleCache.role_id_to_role_category_lookup[2] = RoleType.Category.INSTRUMENTS

        # Act
        result = RoleCache.get_all_roles()

        # Assert
        assert "roles" in result
        assert len(result["roles"]) == 2
        
        # Check first role
        role_1 = next(role for role in result["roles"] if role["id"] == 1)
        assert role_1["id"] == 1
        assert role_1["role_name"] == "Vocalist"
        assert role_1["role_category"] == "VOCAL"
        
        # Check second role
        role_2 = next(role for role in result["roles"] if role["id"] == 2)
        assert role_2["id"] == 2
        assert role_2["role_name"] == "Guitarist"
        assert role_2["role_category"] == "INSTRUMENTS"

    def test_get_all_roles_multiple_categories(self):
        """Test get_all_roles with multiple role categories."""
        # Arrange
        RoleCache.role_id_to_role_name_lookup[1] = "Producer"
        RoleCache.role_id_to_role_name_lookup[2] = "Singer"
        RoleCache.role_id_to_role_name_lookup[3] = "Engineer"
        RoleCache.role_id_to_role_category_lookup[1] = RoleType.Category.PRODUCTION
        RoleCache.role_id_to_role_category_lookup[2] = RoleType.Category.VOCAL
        RoleCache.role_id_to_role_category_lookup[3] = RoleType.Category.TECHNICAL

        # Act
        result = RoleCache.get_all_roles()

        # Assert
        assert len(result["roles"]) == 3
        
        categories = [role["role_category"] for role in result["roles"]]
        assert "PRODUCTION" in categories
        assert "VOCAL" in categories
        assert "TECHNICAL" in categories

    def test_get_all_roles_data_structure(self):
        """Test that get_all_roles returns proper data structure."""
        # Arrange
        RoleCache.role_id_to_role_name_lookup[1] = "Test Role"
        RoleCache.role_id_to_role_category_lookup[1] = RoleType.Category.VOCAL

        # Act
        result = RoleCache.get_all_roles()

        # Assert
        assert isinstance(result, dict)
        assert "roles" in result
        assert isinstance(result["roles"], list)
        
        role = result["roles"][0]
        assert isinstance(role, dict)
        assert "id" in role
        assert "role_name" in role
        assert "role_category" in role

    @patch.object(RuntimeRoleJSTreeWrapper, 'model_dump_json')
    def test_get_roles_json_success(self, mock_model_dump_json):
        """Test get_roles_json method."""
        # Arrange
        expected_json = '{"test": "data"}'
        mock_model_dump_json.return_value = expected_json

        # Act
        result = RoleCache.get_roles_json()

        # Assert
        assert result == expected_json
        mock_model_dump_json.assert_called_once()

    @patch.object(RuntimeRoleJSTreeWrapper, 'model_dump_json')
    def test_get_roles_json_wrapper_creation(self, mock_model_dump_json):
        """Test that get_roles_json creates proper wrapper."""
        # Arrange
        mock_model_dump_json.return_value = "{}"

        # Act
        RoleCache.get_roles_json()

        # Assert
        # The wrapper should be created with specific parameters
        mock_model_dump_json.assert_called_once()

    def test_get_roles_json_integration(self):
        """Test get_roles_json integration without mocking."""
        # Act
        result = RoleCache.get_roles_json()

        # Assert
        assert isinstance(result, str)
        # Should be valid JSON
        parsed = json.loads(result)
        assert isinstance(parsed, dict)

    def test_role_name_to_role_id_lookup_functionality(self):
        """Test role_name_to_role_id_lookup behavior."""
        # Arrange
        RoleCache.role_name_to_role_id_lookup["test_role"] = 123

        # Act & Assert
        assert RoleCache.role_name_to_role_id_lookup["test_role"] == 123
        assert "test_role" in RoleCache.role_name_to_role_id_lookup

    def test_role_name_set_functionality(self):
        """Test role_name_set behavior."""
        # Arrange
        RoleCache.role_name_set.add("test_role")

        # Act & Assert
        assert "test_role" in RoleCache.role_name_set
        assert len(RoleCache.role_name_set) == 1

    def test_role_category_to_role_name_lookup_functionality(self):
        """Test role_category_to_role_name_lookup behavior."""
        # Arrange
        RoleCache.role_category_to_role_name_lookup["VOCAL"] = ["Singer", "Vocalist"]

        # Act & Assert
        assert "VOCAL" in RoleCache.role_category_to_role_name_lookup
        assert RoleCache.role_category_to_role_name_lookup["VOCAL"] == ["Singer", "Vocalist"]

    def test_role_jstree_functionality(self):
        """Test role_jstree behavior."""
        # Arrange
        original_jstree = RoleCache.role_jstree
        new_jstree = RuntimeRoleJSTree()

        # Act
        RoleCache.role_jstree = new_jstree

        # Assert
        assert RoleCache.role_jstree == new_jstree
        assert RoleCache.role_jstree is not original_jstree


class TestRoleCacheEdgeCases:
    """Test edge cases for RoleCache."""

    @staticmethod
    def setup_method():
        """Set up test fixtures before each test method."""
        # Clear all class variables to ensure clean state
        RoleCache.role_name_to_role_id_lookup.clear()
        RoleCache.role_name_set.clear()
        RoleCache.role_id_to_role_category_lookup.clear()
        RoleCache.role_id_to_role_name_lookup.clear()
        RoleCache.role_jstree = RuntimeRoleJSTree()
        RoleCache.role_category_to_role_name_lookup.clear()

    def test_get_all_roles_missing_category(self):
        """Test get_all_roles when role_id_to_role_category_lookup is missing entry."""
        # Arrange
        RoleCache.role_id_to_role_name_lookup[1] = "Test Role"
        # Intentionally not adding to role_id_to_role_category_lookup

        # Act & Assert
        with pytest.raises(KeyError):
            RoleCache.get_all_roles()

    def test_get_all_roles_inconsistent_data(self):
        """Test get_all_roles with inconsistent data between lookups."""
        # Arrange
        RoleCache.role_id_to_role_name_lookup[1] = "Role 1"
        RoleCache.role_id_to_role_name_lookup[2] = "Role 2"
        RoleCache.role_id_to_role_category_lookup[1] = RoleType.Category.VOCAL
        # Missing category for role_id 2

        # Act & Assert
        with pytest.raises(KeyError):
            RoleCache.get_all_roles()

    def test_large_dataset(self):
        """Test with large dataset to ensure performance."""
        # Arrange
        for i in range(1000):
            RoleCache.role_id_to_role_name_lookup[i] = f"Role {i}"
            RoleCache.role_id_to_role_category_lookup[i] = RoleType.Category.VOCAL

        # Act
        result = RoleCache.get_all_roles()

        # Assert
        assert len(result["roles"]) == 1000
        assert all(role["role_category"] == "VOCAL" for role in result["roles"])

    def test_role_names_with_special_characters(self):
        """Test role names with special characters."""
        # Arrange
        special_names = ["Role with spaces", "Role-with-dashes", "Role_with_underscores", "Role@#$%"]
        for i, name in enumerate(special_names, 1):
            RoleCache.role_id_to_role_name_lookup[i] = name
            RoleCache.role_id_to_role_category_lookup[i] = RoleType.Category.VOCAL

        # Act
        result = RoleCache.get_all_roles()

        # Assert
        assert len(result["roles"]) == len(special_names)
        role_names = [role["role_name"] for role in result["roles"]]
        for name in special_names:
            assert name in role_names


class TestRoleCacheStaticMethods:
    """Test static methods of RoleCache."""

    @staticmethod
    def setup_method():
        """Set up test fixtures before each test method."""
        # Clear all class variables to ensure clean state
        RoleCache.role_name_to_role_id_lookup.clear()
        RoleCache.role_name_set.clear()
        RoleCache.role_id_to_role_category_lookup.clear()
        RoleCache.role_id_to_role_name_lookup.clear()
        RoleCache.role_jstree = RuntimeRoleJSTree()
        RoleCache.role_category_to_role_name_lookup.clear()

    def test_get_all_roles_is_static(self):
        """Test that get_all_roles is callable as static method."""
        # Act
        result = RoleCache.get_all_roles()

        # Assert
        assert isinstance(result, dict)
        assert "roles" in result

    def test_get_roles_json_is_static(self):
        """Test that get_roles_json is callable as static method."""
        # Act
        result = RoleCache.get_roles_json()

        # Assert
        assert isinstance(result, str)

    def test_multiple_calls_same_result(self):
        """Test that multiple calls return same result."""
        # Arrange
        RoleCache.role_id_to_role_name_lookup[1] = "Test Role"
        RoleCache.role_id_to_role_category_lookup[1] = RoleType.Category.VOCAL

        # Act
        result1 = RoleCache.get_all_roles()
        result2 = RoleCache.get_all_roles()

        # Assert
        assert result1 == result2 