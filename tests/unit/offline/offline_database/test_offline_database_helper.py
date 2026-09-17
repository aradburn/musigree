"""Unit tests for OfflineDatabaseHelper table creation helpers."""

from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from sqlalchemy.engine import Connection
from sqlalchemy.sql.ddl import DropTable

# noinspection protected-member
from musigree.offline.offline_database.offline_database_helper import (
    OfflineDatabaseHelper,
    _create_all_tables,
)


class TestCreateAllTablesAdapter:
    """Tests for the run_sync adapter around MetaData.create_all."""

    def test_create_all_tables_passes_connection_as_bind(self) -> None:
        """The adapter must bind create_all to a sync Connection."""
        connection = Mock(spec=Connection)
        tables = [Mock()]

        with patch(
            "musigree.offline.offline_database.offline_database_helper.OfflineBase"
        ) as mock_base:
            _create_all_tables(connection, tables=tables, checkfirst=True)

        mock_base.metadata.create_all.assert_called_once_with(
            bind=connection,
            tables=tables,
            checkfirst=True,
        )

    def test_create_all_tables_defaults_checkfirst(self) -> None:
        """checkfirst defaults to True to skip existing tables."""
        connection = Mock(spec=Connection)

        with patch(
            "musigree.offline.offline_database.offline_database_helper.OfflineBase"
        ) as mock_base:
            _create_all_tables(connection)

        mock_base.metadata.create_all.assert_called_once_with(
            bind=connection,
            tables=None,
            checkfirst=True,
        )


class TestOfflineDatabaseHelperCreateTables:
    """Tests for OfflineDatabaseHelper.create_tables."""

    @pytest.mark.asyncio
    @patch("musigree.offline.offline_database_manager.OfflineDatabaseManager")
    async def test_create_tables_passes_connection_adapter_to_run_sync(
        self,
        mock_manager: Mock,
    ) -> None:
        """create_tables must use the Connection adapter, not metadata.create_all."""
        mock_conn = AsyncMock()
        mock_engine = MagicMock()
        mock_begin_cm = MagicMock()
        mock_begin_cm.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_begin_cm.__aexit__ = AsyncMock(return_value=False)
        mock_engine.begin.return_value = mock_begin_cm

        mock_helper = MagicMock()
        mock_helper.offline_async_engine = mock_engine
        mock_manager.offline_database_helper = mock_helper

        mock_table = Mock()
        mock_table.name = "role"

        with patch(
            "musigree.offline.offline_database.offline_database_helper.OfflineBase"
        ) as mock_base:
            mock_base.metadata.tables = {"role": mock_table}
            await OfflineDatabaseHelper.create_tables(["role"])

        mock_conn.run_sync.assert_awaited_once_with(
            _create_all_tables,
            tables=[mock_table],
            checkfirst=True,
        )

    @pytest.mark.asyncio
    @patch("musigree.offline.offline_database_manager.OfflineDatabaseManager")
    async def test_create_tables_requires_helper(self, mock_manager: Mock) -> None:
        """create_tables fails when the offline helper is missing."""
        mock_manager.offline_database_helper = None

        with pytest.raises(
            AssertionError,
            match="offline_database_helper must be initialized",
        ):
            await OfflineDatabaseHelper.create_tables(["role"])

    @pytest.mark.asyncio
    @patch("musigree.offline.offline_database_manager.OfflineDatabaseManager")
    async def test_create_tables_requires_engine(self, mock_manager: Mock) -> None:
        """create_tables fails when the async engine is missing."""
        mock_helper = MagicMock()
        mock_helper.offline_async_engine = None
        mock_manager.offline_database_helper = mock_helper

        with pytest.raises(
            AssertionError,
            match="offline_async_engine must be initialized",
        ):
            await OfflineDatabaseHelper.create_tables(["role"])


class TestOfflineDatabaseHelperDropTables:
    """Tests for OfflineDatabaseHelper.drop_tables."""

    @staticmethod
    def _engine_with_connection(mock_conn: AsyncMock) -> MagicMock:
        mock_engine = MagicMock()
        mock_begin_cm = MagicMock()
        mock_begin_cm.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_begin_cm.__aexit__ = AsyncMock(return_value=False)
        mock_engine.begin.return_value = mock_begin_cm
        return mock_engine

    @pytest.mark.asyncio
    @patch("musigree.offline.offline_database_manager.OfflineDatabaseManager")
    async def test_drop_tables_executes_drop_if_exists_in_one_transaction(
        self,
        mock_manager: Mock,
    ) -> None:
        """drop_tables must issue DROP TABLE IF EXISTS once per table in one begin()."""
        mock_conn = AsyncMock()
        mock_engine = self._engine_with_connection(mock_conn)

        mock_helper = MagicMock()
        mock_helper.offline_async_engine = mock_engine
        mock_manager.offline_database_helper = mock_helper

        mock_role = Mock()
        mock_role.name = "role"
        mock_token = Mock()
        mock_token.name = "token"

        with patch(
            "musigree.offline.offline_database.offline_database_helper.OfflineBase"
        ) as mock_base:
            mock_base.metadata.tables = {"role": mock_role, "token": mock_token}
            await OfflineDatabaseHelper.drop_tables(["role", "token"])

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
    @patch("musigree.offline.offline_database_manager.OfflineDatabaseManager")
    async def test_drop_tables_requires_helper(self, mock_manager: Mock) -> None:
        """drop_tables fails when the offline helper is missing."""
        mock_manager.offline_database_helper = None

        with pytest.raises(
            AssertionError,
            match="offline_database_helper must be initialized",
        ):
            await OfflineDatabaseHelper.drop_tables(["role"])

    @pytest.mark.asyncio
    @patch("musigree.offline.offline_database_manager.OfflineDatabaseManager")
    async def test_drop_tables_requires_engine(self, mock_manager: Mock) -> None:
        """drop_tables fails when the async engine is missing."""
        mock_helper = MagicMock()
        mock_helper.offline_async_engine = None
        mock_manager.offline_database_helper = mock_helper

        with pytest.raises(
            AssertionError,
            match="offline_async_engine must be initialized",
        ):
            await OfflineDatabaseHelper.drop_tables(["role"])
