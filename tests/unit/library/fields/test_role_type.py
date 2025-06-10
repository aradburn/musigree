"""
Unit tests for musigree.library.fields.role_type module.
"""
import pytest
from enum import Enum
import re

from musigree.library.fields.role_type import RoleType


class TestRoleType:
    """Test cases for RoleType class."""

    def test_role_type_is_class(self):
        """Test that RoleType is a regular class."""
        # Assert
        assert isinstance(RoleType, type)
        assert not issubclass(RoleType, Enum)

    def test_role_type_has_nested_enums(self):
        """Test that RoleType has Category and Subcategory nested enums."""
        # Assert
        assert hasattr(RoleType, 'Category')
        assert hasattr(RoleType, 'Subcategory')
        assert issubclass(RoleType.Category, Enum)
        assert issubclass(RoleType.Subcategory, Enum)

    def test_role_type_has_category_names(self):
        """Test that RoleType has category_names mapping."""
        # Assert
        assert hasattr(RoleType, 'category_names')
        assert isinstance(RoleType.category_names, dict)
        assert len(RoleType.category_names) > 0

    def test_role_type_has_subcategory_names(self):
        """Test that RoleType has subcategory_names mapping."""
        # Assert
        assert hasattr(RoleType, 'subcategory_names')
        assert isinstance(RoleType.subcategory_names, dict)
        assert len(RoleType.subcategory_names) > 0

    def test_role_type_has_aggregate_roles(self):
        """Test that RoleType has aggregate_roles tuple."""
        # Assert
        assert hasattr(RoleType, 'aggregate_roles')
        assert isinstance(RoleType.aggregate_roles, tuple)
        assert len(RoleType.aggregate_roles) > 0

    def test_role_type_has_bracket_pattern(self):
        """Test that RoleType has _bracket_pattern regex."""
        # Assert
        assert hasattr(RoleType, '_bracket_pattern')
        assert isinstance(RoleType._bracket_pattern, re.Pattern)

    def test_bracket_pattern_functionality(self):
        """Test that _bracket_pattern works correctly."""
        # Arrange
        test_string = "Role [additional info] with more [details]"
        
        # Act
        matches = RoleType._bracket_pattern.findall(test_string)
        
        # Assert
        assert matches == ["additional info", "details"]

    def test_hornbostel_sachs_to_subcategory_method_exists(self):
        """Test that hornbostel_sachs_to_subcategory method exists."""
        # Assert
        assert hasattr(RoleType, 'hornbostel_sachs_to_subcategory')
        assert callable(RoleType.hornbostel_sachs_to_subcategory)


