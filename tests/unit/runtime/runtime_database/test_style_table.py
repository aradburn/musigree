from typing import Any

from sqlalchemy import inspect

from musigree.runtime.runtime_database.style_table import StyleTable


class TestStyleTable:
    """Unit tests for StyleTable class."""

    def test_init_with_valid_entries(self) -> None:
        """Test initialization with valid column entries."""
        # GIVEN
        entries = {
            "id": 1,
            "style_name": "Electronic",
            "invalid_column": "should_be_ignored",
        }

        # WHEN
        style_table = StyleTable(**entries)

        # THEN
        assert style_table.id == 1
        assert style_table.style_name == "Electronic"
        assert not hasattr(style_table, "invalid_column")

    def test_init_with_empty_entries(self) -> None:
        """Test initialization with empty entries dictionary."""
        # GIVEN
        entries: dict[str, Any] = {}

        # WHEN
        style_table = StyleTable(**entries)

        # THEN
        assert isinstance(style_table, StyleTable)

    def test_tablename(self) -> None:
        """Test that the table name is correctly set."""
        # GIVEN/WHEN
        table_name = StyleTable.__tablename__

        # THEN
        assert table_name == "style"

    def test_columns_exist(self) -> None:
        """Test that expected columns exist in the table."""
        # GIVEN
        expected_columns = {"id", "style_name"}

        # WHEN
        columns = set(column.name for column in inspect(StyleTable).columns)

        # THEN
        assert expected_columns.issubset(columns)

    def test_repr(self) -> None:
        """Test string representation of StyleTable instance."""
        # GIVEN
        style_input = {"id": 1, "style_name": "Rock"}
        style_table = StyleTable(**style_input)

        # WHEN
        repr_str = repr(style_table)

        # THEN
        assert isinstance(repr_str, str)
        assert "Rock" in repr_str
