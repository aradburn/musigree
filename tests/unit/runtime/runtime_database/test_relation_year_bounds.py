"""Year-bounds filtering keeps undated rows and drops years outside the range."""

from sqlalchemy import create_engine, insert, select

from musigree.runtime.runtime_database.runtime_relation_repository import (
    year_bounds_clause,
)
from musigree.runtime.runtime_database.runtime_relation_table import RuntimeRelationTable


def test_year_bounds_clause_keeps_in_range_and_null_years() -> None:
    """Rows inside the range and rows with no year stay. Other years are dropped."""
    engine = create_engine("sqlite://")
    RuntimeRelationTable.__table__.create(engine)
    rows = [
        {"id": 1, "subject": 1, "predicate": 1, "object": 2, "release_id": 1, "year": 1960},
        {"id": 2, "subject": 1, "predicate": 1, "object": 3, "release_id": 2, "year": 1975},
        {"id": 3, "subject": 1, "predicate": 1, "object": 4, "release_id": 3, "year": 1990},
        {"id": 4, "subject": 1, "predicate": 1, "object": 5, "release_id": 4, "year": None},
    ]
    with engine.begin() as connection:
        connection.execute(insert(RuntimeRelationTable), rows)
        statement = select(RuntimeRelationTable.object).where(year_bounds_clause(1970, 1979))
        kept = {row.object for row in connection.execute(statement)}
    assert kept == {3, 5}


def test_year_bounds_clause_honours_an_open_lower_bound() -> None:
    """Only max_year drops years above the bound and keeps undated rows."""
    engine = create_engine("sqlite://")
    RuntimeRelationTable.__table__.create(engine)
    rows = [
        {"id": 1, "subject": 1, "predicate": 1, "object": 2, "release_id": 1, "year": 1960},
        {"id": 2, "subject": 1, "predicate": 1, "object": 3, "release_id": 2, "year": 1990},
        {"id": 3, "subject": 1, "predicate": 1, "object": 4, "release_id": 3, "year": None},
    ]
    with engine.begin() as connection:
        connection.execute(insert(RuntimeRelationTable), rows)
        statement = select(RuntimeRelationTable.object).where(year_bounds_clause(None, 1970))
        kept = {row.object for row in connection.execute(statement)}
    assert kept == {2, 4}
