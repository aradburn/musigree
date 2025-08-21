from musigree.library.fields.entity_type import EntityType


class TestEntityType:
    """Test cases for the EntityType enum."""

    def test_entity_type_values(self) -> None:
        """Test that EntityType enum has correct values."""
        assert 1 == EntityType.ARTIST.value
        assert 2 == EntityType.LABEL.value

    def test_entity_type_names(self) -> None:
        """Test that EntityType enum has correct names."""
        assert "ARTIST" == EntityType.ARTIST.name
        assert "LABEL" == EntityType.LABEL.name

    def test_from_str_artist_lowercase(self) -> None:
        """Test from_str with lowercase 'artist'."""
        result = EntityType.from_str("artist")
        assert EntityType.ARTIST == result

    def test_from_str_artist_uppercase(self) -> None:
        """Test from_str with uppercase 'ARTIST'."""
        result = EntityType.from_str("ARTIST")
        assert EntityType.ARTIST == result

    def test_from_str_label_lowercase(self) -> None:
        """Test from_str with lowercase 'label'."""
        result = EntityType.from_str("label")
        assert EntityType.LABEL == result

    def test_from_str_label_uppercase(self) -> None:
        """Test from_str with uppercase 'LABEL'."""
        result = EntityType.from_str("LABEL")
        assert EntityType.LABEL == result

    def test_from_str_invalid_input(self) -> None:
        """Test from_str with invalid input raises NotImplementedError."""
        import pytest
        with pytest.raises(NotImplementedError):
            EntityType.from_str("invalid")

    def test_from_str_empty_string(self) -> None:
        """Test from_str with empty string raises NotImplementedError."""
        import pytest
        with pytest.raises(NotImplementedError):
            EntityType.from_str("")

    def test_from_str_none(self) -> None:
        """Test from_str with None raises NotImplementedError."""
        import pytest
        with pytest.raises(NotImplementedError):
            EntityType.from_str(None)  # type: ignore

    def test_from_str_mixed_case(self) -> None:
        """Test from_str with mixed case raises NotImplementedError."""
        import pytest
        with pytest.raises(NotImplementedError):
            EntityType.from_str("Artist")

        import pytest
        with pytest.raises(NotImplementedError):
            EntityType.from_str("Label")

    def test_less_than_comparison_artist_label(self) -> None:
        """Test less-than comparison between ARTIST and LABEL."""
        assert EntityType.ARTIST < EntityType.LABEL
        assert not (EntityType.LABEL < EntityType.ARTIST)

    def test_less_than_comparison_same_types(self) -> None:
        """Test less-than comparison between same types."""
        assert not (EntityType.ARTIST < EntityType.ARTIST)
        assert not (EntityType.LABEL < EntityType.LABEL)

    def test_less_than_comparison_with_non_entity_type(self) -> None:
        """Test less-than comparison with non-EntityType returns NotImplemented."""
        result = EntityType.ARTIST.__lt__("not an entity type")  # type: ignore
        assert NotImplemented == result

    def test_repr_method(self) -> None:
        """Test string representation (__repr__) of EntityType."""
        assert "ARTIST" == repr(EntityType.ARTIST)
        assert "LABEL" == repr(EntityType.LABEL)

    def test_str_method(self) -> None:
        """Test string conversion (__str__) of EntityType."""
        assert "EntityType.ARTIST" == str(EntityType.ARTIST)
        assert "EntityType.LABEL" == str(EntityType.LABEL)

    def test_equality_comparison(self) -> None:
        """Test equality comparison between EntityType values."""
        assert EntityType.ARTIST == EntityType.ARTIST
        assert EntityType.LABEL == EntityType.LABEL
        assert EntityType.ARTIST != EntityType.LABEL

    def test_hash_consistency(self) -> None:
        """Test that EntityType values are hashable and consistent."""
        # Should be able to use as dictionary keys
        test_dict = {EntityType.ARTIST: "artist_value", EntityType.LABEL: "label_value"}

        assert "artist_value" == test_dict[EntityType.ARTIST]
        assert "label_value" == test_dict[EntityType.LABEL]

    def test_enum_iteration(self) -> None:
        """Test iteration over EntityType enum values."""
        entity_types = list(EntityType)
        assert 2 == len(entity_types)
        assert EntityType.ARTIST in entity_types
        assert EntityType.LABEL in entity_types

    def test_enum_membership(self) -> None:
        """Test membership testing for EntityType enum."""
        assert EntityType.ARTIST in EntityType
        assert EntityType.LABEL in EntityType

