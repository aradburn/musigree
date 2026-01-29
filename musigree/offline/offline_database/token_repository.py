import logging
import random
from typing import AsyncGenerator

from sqlalchemy import Result, select, func

from musigree.exceptions import DatabaseError
from musigree.offline.offline_database.base_repository import BaseRepository
from musigree.offline.offline_database.token_table import TokenTable
from musigree.offline.offline_domain.token import Token

log = logging.getLogger(__name__)


class TokenRepository(BaseRepository[TokenTable]):
    """
    Repository for managing Token objects in the offline_database.

    This class provides async methods for interacting with the TokenTable
    in the offline_database, including creating, retrieving tokens by ID or
    name, and getting all tokens.

    Inherits from:
        BaseRepository[TokenTable]: Provides the basic offline_database interaction functionality.

    Attributes:
        schema_class (Type[TokenTable]): The SQLAlchemy table class for offline tokens.
    """

    schema_class = TokenTable
    """The SQLAlchemy table class for offline tokens."""

    async def all(self) -> AsyncGenerator[Token, None]:
        """
        Retrieves all tokens from the offline_database.

        Yields:
            AsyncGenerator[Token]: An async iterator yielding each token.
        """
        async for instance in self._all():
            yield Token.model_validate(instance)

    async def count(self) -> int:
        """
        Counts the total number of records in the associated offline_database table.

        Returns:
            int: The total count of records.

        Raises:
            UnprocessableError: If the offline_database query returns a non-integer value.
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
        Creates a new token in the offline_database.

        Args:
            token: The Token object to create.

        Returns:
            Token: The created token.
        """
        instance: TokenTable = await self._save(token.model_dump())
        return Token.model_validate(instance)
