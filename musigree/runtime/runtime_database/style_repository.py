import logging
from collections.abc import Iterator

from sqlalchemy import Result, select

from musigree.exceptions import NotFoundError
from musigree.runtime.runtime_database.style_table import StyleTable
from musigree.runtime.runtime_database.runtime_base_repository import (
    RuntimeBaseRepository,
)
from musigree.runtime.runtime_domain.style import Style

log = logging.getLogger(__name__)


class StyleRepository(RuntimeBaseRepository[StyleTable]):
    """
    Repository for managing Style objects in the runtime database.

    This class provides methods for interacting with the StyleTable
    in the runtime database, including creating, retrieving styles by ID or
    name, and getting all styles.

    Inherits from:
        RuntimeBaseRepository[StyleTable]: Provides the basic runtime
            database interaction functionality.

    Attributes:
        schema_class (Type[StyleTable]): The SQLAlchemy table class for runtime styles.
    """

    schema_class = StyleTable
    """The SQLAlchemy table class for runtime styles."""

    def all(self) -> Iterator[Style]:
        """
        Retrieves all styles from the runtime database.

        Yields:
            Iterator[Style]: An iterator yielding each style.
        """
        for instance in self._all():
            # async for instance in self._all():
            yield Style.model_validate(instance)

    def get(self, style_id: int) -> Style:
        """
        Retrieves a style by its ID.

        Args:
            style_id: The ID of the style to retrieve.

        Returns:
            Style: The retrieved style.

        Raises:
            NotFoundError: If no style is found with the given ID.
        """
        query = select(StyleTable).where(StyleTable.id == style_id)

        result: Result = self.execute(query)
        # result: Result = await self.execute(query)

        if not (instance := result.scalars().one_or_none()):
            raise NotFoundError

        return Style.model_validate(instance)

    def get_by_name(self, name: str) -> Style:
        """
        Retrieves a style by its name.

        Args:
            name: The name of the style to retrieve.

        Returns:
            Style: The retrieved style.

        Raises:
            NotFoundError: If no style is found with the given name.
        """

        query = select(StyleTable).where(StyleTable.style_name == name)

        result: Result = self.execute(query)
        # result: Result = await self.execute(query)

        if not (instance := result.scalars().one_or_none()):
            raise NotFoundError

        style = Style.model_validate(instance)
        """Validate the DB result into the Domain object"""

        return style

    def create(self, style: Style) -> Style:
        """
        Creates a new style in the runtime database.

        Args:
            style: The Style object representing the style to create.

        Returns:
            Style: The created style.
        """
        instance: StyleTable = self._save(style.model_dump())
        # instance: StyleTable = await self._save(schema.model_dump())
        return Style.model_validate(instance) 