"""
Unit tests for the RoleRepository class.

This module tests the RoleRepository class which manages Role objects
in the offline runtime_database.
"""

from typing import Any, AsyncGenerator
from unittest.mock import Mock, patch

import pytest
from sqlalchemy import Result

from musigree.config import SqliteTestConfiguration
from musigree.exceptions import NotFoundError
from musigree.library.fields.role_type import RoleType
from musigree.offline.offline_database.role_repository import RoleRepository
from musigree.offline.offline_database.role_table import RoleTable
from musigree.offline.offline_domain.role import Role, RoleUncommitted


class TestRoleRepository:
    """Test class for RoleRepository."""

    @pytest.fixture(autouse=True)
    def setup_config(self) -> None:
        """Set up test configuration."""
        self.config = SqliteTestConfiguration()

    @pytest.fixture
    def mock_role(self) -> Role:
        """Create a mock role for testing."""
        return Role(
            id=1,
            role_name="performer",
            role_category=RoleType.Category.INSTRUMENTS,
            role_subcategory=RoleType.Subcategory.NONE,
            role_category_name="Instruments",
            role_subcategory_name="None",
        )

    @pytest.fixture
    def mock_role_uncommitted(self) -> RoleUncommitted:
        """Create a mock uncommitted role for testing."""
        return RoleUncommitted(
            role_name="composer",
            role_category=RoleType.Category.WRITING_AND_ARRANGEMENT,
            role_subcategory=RoleType.Subcategory.NONE,
            role_category_name="Writing & Arrangement",
            role_subcategory_name="None",
        )

    @pytest.fixture
    def mock_role_table(self) -> RoleTable:
        """Create a mock role table record."""
        table_mock = Mock(spec=RoleTable)
        table_mock.id = 1
        table_mock.role_name = "performer"
        table_mock.role_description = "A performing artist"
        return table_mock

    @pytest.fixture
    def role_repository(self) -> RoleRepository:
        """Create a RoleRepository instance for testing."""
        return RoleRepository()

    @pytest.mark.asyncio
    async def test_all_success(
        self,
        role_repository: RoleRepository,
        mock_role_table: RoleTable,
        mock_role: Role,
    ) -> None:
        """Test successful all() method execution."""
        # Arrange
        with patch.object(role_repository, "_all") as mock_all:
            async def mock_async_iterator() -> AsyncGenerator[RoleTable, Any]:
                yield mock_role_table

            mock_all.return_value = mock_async_iterator()

            with patch.object(Role, "model_validate") as mock_validate:
                mock_validate.return_value = mock_role

                # Act
                results = []
                async for role in role_repository.all():
                    results.append(role)

                # Assert
                assert len(results) == 1
                assert results[0] == mock_role
                mock_validate.assert_called_once_with(mock_role_table)

    @pytest.mark.asyncio
    async def test_get_by_id_success(
        self,
        role_repository: RoleRepository,
        mock_role_table: RoleTable,
        mock_role: Role,
    ) -> None:
        """Test successful get_by_id execution."""
        # Arrange
        role_id = 1

        with patch.object(role_repository, "execute") as mock_execute:
            mock_result = Mock(spec=Result)
            mock_result.scalars.return_value.one_or_none.return_value = mock_role_table
            mock_execute.return_value = mock_result

            with patch.object(Role, "model_validate") as mock_validate:
                mock_validate.return_value = mock_role

                # Act
                result = await role_repository.get_by_id(role_id)

                # Assert
                assert result == mock_role
                mock_execute.assert_called_once()
                mock_validate.assert_called_once_with(mock_role_table)

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, role_repository: RoleRepository) -> None:
        """Test get_by_id when role is not found."""
        # Arrange
        role_id = 999

        with patch.object(role_repository, "execute") as mock_execute:
            mock_result = Mock(spec=Result)
            mock_result.scalars.return_value.one_or_none.return_value = None
            mock_execute.return_value = mock_result

            # Act & Assert
            with pytest.raises(NotFoundError):
                await role_repository.get_by_id(role_id)

    @pytest.mark.asyncio
    async def test_create_success(
        self,
        role_repository: RoleRepository,
        mock_role_uncommitted: RoleUncommitted,
        mock_role_table: RoleTable,
        mock_role: Role,
    ) -> None:
        """Test successful create execution."""
        # Arrange
        with patch.object(role_repository, "_save") as mock_save:
            mock_save.return_value = mock_role_table

            with patch.object(Role, "model_validate") as mock_validate:
                mock_validate.return_value = mock_role

                # Act
                result = await role_repository.create(mock_role_uncommitted)

                # Assert
                assert result == mock_role
                mock_save.assert_called_once()
                mock_validate.assert_called_once_with(mock_role_table)

    def test_schema_class_is_set(self, role_repository: RoleRepository) -> None:
        """Test that schema_class is properly set."""
        assert role_repository.schema_class == RoleTable

    def test_repository_initialization_success(self) -> None:
        """Test successful repository initialization."""
        repo = RoleRepository()
        assert repo.schema_class == RoleTable

    @pytest.mark.asyncio
    async def test_all_empty_result(self, role_repository: RoleRepository) -> None:
        """Test all() method with empty result."""
        # Arrange
        with patch.object(role_repository, "_all") as mock_all:
            # noinspection PyUnreachableCode
            async def empty_async_iterator() -> AsyncGenerator[None, Any]:
                return
                yield  # This yield will never be reached, creating an empty iterator

            mock_all.return_value = empty_async_iterator()

            # Act
            results = []
            async for role in role_repository.all():
                results.append(role)

            # Assert
            assert len(results) == 0
