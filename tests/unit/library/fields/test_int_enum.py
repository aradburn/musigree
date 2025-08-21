"""
Unit tests for musigree.library.fields.int_enum module.
"""

import pytest
import enum
from typing import Any
from unittest.mock import Mock

from musigree.library.fields.int_enum import IntEnum


class SampleEnum(enum.Enum):
    """Sample enum for testing IntEnum functionality."""

    VALUE_A = 1
    VALUE_B = 2
    VALUE_C = 10


class StringEnum(enum.Enum):
    """Test enum with string values (should not be used with IntEnum but tests edge cases)."""

    ITEM_X = "x"
    ITEM_Y = "y"


class TestIntEnum:
    """Test cases for IntEnum type decorator."""

    def test_init_with_enum_type(self) -> None:
        """Test initialization with an enum type."""
        # Arrange & Act
        int_enum = IntEnum(SampleEnum)

        # Assert
        assert int_enum._enumtype == SampleEnum
        assert int_enum.impl is not None

    def test_init_with_args_and_kwargs(self) -> None:
        """Test initialization with additional args and kwargs."""
        # Arrange & Act
        int_enum = IntEnum(SampleEnum)

        # Assert
        assert int_enum._enumtype == SampleEnum

    def test_cache_ok_attribute(self) -> None:
        """Test that cache_ok is set correctly."""
        # Arrange & Act
        int_enum = IntEnum(SampleEnum)

        # Assert
        assert int_enum.cache_ok is True

    def test_impl_attribute(self) -> None:
        """Test that impl is set to Integer."""
        # Arrange
        from sqlalchemy import Integer

        # Act
        int_enum = IntEnum(SampleEnum)

        # Assert
        assert isinstance(int_enum.impl, Integer)


class TestProcessBindParam:
    """Test cases for process_bind_param method."""

    def test_process_bind_param_with_integer(self) -> None:
        """Test process_bind_param with integer input."""
        # Arrange
        int_enum = IntEnum(SampleEnum)
        integer_value: int = 5
        mock_dialect: Any = Mock()

        # Act
        result = int_enum.process_bind_param(integer_value, mock_dialect)

        # Assert
        assert result == 5

    def test_process_bind_param_with_enum_member(self) -> None:
        """Test process_bind_param with enum member input."""
        # Arrange
        int_enum = IntEnum(SampleEnum)
        enum_value: SampleEnum = SampleEnum.VALUE_A
        mock_dialect: Any = Mock()

        # Act
        result = int_enum.process_bind_param(enum_value, mock_dialect)

        # Assert
        assert result == 1

    def test_process_bind_param_with_different_enum_members(self) -> None:
        """Test process_bind_param with different enum members."""
        # Arrange
        int_enum = IntEnum(SampleEnum)
        mock_dialect: Any = Mock()

        # Act & Assert
        assert int_enum.process_bind_param(SampleEnum.VALUE_A, mock_dialect) == 1
        assert int_enum.process_bind_param(SampleEnum.VALUE_B, mock_dialect) == 2
        assert int_enum.process_bind_param(SampleEnum.VALUE_C, mock_dialect) == 10

    def test_process_bind_param_with_zero(self) -> None:
        """Test process_bind_param with zero integer."""
        # Arrange
        int_enum = IntEnum(SampleEnum)
        mock_dialect: Any = Mock()

        # Act
        result = int_enum.process_bind_param(0, mock_dialect)

        # Assert
        assert result == 0

    def test_process_bind_param_with_negative_integer(self) -> None:
        """Test process_bind_param with negative integer."""
        # Arrange
        int_enum = IntEnum(SampleEnum)
        mock_dialect: Any = Mock()

        # Act
        result = int_enum.process_bind_param(-1, mock_dialect)

        # Assert
        assert result == -1

    def test_process_bind_param_with_none(self) -> None:
        """Test process_bind_param with None value."""
        # Arrange
        int_enum = IntEnum(SampleEnum)
        mock_dialect: Any = Mock()

        # Act
        result = int_enum.process_bind_param(None, mock_dialect)

        # Assert
        assert result is None

    def test_process_bind_param_dialect_parameter_ignored(self) -> None:
        """Test that dialect parameter is ignored in process_bind_param."""
        # Arrange
        int_enum = IntEnum(SampleEnum)
        mock_dialect: Any = Mock()

        # Act
        result = int_enum.process_bind_param(SampleEnum.VALUE_A, mock_dialect)

        # Assert
        assert result == 1

    def test_process_bind_param_with_string_enum(self) -> None:
        """Test process_bind_param with string enum (edge case)."""
        # Arrange
        int_enum = IntEnum(StringEnum)
        mock_dialect: Any = Mock()

        # Act
        result = int_enum.process_bind_param(StringEnum.ITEM_X, mock_dialect)

        # Assert
        assert result == "x"


