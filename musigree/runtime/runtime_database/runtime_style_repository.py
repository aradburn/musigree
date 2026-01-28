import logging
from typing import AsyncGenerator

from sqlalchemy import Result, select

from musigree.exceptions import NotFoundError
from musigree.runtime.runtime_database.runtime_base_repository import (
    RuntimeBaseRepository,
)
from musigree.runtime.runtime_database.runtime_style_table import RuntimeStyleTable
from musigree.runtime.runtime_domain.runtime_style import RuntimeStyle

log = logging.getLogger(__name__)


class RuntimeStyleRepository(RuntimeBaseRepository[RuntimeStyleTable]):
    """
    Repository for managing RuntimeStyle objects in the runtime runtime_database.

    This class provides async methods for interacting with the RuntimeStyleTable
    in the runtime runtime_database, including creating, retrieving styles by ID or
    name, and getting all styles.

    Inherits from:
        RuntimeBaseRepository[RuntimeStyleTable]: Provides the basic runtime
            runtime_database interaction functionality.

    Attributes:
        schema_class (Type[RuntimeStyleTable]): The SQLAlchemy table class for runtime styles.
    """

    schema_class = RuntimeStyleTable
    """The SQLAlchemy table class for runtime styles."""

    async def all(self) -> AsyncGenerator[RuntimeStyle, None]:
        """
        Retrieves all styles from the runtime runtime_database.

        Yields:
            AsyncGenerator[RuntimeStyle]: An async iterator yielding each style.
        """
        async for instance in self._all():
            yield RuntimeStyle.model_validate(instance)

    async def get_by_id(self, id_: int) -> RuntimeStyle:
        """
        Retrieves a style by its ID.

        Args:
            id_: The ID of the style to retrieve.

        Returns:
            RuntimeStyle: The retrieved style.

        Raises:
            NotFoundError: If no style is found with the given ID.
        """
        query = select(RuntimeStyleTable).where(RuntimeStyleTable.id == id_)

        result: Result = await self.execute(query)

        if not (instance := result.scalars().one_or_none()):
            raise NotFoundError

        return RuntimeStyle.model_validate(instance)

    async def get_by_name(self, name: str) -> RuntimeStyle:
        """
        Retrieves a style by its name.

        Args:
            name: The name of the style to retrieve.

        Returns:
            RuntimeStyle: The retrieved style.

        Raises:
            NotFoundError: If no style is found with the given name.
        """
        query = select(RuntimeStyleTable).where(RuntimeStyleTable.style_name == name)
        result: Result = await self.execute(query)

        if not (instance := result.scalars().one_or_none()):
            raise NotFoundError

        return RuntimeStyle.model_validate(instance)

    async def create(self, style: RuntimeStyle) -> RuntimeStyle:
        """
        Creates a new style in the runtime runtime_database.

        Args:
            style: The Style object to create.

        Returns:
            RuntimeStyle: The created style.
        """
        instance: RuntimeStyleTable = await self._save(style.model_dump())
        return RuntimeStyle.model_validate(instance)
