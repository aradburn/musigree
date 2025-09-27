"""
Unit tests for the offline.domain.role module.

This module contains comprehensive unit tests for the role domain objects,
including RoleUncommitted and Role classes.
"""
import pytest
from pydantic import ValidationError

from musigree.library.fields.role_type import RoleType
# noinspection PyProtectedMember
from musigree.offline.domain.role import (
    _RoleBase,
    RoleUncommitted,
    Role,
)


class TestRoleBase:
    """Test class for _RoleBase."""

    def test_role_base_can_be_instantiated(self) -> None:
        """Test that _RoleBase can be instantiated (not abstract)."""
        role_base = _RoleBase(
            role_name="Producer",
            role_category=RoleType.Category.PRODUCTION,
            role_subcategory=RoleType.Subcategory.NONE,
            role_category_name="Production",
            role_subcategory_name="None"
        )
        
        assert role_base.role_name == "Producer"
        assert role_base.role_category == RoleType.Category.PRODUCTION
        assert role_base.role_subcategory == RoleType.Subcategory.NONE
        assert role_base.role_category_name == "Production"
        assert role_base.role_subcategory_name == "None"

    def test_role_base_validation_missing_fields(self) -> None:
        """Test validation error when required fields are missing."""
        with pytest.raises(ValidationError):
            _RoleBase()  # type: ignore

    def test_role_base_validation_wrong_types(self) -> None:
        """Test validation error for wrong field types."""
        with pytest.raises(ValidationError):
            _RoleBase(
                role_name=123,  # type: ignore
                role_category=RoleType.Category.PRODUCTION,
                role_subcategory=RoleType.Subcategory.NONE,
                role_category_name="Production",
                role_subcategory_name="None"
            )

    def test_role_base_string_fields(self) -> None:
        """Test that string fields work correctly."""
        role_base = _RoleBase(
            role_name="",  # Empty string should be valid
            role_category=RoleType.Category.PRODUCTION,
            role_subcategory=RoleType.Subcategory.NONE,
            role_category_name="",
            role_subcategory_name=""
        )
        
        assert role_base.role_name == ""
        assert role_base.role_category_name == ""
        assert role_base.role_subcategory_name == ""


class TestRoleUncommitted:
    """Test class for RoleUncommitted."""

    def test_role_uncommitted_creation(self) -> None:
        """Test successful creation of RoleUncommitted."""
        role = RoleUncommitted(
            role_name="Engineer",
            role_category=RoleType.Category.PRODUCTION,
            role_subcategory=RoleType.Subcategory.NONE,
            role_category_name="Production",
            role_subcategory_name="Production"
        )
        
        assert role.role_name == "Engineer"
        assert role.role_category == RoleType.Category.PRODUCTION
        assert role.role_subcategory == RoleType.Subcategory.NONE
        assert role.role_category_name == "Production"
        assert role.role_subcategory_name == "Production"

    def test_role_uncommitted_inherits_from_base(self) -> None:
        """Test that RoleUncommitted inherits from _RoleBase."""
        assert issubclass(RoleUncommitted, _RoleBase)

    def test_role_uncommitted_no_id_field(self) -> None:
        """Test that RoleUncommitted doesn't have id field."""
        role = RoleUncommitted(
            role_name="Mixer",
            role_category=RoleType.Category.PRODUCTION,
            role_subcategory=RoleType.Subcategory.TECHNICAL_MUSICAL,
            role_category_name="Production",
            role_subcategory_name="Technical Musical"
        )
        
        # Should have base fields
        assert hasattr(role, "role_name")
        assert hasattr(role, "role_category")
        
        # Should not have database-specific fields
        assert not hasattr(role, "id")

    def test_role_uncommitted_validation(self) -> None:
        """Test validation behavior of RoleUncommitted."""
        with pytest.raises(ValidationError):
            RoleUncommitted(
                role_name="Test",
                # Missing required fields
            )  # type: ignore

    def test_role_uncommitted_json_serialization(self) -> None:
        """Test JSON serialization of RoleUncommitted."""
        role = RoleUncommitted(
            role_name="Vocalist",
            role_category=RoleType.Category.VOCAL,
            role_subcategory=RoleType.Subcategory.NONE,
            role_category_name="Vocal",
            role_subcategory_name="None"
        )
        
        dumped = role.model_dump()
        
        assert dumped["role_name"] == "Vocalist"
        assert dumped["role_category"] == RoleType.Category.VOCAL
        assert dumped["role_subcategory"] == RoleType.Subcategory.NONE
        assert dumped["role_category_name"] == "Vocal"
        assert dumped["role_subcategory_name"] == "None"

    def test_role_uncommitted_from_dict(self) -> None:
        """Test creating RoleUncommitted from dictionary."""
        data = {
            "role_name": "Guitarist",
            "role_category": RoleType.Category.VOCAL,
            "role_subcategory": RoleType.Subcategory.STRINGED_INSTRUMENTS,
            "role_category_name": "Vocal",
            "role_subcategory_name": "String Instruments"
        }
        
        role = RoleUncommitted.model_validate(data)
        
        assert role.role_name == "Guitarist"
        assert role.role_category == RoleType.Category.VOCAL
        assert role.role_subcategory == RoleType.Subcategory.STRINGED_INSTRUMENTS
        assert role.role_category_name == "Vocal"
        assert role.role_subcategory_name == "String Instruments"


