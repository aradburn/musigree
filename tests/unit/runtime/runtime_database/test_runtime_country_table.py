from sqlalchemy.orm import class_mapper

from musigree.runtime.runtime_database.runtime_country_table import RuntimeCountryTable


class TestRuntimeCountryTable:
    """Unit tests for RuntimeCountryTable class."""

    def test_init_with_valid_entries(self) -> None:
        """Test initialization with valid column entries."""
        # GIVEN
        entries = {
            "id": 1,
            "country_name": "United States",
            "invalid_column": "should_be_ignored",
        }

        # WHEN
        country_table = RuntimeCountryTable(**entries)

        # THEN
        assert country_table.id == 1
        assert country_table.country_name == "United States"
        assert not hasattr(country_table, "invalid_column")

    def test_init_with_empty_entries(self) -> None:
        """Test initialization with empty entries dictionary."""
        # GIVEN
        entries: dict = {}

        # WHEN
        country_table = RuntimeCountryTable(**entries)

        # THEN
        assert isinstance(country_table, RuntimeCountryTable)

    def test_tablename(self) -> None:
        """Test that the table name is correctly set."""
        # GIVEN/WHEN
        table_name = RuntimeCountryTable.__tablename__

        # THEN
        assert table_name == "country"

    def test_columns_exist(self) -> None:
        """Test that expected columns exist in the table."""
        # GIVEN
        expected_columns = {"id", "country_name"}

        # WHEN
        columns = set(column.name for column in class_mapper(RuntimeCountryTable).columns)

        # THEN
        assert expected_columns.issubset(columns)

    def test_repr(self) -> None:
        """Test string representation of RuntimeCountryTable instance."""
        # GIVEN
        country_input = {"id": 1, "country_name": "United Kingdom"}
        country_table = RuntimeCountryTable(**country_input)

        # WHEN
        repr_str = repr(country_table)

        # THEN
        assert isinstance(repr_str, str)
        assert "United Kingdom" in repr_str
