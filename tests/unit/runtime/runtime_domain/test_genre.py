"""
Unit tests for the Genre domain class.

This module contains comprehensive tests for the Genre class from the
musigree.runtime.runtime_domain.genre module.
"""

import pytest
from pydantic import ValidationError

from musigree.runtime.runtime_domain.genre import Genre


class TestGenre:
    """Test cases for the Genre class."""

    def test_create_genre_with_valid_data(self) -> None:
        """Test creating a Genre instance with valid data."""
        genre = Genre(id=1, genre_name="Rock")

        assert genre.id == 1
        assert genre.genre_name == "Rock"

    def test_create_genre_with_different_id_types(self) -> None:
        """Test creating Genre with different valid ID types."""
        # Test with positive integer
        genre1 = Genre(id=42, genre_name="Pop")
        assert genre1.id == 42

        # Test with zero
        genre2 = Genre(id=0, genre_name="Classical")
        assert genre2.id == 0

    def test_create_genre_with_various_name_formats(self) -> None:
        """Test creating Genre with various name formats."""
        # Test with simple name
        genre1 = Genre(id=1, genre_name="Jazz")
        assert genre1.genre_name == "Jazz"

        # Test with name containing spaces
        genre2 = Genre(id=2, genre_name="Hip Hop")
        assert genre2.genre_name == "Hip Hop"

        # Test with name containing special characters
        genre3 = Genre(id=3, genre_name="R&B")
        assert genre3.genre_name == "R&B"

        # Test with name containing numbers
        genre4 = Genre(id=4, genre_name="Synthwave80")
        assert genre4.genre_name == "Synthwave80"

    def test_create_genre_with_empty_name(self) -> None:
        """Test creating Genre with empty string name."""
        genre = Genre(id=1, genre_name="")
        assert genre.genre_name == ""

    def test_create_genre_with_unicode_name(self) -> None:
        """Test creating Genre with unicode characters in name."""
        genre = Genre(id=1, genre_name="ロック")
        assert genre.genre_name == "ロック"

    def test_genre_validation_error_missing_id(self) -> None:
        """Test that Genre raises ValidationError when id is missing."""
        with pytest.raises(ValidationError) as exc_info:
            Genre(genre_name="Test Genre")  # type: ignore

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["type"] == "missing"
        assert errors[0]["loc"] == ("id",)

    def test_genre_validation_error_missing_name(self) -> None:
        """Test that Genre raises ValidationError when genre_name is missing."""
        with pytest.raises(ValidationError) as exc_info:
            Genre(id=1)  # type: ignore

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["type"] == "missing"
        assert errors[0]["loc"] == ("genre_name",)

    def test_genre_validation_error_invalid_id_type(self) -> None:
        """Test that Genre raises ValidationError for invalid id types."""
        with pytest.raises(ValidationError) as exc_info:
            Genre(id="invalid", genre_name="Test Genre")  # type: ignore

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["type"] == "int_parsing"
        assert errors[0]["loc"] == ("id",)

    def test_genre_validation_error_invalid_name_type(self) -> None:
        """Test that Genre raises ValidationError for invalid genre_name types."""
        with pytest.raises(ValidationError) as exc_info:
            Genre(id=1, genre_name=123)  # type: ignore

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["type"] == "string_type"
        assert errors[0]["loc"] == ("genre_name",)

    def test_genre_string_coercion_for_id(self) -> None:
        """Test that string numbers are coerced to integers for id."""
        genre = Genre(id="42", genre_name="Test Genre")  # type: ignore
        assert genre.id == 42
        assert isinstance(genre.id, int)

    def test_genre_equality(self) -> None:
        """Test equality comparison between Genre instances."""
        genre1 = Genre(id=1, genre_name="Electronic")
        genre2 = Genre(id=1, genre_name="Electronic")
        genre3 = Genre(id=2, genre_name="Electronic")
        genre4 = Genre(id=1, genre_name="Acoustic")

        assert genre1 == genre2
        assert genre1 != genre3
        assert genre1 != genre4

    def test_genre_model_dump(self) -> None:
        """Test the model_dump functionality."""
        genre = Genre(id=1, genre_name="Folk")
        dumped = genre.model_dump()

        assert dumped == {"id": 1, "genre_name": "Folk"}

    def test_genre_model_dump_json(self) -> None:
        """Test the model_dump_json functionality."""
        genre = Genre(id=1, genre_name="Country")
        json_str = genre.model_dump_json()

        assert '"id":1' in json_str
        assert '"genre_name":"Country"' in json_str

    def test_genre_from_attributes(self) -> None:
        """Test creating Genre from object attributes."""

        class MockObject:
            id = 99
            genre_name = "Test Genre"

        mock_obj = MockObject()
        genre = Genre.model_validate(mock_obj)

        assert genre.id == 99
        assert genre.genre_name == "Test Genre"

    def test_genre_repr(self) -> None:
        """Test the string representation of Genre."""
        genre = Genre(id=1, genre_name="Metal")
        repr_str = repr(genre)

        # The repr should contain the normalized dict representation
        assert "1" in repr_str
        assert "Metal" in repr_str

    def test_genre_extra_fields_ignored(self) -> None:
        """Test that extra fields are ignored during validation."""
        # This should not raise an error due to extra="ignore" in model config
        genre = Genre(id=1, genre_name="Blues", extra_field="ignored")  # type: ignore

        assert genre.id == 1
        assert genre.genre_name == "Blues"
        assert not hasattr(genre, "extra_field")

    def test_genre_assignment_validation(self) -> None:
        """Test that assignment validation works correctly."""
        genre = Genre(id=1, genre_name="Reggae")

        # Valid assignment
        genre.id = 2
        assert genre.id == 2

        # Valid assignment
        genre.genre_name = "New Genre"
        assert genre.genre_name == "New Genre"

        # Invalid assignment should raise ValidationError
        with pytest.raises(ValidationError):
            genre.id = "invalid"  # type: ignore

        with pytest.raises(ValidationError):
            genre.genre_name = 123  # type: ignore

    def test_genre_negative_id(self) -> None:
        """Test Genre with negative ID."""
        genre = Genre(id=-1, genre_name="Test Genre")
        assert genre.id == -1

    def test_genre_long_name(self) -> None:
        """Test Genre with very long name."""
        long_name = "B" * 1000
        genre = Genre(id=1, genre_name=long_name)
        assert genre.genre_name == long_name
        assert len(genre.genre_name) == 1000

    def test_genre_with_special_characters(self) -> None:
        """Test Genre names with various special characters."""
        special_names = [
            "Hip-Hop",
            "R&B/Soul",
            "New Wave (Post-Punk)",
            "Bossa Nova",
            "Música Clásica",
            "Heavy Metal/Death Metal",
            "Indie-Rock",
            "World Music",
        ]

        for i, name in enumerate(special_names):
            genre = Genre(id=i + 1, genre_name=name)
            assert genre.genre_name == name

    def test_genre_case_sensitivity(self) -> None:
        """Test that Genre names are case sensitive."""
        genre1 = Genre(id=1, genre_name="rock")
        genre2 = Genre(id=2, genre_name="Rock")
        genre3 = Genre(id=3, genre_name="ROCK")

        assert genre1.genre_name != genre2.genre_name
        assert genre2.genre_name != genre3.genre_name
        assert genre1.genre_name != genre3.genre_name

    def test_genre_whitespace_handling(self) -> None:
        """Test Genre names with various whitespace scenarios."""
        # Leading and trailing spaces should be preserved
        genre1 = Genre(id=1, genre_name=" Jazz ")
        assert genre1.genre_name == " Jazz "

        # Multiple spaces should be preserved
        genre2 = Genre(id=2, genre_name="Hip  Hop")
        assert genre2.genre_name == "Hip  Hop"

        # Tabs and newlines should be preserved
        genre3 = Genre(id=3, genre_name="Rock\n\tMusic")
        assert genre3.genre_name == "Rock\n\tMusic"

    def test_genre_boundary_values(self) -> None:
        """Test Genre with boundary values for ID."""
        # Test with maximum integer value
        import sys

        max_int = sys.maxsize
        genre = Genre(id=max_int, genre_name="Test Genre")
        assert genre.id == max_int

        # Test with minimum integer value
        min_int = -sys.maxsize - 1
        genre = Genre(id=min_int, genre_name="Test Genre")
        assert genre.id == min_int
