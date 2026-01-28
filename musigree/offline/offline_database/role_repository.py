import logging
from typing import AsyncGenerator

from sqlalchemy import select, Result

from musigree.exceptions import NotFoundError
from musigree.offline.offline_database.base_repository import BaseRepository
from musigree.offline.offline_database.role_table import RoleTable
from musigree.offline.offline_domain.role import Role, RoleUncommitted

log = logging.getLogger(__name__)


class RoleRepository(BaseRepository[RoleTable]):
    """
    Repository for managing Role objects in the runtime_database.

    This class provides async methods for interacting with the RoleTable in the
    runtime_database, including creating, retrieving, and managing roles.

    Inherits from:
        BaseRepository[RoleTable]: Provides the basic async runtime_database interaction
            functionality.

    Attributes:
        schema_class (Type[RoleTable]): The SQLAlchemy table class for roles.
    """

    schema_class = RoleTable
    """The SQLAlchemy table class for roles."""

    async def all(self) -> AsyncGenerator[Role, None]:
        """
        Retrieves all roles from the runtime_database.

        Yields:
            AsyncGenerator[Role]: An async iterator yielding each role.
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
        Creates a new role in the runtime_database.

        Args:
            role: The RoleUncommitted object to create.

        Returns:
            Role: The created role.
        """
        instance: RoleTable = await self._save(role.model_dump())
        return Role.model_validate(instance)

    async def create_bulk(
        self, roles: list[RoleUncommitted], on_conflict_do_nothing: bool = False
    ) -> None:
        """
        Creates multiple relations in the runtime_database in bulk.

        Args:
            roles: A list of RoleUncommitted objects to create.
            on_conflict_do_nothing: If True, ignore conflicts during insertion.
        """
        from musigree.offline.offline_database_manager import OfflineDatabaseManager

        assert OfflineDatabaseManager.offline_database_helper is not None, (
            "OfflineDatabaseManager.offline_database_helper must be initialized before calling create_bulk()"
        )

        role_dicts = []
        for role in roles:
            role_dict = role.model_dump()
            role_dicts.append(role_dict)
        query = OfflineDatabaseManager.offline_database_helper.generate_insert_bulk_query(
            self.schema_class, role_dicts, on_conflict_do_nothing
        )
        await self._session.execute(query)
