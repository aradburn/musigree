import logging
import random
from typing import AsyncGenerator

from sqlalchemy import Result, select, func

from musigree.exceptions import DatabaseError
from musigree.runtime.runtime_database.runtime_base_repository import (
    RuntimeBaseRepository,
)
from musigree.runtime.runtime_database.runtime_token_table import RuntimeTokenTable
from musigree.runtime.runtime_domain.runtime_token import RuntimeToken

log = logging.getLogger(__name__)


class RuntimeTokenRepository(RuntimeBaseRepository[RuntimeTokenTable]):
    """
    Repository for managing RuntimeToken objects in the runtime runtime_database.

    This class provides async methods for interacting with the RuntimeTokenTable
    in the runtime runtime_database, including creating, retrieving tokens by ID or
    name, and getting all tokens.

    Inherits from:
        RuntimeBaseRepository[RuntimeTokenTable]: Provides the basic runtime
            runtime_database interaction functionality.

    Attributes:
        schema_class (Type[RuntimeTokenTable]): The SQLAlchemy table class for runtime tokens.
    """

    schema_class = RuntimeTokenTable
    """The SQLAlchemy table class for runtime tokens."""

    async def all(self) -> AsyncGenerator[RuntimeToken, None]:
        """
        Retrieves all tokens from the runtime runtime_database.

        Yields:
            AsyncGenerator[RuntimeToken]: An async iterator yielding each token.
        """
        async for instance in self._all():
            yield RuntimeToken.model_validate(instance)

    async def count(self) -> int:
        """
        Counts the total number of records in the associated runtime_database table.

        Returns:
            int: The total count of records.

        Raises:
            UnprocessableError: If the runtime_database query returns a non-integer value.
        """
        query = select(func.count()).select_from(self.schema_class)
        result: Result = await self.execute(query)
        value = result.scalar()

        if not isinstance(value, int):
            raise DatabaseError(
                message=f"Count function returned non integer value: {value}",
            )

        return value

    async def get_by_token(self, token: str) -> list[int]:
        """
        Retrieves all ids for a token.

        Args:
            token: The token to retrieve.

        Returns:
            ids: The list of ids.

        Raises:
            NotFoundError: If no token is found.
        """
        query = select(RuntimeTokenTable.entity_id).where(RuntimeTokenTable.token == token)
        result: Result = await self.execute(query)

        ids = result.scalars().all()

        return [int(item) for item in ids]

    async def get_random_id(self) -> int | None:
        """
        Retrieves a random entity id.

        Returns:
            int | None: The entity id or None if none found.
        """
        max_row = await self.count()
        random_row = random.randint(0, max_row - 1)
        query = select(RuntimeTokenTable.entity_id).where(RuntimeTokenTable.id == random_row)
        result: Result = await self.execute(query)

        return result.scalar_one_or_none()

    async def create(self, token: RuntimeToken) -> RuntimeToken:
        """
        Creates a new token in the runtime runtime_database.

        Args:
            token: The Token object to create.

        Returns:
            RuntimeToken: The created token.
        """
        instance: RuntimeTokenTable = await self._save(token.model_dump())
        return RuntimeToken.model_validate(instance)
