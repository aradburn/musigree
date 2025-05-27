import logging
from collections.abc import Iterator

from sqlalchemy import Result, select

from musigree.exceptions import NotFoundError
from musigree.runtime.runtime_database.genre_table import GenreTable
from musigree.runtime.runtime_database.runtime_base_repository import (
    RuntimeBaseRepository,
)
from musigree.runtime.runtime_domain.genre import Genre

log = logging.getLogger(__name__)


class GenreRepository(RuntimeBaseRepository[GenreTable]):
    """
    Repository for managing Genre objects in the runtime database.

    This class provides methods for interacting with the GenreTable
    in the runtime database, including creating, retrieving genres by ID or
    name, and getting all genres.

    Inherits from:
        RuntimeBaseRepository[GenreTable]: Provides the basic runtime
            database interaction functionality.

    Attributes:
        schema_class (Type[GenreTable]): The SQLAlchemy table class for runtime genres.
    """

    schema_class = GenreTable
    """The SQLAlchemy table class for runtime genres."""

    def all(self) -> Iterator[Genre]:
        """
        Retrieves all genres from the runtime database.

        Yields:
            Iterator[Genre]: An iterator yielding each genre.
        """
        for instance in self._all():
            # async for instance in self._all():
            yield Genre.model_validate(instance)

    def get(self, genre_id: int) -> Genre:
        """
        Retrieves a genre by its ID.

        Args:
            genre_id: The ID of the genre to retrieve.

        Returns:
            Genre: The retrieved genre.

        Raises:
            NotFoundError: If no genre is found with the given ID.
        """
        query = select(GenreTable).where(GenreTable.id == genre_id)

        result: Result = self.execute(query)
        # result: Result = await self.execute(query)

        if not (instance := result.scalars().one_or_none()):
            raise NotFoundError

        return Genre.model_validate(instance)

    def get_by_name(self, name: str) -> Genre:
        """
        Retrieves a genre by its name.

        Args:
            name: The name of the genre to retrieve.

        Returns:
            Genre: The retrieved genre.

        Raises:
            NotFoundError: If no genre is found with the given name.
        """

        query = select(GenreTable).where(GenreTable.genre_name == name)

        result: Result = self.execute(query)
        # result: Result = await self.execute(query)

        if not (instance := result.scalars().one_or_none()):
            raise NotFoundError

        genre = Genre.model_validate(instance)
        """Validate the DB result into the Domain object"""

        return genre

    def create(self, genre: Genre) -> Genre:
        """
        Creates a new genre in the runtime database.

        Args:
            genre: The Genre object representing the genre to create.

        Returns:
            Genre: The created genre.
        """
        instance: GenreTable = self._save(genre.model_dump())
        # instance: GenreTable = await self._save(schema.model_dump())
        return Genre.model_validate(instance) 