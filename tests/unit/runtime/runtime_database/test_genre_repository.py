from typing import AsyncGenerator
from unittest.mock import Mock, patch

import pytest
from sqlalchemy import Result
from musigree.exceptions import NotFoundError
from musigree.runtime.runtime_database.genre_repository import GenreRepository
from musigree.runtime.runtime_database.genre_table import GenreTable
from musigree.runtime.runtime_domain.genre import Genre


class TestGenreRepository:
    """Unit tests for GenreRepository class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.repository = GenreRepository()

    def test_schema_class(self) -> None:
        """Test that schema_class is correctly set."""
        # GIVEN/WHEN/THEN
        assert self.repository.schema_class == GenreTable

    @pytest.mark.asyncio
    @patch.object(GenreRepository, "_all")
    async def test_all(self, mock_all: Mock) -> None:
        """Test retrieving all genres."""
        # GIVEN
        mock_instance1 = Mock()
        mock_instance1.id = 1
        mock_instance1.genre_name = "Electronic"

        mock_instance2 = Mock()
        mock_instance2.id = 2
        mock_instance2.genre_name = "Rock"

        # Create an async generator for the mock
        async def async_generator() -> AsyncGenerator[Mock, None]:
            for item in [mock_instance1, mock_instance2]:
                yield item

        mock_all.return_value = async_generator()

        with patch.object(Genre, "model_validate") as mock_validate:
            mock_validate.side_effect = [
                Genre(id=1, genre_name="Electronic"),
                Genre(id=2, genre_name="Rock"),
            ]

            # WHEN
            result = []
            async for genre in self.repository.all():
                result.append(genre)

            # THEN
            assert len(result) == 2
            assert isinstance(result[0], Genre)
            assert isinstance(result[1], Genre)
            assert result[0].genre_name == "Electronic"
            assert result[1].genre_name == "Rock"

    @pytest.mark.asyncio
    @patch.object(GenreRepository, "execute")
    async def test_get_success(self, mock_execute: Mock) -> None:
        """Test successfully retrieving a genre by ID."""
        # GIVEN
        genre_id = 1
        mock_instance = Mock()
        mock_instance.id = genre_id
        mock_instance.genre_name = "Electronic"

        mock_result = Mock(spec=Result)
        mock_scalars = Mock()
        mock_scalars.one_or_none.return_value = mock_instance
        mock_result.scalars.return_value = mock_scalars
        mock_execute.return_value = mock_result

        with patch.object(Genre, "model_validate") as mock_validate:
            expected_genre = Genre(id=genre_id, genre_name="Electronic")
            mock_validate.return_value = expected_genre

            # WHEN
            result = await self.repository.get_by_id(genre_id)

            # THEN
            assert result == expected_genre
            mock_validate.assert_called_once_with(mock_instance)

    @pytest.mark.asyncio
    @patch.object(GenreRepository, "execute")
    async def test_get_not_found(self, mock_execute: Mock) -> None:
        """Test retrieving a genre by ID when not found."""
        # GIVEN
        genre_id = 999

        mock_result = Mock(spec=Result)
        mock_scalars = Mock()
        mock_scalars.one_or_none.return_value = None
        mock_result.scalars.return_value = mock_scalars
        mock_execute.return_value = mock_result

        # WHEN/THEN
        with pytest.raises(NotFoundError):
            await self.repository.get_by_id(genre_id)

    @pytest.mark.asyncio
    @patch.object(GenreRepository, "execute")
    async def test_get_by_name_success(self, mock_execute: Mock) -> None:
        """Test successfully retrieving a genre by name."""
        # GIVEN
        genre_name = "Electronic"
        mock_instance = Mock()
        mock_instance.id = 1
        mock_instance.genre_name = genre_name

        mock_result = Mock(spec=Result)
        mock_scalars = Mock()
        mock_scalars.one_or_none.return_value = mock_instance
        mock_result.scalars.return_value = mock_scalars
        mock_execute.return_value = mock_result

        with patch.object(Genre, "model_validate") as mock_validate:
            expected_genre = Genre(id=1, genre_name=genre_name)
            mock_validate.return_value = expected_genre

            # WHEN
            result = await self.repository.get_by_name(genre_name)

            # THEN
            assert result == expected_genre
            mock_validate.assert_called_once_with(mock_instance)

    @pytest.mark.asyncio
    @patch.object(GenreRepository, "execute")
    async def test_get_by_name_not_found(self, mock_execute: Mock) -> None:
        """Test retrieving a genre by name when not found."""
        # GIVEN
        genre_name = "NonexistentGenre"

        mock_result = Mock(spec=Result)
        mock_scalars = Mock()
        mock_scalars.one_or_none.return_value = None
        mock_result.scalars.return_value = mock_scalars
        mock_execute.return_value = mock_result

        # WHEN/THEN
        with pytest.raises(NotFoundError):
            await self.repository.get_by_name(genre_name)

    @pytest.mark.asyncio
    @patch.object(GenreRepository, "_save")
    async def test_create(self, mock_save: Mock) -> None:
        """Test creating a new genre."""
        # GIVEN
        genre = Genre(id=1, genre_name="Electronic")
        mock_instance = Mock()
        mock_instance.id = 1
        mock_instance.genre_name = "Electronic"
        mock_save.return_value = mock_instance

        with patch.object(Genre, "model_validate") as mock_validate:
            expected_genre = Genre(id=1, genre_name="Electronic")
            mock_validate.return_value = expected_genre

            # WHEN
            result = await self.repository.create(genre)

            # THEN
            assert result == expected_genre
            mock_save.assert_called_once_with(genre.model_dump())
            mock_validate.assert_called_once_with(mock_instance)
