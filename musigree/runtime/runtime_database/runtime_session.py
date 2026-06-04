"""
This module defines the `RuntimeSession` class and related utilities for managing runtime_database sessions
in the runtime environment.

It provides a centralized way to handle async runtime_database sessions, including creating,
executing queries, and managing transactions. It also utilizes a context variable
to manage sessions within asynchronous contexts.

Key functionalities include:
    - Creating new async runtime_database sessions using `get_runtime_session`.
    - Providing a base class `RuntimeSession` for runtime_database operations within an async session.
    - Executing SQL queries and handling common runtime_database errors.
    - Managing the runtime_database session through a context variable (`CTX_RUNTIME_SESSION`).
"""

# noinspection PyPackageRequirements
from contextvars import ContextVar
from typing import Any

from sqlalchemy import Executable
from sqlalchemy.engine import Result
from sqlalchemy.exc import IntegrityError, InvalidRequestError
from sqlalchemy.ext.asyncio import AsyncSession

from musigree.exceptions import DatabaseError


async def get_runtime_session() -> AsyncSession:
    """
    Creates a new async session to execute SQL queries.

    This function is responsible for creating a new async runtime_database session,
    which is used to interact with the runtime_database. It determines whether to
    use a scoped session or a regular session based on the concurrency
    count.

    Returns:
        AsyncSession: A new async runtime_database session.
    """
    from musigree.runtime.runtime_database_manager import RuntimeDatabaseManager

    assert RuntimeDatabaseManager.runtime_database_helper is not None, (
        "RuntimeDatabaseManager.runtime_database_helper must be initialized before calling get_offline_session()"
    )
    assert (
        RuntimeDatabaseManager.runtime_database_helper.runtime_async_session_factory is not None
    ), (
        "RuntimeDatabaseManager.runtime_database_helper.runtime_async_engine must be initialized before calling get_offline_session()"
    )

    async_session_factory = (
        RuntimeDatabaseManager.runtime_database_helper.runtime_async_session_factory
    )
    return async_session_factory()  # type: ignore


CTX_RUNTIME_SESSION: ContextVar[AsyncSession] = ContextVar("runtime_session")
"""
Context variable to store the current async runtime_database session.

This context variable allows async runtime_database sessions to be managed within
asynchronous contexts. Each asynchronous task can have its own session
stored in this variable.
"""


class RuntimeSession:
    """
    The basic class to perform runtime_database operations within an async session.

    This class provides a base for performing runtime_database operations within a
    specific async session. It handles session management, query execution, and
    common runtime_database error handling.
    """

    async def execute(self, query: Executable) -> Result[Any]:
        """
        Executes a SQL query within the current async session.

        Args:
            query: The SQL query to execute.

        Returns:
            Result: The result of the query execution.

        Raises:
            DatabaseError: If there is an error during query execution.
        """
        try:
            result = await self._session.execute(query)
            return result
        except (IntegrityError, InvalidRequestError) as err:
            raise DatabaseError from err

    @property
    def _session(self) -> AsyncSession:
        """
        Retrieves the current async runtime_database session.

        This property checks if a session is already available in the context
        variable. If it is, it returns that session; otherwise, it raises a
        DatabaseError.

        Returns:
            AsyncSession: The current async runtime_database session.

        Raises:
            DatabaseError: If no session is found in the context variable.
        """
        try:
            _session = CTX_RUNTIME_SESSION.get()
        except LookupError:
            raise DatabaseError(message="Not in a transaction") from None
        return _session
