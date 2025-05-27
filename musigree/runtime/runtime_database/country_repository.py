import logging
from collections.abc import Iterator

from sqlalchemy import Result, select

from musigree.exceptions import NotFoundError
from musigree.library.cache.cache_manager import CacheManager
from musigree.runtime.runtime_database import RuntimeRoleTable
from musigree.runtime.runtime_database.country_table import CountryTable
from musigree.runtime.runtime_database.runtime_base_repository import (
    RuntimeBaseRepository,
)
from musigree.runtime.runtime_domain.country import Country
from musigree.runtime.runtime_domain.role import RuntimeRole

log = logging.getLogger(__name__)


class CountryRepository(RuntimeBaseRepository[CountryTable]):
    """
    Repository for managing Country objects in the runtime database.

    This class provides methods for interacting with the CountryTable
    in the runtime database, including creating, retrieving countries by ID or
    name, and getting all countries.

    Inherits from:
        RuntimeBaseRepository[CountryTable]: Provides the basic runtime
            database interaction functionality.

    Attributes:
        schema_class (Type[CountryTable]): The SQLAlchemy table class for runtime countries.
    """

    schema_class = CountryTable
    """The SQLAlchemy table class for runtime roles."""

    def all(self) -> Iterator[Country]:
        """
        Retrieves all countries from the runtime database.

        Yields:
            Iterator[Country]: An iterator yielding each country.
        """
        for instance in self._all():
            # async for instance in self._all():
            yield Country.model_validate(instance)

    def get(self, role_id: int) -> Country:
        """
        Retrieves a country by its ID.

        Args:
            role_id: The ID of the country to retrieve.

        Returns:
            Country: The retrieved country.

        Raises:
            NotFoundError: If no country is found with the given ID.
        """
        query = select(CountryTable).where(CountryTable.id == role_id)

        result: Result = self.execute(query)
        # result: Result = await self.execute(query)

        if not (instance := result.scalars().one_or_none()):
            raise NotFoundError

        return Country.model_validate(instance)

    def get_by_name(self, name: str) -> Country:
        """
        Retrieves a country by its name.

        Args:
            name: The name of the country to retrieve.

        Returns:
            Country: The retrieved country.

        Raises:
            NotFoundError: If no country is found with the given name.
        """

        query = select(CountryTable).where(CountryTable.country_name == name)

        result: Result = self.execute(query)
        # result: Result = await self.execute(query)

        if not (instance := result.scalars().one_or_none()):
            raise NotFoundError

        country = Country.model_validate(instance)
        """Validate the DB result into the Domain object"""

        return country

    def create(self, country: Country) -> Country:
        """
        Creates a new country in the runtime database.

        Args:
            country: The Country object representing the country to create.

        Returns:
            Country: The created country.
        """
        instance: CountryTable = self._save(country.model_dump())
        # instance: CountryTable = await self._save(schema.model_dump())
        return Country.model_validate(instance)
