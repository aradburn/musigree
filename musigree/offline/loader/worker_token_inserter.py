import asyncio
import logging
import multiprocessing
from typing import Any

from musigree.exceptions import DatabaseError
from musigree.offline.data_access_layer.offline_entity_data_access import OfflineEntityDataAccess
from musigree.offline.offline_database.offline_transaction import offline_transaction
from musigree.offline.offline_database.token_repository import TokenRepository
from musigree.offline.offline_database_manager import OfflineDatabaseManager
from musigree.offline.offline_domain.token import Token

log = logging.getLogger(__name__)


async def worker_token_inserter_async(
    bulk_inserts: list[dict[str, Any]], inserted_count: int, total_count: int
) -> None:
    """
    A worker process for inserting token records into the offline database.
    This function is designed to be run in a separate process to handle the
    insertion of a batch of token records (`bulk_inserts`) into the
    offline database, improving the efficiency of the data transfer process
    """

    proc_name = multiprocessing.current_process().name
    """Get the name of the current process."""

    count = 0

    """Async function to handle entity insertion."""
    async with offline_transaction():
        """Ensure that database operations are performed within a transaction."""
        offline_token_repository = TokenRepository()
        """Instance of TokenRepository for database operations on entities."""
        try:
            """Attempt to insert the entities."""
            await offline_token_repository.save_all(bulk_inserts)
            """Insert the entities."""
            await offline_token_repository.commit()
            """Commit the transaction."""
            count += len(bulk_inserts)
        except DatabaseError:
            """Handle potential database errors."""
            log.error("Error in worker_token_inserter")

    log.info(f"[{proc_name}] inserted {inserted_count + count} tokens of {total_count}")
    """Log the number of tokens inserted."""


def worker_token_inserter(token_list: list[Token], current_total: int, total_count: int) -> None:
    # Run the async function
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        """Check if the event loop is already running."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        """Set a new event loop if none exists."""

    OfflineDatabaseManager.reinitialize_offline_database_async_engine(loop)
    """Initialize the database engine."""

    offline_token_dicts_list = OfflineEntityDataAccess.get_offline_token_dicts_from_offline_tokens(
        token_list
    )

    loop.run_until_complete(
        worker_token_inserter_async(offline_token_dicts_list, current_total, total_count)
    )

    OfflineDatabaseManager.dispose_offline_database_async_engine(loop)
    """Close the database engine."""
