"""
Unit tests for the RuntimeStyle offline_domain class.

This module contains comprehensive tests for the RuntimeStyle class from the
musigree.runtime.runtime_domain.runtime_style module.
"""

import pytest
from pydantic import ValidationError

from musigree.runtime.runtime_domain.runtime_style import RuntimeStyle


class TestRuntimeStyle:
    """Test cases for the RuntimeStyle class."""

    def test_create_style_with_valid_data(self) -> None:
        """Test creating a RuntimeStyle instance with valid data."""
        style = RuntimeStyle(id=1, style_name="Jazz")

        assert style.id == 1
        assert style.style_name == "Jazz"

    def test_create_style_with_different_id_types(self) -> None:
        """Test creating RuntimeStyle with different valid ID types."""
        # Test with positive integer
        style1 = RuntimeStyle(id=42, style_name="Blues")
        assert style1.id == 42

        # Test with zero
        style2 = RuntimeStyle(id=0, style_name="Classical")
        assert style2.id == 0

    def test_create_style_with_various_name_formats(self) -> None:
        """Test creating RuntimeStyle with various name formats."""
        # Test with simple name
        style1 = RuntimeStyle(id=1, style_name="Rock")
        assert style1.style_name == "Rock"

        # Test with name containing spaces
        style2 = RuntimeStyle(id=2, style_name="Progressive Rock")
        assert style2.style_name == "Progressive Rock"

        # Test with name containing special characters
        style3 = RuntimeStyle(id=3, style_name="Nu-Metal")
        assert style3.style_name == "Nu-Metal"

        # Test with name containing numbers
        style4 = RuntimeStyle(id=4, style_name="90s Hip-Hop")
        assert style4.style_name == "90s Hip-Hop"

    def test_create_style_with_empty_name(self) -> None:
        """Test creating RuntimeStyle with empty string name."""
        style = RuntimeStyle(id=1, style_name="")
        assert style.style_name == ""

    def test_create_style_with_unicode_name(self) -> None:
        """Test creating RuntimeStyle with unicode characters in name."""
        style = RuntimeStyle(id=1, style_name="クラシック")
        assert style.style_name == "クラシック"

    def test_style_validation_error_missing_id(self) -> None:
        """Test that RuntimeStyle raises ValidationError when id is missing."""
        with pytest.raises(ValidationError) as exc_info:
            RuntimeStyle(style_name="Test Style")  # type: ignore

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["type"] == "missing"
        assert errors[0]["loc"] == ("id",)

    def test_style_validation_error_missing_name(self) -> None:
        """Test that RuntimeStyle raises ValidationError when style_name is missing."""
        with pytest.raises(ValidationError) as exc_info:
            RuntimeStyle(id=1)  # type: ignore

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["type"] == "missing"
        assert errors[0]["loc"] == ("style_name",)

    def test_style_validation_error_invalid_id_type(self) -> None:
        """Test that RuntimeStyle raises ValidationError for invalid id types."""
        with pytest.raises(ValidationError) as exc_info:
            RuntimeStyle(id="invalid", style_name="Test Style")  # type: ignore

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["type"] == "int_type"
        assert errors[0]["loc"] == ("id",)

    def test_style_validation_error_invalid_name_type(self) -> None:
        """Test that RuntimeStyle raises ValidationError for invalid style_name types."""
        with pytest.raises(ValidationError) as exc_info:
            RuntimeStyle(id=1, style_name=123)  # type: ignore

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["type"] == "string_type"
        assert errors[0]["loc"] == ("style_name",)

    def test_style_string_coercion_for_id(self) -> None:
        """Test that StrictInt id rejects string values (no coercion)."""
        with pytest.raises(ValidationError) as exc_info:
            RuntimeStyle(id="42", style_name="Test Style")  # type: ignore

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["type"] == "int_type"
        assert errors[0]["loc"] == ("id",)

    def test_style_equality(self) -> None:
        """Test equality comparison between RuntimeStyle instances."""
        style1 = RuntimeStyle(id=1, style_name="Ambient")
        style2 = RuntimeStyle(id=1, style_name="Ambient")
        style3 = RuntimeStyle(id=2, style_name="Ambient")
        style4 = RuntimeStyle(id=1, style_name="Drone")

        assert style1 == style2
        assert style1 != style3
        assert style1 != style4

    def test_style_model_dump(self) -> None:
        """Test the model_dump functionality."""
        style = RuntimeStyle(id=1, style_name="Techno")
        dumped = style.model_dump()

        assert dumped == {"id": 1, "style_name": "Techno"}

    def test_style_model_dump_json(self) -> None:
        """Test the model_dump_json functionality."""
        style = RuntimeStyle(id=1, style_name="House")
        json_str = style.model_dump_json()

        assert '"id":1' in json_str
        assert '"style_name":"House"' in json_str

    def test_style_from_attributes(self) -> None:
        """Test creating RuntimeStyle from object attributes."""

        class MockObject:
            id = 99
            style_name = "Test RuntimeStyle"

        mock_obj = MockObject()
        style = RuntimeStyle.model_validate(mock_obj)

        assert style.id == 99
        assert style.style_name == "Test RuntimeStyle"

    def test_style_repr(self) -> None:
        """Test the string representation of RuntimeStyle."""
        style = RuntimeStyle(id=1, style_name="Punk")
        repr_str = repr(style)

        # The repr should contain the normalized dict representation
        assert "1" in repr_str
        assert "Punk" in repr_str

    def test_style_extra_fields_ignored(self) -> None:
        """Test that extra fields are ignored during validation."""
        # This should not raise an error due to extra="ignore" in model config
        style = RuntimeStyle(id=1, style_name="Funk", extra_field="ignored")  # type: ignore

        assert style.id == 1
        assert style.style_name == "Funk"
        assert not hasattr(style, "extra_field")

    def test_style_assignment_validation(self) -> None:
        """Test that assignment validation works correctly."""
        style = RuntimeStyle(id=1, style_name="Reggae")

        # Valid assignment
        style.id = 2
        assert style.id == 2

        # Valid assignment
        style.style_name = "New Style"
        assert style.style_name == "New Style"

        # Invalid assignment should raise ValidationError
        with pytest.raises(ValidationError):
            style.id = "invalid"  # type: ignore

        with pytest.raises(ValidationError):
            style.style_name = 123  # type: ignore

    def test_style_negative_id(self) -> None:
        """Test RuntimeStyle with negative ID."""
        style = RuntimeStyle(id=-1, style_name="Test Style")
        assert style.id == -1

    def test_style_long_name(self) -> None:
        """Test RuntimeStyle with very long name."""
        long_name = "A" * 1000
        style = RuntimeStyle(id=1, style_name=long_name)
        assert style.style_name == long_name
        assert len(style.style_name) == 1000

    def test_style_with_special_characters(self) -> None:
        """Test RuntimeStyle names with various special characters."""
        special_names = [
            "Drum & Bass",
            "Post-Rock",
            "IDM (Intelligent Dance Music)",
            "Café del Mar",
            "Música Popular Brasileira",
            "Psytrance/Goa",
            "Neo-Soul",
            "Alt-Country",
        ]

        for i, name in enumerate(special_names):
            style = RuntimeStyle(id=i + 1, style_name=name)
            assert style.style_name == name

    def test_style_case_sensitivity(self) -> None:
        """Test that RuntimeStyle names are case sensitive."""
        style1 = RuntimeStyle(id=1, style_name="jazz")
        style2 = RuntimeStyle(id=2, style_name="Jazz")
        style3 = RuntimeStyle(id=3, style_name="JAZZ")

        assert style1.style_name != style2.style_name
        assert style2.style_name != style3.style_name
        assert style1.style_name != style3.style_name
