from typing import Any

from sqlalchemy import inspect

from musigree.runtime.runtime_database.runtime_relation_table import (
    RuntimeRelationTable,
)


class TestRuntimeRelationTable:
    """Unit tests for RuntimeRelationTable class."""

    def test_init_with_valid_entries(self) -> None:
        """Test initialization with valid column entries."""
        # GIVEN
        entries = {
            "id": 1,
            "subject": 12345,
            "predicate": 3,
            "object": 67890,
            "invalid_column": "should_be_ignored",
        }

        # WHEN
        relation_table = RuntimeRelationTable(**entries)

        # THEN
        assert relation_table.id == 1
        assert relation_table.subject == 12345
        assert relation_table.predicate == 3
        assert relation_table.object == 67890
        assert not hasattr(relation_table, "invalid_column")

    def test_init_with_empty_entries(self) -> None:
        """Test initialization with empty entries dictionary."""
        # GIVEN
        entries: dict[str, Any] = {}

        # WHEN
        relation_table = RuntimeRelationTable(**entries)

        # THEN
        assert isinstance(relation_table, RuntimeRelationTable)

    def test_init_with_minimal_required_entries(self) -> None:
        """Test initialization with minimal required entries."""
        # GIVEN
        entries = {"subject": 123, "predicate": 456, "object": 789}

        # WHEN
        relation_table = RuntimeRelationTable(**entries)

        # THEN
        assert relation_table.subject == 123
        assert relation_table.predicate == 456
        assert relation_table.object == 789

    def test_tablename(self) -> None:
        """Test that the table name is correctly set."""
        # GIVEN/WHEN
        table_name = RuntimeRelationTable.__tablename__

        # THEN
        assert table_name == "runtime_relation"

    def test_columns_exist(self) -> None:
        """Test that expected columns exist in the table."""
        # GIVEN
        expected_columns = {"id", "subject", "predicate", "object"}

        # WHEN
        columns = set(column.name for column in inspect(RuntimeRelationTable).columns)

        # THEN
        assert expected_columns.issubset(columns)

    def test_primary_key(self) -> None:
        """Test that id column is the primary key."""
        # GIVEN/WHEN
        primary_key_columns = [
            col.name for col in inspect(RuntimeRelationTable).primary_key
        ]

        # THEN
        assert primary_key_columns == ["id"]

    def test_table_args_defined(self) -> None:
        """Test that table args are properly defined."""
        # GIVEN/WHEN
        table_args = RuntimeRelationTable.__table_args__

        # THEN
        assert table_args is not None
        assert isinstance(table_args, tuple)

    def test_repr_with_data(self) -> None:
        """Test string representation of RuntimeRelationTable instance with data."""
        # GIVEN
        relation_input = {"id": 1, "subject": 12345, "predicate": 3, "object": 67890}
        relation_table = RuntimeRelationTable(**relation_input)

        # WHEN
        repr_str = repr(relation_table)

        # THEN
        assert isinstance(repr_str, str)
        assert "12345" in repr_str
        assert "67890" in repr_str

    def test_repr_with_minimal_data(self) -> None:
        """Test string representation with minimal data."""
        # GIVEN
        relation_input = {"subject": 111, "predicate": 222, "object": 333}
        relation_table = RuntimeRelationTable(**relation_input)

        # WHEN
        repr_str = repr(relation_table)

        # THEN
        assert isinstance(repr_str, str)
        assert "111" in repr_str
        assert "333" in repr_str

    def test_column_filtering_in_init(self) -> None:
        """Test that initialization only uses valid column names."""
        # GIVEN
        entries = {
            "subject": 100,
            "predicate": 200,
            "object": 300,
            "nonexistent_column": "Should be ignored",
            "another_invalid": 123,
            "random_field": ["should", "not", "exist"],
        }

        # WHEN
        relation_table = RuntimeRelationTable(**entries)

        # THEN
        assert relation_table.subject == 100
        assert relation_table.predicate == 200
        assert relation_table.object == 300
        assert not hasattr(relation_table, "nonexistent_column")
        assert not hasattr(relation_table, "another_invalid")
        assert not hasattr(relation_table, "random_field")
