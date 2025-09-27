"""
Unit tests for the runtime_transaction module.

This module contains comprehensive unit tests for the runtime_transaction context manager,
which provides transaction management functionality for database operations in the runtime system.
It tests successful transactions, error handling, rollback scenarios, and session management.
"""
from unittest.mock import AsyncMock, Mock, patch

import pytest
from sqlalchemy.exc import IntegrityError, InvalidRequestError
from sqlalchemy.ext.asyncio import AsyncSession

from musigree.exceptions import DatabaseError
from musigree.runtime.runtime_database.runtime_transaction import runtime_transaction


class TestRuntimeTransaction:
    """Test class for runtime_transaction context manager."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        """Fixture for mock async session."""
        session = AsyncMock(spec=AsyncSession)
        return session

    @patch("musigree.runtime.runtime_database.runtime_transaction.get_runtime_session")
    @patch("musigree.runtime.runtime_database.runtime_transaction.CTX_RUNTIME_SESSION")
    async def test_runtime_transaction_success(
        self, mock_ctx: Mock, mock_get_session: AsyncMock, mock_session: AsyncMock
    ) -> None:
        """Test successful runtime transaction with commit."""
        # Setup
        mock_get_session.return_value = mock_session
        mock_ctx.set.return_value = "old_token"

        # Execute
        async with runtime_transaction() as session:
            assert session is mock_session
            # Simulate some database operations
            pass

        # Verify
        mock_get_session.assert_called_once()
        mock_ctx.set.assert_called_once_with(mock_session)
        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()
        mock_ctx.reset.assert_called_once_with("old_token")
        mock_session.rollback.assert_not_called()

    @patch("musigree.runtime.runtime_database.runtime_transaction.get_runtime_session")
    @patch("musigree.runtime.runtime_database.runtime_transaction.CTX_RUNTIME_SESSION")
    async def test_runtime_transaction_database_error(
        self,
        mock_ctx: Mock,
        mock_get_session: AsyncMock,
        mock_session: AsyncMock,
    ) -> None:
        """Test runtime transaction with DatabaseError handling."""
        # Setup
        mock_get_session.return_value = mock_session
        mock_ctx.set.return_value = "old_token"
        test_error = DatabaseError(message="Test database error")

        # Execute & Verify
        with pytest.raises(DatabaseError, match="Test database error"):
            async with runtime_transaction() as session:
                assert session is mock_session
                raise test_error

        # Verify
        mock_get_session.assert_called_once()
        mock_ctx.set.assert_called_once_with(mock_session)
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()
        mock_ctx.reset.assert_called_once_with("old_token")
        mock_session.commit.assert_not_called()

    # noinspection PyUnreachableCode
    @patch("musigree.runtime.runtime_database.runtime_transaction.get_runtime_session")
    @patch("musigree.runtime.runtime_database.runtime_transaction.CTX_RUNTIME_SESSION")
    async def test_runtime_transaction_integrity_error(
        self,
        mock_ctx: Mock,
        mock_get_session: AsyncMock,
        mock_session: AsyncMock,
    ) -> None:
        """Test runtime transaction with IntegrityError handling."""
        # Setup
        mock_get_session.return_value = mock_session
        mock_ctx.set.return_value = "old_token"
        test_error = IntegrityError(
            "Test integrity error", None, Exception("Original error")
        )

        # Execute
        async with runtime_transaction() as session:
            assert session is mock_session
            raise test_error

        # Verify
        mock_get_session.assert_called_once()
        mock_ctx.set.assert_called_once_with(mock_session)
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()
        mock_ctx.reset.assert_called_once_with("old_token")
        mock_session.commit.assert_not_called()

    # noinspection PyUnreachableCode
    @patch("musigree.runtime.runtime_database.runtime_transaction.get_runtime_session")
    @patch("musigree.runtime.runtime_database.runtime_transaction.CTX_RUNTIME_SESSION")
    async def test_runtime_transaction_invalid_request_error(
        self,
        mock_ctx: Mock,
        mock_get_session: AsyncMock,
        mock_session: AsyncMock,
    ) -> None:
        """Test runtime transaction with InvalidRequestError handling."""
        # Setup
        mock_get_session.return_value = mock_session
        mock_ctx.set.return_value = "old_token"
        test_error = InvalidRequestError("Test invalid request error")

        # Execute
        async with runtime_transaction() as session:
            assert session is mock_session
            raise test_error

        # Verify
        mock_get_session.assert_called_once()
        mock_ctx.set.assert_called_once_with(mock_session)
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()
        mock_ctx.reset.assert_called_once_with("old_token")
        mock_session.commit.assert_not_called()

    @patch("musigree.runtime.runtime_database.runtime_transaction.get_runtime_session")
    @patch("musigree.runtime.runtime_database.runtime_transaction.CTX_RUNTIME_SESSION")
    async def test_runtime_transaction_commit_error(
        self,
        mock_ctx: Mock,
        mock_get_session: AsyncMock,
        mock_session: AsyncMock,
    ) -> None:
        """Test runtime transaction when commit raises an error."""
        # Setup
        mock_get_session.return_value = mock_session
        mock_ctx.set.return_value = "old_token"
        test_error = IntegrityError("Commit error", None, Exception("Original error"))
        mock_session.commit.side_effect = test_error

        # Execute
        async with runtime_transaction() as session:
            assert session is mock_session
            # No exceptions raised in the block
            pass

        # Verify
        mock_get_session.assert_called_once()
        mock_ctx.set.assert_called_once_with(mock_session)
        mock_session.commit.assert_called_once()
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()
        mock_ctx.reset.assert_called_once_with("old_token")

    @patch("musigree.runtime.runtime_database.runtime_transaction.get_runtime_session")
    @patch("musigree.runtime.runtime_database.runtime_transaction.CTX_RUNTIME_SESSION")
    async def test_runtime_transaction_generic_exception(
        self, mock_ctx: Mock, mock_get_session: AsyncMock, mock_session: AsyncMock
    ) -> None:
        """Test runtime transaction with generic exception (not handled)."""
        # Setup
        mock_get_session.return_value = mock_session
        mock_ctx.set.return_value = "old_token"
        test_error = ValueError("Generic error")

        # Execute & Verify
        with pytest.raises(ValueError, match="Generic error"):
            async with runtime_transaction() as session:
                assert session is mock_session
                raise test_error

        # Verify - generic exceptions should not trigger rollback in catch
        mock_get_session.assert_called_once()
        mock_ctx.set.assert_called_once_with(mock_session)
        mock_session.close.assert_called_once()
        mock_ctx.reset.assert_called_once_with("old_token")
        mock_session.commit.assert_not_called()
        mock_session.rollback.assert_not_called()

    @patch("musigree.runtime.runtime_database.runtime_transaction.get_runtime_session")
    @patch("musigree.runtime.runtime_database.runtime_transaction.CTX_RUNTIME_SESSION")
    async def test_runtime_transaction_context_management(
        self, mock_ctx: Mock, mock_get_session: AsyncMock, mock_session: AsyncMock
    ) -> None:
        """Test that context management works correctly."""
        # Setup
        mock_get_session.return_value = mock_session
        old_token = "test_old_token"
        mock_ctx.set.return_value = old_token

        # Execute
        async with runtime_transaction() as session:
            # Verify that session is properly set
            assert session is mock_session
            # Verify context is set
            mock_ctx.set.assert_called_once_with(mock_session)

        # Verify context is properly reset after exiting
        mock_ctx.reset.assert_called_once_with(old_token)

    @patch("musigree.runtime.runtime_database.runtime_transaction.get_runtime_session")
    @patch("musigree.runtime.runtime_database.runtime_transaction.CTX_RUNTIME_SESSION")
    async def test_runtime_transaction_session_close_always_called(
        self, mock_ctx: Mock, mock_get_session: AsyncMock, mock_session: AsyncMock
    ) -> None:
        """Test that session.close() is always called, even with errors."""
        # Setup
        mock_get_session.return_value = mock_session
        mock_ctx.set.return_value = "old_token"
        test_error = RuntimeError("Test error")

        # Execute & Verify
        with pytest.raises(RuntimeError, match="Test error"):
            async with runtime_transaction() as _session:
                raise test_error

        # Verify session is always closed
        mock_session.close.assert_called_once()
        mock_ctx.reset.assert_called_once_with("old_token")

    async def test_runtime_transaction_return_type(self) -> None:
        """Test that runtime_transaction returns the correct type."""
        # This test verifies the function signature and return type
        transaction_generator = runtime_transaction()
        assert hasattr(transaction_generator, "__aenter__")
        assert hasattr(transaction_generator, "__aexit__")

        # The context manager doesn't need explicit cleanup
