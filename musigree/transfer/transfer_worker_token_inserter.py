import asyncio
import logging
import multiprocessing
from typing import Any

from musigree.exceptions import DatabaseError
from musigree.runtime.data_access_layer.runtime_entity_data_access import RuntimeEntityDataAccess
from musigree.runtime.runtime_database.runtime_token_repository import RuntimeTokenRepository
from musigree.runtime.runtime_database.runtime_transaction import runtime_transaction
from musigree.runtime.runtime_database_manager import RuntimeDatabaseManager
from musigree.runtime.runtime_domain.runtime_token import RuntimeToken

log = logging.getLogger(__name__)


async def transfer_worker_token_inserter_async(
    bulk_inserts: list[dict[str, Any]], inserted_count: int, total_count: int
) -> None:
    """
    A worker process for inserting token records into the runtime database.
    This function is designed to be run in a separate process to handle the
    insertion of a batch of token records (`bulk_inserts`) into the
    runtime database, improving the efficiency of the data transfer process
    """

    proc_name = multiprocessing.current_process().name
    """Get the name of the current process."""

    count = 0

    """Async function to handle entity insertion."""
    async with runtime_transaction():
        """Ensure that database operations are performed within a transaction."""
        runtime_token_repository = RuntimeTokenRepository()
        """Instance of RuntimeTokenRepository for database operations on entities."""
        try:
            """Attempt to insert the entities."""
            await runtime_token_repository.save_all(bulk_inserts)
            """Insert the entities."""
            await runtime_token_repository.commit()
            """Commit the transaction."""
            count += len(bulk_inserts)
        except DatabaseError:
            """Handle potential database errors."""
            log.error("Error in transfer_worker_token_inserter")

    log.info(f"[{proc_name}] inserted {inserted_count + count} tokens of {total_count}")
    """Log the number of entities inserted."""


def transfer_worker_token_inserter(
    token_list: list[RuntimeToken], current_total: int, total_count: int
) -> None:
    # Run the async function
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        """Check if the event loop is already running."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        """Set a new event loop if none exists."""

    RuntimeDatabaseManager.reinitialize_runtime_database_async_engine(loop)
    """Initialize the database engine."""

    runtime_token_dicts_list = RuntimeEntityDataAccess.get_runtime_token_dicts_from_runtime_tokens(
        token_list
    )

    loop.run_until_complete(
        transfer_worker_token_inserter_async(runtime_token_dicts_list, current_total, total_count)
    )

    RuntimeDatabaseManager.dispose_runtime_database_async_engine(loop)
    """Close the database engine."""
