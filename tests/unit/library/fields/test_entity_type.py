"""
Unit tests for the entity_type module.

This module contains unit tests for the EntityType enum and its utility methods.
"""

import enum

import pytest

from musigree.library.fields.entity_type import EntityType


class TestEntityType:
    """Test class for EntityType enum."""

    def test_entity_type_is_enum(self) -> None:
        """Test that EntityType is an enum."""
        assert issubclass(EntityType, enum.Enum)

    def test_entity_type_values(self) -> None:
        """Test EntityType enum values."""
        assert EntityType.ARTIST.value == 1
        assert EntityType.LABEL.value == 2

    def test_entity_type_members(self) -> None:
        """Test EntityType enum members."""
        assert hasattr(EntityType, "ARTIST")
        assert hasattr(EntityType, "LABEL")

        # Test that these are the only members
        members = list(EntityType)
        assert len(members) == 2
        assert EntityType.ARTIST in members
        assert EntityType.LABEL in members

    def test_entity_type_equality(self) -> None:
        """Test EntityType equality comparison."""
        assert EntityType.ARTIST == EntityType.ARTIST
        assert EntityType.LABEL == EntityType.LABEL
        assert EntityType.ARTIST != EntityType.LABEL

    def test_entity_type_string_representation(self) -> None:
        """Test string representation of EntityType."""
        assert str(EntityType.ARTIST) == "EntityType.ARTIST"
        assert str(EntityType.LABEL) == "EntityType.LABEL"

    def test_entity_type_name_property(self) -> None:
        """Test name property of EntityType."""
        assert EntityType.ARTIST.name == "ARTIST"
        assert EntityType.LABEL.name == "LABEL"


class TestEntityTypeFromStr:
    """Test class for EntityType.from_str method."""

    def test_from_str_artist_lowercase(self) -> None:
        """Test from_str with lowercase 'artist'."""
        result = EntityType.from_str("artist")
        assert result == EntityType.ARTIST

    def test_from_str_artist_uppercase(self) -> None:
        """Test from_str with uppercase 'ARTIST'."""
        result = EntityType.from_str("ARTIST")
        assert result == EntityType.ARTIST

    def test_from_str_label_lowercase(self) -> None:
        """Test from_str with lowercase 'label'."""
        result = EntityType.from_str("label")
        assert result == EntityType.LABEL

    def test_from_str_label_uppercase(self) -> None:
        """Test from_str with uppercase 'LABEL'."""
        result = EntityType.from_str("LABEL")
        assert result == EntityType.LABEL

    def test_from_str_invalid_string(self) -> None:
        """Test from_str with invalid string."""
        with pytest.raises(NotImplementedError):
            EntityType.from_str("invalid")

    def test_from_str_empty_string(self) -> None:
        """Test from_str with empty string."""
        with pytest.raises(NotImplementedError):
            EntityType.from_str("")

    def test_from_str_mixed_case(self) -> None:
        """Test from_str with mixed case (should fail)."""
        with pytest.raises(NotImplementedError):
            EntityType.from_str("Artist")

        with pytest.raises(NotImplementedError):
            EntityType.from_str("Label")

    def test_from_str_partial_match(self) -> None:
        """Test from_str with partial matches (should fail)."""
        with pytest.raises(NotImplementedError):
            EntityType.from_str("art")

        with pytest.raises(NotImplementedError):
            EntityType.from_str("lab")

    def test_from_str_with_spaces(self) -> None:
        """Test from_str with strings containing spaces (should fail)."""
        with pytest.raises(NotImplementedError):
            EntityType.from_str(" artist ")

        with pytest.raises(NotImplementedError):
            EntityType.from_str(" label ")


class TestEntityTypeLessThan:
    """Test class for EntityType.__lt__ method."""

    def test_less_than_artist_label(self) -> None:
        """Test that ARTIST < LABEL."""
        assert EntityType.ARTIST < EntityType.LABEL

    def test_less_than_label_artist(self) -> None:
        """Test that LABEL is not < ARTIST."""
        assert not (EntityType.LABEL < EntityType.ARTIST)

    def test_less_than_same_value(self) -> None:
        """Test that equal values are not less than each other."""
        assert not (EntityType.ARTIST < EntityType.ARTIST)
        assert not (EntityType.LABEL < EntityType.LABEL)

    def test_less_than_different_type(self) -> None:
        """Test less than comparison with different type."""
        result = EntityType.ARTIST.__lt__("not_an_entity_type")  # type: ignore
        assert result is NotImplemented

    def test_less_than_ordering(self) -> None:
        """Test that EntityTypes can be sorted."""
        types_list = [EntityType.LABEL, EntityType.ARTIST]
        sorted_types = sorted(types_list)

        assert sorted_types[0] == EntityType.ARTIST
        assert sorted_types[1] == EntityType.LABEL


class TestEntityTypeRepr:
    """Test class for EntityType.__repr__ method."""

    def test_repr_artist(self) -> None:
        """Test __repr__ for ARTIST."""
        result = repr(EntityType.ARTIST)
        assert result == "ARTIST"

    def test_repr_label(self) -> None:
        """Test __repr__ for LABEL."""
        result = repr(EntityType.LABEL)
        assert result == "LABEL"

    def test_repr_consistency(self) -> None:
        """Test that __repr__ returns the name property."""
        assert repr(EntityType.ARTIST) == EntityType.ARTIST.name
        assert repr(EntityType.LABEL) == EntityType.LABEL.name


class TestEntityTypeIntegration:
    """Test class for EntityType integration scenarios."""

    def test_entity_type_in_set(self) -> None:
        """Test EntityType in set operations."""
        entity_set = {EntityType.ARTIST, EntityType.LABEL}

        assert EntityType.ARTIST in entity_set
        assert EntityType.LABEL in entity_set
        assert len(entity_set) == 2

    def test_entity_type_as_dict_key(self) -> None:
        """Test EntityType as dictionary keys."""
        entity_dict = {EntityType.ARTIST: "artist_data", EntityType.LABEL: "label_data"}

        assert entity_dict[EntityType.ARTIST] == "artist_data"
        assert entity_dict[EntityType.LABEL] == "label_data"

    def test_entity_type_iteration(self) -> None:
        """Test iterating over EntityType values."""
        all_types = list(EntityType)

        assert len(all_types) == 2
        assert EntityType.ARTIST in all_types
        assert EntityType.LABEL in all_types

    def test_entity_type_membership(self) -> None:
        """Test membership testing with EntityType."""
        assert EntityType.ARTIST in EntityType
        assert EntityType.LABEL in EntityType

    def test_from_str_round_trip(self) -> None:
        """Test round trip conversion using from_str and name."""
        for entity_type in EntityType:
            # Convert to string using name, then back using from_str
            name = entity_type.name.lower()
            converted = EntityType.from_str(name)
            assert converted == entity_type
