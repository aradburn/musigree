"""
Unit tests for the TokenRepository class.

This module tests the TokenRepository class which manages Token objects
in the offline database.
"""

from typing import Any, AsyncGenerator
from unittest.mock import AsyncMock, Mock, patch

import pytest
from sqlalchemy.engine import Result

from musigree.config import SqliteTestConfiguration
from musigree.exceptions import DatabaseError
from musigree.offline.offline_database.token_repository import TokenRepository
from musigree.offline.offline_database.token_table import TokenTable
from musigree.offline.offline_domain.token import Token


class TestTokenRepository:
    """Test class for TokenRepository."""

    @pytest.fixture(autouse=True)
    def setup_config(self) -> None:
        """Set up test configuration."""
        self.config = SqliteTestConfiguration()

    @pytest.fixture
    def mock_token(self) -> Token:
        """Create a mock token for testing."""
        return Token(token="test_token", entity_id=12345)

    @pytest.fixture
    def mock_token_table(self) -> TokenTable:
        """Create a mock token table record."""
        table_mock = Mock(spec=TokenTable)
        table_mock.token = "test_token"
        table_mock.entity_id = 12345
        return table_mock

    @pytest.fixture
    def token_repository(self) -> TokenRepository:
        """Create a TokenRepository instance for testing."""
        return TokenRepository()

    @pytest.mark.asyncio
    async def test_all_success(
        self,
        token_repository: TokenRepository,
        mock_token_table: TokenTable,
        mock_token: Token,
    ) -> None:
        """Test successful all() method execution."""
        async def mock_iterator() -> AsyncGenerator[TokenTable, Any]:
            yield mock_token_table

        with patch.object(token_repository, "_all", return_value=mock_iterator()):
            with patch.object(Token, "model_validate", return_value=mock_token):
                results = []
                async for t in token_repository.all():
                    results.append(t)
                assert len(results) == 1
                assert results[0] == mock_token

    @pytest.mark.asyncio
    async def test_count_success(self, token_repository: TokenRepository) -> None:
        """Test count returns integer."""
        with patch.object(token_repository, "execute", AsyncMock()) as mock_execute:
            mock_result = Mock(spec=Result)
            mock_result.scalar.return_value = 42
            mock_execute.return_value = mock_result
            result = await token_repository.count()
            assert result == 42

    @pytest.mark.asyncio
    async def test_count_non_integer_raises(self, token_repository: TokenRepository) -> None:
        """Test count raises DatabaseError when result is not integer."""
        with patch.object(token_repository, "execute", AsyncMock()) as mock_execute:
            mock_result = Mock(spec=Result)
            mock_result.scalar.return_value = "not_an_int"
            mock_execute.return_value = mock_result
            with pytest.raises(DatabaseError, match="non integer value"):
                await token_repository.count()

    @pytest.mark.asyncio
    async def test_get_by_token_success(self, token_repository: TokenRepository) -> None:
        """Test get_by_token returns list of entity ids."""
        with patch.object(token_repository, "execute", AsyncMock()) as mock_execute:
            mock_result = Mock(spec=Result)
            mock_result.scalars.return_value.all.return_value = [100, 200]
            mock_execute.return_value = mock_result
            result = await token_repository.get_by_token("some_token")
            assert result == [100, 200]

    @pytest.mark.asyncio
    async def test_get_random_id_returns_id(self, token_repository: TokenRepository) -> None:
        """Test get_random_id returns entity id when count > 0."""
        with patch.object(token_repository, "count", AsyncMock(return_value=10)):
            with patch.object(token_repository, "execute", AsyncMock()) as mock_execute:
                mock_result = Mock(spec=Result)
                mock_result.scalar_one_or_none.return_value = 999
                mock_execute.return_value = mock_result
                with patch("musigree.offline.offline_database.token_repository.random") as mock_random:
                    mock_random.randint.return_value = 5
                    result = await token_repository.get_random_id()
                    assert result == 999

    @pytest.mark.asyncio
    async def test_create_success(
        self,
        token_repository: TokenRepository,
        mock_token: Token,
        mock_token_table: TokenTable,
    ) -> None:
        """Test successful create execution."""
        with patch.object(
            token_repository, "_save", AsyncMock(return_value=mock_token_table)
        ):
            with patch.object(Token, "model_validate", return_value=mock_token):
                result = await token_repository.create(mock_token)
                assert result == mock_token

    def test_schema_class_is_set(self, token_repository: TokenRepository) -> None:
        """Test that schema_class is properly set."""
        assert token_repository.schema_class == TokenTable
