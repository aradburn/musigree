"""Unit tests for RuntimeDatabaseHelper table management."""

from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from sqlalchemy.sql.ddl import DropTable

from musigree.runtime.runtime_database.runtime_database_helper import RuntimeDatabaseHelper


class TestRuntimeDatabaseHelperDropTables:
    """Tests for RuntimeDatabaseHelper.drop_tables."""

    @staticmethod
    def _engine_with_connection(mock_conn: AsyncMock) -> MagicMock:
        mock_engine = MagicMock()
        mock_begin_cm = MagicMock()
        mock_begin_cm.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_begin_cm.__aexit__ = AsyncMock(return_value=False)
        mock_engine.begin.return_value = mock_begin_cm
        return mock_engine

    @pytest.mark.asyncio
    @patch("musigree.runtime.runtime_database_manager.RuntimeDatabaseManager")
    async def test_drop_tables_executes_drop_if_exists_in_one_transaction(
        self,
        mock_manager: Mock,
    ) -> None:
        """drop_tables must issue DROP TABLE IF EXISTS once per table in one begin()."""
        mock_conn = AsyncMock()
        mock_engine = self._engine_with_connection(mock_conn)

        mock_helper = MagicMock()
        mock_helper.runtime_async_engine = mock_engine
        mock_manager.runtime_database_helper = mock_helper

        mock_role = Mock()
        mock_role.name = "runtime_role"
        mock_token = Mock()
        mock_token.name = "token"

        with patch(
            "musigree.runtime.runtime_database.runtime_database_helper.RuntimeBase"
        ) as mock_base:
            mock_base.metadata.tables = {"runtime_role": mock_role, "token": mock_token}
            await RuntimeDatabaseHelper.drop_tables(["runtime_role", "token"])

        mock_engine.begin.assert_called_once()
        mock_conn.run_sync.assert_not_called()
        mock_conn.commit.assert_not_called()
        assert mock_conn.execute.await_count == 2

        drop_statements = [call.args[0] for call in mock_conn.execute.await_args_list]
        assert all(isinstance(stmt, DropTable) for stmt in drop_statements)
        assert drop_statements[0].element is mock_role
        assert drop_statements[1].element is mock_token
        assert all(stmt.if_exists is True for stmt in drop_statements)

    @pytest.mark.asyncio
    @patch("musigree.runtime.runtime_database_manager.RuntimeDatabaseManager")
    async def test_drop_tables_requires_helper(self, mock_manager: Mock) -> None:
        """drop_tables fails when the runtime helper is missing."""
        mock_manager.runtime_database_helper = None

        with pytest.raises(
            AssertionError,
            match="runtime_database_helper must be initialized",
        ):
            await RuntimeDatabaseHelper.drop_tables(["runtime_role"])

    @pytest.mark.asyncio
    @patch("musigree.runtime.runtime_database_manager.RuntimeDatabaseManager")
    async def test_drop_tables_requires_engine(self, mock_manager: Mock) -> None:
        """drop_tables fails when the async engine is missing."""
        mock_helper = MagicMock()
        mock_helper.runtime_async_engine = None
        mock_manager.runtime_database_helper = mock_helper

        with pytest.raises(
            AssertionError,
            match="runtime_async_engine must be initialized",
        ):
            await RuntimeDatabaseHelper.drop_tables(["runtime_role"])