class TestProcessResultValue:
    """Test cases for process_result_value method."""

    def test_process_result_value_with_valid_integer(self) -> None:
        """Test process_result_value with valid integer."""
        # Arrange
        int_enum = IntEnum(SampleEnum)
        mock_dialect: Any = Mock()

        # Act
        result = int_enum.process_result_value(1, mock_dialect)

        # Assert
        assert result == SampleEnum.VALUE_A
        assert isinstance(result, SampleEnum)

    def test_process_result_value_with_different_values(self) -> None:
        """Test process_result_value with different valid values."""
        # Arrange
        int_enum = IntEnum(SampleEnum)
        mock_dialect: Any = Mock()

        # Act & Assert
        assert int_enum.process_result_value(1, mock_dialect) == SampleEnum.VALUE_A
        assert int_enum.process_result_value(2, mock_dialect) == SampleEnum.VALUE_B
        assert int_enum.process_result_value(10, mock_dialect) == SampleEnum.VALUE_C

    def test_process_result_value_with_invalid_integer(self) -> None:
        """Test process_result_value with invalid integer (not in enum)."""
        # Arrange
        int_enum = IntEnum(SampleEnum)
        mock_dialect: Any = Mock()

        # Act & Assert
        with pytest.raises(ValueError):
            int_enum.process_result_value(999, mock_dialect)

    def test_process_result_value_dialect_parameter_ignored(self) -> None:
        """Test that dialect parameter is ignored in process_result_value."""
        # Arrange
        int_enum = IntEnum(SampleEnum)
        mock_dialect: Any = Mock()

        # Act
        result = int_enum.process_result_value(1, mock_dialect)

        # Assert
        assert result == SampleEnum.VALUE_A

    def test_process_result_value_with_none(self) -> None:
        """Test process_result_value with None value."""
        # Arrange
        int_enum = IntEnum(SampleEnum)
        mock_dialect: Any = Mock()

        # Act
        result = int_enum.process_result_value(None, mock_dialect)

        # Assert
        assert result is None

    def test_process_result_value_with_string(self) -> None:
        """Test process_result_value with string input (should fail)."""
        # Arrange
        int_enum = IntEnum(SampleEnum)
        mock_dialect: Any = Mock()

        # Act & Assert
        with pytest.raises(ValueError):
            int_enum.process_result_value("invalid", mock_dialect)


class TestIntegration:
    """Integration tests for IntEnum."""

    def test_round_trip_conversion(self) -> None:
        """Test round-trip conversion: enum -> int -> enum."""
        # Arrange
        int_enum = IntEnum(SampleEnum)
        original_enum = SampleEnum.VALUE_B
        mock_dialect: Any = Mock()

        # Act
        bound_value = int_enum.process_bind_param(original_enum, mock_dialect)
        result_value = int_enum.process_result_value(bound_value, mock_dialect)

        # Assert
        assert result_value == original_enum
        assert bound_value == 2

    def test_round_trip_conversion_all_values(self) -> None:
        """Test round-trip conversion for all enum values."""
        # Arrange
        int_enum = IntEnum(SampleEnum)
        mock_dialect: Any = Mock()

        # Act & Assert
        for enum_member in SampleEnum:
            bound_value = int_enum.process_bind_param(enum_member, mock_dialect)
            result_value = int_enum.process_result_value(bound_value, mock_dialect)
            assert result_value == enum_member
            assert bound_value == enum_member.value

    def test_integer_passthrough(self) -> None:
        """Test that integers pass through bind_param unchanged."""
        # Arrange
        int_enum = IntEnum(SampleEnum)
        mock_dialect: Any = Mock()

        # Act & Assert
        for value in [1, 2, 10]:
            bound_value = int_enum.process_bind_param(value, mock_dialect)
            assert bound_value == value


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_enum(self) -> None:
        """Test with an empty enum."""

        # Arrange
        class EmptyEnum(enum.Enum):
            pass

        int_enum = IntEnum(EmptyEnum)
        mock_dialect: Any = Mock()

        # Act & Assert - should handle empty enum gracefully
        result = int_enum.process_bind_param(None, mock_dialect)
        assert result is None

    def test_enum_with_duplicate_values(self) -> None:
        """Test with enum having duplicate values."""

        # Arrange
        class DuplicateEnum(enum.Enum):
            FIRST = 1
            SECOND = 1  # Same value as FIRST
            THIRD = 2

        int_enum = IntEnum(DuplicateEnum)
        mock_dialect: Any = Mock()

        # Act
        result = int_enum.process_result_value(1, mock_dialect)

        # Assert
        # Should return the first enum member with that value
        assert result == DuplicateEnum.FIRST

    def test_large_integer_values(self) -> None:
        """Test with large integer values."""

        # Arrange
        class LargeEnum(enum.Enum):
            SMALL = 1
            LARGE = 999999999

        int_enum = IntEnum(LargeEnum)
        mock_dialect: Any = Mock()

        # Act & Assert
        assert int_enum.process_bind_param(LargeEnum.LARGE, mock_dialect) == 999999999
        assert int_enum.process_result_value(999999999, mock_dialect) == LargeEnum.LARGE
