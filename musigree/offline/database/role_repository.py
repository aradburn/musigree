import logging
from collections.abc import AsyncIterator

from sqlalchemy import select, Result

from musigree.exceptions import NotFoundError
from musigree.offline.database.base_repository import BaseRepository
from musigree.offline.database.role_table import RoleTable
from musigree.offline.domain.role import Role, RoleUncommitted

log = logging.getLogger(__name__)


class RoleRepository(BaseRepository[RoleTable]):
    """
    Repository for managing Role objects in the database.

    This class provides async methods for interacting with the RoleTable in the
    database, including creating, retrieving, and managing roles.

    Inherits from:
        BaseRepository[RoleTable]: Provides the basic async database interaction
            functionality.

    Attributes:
        schema_class (Type[RoleTable]): The SQLAlchemy table class for roles.
    """

    schema_class = RoleTable
    """The SQLAlchemy table class for roles."""

    async def all(self) -> AsyncIterator[Role]:
        """
        Retrieves all roles from the database.

        Yields:
            AsyncIterator[Role]: An async iterator yielding each role.
        """
        async for instance in self._all():
            yield Role.model_validate(instance)

    async def get_by_id(self, role_id: int) -> Role:
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

        result: Result = await self.execute(query)

        if not (instance := result.scalars().one_or_none()):
            raise NotFoundError
        return Role.model_validate(instance)

    async def get_by_name(self, name: str) -> Role:
        """
        Retrieves a role by its name.

        Args:
            name: The name of the role to retrieve.

        Returns:
            Role: The retrieved role.

        Raises:
            NotFoundError: If no role is found with the given name.
        """
        query = select(RoleTable).where(RoleTable.role_name == name)
        result = await self._session.execute(query)

        if not (instance := result.scalars().one_or_none()):
            raise NotFoundError
        return Role.model_validate(instance)

    async def create(self, role: RoleUncommitted) -> Role:
        """
        Creates a new role in the database.

        Args:
            role: The RoleUncommitted object to create.

        Returns:
            Role: The created role.
        """
        instance: RoleTable = await self._save(role.model_dump())
        return Role.model_validate(instance)
