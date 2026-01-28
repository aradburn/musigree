from typing import AsyncGenerator
from unittest.mock import Mock, patch

import pytest
from sqlalchemy import Result

from musigree.exceptions import NotFoundError
from musigree.runtime.runtime_database.runtime_style_repository import RuntimeStyleRepository
from musigree.runtime.runtime_database.runtime_style_table import RuntimeStyleTable
from musigree.runtime.runtime_domain.runtime_style import RuntimeStyle


class TestRuntimeStyleRepository:
    """Unit tests for RuntimeStyleRepository class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.repository = RuntimeStyleRepository()

    def test_schema_class(self) -> None:
        """Test that schema_class is correctly set."""
        # GIVEN/WHEN/THEN
        assert self.repository.schema_class == RuntimeStyleTable

    @pytest.mark.asyncio
    @patch.object(RuntimeStyleRepository, "_all")
    async def test_all(self, mock_all: Mock) -> None:
        """Test retrieving all styles."""
        # GIVEN
        mock_result1 = Mock()
        mock_result1.id = 1
        mock_result1.style_name = "Electronic"

        mock_result2 = Mock()
        mock_result2.id = 2
        mock_result2.style_name = "Jazz"

        # Mock async generator
        async def async_generator() -> AsyncGenerator[Mock, None]:
            yield mock_result1
            yield mock_result2

        mock_all.return_value = async_generator()

        with patch.object(RuntimeStyle, "model_validate") as mock_validate:
            style1 = RuntimeStyle(id=1, style_name="Electronic")
            style2 = RuntimeStyle(id=2, style_name="Jazz")
            mock_validate.side_effect = [style1, style2]

            # WHEN
            result = []
            async for style in self.repository.all():
                result.append(style)

            # THEN
            assert len(result) == 2
            assert result[0] == style1
            assert result[1] == style2

    @pytest.mark.asyncio
    @patch.object(RuntimeStyleRepository, "execute")
    async def test_get_success(self, mock_execute: Mock) -> None:
        """Test successfully retrieving a style by ID."""
        # GIVEN
        style_id = 1
        mock_instance = Mock()
        mock_instance.id = style_id
        mock_instance.style_name = "Electronic"

        mock_result = Mock(spec=Result)
        mock_scalars = Mock()
        mock_scalars.one_or_none.return_value = mock_instance
        mock_result.scalars.return_value = mock_scalars
        mock_execute.return_value = mock_result

        with patch.object(RuntimeStyle, "model_validate") as mock_validate:
            expected_style = RuntimeStyle(id=style_id, style_name="Electronic")
            mock_validate.return_value = expected_style

            # WHEN
            result = await self.repository.get_by_id(style_id)

            # THEN
            assert result == expected_style
            mock_validate.assert_called_once_with(mock_instance)

    @pytest.mark.asyncio
    @patch.object(RuntimeStyleRepository, "execute")
    async def test_get_not_found(self, mock_execute: Mock) -> None:
        """Test retrieving a style by ID when not found."""
        # GIVEN
        style_id = 999

        mock_result = Mock(spec=Result)
        mock_scalars = Mock()
        mock_scalars.one_or_none.return_value = None
        mock_result.scalars.return_value = mock_scalars
        mock_execute.return_value = mock_result

        # WHEN/THEN
        with pytest.raises(NotFoundError):
            await self.repository.get_by_id(style_id)

    @pytest.mark.asyncio
    @patch.object(RuntimeStyleRepository, "execute")
    async def test_get_by_name_success(self, mock_execute: Mock) -> None:
        """Test successfully retrieving a style by name."""
        # GIVEN
        style_name = "Electronic"
        mock_instance = Mock()
        mock_instance.id = 1
        mock_instance.style_name = style_name

        mock_result = Mock(spec=Result)
        mock_scalars = Mock()
        mock_scalars.one_or_none.return_value = mock_instance
        mock_result.scalars.return_value = mock_scalars
        mock_execute.return_value = mock_result

        with patch.object(RuntimeStyle, "model_validate") as mock_validate:
            expected_style = RuntimeStyle(id=1, style_name=style_name)
            mock_validate.return_value = expected_style

            # WHEN
            result = await self.repository.get_by_name(style_name)

            # THEN
            assert result == expected_style
            mock_validate.assert_called_once_with(mock_instance)

    @pytest.mark.asyncio
    @patch.object(RuntimeStyleRepository, "execute")
    async def test_get_by_name_not_found(self, mock_execute: Mock) -> None:
        """Test retrieving a style by name when not found."""
        # GIVEN
        style_name = "NonexistentStyle"

        mock_result = Mock(spec=Result)
        mock_scalars = Mock()
        mock_scalars.one_or_none.return_value = None
        mock_result.scalars.return_value = mock_scalars
        mock_execute.return_value = mock_result

        # WHEN/THEN
        with pytest.raises(NotFoundError):
            await self.repository.get_by_name(style_name)

    @pytest.mark.asyncio
    @patch.object(RuntimeStyleRepository, "_save")
    async def test_create(self, mock_save: Mock) -> None:
        """Test creating a new style."""
        # GIVEN
        style = RuntimeStyle(id=1, style_name="Electronic")
        mock_instance = Mock()
        mock_instance.id = 1
        mock_instance.style_name = "Electronic"
        mock_save.return_value = mock_instance

        with patch.object(RuntimeStyle, "model_validate") as mock_validate:
            expected_style = RuntimeStyle(id=1, style_name="Electronic")
            mock_validate.return_value = expected_style

            # WHEN
            result = await self.repository.create(style)

            # THEN
            assert result == expected_style
            mock_save.assert_called_once_with(style.model_dump())
            mock_validate.assert_called_once_with(mock_instance)
