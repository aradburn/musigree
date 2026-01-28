"""
This module provides a context manager for managing runtime_database transactions in the offline environment.

It ensures that runtime_database operations are performed within a transaction,
and that transactions are committed or rolled back appropriately based on the
success or failure of the operations.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.exc import IntegrityError, InvalidRequestError, MultipleResultsFound
from sqlalchemy.ext.asyncio import AsyncSession

from musigree.exceptions import DatabaseError
from musigree.offline.offline_database.offline_session import (
    get_offline_session,
    CTX_OFFLINE_SESSION,
)

log = logging.getLogger(__name__)


@asynccontextmanager
async def offline_transaction() -> AsyncGenerator[AsyncSession, None]:
    """
    Async context manager for handling offline runtime_database transactions.

    This context manager provides an offline runtime_database session and automatically
    handles transaction commit and rollback operations. It ensures that all
    runtime_database operations within the context are executed within a single
    transaction.

    Usage:
        async with offline_transaction() as session:
            # Perform runtime_database operations using the session
            pass

    Yields:
        AsyncSession: An async runtime_database session for performing operations.

    Raises:
        DatabaseError: If any error occurs during the transaction, including
            issues at the BaseCRUD level that are raised as DatabaseError,
            or if `session.commit()` raises an error.
    """
    session: AsyncSession = await get_offline_session()
    """Get a new offline runtime_database session."""
    old_token = CTX_OFFLINE_SESSION.set(session)
    """Set the new session to the context manager."""

    try:
        # log.debug("Transaction: yield session")
        yield session
        # log.debug("Transaction: after yield session")
        """Yield the session to be used in the transaction block."""
        await session.commit()
        """Commit the session, persist the changes to DB."""
    except DatabaseError as error:
        # NOTE: If any sort of issues are occurred in the code
        #       they are handled on the BaseCRUD level and raised
        #       as a DatabseError.
        #       If the DatabseError is handled within offline_domain/application
        #       levels it is possible that `await session.commit()`
        #       would raise an error.
        log.error(f"DatabaseError: Rolling back changes. {error}")
        """Log the error that happened during the session."""
        await session.rollback()
        """Rollback all the change made in this session."""
        raise error
    except IntegrityError as error:
        # NOTE: Since there is a session commit on this level it should
        #       be handled because it can raise some errors also
        log.error(f"IntegrityError: Rolling back changes. {error}")
        log.error(error.orig)
        log.error(error.statement)
        """Log the error that happened during the session."""
        await session.rollback()
        """Rollback all the change made in this session."""
        raise error
    except MultipleResultsFound as error:
        # NOTE: Since there is a session commit on this level it should
        #       be handled because it can raise some errors also
        log.error(f"MultipleResultsFound: Rolling back changes. {error}")
        log.error(error.__dict__)
        """Log the error that happened during the session."""
        await session.rollback()
        """Rollback all the change made in this session."""
        raise error
    except InvalidRequestError as error:
        # NOTE: Since there is a session commit on this level it should
        #       be handled because it can raise some errors also
        log.error(f"InvalidRequestError: Rolling back changes. {error}")
        log.error(error.args)
        log.error(error.code)
        """Log the error that happened during the session."""
        await session.rollback()
        """Rollback all the change made in this session."""
        raise error
    finally:
        # log.debug("Transaction: close session")
        await session.close()
        CTX_OFFLINE_SESSION.reset(old_token)
        """Close the session."""