class TestRole:
    """Test class for Role."""

    def test_role_creation(self) -> None:
        """Test successful creation of Role."""
        role = Role(
            role_name="Director",
            role_category=RoleType.Category.PRODUCTION,
            role_subcategory=RoleType.Subcategory.NONE,
            role_category_name="Production",
            role_subcategory_name="Production",
            id=1
        )
        
        assert role.role_name == "Director"
        assert role.role_category == RoleType.Category.PRODUCTION
        assert role.role_subcategory == RoleType.Subcategory.NONE
        assert role.role_category_name == "Production"
        assert role.role_subcategory_name == "Production"
        assert role.id == 1

    def test_role_inherits_from_base(self) -> None:
        """Test that Role inherits from _RoleBase."""
        assert issubclass(Role, _RoleBase)

    def test_role_validation_missing_id(self) -> None:
        """Test validation error when id is missing."""
        with pytest.raises(ValidationError):
            Role(
                role_name="Test",
                role_category=RoleType.Category.PRODUCTION,
                role_subcategory=RoleType.Subcategory.NONE,
                role_category_name="Production",
                role_subcategory_name="None"
                # id is missing
            )  # type: ignore

    def test_role_validation_wrong_id_type(self) -> None:
        """Test validation error for wrong id type."""
        with pytest.raises(ValidationError):
            Role(
                role_name="Test",
                role_category=RoleType.Category.PRODUCTION,
                role_subcategory=RoleType.Subcategory.NONE,
                role_category_name="Production",
                role_subcategory_name="Production",
                id="not_an_int"  # type: ignore
            )

    def test_role_json_serialization(self) -> None:
        """Test JSON serialization of Role."""
        role = Role(
            role_name="Bassist",
            role_category=RoleType.Category.VOCAL,
            role_subcategory=RoleType.Subcategory.STRINGED_INSTRUMENTS,
            role_category_name="Vocal",
            role_subcategory_name="String Instruments",
            id=42
        )
        
        dumped = role.model_dump()
        
        assert dumped["role_name"] == "Bassist"
        assert dumped["role_category"] == RoleType.Category.VOCAL
        assert dumped["role_subcategory"] == RoleType.Subcategory.STRINGED_INSTRUMENTS
        assert dumped["role_category_name"] == "Vocal"
        assert dumped["role_subcategory_name"] == "String Instruments"
        assert dumped["id"] == 42

    def test_role_from_dict(self) -> None:
        """Test creating Role from dictionary."""
        data = {
            "role_name": "Drummer",
            "role_category": RoleType.Category.VOCAL,
            "role_subcategory": RoleType.Subcategory.STRINGED_INSTRUMENTS,
            "role_category_name": "Vocal",
            "role_subcategory_name": "String Instruments",
            "id": 100
        }
        
        role = Role.model_validate(data)
        
        assert role.role_name == "Drummer"
        assert role.role_category == RoleType.Category.VOCAL
        assert role.role_subcategory == RoleType.Subcategory.STRINGED_INSTRUMENTS
        assert role.role_category_name == "Vocal"
        assert role.role_subcategory_name == "String Instruments"
        assert role.id == 100


