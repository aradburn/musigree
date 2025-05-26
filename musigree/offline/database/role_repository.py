import logging
from collections.abc import Iterator

from sqlalchemy import Result, select

from musigree.exceptions import NotFoundError
from musigree.library.cache.cache_manager import CacheManager
from musigree.offline.database.base_repository import BaseRepository
from musigree.offline.database.role_table import RoleTable
from musigree.offline.domain.role import Role, RoleUncommitted

log = logging.getLogger(__name__)


class RoleRepository(BaseRepository[RoleTable]):
    """
    Repository for managing Role objects in the database.

    This class provides methods for interacting with the RoleTable in the
    database, including creating, retrieving roles by ID or name, and
    getting all roles. It also utilizes a cache to optimize retrieval of
    roles by name.

    Inherits from:
        BaseRepository[RoleTable]: Provides the basic database interaction
            functionality.

    Attributes:
        schema_class (Type[RoleTable]): The SQLAlchemy table class for roles.
    """

    schema_class = RoleTable
    """The SQLAlchemy table class for roles."""

    def all(self) -> Iterator[Role]:
        """
        Retrieves all roles from the database.

        Yields:
            Iterator[Role]: An iterator yielding each role.
        """
        for instance in self._all():
            # async for instance in self._all():
            yield Role.model_validate(instance)

    def get(self, role_id: int) -> Role:
        """
        Retrieves a role by its ID.

        Args:
            role_id: The ID of the role to retrieve.

        Returns:
            Role: The retrieved role.

        Raises:
            NotFoundError: If no role is found with the given ID.
        """
        query = select(RoleTable).where(RoleTable.id == role_id)

        result: Result = self.execute(query)
        # result: Result = await self.execute(query)

        if not (instance := result.scalars().one_or_none()):
            raise NotFoundError

        return Role.model_validate(instance)

    def get_by_name(self, name: str) -> Role:
        """
        Retrieves a role by its name.

        This method first checks the cache for the role. If it's not in the
        cache, it queries the database, caches the result, and then returns it.

        Args:
            name: The name of the role to retrieve.

        Returns:
            Role: The retrieved role.

        Raises:
            NotFoundError: If no role is found with the given name.
        """
        cache = CacheManager.get_cache()

        role_key_str = f"ROLE-{name}"
        role = cache.get(role_key_str)
        if role:
            return role

        query = select(RoleTable).where(RoleTable.role_name == name)

        result: Result = self.execute(query)
        # result: Result = await self.execute(query)

        if not (instance := result.scalars().one_or_none()):
            raise NotFoundError

        role = Role.model_validate(instance)
        cache.set(role_key_str, role)
        # log.debug(f"cached role: {role_key_str}")
        return role

    def create(self, schema: RoleUncommitted) -> Role:
        """
        Creates a new role in the database.

        Args:
            schema: The RoleUncommitted object representing the role to create.

        Returns:
            Role: The created role.
        """
        instance: RoleTable = self._save(schema.model_dump())
        # instance: RoleTable = await self._save(schema.model_dump())
        return Role.model_validate(instance)