class TestRoleTypeCategory:
    """Test cases for RoleType.Category nested enum."""

    def test_category_inheritance(self):
        """Test that Category inherits from Enum."""
        # Assert
        assert issubclass(RoleType.Category, Enum)

    def test_category_values(self):
        """Test Category enum values are correct."""
        # Act & Assert
        assert RoleType.Category.ACTING_LITERARY_AND_SPOKEN.value == 1
        assert RoleType.Category.COMPANIES.value == 2
        assert RoleType.Category.CONDUCTING_AND_LEADING.value == 3
        assert RoleType.Category.DJ_MIX.value == 4
        assert RoleType.Category.FEATURING_AND_PRESENTING.value == 5
        assert RoleType.Category.INSTRUMENTS.value == 6
        assert RoleType.Category.MANAGEMENT.value == 7
        assert RoleType.Category.PRODUCTION.value == 8
        assert RoleType.Category.RELATION.value == 9
        assert RoleType.Category.REMIX.value == 10
        assert RoleType.Category.TECHNICAL.value == 11
        assert RoleType.Category.VISUAL.value == 12
        assert RoleType.Category.VOCAL.value == 13
        assert RoleType.Category.WRITING_AND_ARRANGEMENT.value == 14

    def test_category_names(self):
        """Test Category enum names are correct."""
        # Act & Assert
        assert RoleType.Category.ACTING_LITERARY_AND_SPOKEN.name == "ACTING_LITERARY_AND_SPOKEN"
        assert RoleType.Category.COMPANIES.name == "COMPANIES"
        assert RoleType.Category.CONDUCTING_AND_LEADING.name == "CONDUCTING_AND_LEADING"
        assert RoleType.Category.DJ_MIX.name == "DJ_MIX"
        assert RoleType.Category.FEATURING_AND_PRESENTING.name == "FEATURING_AND_PRESENTING"
        assert RoleType.Category.INSTRUMENTS.name == "INSTRUMENTS"
        assert RoleType.Category.MANAGEMENT.name == "MANAGEMENT"
        assert RoleType.Category.PRODUCTION.name == "PRODUCTION"
        assert RoleType.Category.RELATION.name == "RELATION"
        assert RoleType.Category.REMIX.name == "REMIX"
        assert RoleType.Category.TECHNICAL.name == "TECHNICAL"
        assert RoleType.Category.VISUAL.name == "VISUAL"
        assert RoleType.Category.VOCAL.name == "VOCAL"
        assert RoleType.Category.WRITING_AND_ARRANGEMENT.name == "WRITING_AND_ARRANGEMENT"

    def test_category_count(self):
        """Test that all expected Category values exist."""
        # Act
        categories = list(RoleType.Category)

        # Assert
        assert len(categories) == 14

    def test_category_creation_from_value(self):
        """Test creating Category from integer values."""
        # Act & Assert
        assert RoleType.Category(1) == RoleType.Category.ACTING_LITERARY_AND_SPOKEN
        assert RoleType.Category(8) == RoleType.Category.PRODUCTION
        assert RoleType.Category(13) == RoleType.Category.VOCAL
        assert RoleType.Category(14) == RoleType.Category.WRITING_AND_ARRANGEMENT

    def test_category_invalid_value(self):
        """Test creating Category with invalid values raises error."""
        # Act & Assert
        with pytest.raises(ValueError):
            RoleType.Category(0)
        with pytest.raises(ValueError):
            RoleType.Category(15)
        with pytest.raises(ValueError):
            RoleType.Category(-1)

    def test_category_iteration(self):
        """Test iterating over Category values."""
        # Arrange
        expected_count = 14

        # Act
        categories = list(RoleType.Category)

        # Assert
        assert len(categories) == expected_count
        # Check that all values are unique
        values = [category.value for category in categories]
        assert len(set(values)) == expected_count

    def test_category_membership(self):
        """Test membership testing with Category."""
        # Act & Assert
        assert RoleType.Category.PRODUCTION in RoleType.Category
        assert RoleType.Category.TECHNICAL in RoleType.Category
        assert RoleType.Category.INSTRUMENTS in RoleType.Category
        assert RoleType.Category.VOCAL in RoleType.Category

    def test_category_hash(self):
        """Test Category instances are hashable."""
        # Act
        category_set = {
            RoleType.Category.PRODUCTION,
            RoleType.Category.TECHNICAL,
            RoleType.Category.INSTRUMENTS,
            RoleType.Category.VOCAL
        }

        # Assert
        assert len(category_set) == 4
        assert RoleType.Category.PRODUCTION in category_set
        assert RoleType.Category.VOCAL in category_set


class TestRoleTypeSubcategory:
    """Test cases for RoleType.Subcategory nested enum."""

    def test_subcategory_inheritance(self):
        """Test that Subcategory inherits from Enum."""
        # Assert
        assert issubclass(RoleType.Subcategory, Enum)

    def test_subcategory_values(self):
        """Test Subcategory enum values are correct."""
        # Act & Assert
        assert RoleType.Subcategory.NONE.value == 0
        assert RoleType.Subcategory.DRUMS_AND_PERCUSSION.value == 1
        assert RoleType.Subcategory.KEYBOARDS.value == 2
        assert RoleType.Subcategory.OTHER_MUSICAL.value == 3
        assert RoleType.Subcategory.STRINGED_INSTRUMENTS.value == 4
        assert RoleType.Subcategory.TECHNICAL_MUSICAL.value == 5
        assert RoleType.Subcategory.TUNED_PERCUSSION.value == 6
        assert RoleType.Subcategory.WIND_INSTRUMENTS.value == 7

    def test_subcategory_names(self):
        """Test Subcategory enum names are correct."""
        # Act & Assert
        assert RoleType.Subcategory.NONE.name == "NONE"
        assert RoleType.Subcategory.DRUMS_AND_PERCUSSION.name == "DRUMS_AND_PERCUSSION"
        assert RoleType.Subcategory.KEYBOARDS.name == "KEYBOARDS"
        assert RoleType.Subcategory.OTHER_MUSICAL.name == "OTHER_MUSICAL"
        assert RoleType.Subcategory.STRINGED_INSTRUMENTS.name == "STRINGED_INSTRUMENTS"
        assert RoleType.Subcategory.TECHNICAL_MUSICAL.name == "TECHNICAL_MUSICAL"
        assert RoleType.Subcategory.TUNED_PERCUSSION.name == "TUNED_PERCUSSION"
        assert RoleType.Subcategory.WIND_INSTRUMENTS.name == "WIND_INSTRUMENTS"

    def test_subcategory_count(self):
        """Test that all expected Subcategory values exist."""
        # Act
        subcategories = list(RoleType.Subcategory)

        # Assert
        assert len(subcategories) == 8

    def test_subcategory_creation_from_value(self):
        """Test creating Subcategory from integer values."""
        # Act & Assert
        assert RoleType.Subcategory(0) == RoleType.Subcategory.NONE
        assert RoleType.Subcategory(1) == RoleType.Subcategory.DRUMS_AND_PERCUSSION
        assert RoleType.Subcategory(7) == RoleType.Subcategory.WIND_INSTRUMENTS

    def test_subcategory_invalid_value(self):
        """Test creating Subcategory with invalid values raises error."""
        # Act & Assert
        with pytest.raises(ValueError):
            RoleType.Subcategory(8)
        with pytest.raises(ValueError):
            RoleType.Subcategory(-1)


