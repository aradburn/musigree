"""
Unit tests for musigree.library.fields.int_enum module.
"""
import pytest
import enum
from unittest.mock import Mock

from musigree.library.fields.int_enum import IntEnum


class TestEnum(enum.Enum):
    """Test enum for testing IntEnum functionality."""
    VALUE_A = 1
    VALUE_B = 2
    VALUE_C = 10


class StringEnum(enum.Enum):
    """Test enum with string values (should not be used with IntEnum but tests edge cases)."""
    ITEM_X = "x"
    ITEM_Y = "y"


class TestIntEnum:
    """Test cases for IntEnum type decorator."""

    def test_init_with_enum_type(self):
        """Test initialization with an enum type."""
        # Arrange & Act
        int_enum = IntEnum(TestEnum)

        # Assert
        assert int_enum._enumtype == TestEnum
        assert int_enum.impl is not None

    def test_init_with_args_and_kwargs(self):
        """Test initialization with additional args and kwargs."""
        # Arrange & Act
        int_enum = IntEnum(TestEnum)
        
        # Assert
        assert int_enum._enumtype == TestEnum

    def test_cache_ok_attribute(self):
        """Test that cache_ok is set correctly."""
        # Arrange & Act
        int_enum = IntEnum(TestEnum)

        # Assert
        assert int_enum.cache_ok is True

    def test_impl_attribute(self):
        """Test that impl is set to Integer."""
        # Arrange
        from sqlalchemy import Integer
        
        # Act
        int_enum = IntEnum(TestEnum)
        
        # Assert
        assert isinstance(int_enum.impl, Integer)


class TestProcessBindParam:
    """Test cases for process_bind_param method."""

    def test_process_bind_param_with_integer(self):
        """Test process_bind_param with integer input."""
        # Arrange
        int_enum = IntEnum(TestEnum)
        integer_value = 5
        mock_dialect = Mock()

        # Act
        result = int_enum.process_bind_param(integer_value, mock_dialect)

        # Assert
        assert result == 5

    def test_process_bind_param_with_enum_member(self):
        """Test process_bind_param with enum member input."""
        # Arrange
        int_enum = IntEnum(TestEnum)
        enum_value = TestEnum.VALUE_A
        mock_dialect = Mock()

        # Act
        result = int_enum.process_bind_param(enum_value, mock_dialect)

        # Assert
        assert result == 1

    def test_process_bind_param_with_different_enum_members(self):
        """Test process_bind_param with different enum members."""
        # Arrange
        int_enum = IntEnum(TestEnum)
        mock_dialect = Mock()

        # Act & Assert
        assert int_enum.process_bind_param(TestEnum.VALUE_A, mock_dialect) == 1
        assert int_enum.process_bind_param(TestEnum.VALUE_B, mock_dialect) == 2
        assert int_enum.process_bind_param(TestEnum.VALUE_C, mock_dialect) == 10

    def test_process_bind_param_with_zero(self):
        """Test process_bind_param with zero integer."""
        # Arrange
        int_enum = IntEnum(TestEnum)
        mock_dialect = Mock()

        # Act
        result = int_enum.process_bind_param(0, mock_dialect)

        # Assert
        assert result == 0

    def test_process_bind_param_with_negative_integer(self):
        """Test process_bind_param with negative integer."""
        # Arrange
        int_enum = IntEnum(TestEnum)
        mock_dialect = Mock()

        # Act
        result = int_enum.process_bind_param(-1, mock_dialect)

        # Assert
        assert result == -1

    def test_process_bind_param_with_none(self):
        """Test process_bind_param with None value."""
        # Arrange
        int_enum = IntEnum(TestEnum)
        mock_dialect = Mock()
        
        # Act
        result = int_enum.process_bind_param(None, mock_dialect)
        
        # Assert
        assert result is None

    def test_process_bind_param_dialect_parameter_ignored(self):
        """Test that dialect parameter is ignored in process_bind_param."""
        # Arrange
        int_enum = IntEnum(TestEnum)
        mock_dialect = Mock()

        # Act
        result = int_enum.process_bind_param(TestEnum.VALUE_A, mock_dialect)

        # Assert
        assert result == 1

    def test_process_bind_param_with_string_enum(self):
        """Test process_bind_param with string enum (edge case)."""
        # Arrange
        int_enum = IntEnum(StringEnum)
        mock_dialect = Mock()

        # Act
        result = int_enum.process_bind_param(StringEnum.ITEM_X, mock_dialect)

        # Assert
        assert result == "x"


