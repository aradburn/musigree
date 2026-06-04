"""
This module defines the OfflineSession class and related utilities for managing
runtime_database sessions in the offline data loading and processing context.

It provides a mechanism for creating and managing SQLAlchemy async sessions,
handling runtime_database errors, and using context variables to manage sessions in
concurrent environments.
"""

# noinspection PyPackageRequirements
from contextvars import ContextVar
from typing import Any

from sqlalchemy import CursorResult, Executable
from sqlalchemy.engine import Result
from sqlalchemy.exc import IntegrityError, InvalidRequestError
from sqlalchemy.ext.asyncio import AsyncSession

from musigree.exceptions import DatabaseError

CTX_OFFLINE_SESSION: ContextVar[AsyncSession] = ContextVar("offline_session")
"""
A ContextVar to store the active offline runtime_database async session.

This allows for managing the session within a specific context, ensuring that
each coroutine or thread has its own session.
"""


async def get_offline_session() -> AsyncSession:
    """
    Creates a new async session to execute SQL queries against the offline runtime_database.

    This function retrieves the session factory from the OfflineDatabaseManager
    and creates a new async session. If concurrency is detected (more than one thread
    or process accessing the runtime_database), it uses an `async_scoped_session` to ensure
    thread-safety. Otherwise, it creates a regular async session.

    Returns:
        AsyncSession: A new SQLAlchemy async session.
    """
    from musigree.offline.offline_database_manager import OfflineDatabaseManager

    assert OfflineDatabaseManager.offline_database_helper is not None, (
        "OfflineDatabaseManager.offline_database_helper must be initialized before calling get_offline_session()"
    )
    assert (
        OfflineDatabaseManager.offline_database_helper.offline_async_session_factory is not None
    ), (
        "OfflineDatabaseManager.offline_database_helper.offline_async_session_factory must be initialized before calling get_offline_session()"
    )
    assert OfflineDatabaseManager.offline_database_helper.offline_async_engine is not None, (
        "OfflineDatabaseManager.offline_database_helper.offline_async_engine must be initialized before calling get_offline_session()"
    )

    # from sqlalchemy.ext.asyncio import (
    #     async_scoped_session,
    #     async_sessionmaker,
    # )
    #
    # async_session_factory = async_sessionmaker(
    #     OfflineDatabaseManager.offline_database_helper.offline_async_engine,
    #     expire_on_commit=False,
    # )
    # get_async_scoped_session = async_scoped_session(
    #     async_session_factory,
    #     scopefunc=current_task,
    # )
    # return get_async_scoped_session()

    async_session_factory = (
        OfflineDatabaseManager.offline_database_helper.offline_async_session_factory
    )
    return async_session_factory()  # type: ignore


class OfflineSession:
    """
    The basic class to perform runtime_database operations within an async session.

    This class provides an interface for interacting with the runtime_database within a
    session context. It handles async session management, query execution, and error
    handling.
    """

    async def execute(self, query: Executable) -> Result[Any] | CursorResult[Any]:
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
            return result  # type: ignore
        except (IntegrityError, InvalidRequestError) as err:
            raise DatabaseError from err

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
        try:
            _session = CTX_OFFLINE_SESSION.get()
        except LookupError:
            raise DatabaseError(message="Not in a transaction") from None
        return _session
