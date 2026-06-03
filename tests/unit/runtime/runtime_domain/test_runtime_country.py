"""
Unit tests for the RuntimeCountry offline_domain class.

This module contains comprehensive tests for the RuntimeCountry class from the
musigree.runtime.runtime_domain.country module.
"""

import pytest
from pydantic import ValidationError

from musigree.runtime.runtime_domain.runtime_country import RuntimeCountry


class TestRuntimeCountry:
    """Test cases for the RuntimeCountry class."""

    def test_create_country_with_valid_data(self) -> None:
        """Test creating a RuntimeCountry instance with valid data."""
        country = RuntimeCountry(id=1, country_name="United States")

        assert country.id == 1
        assert country.country_name == "United States"

    def test_create_country_with_different_id_types(self) -> None:
        """Test creating RuntimeCountry with different valid ID types."""
        # Test with positive integer
        country1 = RuntimeCountry(id=42, country_name="Canada")
        assert country1.id == 42

        # Test with zero
        country2 = RuntimeCountry(id=0, country_name="Mexico")
        assert country2.id == 0

    def test_create_country_with_various_name_formats(self) -> None:
        """Test creating RuntimeCountry with various name formats."""
        # Test with simple name
        country1 = RuntimeCountry(id=1, country_name="Japan")
        assert country1.country_name == "Japan"

        # Test with name containing spaces
        country2 = RuntimeCountry(id=2, country_name="United Kingdom")
        assert country2.country_name == "United Kingdom"

        # Test with name containing special characters
        country3 = RuntimeCountry(id=3, country_name="Côte d'Ivoire")
        assert country3.country_name == "Côte d'Ivoire"

        # Test with name containing numbers
        country4 = RuntimeCountry(id=4, country_name="RuntimeCountry 51")
        assert country4.country_name == "RuntimeCountry 51"

    def test_create_country_with_empty_name(self) -> None:
        """Test creating RuntimeCountry with empty string name."""
        country = RuntimeCountry(id=1, country_name="")
        assert country.country_name == ""

    def test_create_country_with_unicode_name(self) -> None:
        """Test creating RuntimeCountry with unicode characters in name."""
        country = RuntimeCountry(id=1, country_name="中国")
        assert country.country_name == "中国"

    def test_country_validation_error_missing_id(self) -> None:
        """Test that RuntimeCountry raises ValidationError when id is missing."""
        with pytest.raises(ValidationError) as exc_info:
            RuntimeCountry(country_name="Test RuntimeCountry")  # type: ignore

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["type"] == "missing"
        assert errors[0]["loc"] == ("id",)

    def test_country_validation_error_missing_name(self) -> None:
        """Test that RuntimeCountry raises ValidationError when country_name is missing."""
        with pytest.raises(ValidationError) as exc_info:
            RuntimeCountry(id=1)  # type: ignore

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["type"] == "missing"
        assert errors[0]["loc"] == ("country_name",)

    def test_country_validation_error_invalid_id_type(self) -> None:
        """Test that RuntimeCountry raises ValidationError for invalid id types."""
        with pytest.raises(ValidationError) as exc_info:
            RuntimeCountry(id="invalid", country_name="Test RuntimeCountry")  # type: ignore

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["type"] == "int_type"
        assert errors[0]["loc"] == ("id",)

    def test_country_validation_error_invalid_name_type(self) -> None:
        """Test that RuntimeCountry raises ValidationError for invalid country_name types."""
        with pytest.raises(ValidationError) as exc_info:
            RuntimeCountry(id=1, country_name=123)  # type: ignore

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["type"] == "string_type"
        assert errors[0]["loc"] == ("country_name",)

    def test_country_string_coercion_for_id(self) -> None:
        """Test that StrictInt id rejects string values (no coercion)."""
        with pytest.raises(ValidationError) as exc_info:
            RuntimeCountry(id="42", country_name="Test RuntimeCountry")  # type: ignore

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["type"] == "int_type"
        assert errors[0]["loc"] == ("id",)

    def test_country_equality(self) -> None:
        """Test equality comparison between RuntimeCountry instances."""
        country1 = RuntimeCountry(id=1, country_name="France")
        country2 = RuntimeCountry(id=1, country_name="France")
        country3 = RuntimeCountry(id=2, country_name="France")
        country4 = RuntimeCountry(id=1, country_name="Germany")

        assert country1 == country2
        assert country1 != country3
        assert country1 != country4

    def test_country_model_dump(self) -> None:
        """Test the model_dump functionality."""
        country = RuntimeCountry(id=1, country_name="Brazil")
        dumped = country.model_dump()

        assert dumped == {"id": 1, "country_name": "Brazil"}

    def test_country_model_dump_json(self) -> None:
        """Test the model_dump_json functionality."""
        country = RuntimeCountry(id=1, country_name="Australia")
        json_str = country.model_dump_json()

        assert '"id":1' in json_str
        assert '"country_name":"Australia"' in json_str

    def test_country_from_attributes(self) -> None:
        """Test creating RuntimeCountry from object attributes."""

        class MockObject:
            id = 99
            country_name = "Test Country"

        mock_obj = MockObject()
        country = RuntimeCountry.model_validate(mock_obj)

        assert country.id == 99
        assert country.country_name == "Test Country"

    def test_country_repr(self) -> None:
        """Test the string representation of RuntimeCountry."""
        country = RuntimeCountry(id=1, country_name="India")
        repr_str = repr(country)

        # The repr should contain the normalized dict representation
        assert "1" in repr_str
        assert "India" in repr_str

    def test_country_extra_fields_ignored(self) -> None:
        """Test that extra fields are ignored during validation."""
        # This should not raise an error due to extra="ignore" in model config
        country = RuntimeCountry(id=1, country_name="China", extra_field="ignored")  # type: ignore

        assert country.id == 1
        assert country.country_name == "China"
        assert not hasattr(country, "extra_field")

    def test_country_assignment_validation(self) -> None:
        """Test that assignment validation works correctly."""
        country = RuntimeCountry(id=1, country_name="Russia")

        # Valid assignment
        country.id = 2
        assert country.id == 2

        # Valid assignment
        country.country_name = "New Name"
        assert country.country_name == "New Name"

        # Invalid assignment should raise ValidationError
        with pytest.raises(ValidationError):
            country.id = "invalid"  # type: ignore

        with pytest.raises(ValidationError):
            country.country_name = 123  # type: ignore

    def test_country_negative_id(self) -> None:
        """Test RuntimeCountry with negative ID."""
        country = RuntimeCountry(id=-1, country_name="Test RuntimeCountry")
        assert country.id == -1
