import logging
import random
from typing import AsyncGenerator

from sqlalchemy import Result, select, func

from musigree.exceptions import UnprocessableError
from musigree.runtime.runtime_database.runtime_base_repository import (
    RuntimeBaseRepository,
)
from musigree.runtime.runtime_database.token_table import TokenTable
from musigree.runtime.runtime_domain.token import Token

log = logging.getLogger(__name__)


class TokenRepository(RuntimeBaseRepository[TokenTable]):
    """
    Repository for managing Token objects in the runtime database.

    This class provides async methods for interacting with the TokenTable
    in the runtime database, including creating, retrieving tokens by ID or
    name, and getting all tokens.

    Inherits from:
        RuntimeBaseRepository[TokenTable]: Provides the basic runtime
            database interaction functionality.

    Attributes:
        schema_class (Type[TokenTable]): The SQLAlchemy table class for runtime tokens.
    """

    schema_class = TokenTable
    """The SQLAlchemy table class for runtime tokens."""

    async def all(self) -> AsyncGenerator[Token, None]:
        """
        Retrieves all tokens from the runtime database.

        Yields:
            AsyncGenerator[Token]: An async iterator yielding each token.
        """
        async for instance in self._all():
            yield Token.model_validate(instance)

    async def count(self) -> int:
        """
        Counts the total number of records in the associated database table.

        Returns:
            int: The total count of records.

        Raises:
            UnprocessableError: If the database query returns a non-integer value.
        """
        query = select(func.count()).select_from(self.schema_class)
        result: Result = await self.execute(query)
        value = result.scalar()

        if not isinstance(value, int):
            raise UnprocessableError(
                message=f"For some reason count function returned not an integer.Value: {value}",
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
        query = select(TokenTable.entity_id).where(TokenTable.token == token)
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
        query = select(TokenTable.entity_id).where(TokenTable.id == random_row)
        result: Result = await self.execute(query)

        return result.scalar_one_or_none()

    async def create(self, token: Token) -> Token:
        """
        Creates a new token in the runtime database.

        Args:
            token: The Token object to create.

        Returns:
            Token: The created token.
        """
        instance: TokenTable = await self._save(token.model_dump())
        return Token.model_validate(instance)
