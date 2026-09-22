"""
Unit tests for the BaseRepository class.

This module contains comprehensive unit tests for the BaseRepository class,
which provides the base offline_database repository functionality for the offline system.
It tests initialization, error handling, and core functionality that can be tested in isolation.
"""

from typing import Any
from unittest.mock import AsyncMock, Mock, patch, PropertyMock

import pytest
from sqlalchemy import Column, Integer, String
from sqlalchemy.engine import Result
from sqlalchemy.exc import IntegrityError, InvalidRequestError

from musigree.exceptions import DatabaseError, NotFoundError
from musigree.offline.offline_database.base_repository import BaseRepository
from musigree.offline.offline_database.base_table import OfflineBase, mapped_entity
from musigree.offline.offline_database.offline_session import OfflineSession


class MockTable(OfflineBase):
    """Mock table class for testing BaseRepository."""

    __tablename__ = "mock_table"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    value = Column(Integer)


# noinspection PyTypeChecker
class ConcreteTestRepository(BaseRepository):
    """Concrete repository used by BaseRepository unit tests."""

    schema_class: Any = mapped_entity(MockTable)


# noinspection PyTypeChecker
class TestBaseRepository:
    """Test class for BaseRepository."""

    def test_mapped_entity_returns_the_same_class(self) -> None:
        """mapped_entity is an identity helper for type checkers."""
        assert mapped_entity(MockTable) is MockTable

    def test_base_repository_init_success(self) -> None:
        """Test successful initialization of BaseRepository."""
        with patch.object(OfflineSession, "_session", new_callable=PropertyMock):
            repo = ConcreteTestRepository()
            assert repo.schema_class == MockTable

    def test_base_repository_init_no_schema_class(self) -> None:
        """Test initialization fails without schema_class."""

        class BadRepository(BaseRepository):
            schema_class = None  # type: ignore[assignment]

        with pytest.raises(
            DatabaseError,
            match="Can not initiate the class without schema_class attribute",
        ):
            BadRepository()

    @patch("musigree.offline.offline_database.offline_session.OfflineSession.execute")
    async def test_count_success(self, mock_execute: AsyncMock) -> None:
        """Test successful count operation."""

        # Setup
        with patch.object(OfflineSession, "_session", new_callable=PropertyMock):
            repo = ConcreteTestRepository()

            mock_result = Mock(spec=Result)
            mock_result.scalar.return_value = 5
            mock_execute.return_value = mock_result

            # Execute
            result = await repo.count()

            # Verify
            assert result == 5
            mock_execute.assert_called_once()
            mock_result.scalar.assert_called_once()

    @patch("musigree.offline.offline_database.offline_session.OfflineSession.execute")
    async def test_count_non_integer_result(self, mock_execute: AsyncMock) -> None:
        """Test count operation with non-integer result."""

        # Setup
        with patch.object(OfflineSession, "_session", new_callable=PropertyMock):
            repo = ConcreteTestRepository()

            mock_result = Mock(spec=Result)
            mock_result.scalar.return_value = "not_an_integer"
            mock_execute.return_value = mock_result

            # Execute & Verify
            with pytest.raises(
                DatabaseError,
                match="Count function returned non integer value",
            ):
                await repo.count()

    async def test_save_success(self) -> None:
        """Test successful save operation with proper mocking."""

        # Mock session and schema creation
        mock_session = Mock()
        mock_session.add = Mock()
        mock_session.flush = AsyncMock()
        mock_session.refresh = AsyncMock()
        mock_table_instance = Mock()

        with patch.object(
            OfflineSession, "_session", new_callable=PropertyMock
        ) as mock_session_prop:
            mock_session_prop.return_value = mock_session

            repo = ConcreteTestRepository()
            payload = {"name": "test", "value": 123}

            # Mock the schema class instantiation
            with patch.object(
                repo, "schema_class", return_value=mock_table_instance
            ) as mock_schema:
                # Execute
                result = await repo._save(payload)

                # Verify
                mock_schema.assert_called_once_with(**payload)
                mock_session.add.assert_called_once_with(mock_table_instance)
                mock_session.flush.assert_called_once()
                mock_session.refresh.assert_called_once_with(mock_table_instance)
                assert result == mock_table_instance

    async def test_save_integrity_error(self) -> None:
        """Test save operation with IntegrityError."""

        mock_session = AsyncMock()

        with patch.object(
            OfflineSession, "_session", new_callable=PropertyMock
        ) as mock_session_prop:
            mock_session_prop.return_value = mock_session

            repo = ConcreteTestRepository()
            payload = {"name": "test"}

            # Mock the schema class to raise IntegrityError during instantiation
            with patch.object(
                repo,
                "schema_class",
                side_effect=IntegrityError("Integrity error", None, Exception("Original error")),
            ):
                # Execute & Verify
                with pytest.raises(DatabaseError):
                    await repo._save(payload)

    async def test_save_invalid_request_error(self) -> None:
        """Test save operation with InvalidRequestError."""

        mock_session = AsyncMock()

        with patch.object(
            OfflineSession, "_session", new_callable=PropertyMock
        ) as mock_session_prop:
            mock_session_prop.return_value = mock_session

            repo = ConcreteTestRepository()
            payload = {"name": "test"}

            # Mock the schema class to raise InvalidRequestError during instantiation
            with patch.object(
                repo, "schema_class", side_effect=InvalidRequestError("Invalid request")
            ):
                # Execute & Verify
                with pytest.raises(DatabaseError):
                    await repo._save(payload)

    async def test_save_all_success(self) -> None:
        """Test successful save_all operation."""

        mock_session = AsyncMock()

        with patch.object(
            OfflineSession, "_session", new_callable=PropertyMock
        ) as mock_session_prop:
            mock_session_prop.return_value = mock_session

            repo = ConcreteTestRepository()
            payloads = [{"name": "test1"}, {"name": "test2"}]

            # Execute
            await repo.save_all(payloads)

            # Verify
            mock_session.execute.assert_called_once()

    async def test_save_all_integrity_error(self) -> None:
        """Test save_all operation with IntegrityError."""

        mock_session = AsyncMock()

        with patch.object(
            OfflineSession, "_session", new_callable=PropertyMock
        ) as mock_session_prop:
            mock_session_prop.return_value = mock_session

            repo = ConcreteTestRepository()
            payloads = [{"name": "test1"}, {"name": "test2"}]

            # Mock the execute method to raise IntegrityError
            mock_session.execute.side_effect = IntegrityError(
                "Integrity error", None, Exception("Original error")
            )
            # Execute & Verify
            with pytest.raises(DatabaseError):
                await repo.save_all(payloads)

    async def test_commit(self) -> None:
        """Test commit operation."""

        mock_session = AsyncMock()

        with patch.object(
            OfflineSession, "_session", new_callable=PropertyMock
        ) as mock_session_prop:
            mock_session_prop.return_value = mock_session

            repo = ConcreteTestRepository()

            # Execute
            await repo.commit()

            # Verify
            mock_session.commit.assert_called_once()

    async def test_rollback(self) -> None:
        """Test rollback operation."""

        mock_session = AsyncMock()

        with patch.object(
            OfflineSession, "_session", new_callable=PropertyMock
        ) as mock_session_prop:
            mock_session_prop.return_value = mock_session

            repo = ConcreteTestRepository()

            # Execute
            await repo.rollback()

            # Verify
            mock_session.rollback.assert_called_once()

    @patch("musigree.offline.offline_database.offline_session.OfflineSession.execute")
    async def test_update_integrity_error_during_execute(self, mock_execute: AsyncMock) -> None:
        """Test update operation with IntegrityError during execution."""

        # Setup
        with patch.object(OfflineSession, "_session", new_callable=PropertyMock):
            repo = ConcreteTestRepository()
            mock_execute.side_effect = IntegrityError(
                "Integrity error", None, Exception("Original error")
            )

            # Execute & Verify
            with pytest.raises(DatabaseError):
                await repo._update("id", 1, {"name": "updated"})

    @patch("musigree.offline.offline_database.offline_session.OfflineSession.execute")
    async def test_update_invalid_request_error_during_execute(
        self, mock_execute: AsyncMock
    ) -> None:
        """Test update operation with InvalidRequestError during execution."""

        # Setup
        with patch.object(OfflineSession, "_session", new_callable=PropertyMock):
            repo = ConcreteTestRepository()
            mock_execute.side_effect = InvalidRequestError("Invalid request")

            # Execute & Verify
            with pytest.raises(DatabaseError):
                await repo._update("id", 1, {"name": "updated"})

    @patch("musigree.offline.offline_database.offline_session.OfflineSession.execute")
    async def test_update_no_result(self, mock_execute: AsyncMock) -> None:
        """Test update operation when no record is found."""

        # Setup
        with patch.object(OfflineSession, "_session", new_callable=PropertyMock):
            repo = ConcreteTestRepository()

            mock_result = Mock(spec=Result)
            mock_result.scalar_one_or_none.return_value = None
            mock_execute.return_value = mock_result

            # Execute & Verify
            with pytest.raises(DatabaseError):
                await repo._update("id", 1, {"name": "updated"})

    @patch("musigree.offline.offline_database.offline_session.OfflineSession.execute")
    async def test_get_not_found(self, mock_execute: AsyncMock) -> None:
        """Test get operation when record is not found."""

        # Setup
        with patch.object(OfflineSession, "_session", new_callable=PropertyMock):
            repo = ConcreteTestRepository()

            mock_result = Mock(spec=Result)
            mock_scalars = Mock()
            mock_scalars.one_or_none.return_value = None
            mock_result.scalars.return_value = mock_scalars
            mock_execute.return_value = mock_result

            # Execute & Verify
            with pytest.raises(NotFoundError):
                await repo._get("id", 1)
