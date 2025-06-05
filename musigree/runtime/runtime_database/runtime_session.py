"""
This module defines the `RuntimeSession` class and related utilities for managing database sessions
in the runtime environment.

It provides a centralized way to handle database sessions, including creating,
executing queries, and managing transactions. It also utilizes a context variable
to manage sessions within asynchronous contexts.

Key functionalities include:
    - Creating new database sessions using `get_runtime_session`.
    - Providing a base class `RuntimeSession` for database operations within a session.
    - Executing SQL queries and handling common database errors.
    - Managing the database session through a context variable (`CTX_RUNTIME_SESSION`).
"""

# noinspection PyPackageRequirements
from contextvars import ContextVar

from sqlalchemy.engine import ResultProxy
from sqlalchemy.exc import IntegrityError, InvalidRequestError
from sqlalchemy.orm import Session, scoped_session

from musigree.exceptions import DatabaseError


def get_runtime_session() -> Session:
    """
    Creates a new session to execute SQL queries.

    This function is responsible for creating a new database session,
    which is used to interact with the database. It determines whether to
    use a scoped session or a regular session based on the concurrency
    count.

    Returns:
        Session: A new database session.
    """
    from musigree.runtime.runtime_database_manager import RuntimeDatabaseManager

    if RuntimeDatabaseManager.get_concurrency_count() > 1:
        _scoped_session = scoped_session(
            RuntimeDatabaseManager.runtime_database_helper.runtime_session_factory
        )
        return _scoped_session()
    else:
        _session = RuntimeDatabaseManager.runtime_database_helper.runtime_session_factory
        return _session()


CTX_RUNTIME_SESSION: ContextVar[Session] = ContextVar("runtime_session")
"""
Context variable to store the current database session.

This context variable allows database sessions to be managed within
asynchronous contexts. Each asynchronous task can have its own session
stored in this variable.
"""


class RuntimeSession:
    """
    The basic class to perform database operations within the session.

    This class provides a base for performing database operations within a
    specific session. It handles session management, query execution, and
    common database error handling.

    Attributes:
        _ERRORS (tuple): A tuple of common SQLAlchemy errors that are handled
            by this class.
        _ctx_session (Session | None): an instance of a sqlAlchemy session stored in the
        context variable, if none is stored it will be none.
    """
    _ctx_session: Session | None = None

    # All sqlalchemy errors that can be raised
    _ERRORS = (IntegrityError, InvalidRequestError)

    def __init__(self) -> None:
        """
        Initializes the RuntimeSession instance.

        Sets up the session manager for the database connection.
        """
        self._ctx_session = None

    def execute(self, query) -> ResultProxy:
        """
        Executes a SQL query within the current session.

        Args:
            query: The SQL query to execute.

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
        Retrieves the current database session.

        This property checks if a session is already available in the context
        variable. If it is, it returns that session; otherwise, it raises a
        DatabaseError.

        Returns:
            Session: The current database session.

        Raises:
            DatabaseError: If no session is found in the context variable.
        """
        if not self._ctx_session:
            try:
                self._ctx_session = CTX_RUNTIME_SESSION.get()
            except LookupError:
                raise DatabaseError(message="Not in a transaction")
        return self._ctx_session
