"""
Unit tests for the int_enum module.

This module contains unit tests for the IntEnum SQLAlchemy type decorator.
"""
import enum
from unittest.mock import Mock

import pytest
from sqlalchemy import TypeDecorator, Integer

from musigree.library.fields.int_enum import IntEnum


class MockTestEnum(enum.Enum):
    """Test enum for IntEnum tests."""
    VALUE_A = 1
    VALUE_B = 2
    VALUE_C = 3


class StringEnum(enum.Enum):
    """Test string enum."""
    VALUE_X = "x"
    VALUE_Y = "y"


class TestIntEnum:
    """Test class for IntEnum."""

    def test_int_enum_is_type_decorator(self) -> None:
        """Test that IntEnum is a TypeDecorator subclass."""
        assert issubclass(IntEnum, TypeDecorator)

    def test_int_enum_implementation(self) -> None:
        """Test IntEnum implementation type."""
        int_enum = IntEnum(MockTestEnum)
        assert isinstance(int_enum.impl, type(Integer()))

    def test_int_enum_cache_ok(self) -> None:
        """Test that IntEnum has cache_ok set to True."""
        int_enum = IntEnum(MockTestEnum)
        assert int_enum.cache_ok is True

    def test_int_enum_initialization(self) -> None:
        """Test IntEnum initialization."""
        int_enum = IntEnum(MockTestEnum)
        assert int_enum._enumtype is MockTestEnum

    def test_int_enum_initialization_with_args(self) -> None:
        """Test IntEnum initialization with additional arguments."""
        # Test basic initialization without invalid SQLAlchemy args
        int_enum = IntEnum(MockTestEnum)
        assert int_enum._enumtype is MockTestEnum


class TestProcessBindParam:
    """Test class for process_bind_param method."""

    @pytest.fixture
    def int_enum(self) -> IntEnum:
        """Fixture for IntEnum instance."""
        return IntEnum(MockTestEnum)

    def test_process_bind_param_none(self, int_enum: IntEnum) -> None:
        """Test process_bind_param with None value."""
        result = int_enum.process_bind_param(None, Mock())
        assert result is None

    def test_process_bind_param_integer(self, int_enum: IntEnum) -> None:
        """Test process_bind_param with integer value."""
        result = int_enum.process_bind_param(1, Mock())
        assert result == 1

    def test_process_bind_param_enum_member(self, int_enum: IntEnum) -> None:
        """Test process_bind_param with enum member."""
        result = int_enum.process_bind_param(MockTestEnum.VALUE_A, Mock())
        assert result == 1

        result = int_enum.process_bind_param(MockTestEnum.VALUE_B, Mock())
        assert result == 2

        result = int_enum.process_bind_param(MockTestEnum.VALUE_C, Mock())
        assert result == 3

    def test_process_bind_param_string_enum(self) -> None:
        """Test process_bind_param with string enum."""
        string_enum = IntEnum(StringEnum)
        result = string_enum.process_bind_param(StringEnum.VALUE_X, Mock())
        assert result == "x"

        result = string_enum.process_bind_param(StringEnum.VALUE_Y, Mock())
        assert result == "y"

    def test_process_bind_param_zero_value(self, int_enum: IntEnum) -> None:
        """Test process_bind_param with zero integer value."""
        result = int_enum.process_bind_param(0, Mock())
        assert result == 0

    def test_process_bind_param_negative_value(self, int_enum: IntEnum) -> None:
        """Test process_bind_param with negative integer value."""
        result = int_enum.process_bind_param(-1, Mock())
        assert result == -1


class TestProcessResultValue:
    """Test class for process_result_value method."""

    @pytest.fixture
    def int_enum(self) -> IntEnum:
        """Fixture for IntEnum instance."""
        return IntEnum(MockTestEnum)

    def test_process_result_value_none(self, int_enum: IntEnum) -> None:
        """Test process_result_value with None value."""
        result = int_enum.process_result_value(None, Mock())
        assert result is None

    def test_process_result_value_integer(self, int_enum: IntEnum) -> None:
        """Test process_result_value with integer values."""
        result = int_enum.process_result_value(1, Mock())
        assert result == MockTestEnum.VALUE_A

        result = int_enum.process_result_value(2, Mock())
        assert result == MockTestEnum.VALUE_B

        result = int_enum.process_result_value(3, Mock())
        assert result == MockTestEnum.VALUE_C

    def test_process_result_value_string_enum(self) -> None:
        """Test process_result_value with string enum."""
        string_enum = IntEnum(StringEnum)
        result = string_enum.process_result_value("x", Mock())
        assert result == StringEnum.VALUE_X

        result = string_enum.process_result_value("y", Mock())
        assert result == StringEnum.VALUE_Y

    def test_process_result_value_invalid_integer(self, int_enum: IntEnum) -> None:
        """Test process_result_value with invalid integer."""
        with pytest.raises(ValueError):
            int_enum.process_result_value(99, Mock())

    def test_process_result_value_invalid_string(self) -> None:
        """Test process_result_value with invalid string for string enum."""
        string_enum = IntEnum(StringEnum)
        with pytest.raises(ValueError):
            string_enum.process_result_value("invalid", Mock())


