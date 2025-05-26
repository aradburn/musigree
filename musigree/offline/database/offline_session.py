"""
This module defines the OfflineSession class and related utilities for managing
database sessions in the offline data loading and processing context.

It provides a mechanism for creating and managing SQLAlchemy sessions,
handling database errors, and using context variables to manage sessions in
concurrent environments.
"""

# noinspection PyPackageRequirements
from contextvars import ContextVar

from sqlalchemy.engine import ResultProxy
from sqlalchemy.exc import IntegrityError, InvalidRequestError
from sqlalchemy.orm import Session, scoped_session

from musigree.exceptions import DatabaseError


def get_offline_session() -> Session:
    """
    Creates a new session to execute SQL queries against the offline database.

    This function retrieves the session factory from the OfflineDatabaseManager
    and creates a new session. If concurrency is detected (more than one thread
    or process accessing the database), it uses a `scoped_session` to ensure
    thread-safety. Otherwise, it creates a regular session.

    Returns:
        Session: A new SQLAlchemy session.
    """
    from musigree.offline.offline_database_manager import OfflineDatabaseManager

    if OfflineDatabaseManager.get_concurrency_count() > 1:
        session = scoped_session(
            OfflineDatabaseManager.offline_database_helper.offline_session_factory
        )
    else:
        session = OfflineDatabaseManager.offline_database_helper.offline_session_factory
    return session()


CTX_OFFLINE_SESSION: ContextVar[Session] = ContextVar("offline_session")
"""
A ContextVar to store the active offline database session.

This allows for managing the session within a specific context, ensuring that
each coroutine or thread has its own session.
"""


class OfflineSession:
    """
    The basic class to perform database operations within a session.

    This class provides an interface for interacting with the database within a
    session context. It handles session management, query execution, and error
    handling.

    Attributes:
        _ERRORS (tuple): A tuple of SQLAlchemy exceptions to catch and handle as DatabaseError.
    """

    # All sqlalchemy errors that can be raised
    _ERRORS = (IntegrityError, InvalidRequestError)
    """A tuple of SQLAlchemy exceptions to catch and handle as DatabaseError."""

    def __init__(self) -> None:
        """
        Initializes the OfflineSession.

        Sets the context session to None, which will be populated when the
        session is accessed via the `_session` property.
        """
        self._ctx_session = None
        # self._session: Session = CTX_SESSION.get()

    def execute(self, query) -> ResultProxy:
        """
        Executes a SQL query within the current session.

        Args:
            query: The SQLAlchemy query to execute.

        Returns:
            ResultProxy: The result of the query execution.

        Raises:
            DatabaseError: If there is an error during query execution.
        """
        try:
            result = self._session.execute(query)
            return result
        except self._ERRORS:
            raise DatabaseError

    @property
    def _session(self) -> Session:
        """
        Retrieves the current session from the context or raises an error.

        This is a property that lazily retrieves the session from the
        `CTX_OFFLINE_SESSION` context variable. If no session is found, it
        raises a DatabaseError indicating that the code is not within a
        transaction.

        Returns:
            Session: The current SQLAlchemy session.

        Raises:
            DatabaseError: If no session is found in the context.
        """
        if not self._ctx_session:
            try:
                self._ctx_session: Session = CTX_OFFLINE_SESSION.get()
            except LookupError:
                raise DatabaseError(message="Not in a transaction")
        return self._ctx_session