class TestRoleTypeMappings:
    """Test cases for RoleType mappings."""

    def test_category_names_completeness(self):
        """Test that category_names has entries for all Category values."""
        # Act
        all_categories = set(RoleType.Category)
        mapped_categories = set(RoleType.category_names.keys())

        # Assert
        assert all_categories == mapped_categories

    def test_category_names_values(self):
        """Test specific category name mappings."""
        # Act & Assert
        assert RoleType.category_names[RoleType.Category.PRODUCTION] == "Production"
        assert RoleType.category_names[RoleType.Category.TECHNICAL] == "Technical"
        assert RoleType.category_names[RoleType.Category.INSTRUMENTS] == "Instruments"
        assert RoleType.category_names[RoleType.Category.VOCAL] == "Vocal"

    def test_subcategory_names_completeness(self):
        """Test that subcategory_names has entries for all Subcategory values."""
        # Act
        all_subcategories = set(RoleType.Subcategory)
        mapped_subcategories = set(RoleType.subcategory_names.keys())

        # Assert
        assert all_subcategories == mapped_subcategories

    def test_subcategory_names_values(self):
        """Test specific subcategory name mappings."""
        # Act & Assert
        assert RoleType.subcategory_names[RoleType.Subcategory.NONE] == "None"
        assert RoleType.subcategory_names[RoleType.Subcategory.DRUMS_AND_PERCUSSION] == "Drums & Percussion"
        assert RoleType.subcategory_names[RoleType.Subcategory.KEYBOARDS] == "Keyboards"
        assert RoleType.subcategory_names[RoleType.Subcategory.STRINGED_INSTRUMENTS] == "String Instruments"


class TestRoleTypeAggregateRoles:
    """Test cases for RoleType aggregate_roles."""

    def test_aggregate_roles_type(self):
        """Test that aggregate_roles is a tuple."""
        # Assert
        assert isinstance(RoleType.aggregate_roles, tuple)

    def test_aggregate_roles_content(self):
        """Test specific aggregate roles content."""
        # Act & Assert
        assert "Compiled By" in RoleType.aggregate_roles
        assert "Curated By" in RoleType.aggregate_roles
        assert "DJ Mix" in RoleType.aggregate_roles
        assert "Hosted By" in RoleType.aggregate_roles
        assert "Presenter" in RoleType.aggregate_roles

    def test_aggregate_roles_immutable(self):
        """Test that aggregate_roles is immutable."""
        # Arrange
        original_length = len(RoleType.aggregate_roles)

        # Act & Assert - tuples are immutable by nature
        assert isinstance(RoleType.aggregate_roles, tuple)
        
        # Length should remain the same
        assert len(RoleType.aggregate_roles) == original_length