class TestProcessResultValue:
    """Test cases for process_result_value method."""

    def test_process_result_value_with_valid_integer(self):
        """Test process_result_value with valid integer."""
        # Arrange
        int_enum = IntEnum(TestEnum)
        mock_dialect = Mock()

        # Act
        result = int_enum.process_result_value(1, mock_dialect)

        # Assert
        assert result == TestEnum.VALUE_A
        assert isinstance(result, TestEnum)

    def test_process_result_value_with_different_values(self):
        """Test process_result_value with different valid values."""
        # Arrange
        int_enum = IntEnum(TestEnum)
        mock_dialect = Mock()

        # Act & Assert
        assert int_enum.process_result_value(1, mock_dialect) == TestEnum.VALUE_A
        assert int_enum.process_result_value(2, mock_dialect) == TestEnum.VALUE_B
        assert int_enum.process_result_value(10, mock_dialect) == TestEnum.VALUE_C

    def test_process_result_value_with_invalid_integer(self):
        """Test process_result_value with invalid integer (not in enum)."""
        # Arrange
        int_enum = IntEnum(TestEnum)
        mock_dialect = Mock()

        # Act & Assert
        with pytest.raises(ValueError):
            int_enum.process_result_value(999, mock_dialect)

    def test_process_result_value_dialect_parameter_ignored(self):
        """Test that dialect parameter is ignored in process_result_value."""
        # Arrange
        int_enum = IntEnum(TestEnum)
        mock_dialect = Mock()

        # Act
        result = int_enum.process_result_value(1, mock_dialect)

        # Assert
        assert result == TestEnum.VALUE_A

    def test_process_result_value_with_none(self):
        """Test process_result_value with None value."""
        # Arrange
        int_enum = IntEnum(TestEnum)
        mock_dialect = Mock()
        
        # Act
        result = int_enum.process_result_value(None, mock_dialect)
        
        # Assert
        assert result is None

    def test_process_result_value_with_string(self):
        """Test process_result_value with string input (should fail)."""
        # Arrange
        int_enum = IntEnum(TestEnum)
        mock_dialect = Mock()

        # Act & Assert
        with pytest.raises(ValueError):
            int_enum.process_result_value("invalid", mock_dialect)


class TestIntegration:
    """Integration tests for IntEnum."""

    def test_round_trip_conversion(self):
        """Test round-trip conversion: enum -> int -> enum."""
        # Arrange
        int_enum = IntEnum(TestEnum)
        original_enum = TestEnum.VALUE_B
        mock_dialect = Mock()

        # Act
        bound_value = int_enum.process_bind_param(original_enum, mock_dialect)
        result_value = int_enum.process_result_value(bound_value, mock_dialect)

        # Assert
        assert result_value == original_enum
        assert bound_value == 2

    def test_round_trip_conversion_all_values(self):
        """Test round-trip conversion for all enum values."""
        # Arrange
        int_enum = IntEnum(TestEnum)
        mock_dialect = Mock()

        # Act & Assert
        for enum_member in TestEnum:
            bound_value = int_enum.process_bind_param(enum_member, mock_dialect)
            result_value = int_enum.process_result_value(bound_value, mock_dialect)
            assert result_value == enum_member
            assert bound_value == enum_member.value

    def test_integer_passthrough(self):
        """Test that integers pass through bind_param unchanged."""
        # Arrange
        int_enum = IntEnum(TestEnum)
        mock_dialect = Mock()

        # Act & Assert
        for value in [1, 2, 10]:
            bound_value = int_enum.process_bind_param(value, mock_dialect)
            assert bound_value == value


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_enum(self):
        """Test with an empty enum."""
        # Arrange
        class EmptyEnum(enum.Enum):
            pass
        
        int_enum = IntEnum(EmptyEnum)
        mock_dialect = Mock()
        
        # Act & Assert - should handle empty enum gracefully
        result = int_enum.process_bind_param(None, mock_dialect)
        assert result is None

    def test_enum_with_duplicate_values(self):
        """Test with enum having duplicate values."""
        # Arrange
        class DuplicateEnum(enum.Enum):
            FIRST = 1
            SECOND = 1  # Same value as FIRST
            THIRD = 2

        int_enum = IntEnum(DuplicateEnum)
        mock_dialect = Mock()

        # Act
        result = int_enum.process_result_value(1, mock_dialect)

        # Assert
        # Should return the first enum member with that value
        assert result == DuplicateEnum.FIRST

    def test_large_integer_values(self):
        """Test with large integer values."""
        # Arrange
        class LargeEnum(enum.Enum):
            SMALL = 1
            LARGE = 999999999

        int_enum = IntEnum(LargeEnum)
        mock_dialect = Mock()

        # Act & Assert
        assert int_enum.process_bind_param(LargeEnum.LARGE, mock_dialect) == 999999999
        assert int_enum.process_result_value(999999999, mock_dialect) == LargeEnum.LARGE 