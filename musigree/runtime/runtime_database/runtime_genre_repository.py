import logging
from typing import AsyncGenerator

from sqlalchemy import Result, select

from musigree.exceptions import NotFoundError
from musigree.runtime.runtime_database.runtime_genre_table import RuntimeGenreTable
from musigree.runtime.runtime_database.runtime_base_repository import (
    RuntimeBaseRepository,
)
from musigree.runtime.runtime_domain.runtime_genre import RuntimeGenre

log = logging.getLogger(__name__)


class RuntimeGenreRepository(RuntimeBaseRepository[RuntimeGenreTable]):
    """
    Repository for managing RuntimeGenre objects in the runtime runtime_database.

    This class provides async methods for interacting with the RuntimeGenreTable
    in the runtime runtime_database, including creating, retrieving genres by ID or
    name, and getting all genres.

    Inherits from:
        RuntimeBaseRepository[RuntimeGenreTable]: Provides the basic runtime
            runtime_database interaction functionality.

    Attributes:
        schema_class (Type[RuntimeGenreTable]): The SQLAlchemy table class for runtime genres.
    """

    schema_class = RuntimeGenreTable
    """The SQLAlchemy table class for runtime genres."""

    async def all(self) -> AsyncGenerator[RuntimeGenre, None]:
        """
        Retrieves all genres from the runtime runtime_database.

        Yields:
            AsyncGenerator[RuntimeGenre]: An async iterator yielding each genre.
        """
        async for instance in self._all():
            yield RuntimeGenre.model_validate(instance)

    async def get_by_id(self, id_: int) -> RuntimeGenre:
        """
        Retrieves a genre by its ID.

        Args:
            id_: The ID of the genre to retrieve.

        Returns:
            RuntimeGenre: The retrieved genre.

        Raises:
            NotFoundError: If no genre is found with the given ID.
        """
        query = select(RuntimeGenreTable).where(RuntimeGenreTable.id == id_)

        result: Result = await self.execute(query)

        if not (instance := result.scalars().one_or_none()):
            raise NotFoundError

        return RuntimeGenre.model_validate(instance)

    async def get_by_name(self, name: str) -> RuntimeGenre:
        """
        Retrieves a genre by its name.

        Args:
            name: The name of the genre to retrieve.

        Returns:
            RuntimeGenre: The retrieved genre.

        Raises:
            NotFoundError: If no genre is found with the given name.
        """
        query = select(RuntimeGenreTable).where(RuntimeGenreTable.genre_name == name)
        result: Result = await self.execute(query)

        if not (instance := result.scalars().one_or_none()):
            raise NotFoundError

        return RuntimeGenre.model_validate(instance)

    async def create(self, genre: RuntimeGenre) -> RuntimeGenre:
        """
        Creates a new genre in the runtime runtime_database.

        Args:
            genre: The Genre object to create.

        Returns:
            RuntimeGenre: The created genre.
        """
        instance: RuntimeGenreTable = await self._save(genre.model_dump())
        return RuntimeGenre.model_validate(instance)
