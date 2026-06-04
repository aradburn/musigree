"""
Unit tests for musigree.library.domain.base.
"""

from musigree.library.domain.base import (
    InternalDomainObject,
    PublicDomainObject,
    to_camelcase,
)


class TestToCamelcase:
    """Tests for to_camelcase."""

    def test_single_word_unchanged(self) -> None:
        """Single word is returned unchanged."""
        assert to_camelcase("hello") == "hello"

    def test_snake_case_to_camel_case(self) -> None:
        """Multiple words are converted to camelCase."""
        assert to_camelcase("hello_world") == "helloWorld"
        assert to_camelcase("snake_case_string") == "snakeCaseString"


class TestInternalDomainObject:
    """Tests for InternalDomainObject."""

    def test_repr_uses_normalize_dict(self) -> None:
        """__repr__ returns normalized dict from model_dump."""

        class Concrete(InternalDomainObject):
            value: str = "x"

        obj = Concrete(value="test")
        assert "test" in repr(obj)


class TestPublicDomainObject:
    """Tests for PublicDomainObject."""

    def test_flat_dict_returns_dict(self) -> None:
        """flat_dict returns dict from model_dump_json round-trip."""

        class Concrete(PublicDomainObject):
            name: str = ""
            value: int = 0

        obj = Concrete(name="Alice", value=42)
        result = obj.flat_dict(by_alias=True)
        assert isinstance(result, dict)
        assert result["name"] == "Alice"
        assert result["value"] == 42

    def test_flat_dict_by_alias_false(self) -> None:
        """flat_dict with by_alias=False uses field names."""

        class Concrete(PublicDomainObject):
            name: str = ""

        obj = Concrete(name="Bob")
        result = obj.flat_dict(by_alias=False)
        assert "name" in result
        assert result["name"] == "Bob"
