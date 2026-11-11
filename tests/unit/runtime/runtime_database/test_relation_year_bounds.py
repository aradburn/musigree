"""Year-bounds filtering keeps undated rows and drops years outside the range."""

from typing import TYPE_CHECKING, cast

from sqlalchemy import Table, create_engine, insert, select

from musigree.runtime.runtime_database.runtime_relation_repository import (
    year_bounds_clause,
)
from musigree.runtime.runtime_database.runtime_relation_table import RuntimeRelationTable

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine


def _create_relation_table(engine: Engine) -> None:
    """Create only the runtime relation table on a throwaway engine."""
    cast("Table", RuntimeRelationTable.__table__).create(engine)


def _row(row: dict[str, int | None]) -> dict[str, int | None]:
    """Widen a row literal so its values are ``int | None``.

    ``dict`` is invariant. A row of only integers is ``dict[str, int]`` and
    is not a ``dict[str, int | None]``.
    """
    return row


def test_year_bounds_clause_keeps_in_range_and_null_years() -> None:
    """Rows inside the range and rows with no year stay. Other years are dropped."""
    engine = create_engine("sqlite://")
    _create_relation_table(engine)
    rows: list[dict[str, int | None]] = [
        _row({"id": 1, "subject": 1, "predicate": 1, "object": 2, "release_id": 1, "year": 1960}),
        _row({"id": 2, "subject": 1, "predicate": 1, "object": 3, "release_id": 2, "year": 1975}),
        _row({"id": 3, "subject": 1, "predicate": 1, "object": 4, "release_id": 3, "year": 1990}),
        _row({"id": 4, "subject": 1, "predicate": 1, "object": 5, "release_id": 4, "year": None}),
    ]
    clause = year_bounds_clause(1970, 1979)
    assert clause is not None
    with engine.begin() as connection:
        connection.execute(insert(RuntimeRelationTable), rows)
        statement = select(RuntimeRelationTable.object).where(clause)
        kept = {row.object for row in connection.execute(statement)}
    assert kept == {3, 5}


def test_year_bounds_clause_honours_an_open_lower_bound() -> None:
    """Only max_year drops years above the bound and keeps undated rows."""
    engine = create_engine("sqlite://")
    _create_relation_table(engine)
    rows: list[dict[str, int | None]] = [
        _row({"id": 1, "subject": 1, "predicate": 1, "object": 2, "release_id": 1, "year": 1960}),
        _row({"id": 2, "subject": 1, "predicate": 1, "object": 3, "release_id": 2, "year": 1990}),
        _row({"id": 3, "subject": 1, "predicate": 1, "object": 4, "release_id": 3, "year": None}),
    ]
    clause = year_bounds_clause(None, 1970)
    assert clause is not None
    with engine.begin() as connection:
        connection.execute(insert(RuntimeRelationTable), rows)
        statement = select(RuntimeRelationTable.object).where(clause)
        kept = {row.object for row in connection.execute(statement)}
    assert kept == {2, 4}
