"""
This module provides a context manager for managing database transactions in the runtime environment.

It defines the `runtime_transaction` context manager, which is used to
encapsulate database operations within a transaction. This ensures that
either all operations within the transaction succeed, or none do, maintaining
data integrity.

Key functionalities include:
    - Creating a new database session at the start of the transaction.
    - Setting the database session in a context variable for use within the transaction.
    - Committing the transaction if all operations are successful.
    - Rolling back the transaction if any errors occur.
    - Handling common database errors, such as integrity errors and invalid
      request errors.
    - Closing the database session at the end of the transaction.
"""

import logging
from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy.exc import IntegrityError, InvalidRequestError
from sqlalchemy.orm import Session

from musigree.exceptions import DatabaseError
from musigree.runtime.runtime_database.runtime_session import (
    get_runtime_session,
    CTX_RUNTIME_SESSION,
)

log = logging.getLogger(__name__)


@contextmanager
def runtime_transaction() -> Iterator[Session]:
    """
    Manages a database transaction within a context.

    This context manager is used to perform database transactions, ensuring
    that all operations within the context either succeed as a whole or are
    rolled back in case of any error. It is designed to be used in any
    coroutine within the codebase.

    Yields:
        Iterator[Session]: An iterator that yields the database
            session to be used within the transaction.

    Raises:
        DatabaseError: If any error occurs during the transaction, including
            issues at the BaseCRUD level that are raised as DatabaseError,
            or if `session.commit()` raises an error.
    """
    session: Session = get_runtime_session()
    """Get a new runtime database session."""
    CTX_RUNTIME_SESSION.set(session)
    """Set the new session to the context manager."""

    try:
        yield session
        """Yield the session to be used in the transaction block."""
        session.commit()
        """Commit the session, persist the changes to DB."""
    except DatabaseError as error:
        # NOTE: If any sort of issues are occurred in the code
        #       they are handled on the BaseCRUD level and raised
        #       as a DatabseError.
        #       If the DatabseError is handled within domain/application
        #       levels it is possible that `await session.commit()`
        #       would raise an error.
        log.error(f"Rolling back changes. {error}")
        """Log the error that happened during the session."""
        session.rollback()
        """Rollback all the change made in this session."""
        raise DatabaseError
    except (IntegrityError, InvalidRequestError) as error:
        # NOTE: Since there is a session commit on this level it should
        #       be handled because it can raise some errors also
        log.error(f"Rolling back changes. {error}")
        """Log the error that happened during the session."""
        session.rollback()
        """Rollback all the change made in this session."""
    finally:
        session.close()
        """Close the session."""
