"""
This module defines the `RuntimeSession` class and related utilities for managing database sessions
in the runtime environment.

It provides a centralized way to handle async database sessions, including creating,
executing queries, and managing transactions. It also utilizes a context variable
to manage sessions within asynchronous contexts.

Key functionalities include:
    - Creating new async database sessions using `get_runtime_session`.
    - Providing a base class `RuntimeSession` for database operations within an async session.
    - Executing SQL queries and handling common database errors.
    - Managing the database session through a context variable (`CTX_RUNTIME_SESSION`).
"""

# noinspection PyPackageRequirements
from contextvars import ContextVar
import asyncio

from sqlalchemy.engine import Result
from sqlalchemy.exc import IntegrityError, InvalidRequestError
from sqlalchemy.ext.asyncio import AsyncSession, async_scoped_session

from musigree.exceptions import DatabaseError


async def get_runtime_session() -> AsyncSession:
    """
    Creates a new async session to execute SQL queries.

    This function is responsible for creating a new async database session,
    which is used to interact with the database. It determines whether to
    use a scoped session or a regular session based on the concurrency
    count.

    Returns:
        AsyncSession: A new async database session.
    """
    from musigree.runtime.runtime_database_manager import RuntimeDatabaseManager

    # Note: The session factory should be an async_sessionmaker for this to work properly
    # This will need to be updated in the database helper classes
    session_factory = RuntimeDatabaseManager.runtime_database_helper.runtime_session_factory
    
    if RuntimeDatabaseManager.get_concurrency_count() > 1:
        _scoped_session: async_scoped_session[AsyncSession] = async_scoped_session(
            session_factory,  # type: ignore[arg-type]
            scopefunc=lambda: id(asyncio.current_task())
        )
        return _scoped_session()
    else:
        return session_factory()


CTX_RUNTIME_SESSION: ContextVar[AsyncSession] = ContextVar("runtime_session")
"""
Context variable to store the current async database session.

This context variable allows async database sessions to be managed within
asynchronous contexts. Each asynchronous task can have its own session
stored in this variable.
"""


class RuntimeSession:
    """
    The basic class to perform database operations within an async session.

    This class provides a base for performing database operations within a
    specific async session. It handles session management, query execution, and
    common database error handling.

    Attributes:
        _ERRORS (tuple): A tuple of common SQLAlchemy errors that are handled
            by this class.
        _ctx_session (AsyncSession | None): an instance of a sqlAlchemy async session stored in the
        context variable, if none is stored it will be none.
    """
    _ctx_session: AsyncSession | None = None

    # All sqlalchemy errors that can be raised
    _ERRORS = (IntegrityError, InvalidRequestError)

    def __init__(self) -> None:
        """
        Initializes the RuntimeSession instance.

        Sets up the session manager for the async database connection.
        """
        self._ctx_session = None

    async def execute(self, query) -> Result:
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
        except self._ERRORS:
            raise DatabaseError

    @property
    def _session(self) -> AsyncSession:
        """
        Retrieves the current async database session.

        This property checks if a session is already available in the context
        variable. If it is, it returns that session; otherwise, it raises a
        DatabaseError.

        Returns:
            AsyncSession: The current async database session.

        Raises:
            DatabaseError: If no session is found in the context variable.
        """
        if not self._ctx_session:
            try:
                self._ctx_session = CTX_RUNTIME_SESSION.get()
            except LookupError:
                raise DatabaseError(message="Not in a transaction")
        return self._ctx_session
