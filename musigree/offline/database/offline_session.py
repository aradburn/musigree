"""
This module defines the OfflineSession class and related utilities for managing
database sessions in the offline data loading and processing context.

It provides a mechanism for creating and managing SQLAlchemy async sessions,
handling database errors, and using context variables to manage sessions in
concurrent environments.
"""

from contextvars import ContextVar
import asyncio

from sqlalchemy.engine import Result
from sqlalchemy.exc import IntegrityError, InvalidRequestError
from sqlalchemy.ext.asyncio import AsyncSession, async_scoped_session

from musigree.exceptions import DatabaseError


async def get_offline_session() -> AsyncSession:
    """
    Creates a new async session to execute SQL queries against the offline database.

    This function retrieves the session factory from the OfflineDatabaseManager
    and creates a new async session. If concurrency is detected (more than one thread
    or process accessing the database), it uses an `async_scoped_session` to ensure
    thread-safety. Otherwise, it creates a regular async session.

    Returns:
        AsyncSession: A new SQLAlchemy async session.
    """
    from musigree.offline.offline_database_manager import OfflineDatabaseManager

    assert OfflineDatabaseManager.offline_database_helper is not None, (
        "OfflineDatabaseManager.offline_database_helper must be initialized before calling get_offline_session()"
    )
    assert OfflineDatabaseManager.offline_database_helper.offline_session_factory is not None, (
        "OfflineDatabaseManager.offline_database_helper.offline_engine must be initialized before calling get_offline_session()"
    )

    # Note: The session factory should be an async_sessionmaker for this to work properly
    # This will need to be updated in the database helper classes
    session_factory = OfflineDatabaseManager.offline_database_helper.offline_session_factory
    
    if OfflineDatabaseManager.get_concurrency_count() > 1:
        _scoped_session: async_scoped_session[AsyncSession] = async_scoped_session(
            session_factory,  # type: ignore[arg-type]
            scopefunc=lambda: id(asyncio.current_task())
        )
        return _scoped_session()
    else:
        return session_factory()


CTX_OFFLINE_SESSION: ContextVar[AsyncSession] = ContextVar("offline_session")
"""
A ContextVar to store the active offline database async session.

This allows for managing the session within a specific context, ensuring that
each coroutine or thread has its own session.
"""


class OfflineSession:
    """
    The basic class to perform database operations within an async session.

    This class provides an interface for interacting with the database within a
    session context. It handles async session management, query execution, and error
    handling.

    Attributes:
        _ERRORS (tuple): A tuple of SQLAlchemy exceptions to catch and handle as DatabaseError.
    """
    _ctx_session: AsyncSession | None = None

    # All sqlalchemy errors that can be raised
    _ERRORS = (IntegrityError, InvalidRequestError)

    def __init__(self) -> None:
        """
        Initializes the OfflineSession.

        Sets the context session to None, which will be populated when the
        session is accessed via the `_session` property.
        """
        self._ctx_session = None

    async def execute(self, query) -> Result:
        """
        Executes a SQL query within the current async session.

        Args:
            query: The SQLAlchemy query to execute.

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
        Retrieves the current async session from the context or raises an error.

        This is a property that lazily retrieves the session from the
        `CTX_OFFLINE_SESSION` context variable. If no session is found, it
        raises a DatabaseError indicating that the code is not within a
        transaction.

        Returns:
            AsyncSession: The current SQLAlchemy async session.

        Raises:
            DatabaseError: If no session is found in the context.
        """
        if not self._ctx_session:
            try:
                self._ctx_session = CTX_OFFLINE_SESSION.get()
            except LookupError:
                raise DatabaseError(message="Not in a transaction")
        return self._ctx_session
