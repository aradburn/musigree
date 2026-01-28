import logging
from typing import AsyncGenerator

from sqlalchemy import Result, select

from musigree.exceptions import NotFoundError
from musigree.runtime.runtime_database.runtime_country_table import RuntimeCountryTable
from musigree.runtime.runtime_database.runtime_base_repository import (
    RuntimeBaseRepository,
)
from musigree.runtime.runtime_domain.runtime_country import RuntimeCountry

log = logging.getLogger(__name__)


class RuntimeCountryRepository(RuntimeBaseRepository[RuntimeCountryTable]):
    """
    Repository for managing RuntimeCountry objects in the runtime runtime_database.

    This class provides async methods for interacting with the RuntimeCountryTable
    in the runtime runtime_database, including creating, retrieving countries by ID or
    name, and getting all countries.

    Inherits from:
        RuntimeBaseRepository[RuntimeCountryTable]: Provides the basic runtime
            runtime_database interaction functionality.

    Attributes:
        schema_class (Type[RuntimeCountryTable]): The SQLAlchemy table class for runtime countries.
    """

    schema_class = RuntimeCountryTable
    """The SQLAlchemy table class for runtime countries."""

    async def all(self) -> AsyncGenerator[RuntimeCountry, None]:
        """
        Retrieves all countries from the runtime runtime_database.

        Yields:
            AsyncGenerator[RuntimeCountry]: An async iterator yielding each country.
        """
        async for instance in self._all():
            yield RuntimeCountry.model_validate(instance)

    async def get_by_id(self, id_: int) -> RuntimeCountry:
        """
        Retrieves a country by its ID.

        Args:
            id_: The ID of the country to retrieve.

        Returns:
            RuntimeCountry: The retrieved country.

        Raises:
            NotFoundError: If no country is found with the given ID.
        """
        query = select(RuntimeCountryTable).where(RuntimeCountryTable.id == id_)

        result: Result[tuple[int]] = await self.execute(query)

        if not (instance := result.scalars().one_or_none()):
            raise NotFoundError

        return RuntimeCountry.model_validate(instance)

    async def get_by_name(self, name: str) -> RuntimeCountry:
        """
        Retrieves a country by its name.

        Args:
            name: The name of the country to retrieve.

        Returns:
            RuntimeCountry: The retrieved country.

        Raises:
            NotFoundError: If no country is found with the given name.
        """
        query = select(RuntimeCountryTable).where(RuntimeCountryTable.country_name == name)
        result: Result[tuple[RuntimeCountry]] = await self.execute(query)

        if not (instance := result.scalars().one_or_none()):
            raise NotFoundError

        return RuntimeCountry.model_validate(instance)

    async def create(self, country: RuntimeCountry) -> RuntimeCountry:
        """
        Creates a new country in the runtime runtime_database.

        Args:
            country: The Country object to create.

        Returns:
            RuntimeCountry: The created country.
        """
        instance: RuntimeCountryTable = await self._save(country.model_dump())
        return RuntimeCountry.model_validate(instance)
