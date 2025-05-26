import logging
from collections.abc import Iterator

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

    This class provides methods for interacting with the RuntimeRoleTable
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

    def all(self) -> Iterator[RuntimeRole]:
        """
        Retrieves all roles from the runtime database.

        Yields:
            Iterator[RuntimeRole]: An iterator yielding each role.
        """
        for instance in self._all():
            # async for instance in self._all():
            yield RuntimeRole.model_validate(instance)

    def get(self, role_id: int) -> RuntimeRole:
        """
        Retrieves a role by its ID.

        Args:
            role_id: The ID of the role to retrieve.

        Returns:
            RuntimeRole: The retrieved role.

        Raises:
            NotFoundError: If no role is found with the given ID.
        """
        query = select(RuntimeRoleTable).where(RuntimeRoleTable.id == role_id)

        result: Result = self.execute(query)
        # result: Result = await self.execute(query)

        if not (instance := result.scalars().one_or_none()):
            raise NotFoundError

        return RuntimeRole.model_validate(instance)

    def get_by_name(self, name: str) -> RuntimeRole:
        """
        Retrieves a role by its name.

        This method first checks the cache for the role. If it's not in the
        cache, it queries the database, caches the result, and then returns it.

        Args:
            name: The name of the role to retrieve.

        Returns:
            RuntimeRole: The retrieved role.

        Raises:
            NotFoundError: If no role is found with the given name.
        """
        cache = CacheManager.get_cache()
        """Get the cache from the CacheManager"""

        role_key_str = f"ROLE-{name}"
        """Create a string key for the role."""
        role = cache.get(role_key_str)
        """Get the role from cache by key"""
        if role:
            return role

        query = select(RuntimeRoleTable).where(RuntimeRoleTable.role_name == name)

        result: Result = self.execute(query)
        # result: Result = await self.execute(query)

        if not (instance := result.scalars().one_or_none()):
            raise NotFoundError

        role = RuntimeRole.model_validate(instance)
        """Validate the DB result into the Domain object"""
        cache.set(role_key_str, role)
        """Set the role in cache by key"""
        # log.debug(f"cached role: {role_key_str}")
        return role

    def create(self, runtime_role: RuntimeRole) -> RuntimeRole:
        """
        Creates a new role in the runtime database.

        Args:
            runtime_role: The RuntimeRole object representing the role to create.

        Returns:
            RuntimeRole: The created role.
        """
        instance: RuntimeRoleTable = self._save(runtime_role.model_dump())
        # instance: RoleTable = await self._save(schema.model_dump())
        return RuntimeRole.model_validate(instance)
