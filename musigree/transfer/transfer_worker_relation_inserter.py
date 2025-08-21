import asyncio
import logging
import multiprocessing
from typing import Any

from musigree.exceptions import DatabaseError
from musigree.runtime.runtime_database.runtime_relation_repository import (
    RuntimeRelationRepository,
)
from musigree.runtime.runtime_database.runtime_transaction import runtime_transaction
from musigree.runtime.runtime_database_manager import RuntimeDatabaseManager

log = logging.getLogger(__name__)


def transfer_worker_relation_inserter(
    bulk_inserts: list[dict[str, Any]], inserted_count: int, total_count: int
) -> None:
    """
    A worker process for inserting relation records into the runtime database.
    This function is designed to be run in a separate process to handle the
    insertion of a batch of relation records (`bulk_inserts`) into the
    runtime database, improving the efficiency of the data transfer process
    """

    async def insert_entities(_bulk_inserts: list[dict[str, Any]]) -> None:
        """Async function to handle entity insertion."""
        async with runtime_transaction():
            """Ensure that database operations are performed within a transaction."""
            runtime_relation_repository = RuntimeRelationRepository()
            """Instance of RuntimeRelationRepository for database operations on entities."""
            try:
                """Attempt to insert the entities."""
                await runtime_relation_repository.save_all(_bulk_inserts)
                """Insert the entities."""
                await runtime_relation_repository.commit()
                """Commit the transaction."""
            except DatabaseError:
                """Handle potential database errors."""
                log.error("Error in transfer_worker_relation_inserter")

        log.info(f"[{proc_name}] inserted {inserted_count} relations of {total_count}")
        """Log the number of entities inserted."""

    proc_name = multiprocessing.current_process().name
    """Get the name of the current process."""

    # Run the async function
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        """Check if the event loop is already running."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        """Set a new event loop if none exists."""

    if RuntimeDatabaseManager.get_concurrency_count() > 1:
        assert RuntimeDatabaseManager.runtime_database_helper is not None, (
            "runtime_database_helper must be initialized before calling initialize()"
        )
        """Check if concurrency is enabled."""
        RuntimeDatabaseManager.runtime_database_helper.initialize(loop)
        """Initialize the database helper."""

    loop.run_until_complete(insert_entities(bulk_inserts))
