from typing import Any

from sqlalchemy.orm import class_mapper

from musigree.runtime.runtime_database.runtime_genre_table import RuntimeGenreTable


class TestRuntimeGenreTable:
    """Unit tests for RuntimeGenreTable class."""

    def test_init_with_valid_entries(self) -> None:
        """Test initialization with valid column entries."""
        # GIVEN
        entries = {
            "id": 1,
            "genre_name": "Electronic",
            "invalid_column": "should_be_ignored",
        }

        # WHEN
        genre_table = RuntimeGenreTable(**entries)

        # THEN
        assert genre_table.id == 1
        assert genre_table.genre_name == "Electronic"
        assert not hasattr(genre_table, "invalid_column")

    def test_init_with_empty_entries(self) -> None:
        """Test initialization with empty entries dictionary."""
        # GIVEN
        entries: dict[str, Any] = {}

        # WHEN
        genre_table = RuntimeGenreTable(**entries)

        # THEN
        assert isinstance(genre_table, RuntimeGenreTable)

    def test_tablename(self) -> None:
        """Test that the table name is correctly set."""
        # GIVEN/WHEN
        table_name = RuntimeGenreTable.__tablename__

        # THEN
        assert table_name == "genre"

    def test_columns_exist(self) -> None:
        """Test that expected columns exist in the table."""
        # GIVEN
        expected_columns = {"id", "genre_name"}

        # WHEN
        columns = set(column.name for column in class_mapper(RuntimeGenreTable).columns)

        # THEN
        assert expected_columns.issubset(columns)

    def test_repr(self) -> None:
        """Test string representation of RuntimeGenreTable instance."""
        # GIVEN
        genre_input = {"id": 1, "genre_name": "Rock"}
        genre_table = RuntimeGenreTable(**genre_input)

        # WHEN
        repr_str = repr(genre_table)

        # THEN
        assert isinstance(repr_str, str)
        assert "Rock" in repr_str