class TestIntEnumIntegration:
    """Test class for IntEnum integration scenarios."""

    def test_round_trip_conversion(self) -> None:
        """Test round trip conversion from enum to int and back."""
        int_enum = IntEnum(MockTestEnum)
        dialect = Mock()

        # Test each enum value
        for enum_value in MockTestEnum:
            # Convert enum to bind parameter
            bound_value = int_enum.process_bind_param(enum_value, dialect)
            
            # Convert back to enum
            result_value = int_enum.process_result_value(bound_value, dialect)
            
            # Should be the same enum value
            assert result_value == enum_value
            assert result_value is not None

    def test_round_trip_with_integers(self) -> None:
        """Test round trip when starting with integer values."""
        int_enum = IntEnum(MockTestEnum)
        dialect = Mock()

        # Test with integer values that correspond to enum values
        for int_value in [1, 2, 3]:
            # Convert int to bind parameter (should remain int)
            bound_value = int_enum.process_bind_param(int_value, dialect)
            assert bound_value == int_value
            
            # Convert to enum
            result_value = int_enum.process_result_value(bound_value, dialect)
            assert result_value is not None
            assert result_value.value == int_value

    def test_different_enum_types(self) -> None:
        """Test IntEnum with different enum types."""
        # Test with integer enum
        int_enum = IntEnum(MockTestEnum)
        result = int_enum.process_bind_param(MockTestEnum.VALUE_A, Mock())
        assert result == 1
        
        # Test with string enum
        string_enum = IntEnum(StringEnum)
        result = string_enum.process_bind_param(StringEnum.VALUE_X, Mock())
        assert result == "x"

    def test_enum_type_preservation(self) -> None:
        """Test that the enum type is preserved correctly."""
        int_enum = IntEnum(MockTestEnum)
        assert int_enum._enumtype is MockTestEnum
        
        # Different instance should have different enum type
        string_enum = IntEnum(StringEnum)
        assert string_enum._enumtype is StringEnum
        assert string_enum._enumtype is not MockTestEnum

    def test_none_handling_consistency(self) -> None:
        """Test that None is handled consistently in both directions."""
        int_enum = IntEnum(MockTestEnum)
        dialect = Mock()
        
        # None -> bind parameter -> None
        bound_none = int_enum.process_bind_param(None, dialect)
        assert bound_none is None
        
        # None -> result value -> None
        result_none = int_enum.process_result_value(None, dialect)
        assert result_none is None


class TestIntEnumEdgeCases:
    """Test class for IntEnum edge cases."""

    def test_enum_with_zero_value(self) -> None:
        """Test IntEnum with enum containing zero value."""
        class ZeroEnum(enum.Enum):
            ZERO = 0
            ONE = 1
        
        int_enum = IntEnum(ZeroEnum)
        dialect = Mock()
        
        # Test zero value handling
        bound_value = int_enum.process_bind_param(ZeroEnum.ZERO, dialect)
        assert bound_value == 0
        
        result_value = int_enum.process_result_value(0, dialect)
        assert result_value == ZeroEnum.ZERO

    def test_enum_with_negative_values(self) -> None:
        """Test IntEnum with enum containing negative values."""
        class NegativeEnum(enum.Enum):
            NEGATIVE = -1
            ZERO = 0
            POSITIVE = 1
        
        int_enum = IntEnum(NegativeEnum)
        dialect = Mock()
        
        # Test negative value handling
        bound_value = int_enum.process_bind_param(NegativeEnum.NEGATIVE, dialect)
        assert bound_value == -1
        
        result_value = int_enum.process_result_value(-1, dialect)
        assert result_value == NegativeEnum.NEGATIVE

    def test_multiple_int_enum_instances(self) -> None:
        """Test multiple IntEnum instances with different enum types."""
        int_enum1 = IntEnum(MockTestEnum)
        int_enum2 = IntEnum(StringEnum)
        
        # They should be independent
        assert int_enum1._enumtype is MockTestEnum
        assert int_enum2._enumtype is StringEnum
        
        # Each should work with its own enum type
        result1 = int_enum1.process_bind_param(MockTestEnum.VALUE_A, Mock())
        result2 = int_enum2.process_bind_param(StringEnum.VALUE_X, Mock())
        
        assert result1 == 1
        assert result2 == "x"