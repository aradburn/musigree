"""
Unit tests for the offline_session module.

This module contains comprehensive unit tests for the offline session management,
including session creation, context variable management, and the OfflineSession class.
"""

from contextvars import ContextVar
from unittest.mock import AsyncMock, Mock, patch

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, InvalidRequestError
from sqlalchemy.ext.asyncio import AsyncSession

from musigree.exceptions import DatabaseError
from musigree.offline.offline_database.offline_session import (
    get_offline_session,
    OfflineSession,
    CTX_OFFLINE_SESSION,
)


class TestGetOfflineSession:
    """Test class for get_offline_session function."""

    @patch("musigree.offline.offline_database_manager.OfflineDatabaseManager")
    async def test_get_offline_session_success(self, mock_manager: Mock) -> None:
        """Test successful offline session creation."""
        # Setup
        mock_helper = Mock()
        mock_session_factory = Mock()
        mock_session = AsyncMock(spec=AsyncSession)
        mock_engine = Mock()

        mock_manager.offline_database_helper = mock_helper
        mock_helper.offline_async_session_factory = mock_session_factory
        mock_helper.offline_async_engine = mock_engine
        mock_session_factory.return_value = mock_session

        # Execute
        result = await get_offline_session()

        # Verify
        assert result is mock_session
        mock_session_factory.assert_called_once()

    @patch("musigree.offline.offline_database_manager.OfflineDatabaseManager")
    async def test_get_offline_session_no_helper(self, mock_manager: Mock) -> None:
        """Test get_offline_session fails when helper is not initialized."""
        # Setup
        mock_manager.offline_database_helper = None

        # Execute & Verify
        with pytest.raises(
            AssertionError,
            match="OfflineDatabaseManager.offline_database_helper must be initialized",
        ):
            await get_offline_session()

    @patch("musigree.offline.offline_database_manager.OfflineDatabaseManager")
    async def test_get_offline_session_no_session_factory(self, mock_manager: Mock) -> None:
        """Test get_offline_session fails when session factory is not initialized."""
        # Setup
        mock_helper = Mock()
        mock_manager.offline_database_helper = mock_helper
        mock_helper.offline_async_session_factory = None

        # Execute & Verify
        with pytest.raises(
            AssertionError, match="offline_async_session_factory must be initialized"
        ):
            await get_offline_session()

    @patch("musigree.offline.offline_database_manager.OfflineDatabaseManager")
    async def test_get_offline_session_no_engine(self, mock_manager: Mock) -> None:
        """Test get_offline_session fails when engine is not initialized."""
        # Setup
        mock_helper = Mock()
        mock_session_factory = Mock()
        mock_manager.offline_database_helper = mock_helper
        mock_helper.offline_async_session_factory = mock_session_factory
        mock_helper.offline_async_engine = None

        # Execute & Verify
        with pytest.raises(AssertionError, match="offline_async_engine must be initialized"):
            await get_offline_session()


class TestOfflineSession:
    """Test class for OfflineSession."""

    @pytest.fixture
    def offline_session(self) -> OfflineSession:
        """Fixture for creating OfflineSession instance."""
        return OfflineSession()

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        """Fixture for mock async session."""
        return AsyncMock(spec=AsyncSession)

    @patch("musigree.offline.offline_database.offline_session.CTX_OFFLINE_SESSION")
    async def test_execute_success(
        self, mock_ctx: Mock, offline_session: OfflineSession, mock_session: AsyncMock
    ) -> None:
        """Test successful query execution."""
        # Setup
        query = text("SELECT 1")
        mock_result = Mock()
        mock_session.execute.return_value = mock_result
        mock_ctx.get.return_value = mock_session

        # Execute
        result = await offline_session.execute(query)

        # Verify
        assert result is mock_result
        mock_session.execute.assert_called_once_with(query)
        mock_ctx.get.assert_called_once()

    @patch("musigree.offline.offline_database.offline_session.CTX_OFFLINE_SESSION")
    async def test_execute_integrity_error(
        self, mock_ctx: Mock, offline_session: OfflineSession, mock_session: AsyncMock
    ) -> None:
        """Test execute with IntegrityError."""
        # Setup
        query = text("SELECT 1")
        mock_session.execute.side_effect = IntegrityError("message", {}, Exception("orig"))
        mock_ctx.get.return_value = mock_session

        # Execute & Verify
        with pytest.raises(DatabaseError):
            await offline_session.execute(query)

    @patch("musigree.offline.offline_database.offline_session.CTX_OFFLINE_SESSION")
    async def test_execute_invalid_request_error(
        self, mock_ctx: Mock, offline_session: OfflineSession, mock_session: AsyncMock
    ) -> None:
        """Test execute with InvalidRequestError."""
        # Setup
        query = text("SELECT 1")
        mock_session.execute.side_effect = InvalidRequestError("Invalid request")
        mock_ctx.get.return_value = mock_session

        # Execute & Verify
        with pytest.raises(DatabaseError):
            await offline_session.execute(query)

    @patch("musigree.offline.offline_database.offline_session.CTX_OFFLINE_SESSION")
    def test_session_property_success(
        self, mock_ctx: Mock, offline_session: OfflineSession, mock_session: AsyncMock
    ) -> None:
        """Test successful session property access."""
        mock_ctx.get.return_value = mock_session

        # Execute
        result = offline_session._session

        # Verify
        assert result is mock_session
        mock_ctx.get.assert_called_once()

    @patch("musigree.offline.offline_database.offline_session.CTX_OFFLINE_SESSION")
    def test_session_property_no_context(
        self, mock_ctx: Mock, offline_session: OfflineSession
    ) -> None:
        """Test session property when no context is available."""
        mock_ctx.get.side_effect = LookupError()

        # Execute & Verify
        with pytest.raises(DatabaseError, match="Not in a transaction"):
            _ = offline_session._session


class TestContextVariables:
    """Test class for context variable functionality."""

    def test_ctx_offline_session_type(self) -> None:
        """Test that CTX_OFFLINE_SESSION is properly typed."""
        assert isinstance(CTX_OFFLINE_SESSION, ContextVar)
        assert CTX_OFFLINE_SESSION.name == "offline_session"

    def test_ctx_offline_session_set_get(self) -> None:
        """Test setting and getting context variable."""
        mock_session = Mock(spec=AsyncSession)

        # Set context
        token = CTX_OFFLINE_SESSION.set(mock_session)

        try:
            # Get context
            result = CTX_OFFLINE_SESSION.get()
            assert result is mock_session
        finally:
            # Clean up
            CTX_OFFLINE_SESSION.reset(token)

    def test_ctx_offline_session_no_value(self) -> None:
        """Test getting context variable when no value is set."""
        with pytest.raises(LookupError):
            CTX_OFFLINE_SESSION.get()
