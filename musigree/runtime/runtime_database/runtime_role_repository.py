import logging
from typing import AsyncGenerator

from sqlalchemy import Result, select

from musigree.exceptions import NotFoundError
from musigree.library.cache.cache_manager import CacheManager
from musigree.runtime.runtime_database import RuntimeRoleTable
from musigree.runtime.runtime_database.runtime_base_repository import (
    RuntimeBaseRepository,
)
from musigree.runtime.runtime_domain.role import RuntimeRole

log = logging.getLogger(__name__)


class RuntimeRoleRepository(RuntimeBaseRepository[RuntimeRoleTable]):
    """
    Repository for managing RuntimeRole objects in the runtime database.

    This class provides async methods for interacting with the RuntimeRoleTable
    in the runtime database, including creating, retrieving roles by ID or
    name, and getting all roles. It also utilizes a cache to optimize
    retrieval of roles by name.

    Inherits from:
        RuntimeBaseRepository[RuntimeRoleTable]: Provides the basic runtime
            database interaction functionality.

    Attributes:
        schema_class (Type[RuntimeRoleTable]): The SQLAlchemy table class for runtime roles.
    """

    schema_class = RuntimeRoleTable
    """The SQLAlchemy table class for runtime roles."""

    async def all(self) -> AsyncGenerator[RuntimeRole, None]:
        """
        Retrieves all roles from the runtime database.

        Yields:
            AsyncGenerator[RuntimeRole]: An async iterator yielding each role.
        """
        query = select(RuntimeRoleTable)
        result = await self._session.stream(
            query, execution_options={"yield_per": 1000}
        )
        async for row in result:
            yield RuntimeRole.model_validate(row[0])

        # async for instance in self._all():
        #     yield RuntimeRole.model_validate(instance)

    async def get_by_id(self, id_: int) -> RuntimeRole:
        """
        Retrieves a role by its ID.

        Args:
            id_: The ID of the role to retrieve.

        Returns:
            RuntimeRole: The retrieved role.

        Raises:
            NotFoundError: If no role is found with the given ID.
        """
        query = select(RuntimeRoleTable).where(RuntimeRoleTable.id == id_)

        result: Result = await self.execute(query)

        if not (instance := result.scalars().one_or_none()):
            raise NotFoundError

        return RuntimeRole.model_validate(instance)

    async def get_by_name(self, name: str) -> RuntimeRole:
        """
        Retrieves a role by its name, using cache if available.

        Args:
            name: The name of the role to retrieve.

        Returns:
            RuntimeRole: The retrieved role.

        Raises:
            NotFoundError: If no role is found with the given name.
        """
        # Try to get from cache first
        cache = CacheManager.get_cache()
        role_key_str = f"ROLE-{name}"
        role: RuntimeRole | None = cache.get(role_key_str)
        if role:
            return role

        # If not in cache, query database
        query = select(RuntimeRoleTable).where(RuntimeRoleTable.role_name == name)
        result: Result = await self.execute(query)

        if not (instance := result.scalars().one_or_none()):
            raise NotFoundError

        role = RuntimeRole.model_validate(instance)

        # Cache the result
        cache.set(role_key_str, role)

        return role

    async def create(self, role: RuntimeRole) -> RuntimeRole:
        """
        Creates a new role in the runtime database.

        Args:
            role: The RuntimeRole object to create.

        Returns:
            RuntimeRole: The created role.
        """
        instance: RuntimeRoleTable = await self._save(role.model_dump())
        return RuntimeRole.model_validate(instance)