class TestRoleComparison:
    """Test class for comparing Role and RoleUncommitted."""

    def test_role_vs_uncommitted_structure(self) -> None:
        """Test structural differences between Role and RoleUncommitted."""
        uncommitted = RoleUncommitted(
            role_name="Test Role",
            role_category=RoleType.Category.PRODUCTION,
            role_subcategory=RoleType.Subcategory.NONE,
            role_category_name="Production",
            role_subcategory_name="Production"
        )
        
        committed = Role(
            role_name="Test Role",
            role_category=RoleType.Category.PRODUCTION,
            role_subcategory=RoleType.Subcategory.NONE,
            role_category_name="Production",
            role_subcategory_name="Production",
            id=1
        )
        
        # Both should have base fields
        assert uncommitted.role_name == committed.role_name
        assert uncommitted.role_category == committed.role_category
        assert uncommitted.role_subcategory == committed.role_subcategory
        assert uncommitted.role_category_name == committed.role_category_name
        assert uncommitted.role_subcategory_name == committed.role_subcategory_name
        
        # Only committed should have ID field
        assert hasattr(committed, "id")
        assert not hasattr(uncommitted, "id")

    def test_conversion_workflow(self) -> None:
        """Test typical workflow from uncommitted to committed role."""
        # Start with uncommitted role
        uncommitted = RoleUncommitted(
            role_name="Audio Engineer",
            role_category=RoleType.Category.PRODUCTION,
            role_subcategory=RoleType.Subcategory.NONE,
            role_category_name="Production",
            role_subcategory_name="Production"
        )
        
        # Simulate saving to database (would add ID)
        committed = Role(
            role_name=uncommitted.role_name,
            role_category=uncommitted.role_category,
            role_subcategory=uncommitted.role_subcategory,
            role_category_name=uncommitted.role_category_name,
            role_subcategory_name=uncommitted.role_subcategory_name,
            id=123
        )
        
        assert committed.role_name == "Audio Engineer"
        assert committed.role_category == RoleType.Category.PRODUCTION
        assert committed.role_subcategory == RoleType.Subcategory.NONE
        assert committed.role_category_name == "Production"
        assert committed.role_subcategory_name == "Production"
        assert committed.id == 123

    def test_different_role_categories(self) -> None:
        """Test roles with different categories and subcategories."""
        production_role = Role(
            role_name="Producer",
            role_category=RoleType.Category.PRODUCTION,
            role_subcategory=RoleType.Subcategory.NONE,
            role_category_name="Production",
            role_subcategory_name="None",
            id=1
        )
        
        performance_role = Role(
            role_name="Singer",
            role_category=RoleType.Category.VOCAL,
            role_subcategory=RoleType.Subcategory.DRUMS_AND_PERCUSSION,
            role_category_name="Vocal",
            role_subcategory_name="Drums & Percussion",
            id=2
        )
        
        assert production_role.role_category != performance_role.role_category
        assert production_role.role_subcategory != performance_role.role_subcategory
        assert production_role.role_category_name != performance_role.role_category_name
        assert production_role.role_subcategory_name != performance_role.role_subcategory_name

    def test_role_type_enum_usage(self) -> None:
        """Test correct usage of RoleType enums."""
        role = Role(
            role_name="Test Role",
            role_category=RoleType.Category.PRODUCTION,
            role_subcategory=RoleType.Subcategory.TECHNICAL_MUSICAL,
            role_category_name="Production",
            role_subcategory_name="Technical Musical",
            id=1
        )
        
        # Verify enum types
        assert isinstance(role.role_category, RoleType.Category)
        assert isinstance(role.role_subcategory, RoleType.Subcategory)
        
        # Verify enum values
        assert role.role_category.name == "PRODUCTION"
        assert role.role_subcategory.name == "TECHNICAL_MUSICAL"
