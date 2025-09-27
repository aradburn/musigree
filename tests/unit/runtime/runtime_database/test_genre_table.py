from typing import Any

from sqlalchemy import inspect

from musigree.runtime.runtime_database.genre_table import GenreTable


class TestGenreTable:
    """Unit tests for GenreTable class."""

    def test_init_with_valid_entries(self) -> None:
        """Test initialization with valid column entries."""
        # GIVEN
        entries = {
            "id": 1,
            "genre_name": "Electronic",
            "invalid_column": "should_be_ignored",
        }

        # WHEN
        genre_table = GenreTable(**entries)

        # THEN
        assert genre_table.id == 1
        assert genre_table.genre_name == "Electronic"
        assert not hasattr(genre_table, "invalid_column")

    def test_init_with_empty_entries(self) -> None:
        """Test initialization with empty entries dictionary."""
        # GIVEN
        entries: dict[str, Any] = {}

        # WHEN
        genre_table = GenreTable(**entries)

        # THEN
        assert isinstance(genre_table, GenreTable)

    def test_tablename(self) -> None:
        """Test that the table name is correctly set."""
        # GIVEN/WHEN
        table_name = GenreTable.__tablename__

        # THEN
        assert table_name == "genre"

    def test_columns_exist(self) -> None:
        """Test that expected columns exist in the table."""
        # GIVEN
        expected_columns = {"id", "genre_name"}

        # WHEN
        columns = set(column.name for column in inspect(GenreTable).columns)

        # THEN
        assert expected_columns.issubset(columns)

    def test_repr(self) -> None:
        """Test string representation of GenreTable instance."""
        # GIVEN
        genre_input = {"id": 1, "genre_name": "Rock"}
        genre_table = GenreTable(**genre_input)

        # WHEN
        repr_str = repr(genre_table)

        # THEN
        assert isinstance(repr_str, str)
        assert "Rock" in repr_str
