"""
This module provides a context manager for managing database transactions in the offline environment.

It ensures that database operations are performed within a transaction,
and that transactions are committed or rolled back appropriately based on the
success or failure of the operations.
"""

import logging
from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy.exc import IntegrityError, InvalidRequestError
from sqlalchemy.orm import Session

from musigree.exceptions import DatabaseError
from musigree.offline.database.offline_session import (
    get_offline_session,
    CTX_OFFLINE_SESSION,
)

log = logging.getLogger(__name__)


@contextmanager
def offline_transaction() -> Iterator[Session]:
    """
    Provides a context manager for performing database transactions in the offline environment.

    This context manager handles the creation, commitment, and rollback of database
    transactions, ensuring that operations are performed atomically and consistently.

    It performs the following steps:
        1. Retrieves a new database session using `get_offline_session()`.
        2. Sets the current session in the `CTX_OFFLINE_SESSION` context variable,
           making it accessible to other parts of the application.
        3. Yields the session to the calling code, allowing database operations to be
           performed within the context.
        4. If the operations are successful, commits the transaction.
        5. If a `DatabaseError`, `IntegrityError`, or `InvalidRequestError` occurs, rolls
           back the transaction and re-raises the `DatabaseError`.
        6. Finally, closes the session, regardless of whether an error occurred.

    Yields:
        Iterator[Session]: A iterator that yields the database session.

    Raises:
        DatabaseError: If any error occurs during the transaction, including
            integrity errors or invalid request errors, the transaction is rolled
            back, and this exception is re-raised.
    """
    session: Session = get_offline_session()
    CTX_OFFLINE_SESSION.set(session)

    try:
        yield session
        session.commit()
    except DatabaseError as error:
        # NOTE: If any sort of issues are occurred in the code
        #       they are handled on the BaseCRUD level and raised
        #       as a DatabseError.
        #       If the DatabseError is handled within domain/application
        #       levels it is possible that `session.commit()`
        #       would raise an error.
        log.error(f"Rolling back changes. {error}")
        session.rollback()
        raise DatabaseError from error
    except (IntegrityError, InvalidRequestError) as error:
        # NOTE: Since there is a session commit on this level it should
        #       be handled because it can raise some errors also
        log.error(f"Rolling back changes. {error}")
        session.rollback()
    finally:
        session.close()
