"""Unit tests for SQLite runtime database URL setup."""

import sqlite3
import warnings
from typing import TYPE_CHECKING

import pytest
from sqlalchemy import text
from sqlalchemy.exc import OperationalError, SAWarning

from musigree.config import SqliteReadOnlyTestConfiguration, SqliteTestConfiguration
from musigree.runtime.runtime_database_manager import RuntimeDatabaseManager
from musigree.runtime.sqlite.runtime_sqlite_helper import RuntimeSqliteHelper

if TYPE_CHECKING:
    from pathlib import Path


class TestRuntimeSqliteHelperSetupDatabase:
    """Test RuntimeSqliteHelper.setup_database URL arguments."""

    async def test_read_only_url_applies_sqlite_uri_arguments(self, tmp_path: Path) -> None:
        """Read-only mode must pass mode and immutable through a SQLite URI."""
        database_path = tmp_path / "runtime db.db"
        sqlite3.connect(database_path).close()

        config = SqliteReadOnlyTestConfiguration()
        config.SQLITE_RUNTIME_DATABASE_NAME = database_path
        RuntimeDatabaseManager.threading_model = config.THREADING_MODEL

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            engine = await RuntimeSqliteHelper.setup_database(config)

        try:
            assert not any(issubclass(item.category, SAWarning) for item in caught)
            database = engine.url.database
            assert database is not None
            assert database.startswith("file:")
            assert "%20" in database
            assert engine.url.query["uri"] == "true"
            assert engine.url.query["mode"] == "ro"
            assert engine.url.query["immutable"] == "1"

            async with engine.connect() as connection:
                result = await connection.execute(text("SELECT 1"))
                assert result.scalar_one() == 1
                with pytest.raises(OperationalError):
                    await connection.execute(text("CREATE TABLE blocked (id INTEGER)"))
        finally:
            await engine.dispose()

    async def test_writable_url_has_sqlite_uri_arguments(self, tmp_path: Path) -> None:
        """Writable mode is also a URI."""
        database_path = tmp_path / "runtime.db"
        config = SqliteTestConfiguration()
        config.SQLITE_RUNTIME_DATABASE_NAME = database_path
        RuntimeDatabaseManager.threading_model = config.THREADING_MODEL

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            engine = await RuntimeSqliteHelper.setup_database(config)

        try:
            assert not any(issubclass(item.category, SAWarning) for item in caught)
            assert engine.url.query["uri"] == "true"
            assert engine.url.database == "file:" + str(database_path)
        finally:
            await engine.dispose()