class TestHornbostelSachsMapping:
    """Test cases for hornbostel_sachs_to_subcategory method."""

    def test_hornbostel_sachs_idiophones(self):
        """Test mapping idiophones to drums and percussion."""
        # Act
        result = RoleType.hornbostel_sachs_to_subcategory("idiophones")
        
        # Assert
        assert result == RoleType.Subcategory.DRUMS_AND_PERCUSSION

    def test_hornbostel_sachs_membranophones(self):
        """Test mapping membranophones to drums and percussion."""
        # Act
        result = RoleType.hornbostel_sachs_to_subcategory("membranophones")
        
        # Assert
        assert result == RoleType.Subcategory.DRUMS_AND_PERCUSSION

    def test_hornbostel_sachs_chordophones(self):
        """Test mapping chordophones to stringed instruments."""
        # Act
        result = RoleType.hornbostel_sachs_to_subcategory("chordophones")
        
        # Assert
        assert result == RoleType.Subcategory.STRINGED_INSTRUMENTS

    def test_hornbostel_sachs_aerophones(self):
        """Test mapping aerophones to wind instruments."""
        # Act
        result = RoleType.hornbostel_sachs_to_subcategory("aerophones")
        
        # Assert
        assert result == RoleType.Subcategory.WIND_INSTRUMENTS

    def test_hornbostel_sachs_electrophones(self):
        """Test mapping electrophones to technical musical."""
        # Act
        result = RoleType.hornbostel_sachs_to_subcategory("electrophones")
        
        # Assert
        assert result == RoleType.Subcategory.TECHNICAL_MUSICAL

    def test_hornbostel_sachs_case_insensitive(self):
        """Test that mapping is case insensitive."""
        # Act & Assert
        assert RoleType.hornbostel_sachs_to_subcategory("IDIOPHONES") == RoleType.Subcategory.DRUMS_AND_PERCUSSION
        assert RoleType.hornbostel_sachs_to_subcategory("ChordopHones") == RoleType.Subcategory.STRINGED_INSTRUMENTS
        assert RoleType.hornbostel_sachs_to_subcategory("AeRoPhOnEs") == RoleType.Subcategory.WIND_INSTRUMENTS

    def test_hornbostel_sachs_unknown_classification(self):
        """Test mapping unknown classification to other musical."""
        # Act
        result = RoleType.hornbostel_sachs_to_subcategory("unknown")
        
        # Assert
        assert result == RoleType.Subcategory.OTHER_MUSICAL

    def test_hornbostel_sachs_empty_string(self):
        """Test mapping empty string to other musical."""
        # Act
        result = RoleType.hornbostel_sachs_to_subcategory("")
        
        # Assert
        assert result == RoleType.Subcategory.OTHER_MUSICAL

    def test_hornbostel_sachs_static_method(self):
        """Test that hornbostel_sachs_to_subcategory is a static method."""
        # Act & Assert
        # Should be callable on the class without instantiation
        result = RoleType.hornbostel_sachs_to_subcategory("idiophones")
        assert result == RoleType.Subcategory.DRUMS_AND_PERCUSSION


class TestRoleTypeIntegration:
    """Integration tests for RoleType components."""

    def test_category_and_mapping_consistency(self):
        """Test that all categories have corresponding name mappings."""
        # Act
        for category in RoleType.Category:
            # Assert
            assert category in RoleType.category_names
            assert isinstance(RoleType.category_names[category], str)
            assert len(RoleType.category_names[category]) > 0

    def test_subcategory_and_mapping_consistency(self):
        """Test that all subcategories have corresponding name mappings."""
        # Act
        for subcategory in RoleType.Subcategory:
            # Assert
            assert subcategory in RoleType.subcategory_names
            assert isinstance(RoleType.subcategory_names[subcategory], str)
            assert len(RoleType.subcategory_names[subcategory]) > 0

    def test_enum_value_uniqueness(self):
        """Test that enum values are unique within each enum."""
        # Act
        category_values = [category.value for category in RoleType.Category]
        subcategory_values = [subcategory.value for subcategory in RoleType.Subcategory]

        # Assert
        assert len(category_values) == len(set(category_values))
        assert len(subcategory_values) == len(set(subcategory_values))

    def test_class_attributes_exist(self):
        """Test that all expected class attributes exist."""
        # Assert
        assert hasattr(RoleType, 'Category')
        assert hasattr(RoleType, 'Subcategory')
        assert hasattr(RoleType, 'category_names')
        assert hasattr(RoleType, 'subcategory_names')
        assert hasattr(RoleType, 'aggregate_roles')
        assert hasattr(RoleType, '_bracket_pattern')
        assert hasattr(RoleType, 'hornbostel_sachs_to_subcategory') 