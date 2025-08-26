"""
This module defines the `delete_entities_worker` function, which is a worker function
responsible for deleting entity records and their associated relations from the
Musigree offline database.

It is designed to be used with `concurrent.futures.ProcessPoolExecutor` to enable
concurrent deletion of entities, improving the efficiency of the data loading process.
The function handles the deletion of both entity records and related data in the relation
repository.

Key functionalities include:
    - **Concurrent Deletion**: Designed to work with `ProcessPoolExecutor` to perform
      deletion operations concurrently, speeding up the deletion of large
      numbers of entities.
    - **Batch Deletion**: Processes a list of entity IDs (`bulk_deletes`) in a
      single run, minimizing database interactions.
    - **Database Transactions**: Uses `offline_transaction` to ensure that each
      deletion operation is atomic, maintaining data integrity.
    - **Error Handling**: Implements error handling using `try...except` blocks
      to catch `DatabaseError` exceptions and log them.
    - **Entity and Relation Deletion**: Deletes both the entity record and
      any associated relations using `EntityRepository` and `RelationRepository`.
    - **Process Initialization**: Handles the initialization of the database
      helper in each worker process when concurrency is enabled.
    - **Logging**: Provides detailed logging of the deletion process, including
      the number of processed and deleted entities.

The `delete_entities_worker` function interacts with the following components:
    - `OfflineDatabaseHelper`: For managing database connections and
      initialization in a concurrent environment.
    - `EntityRepository`: For database operations related to entities.
    - `RelationRepository`: For database operations related to relations.
    - `offline_transaction`: A decorator for managing database transactions.
    - `OfflineDatabaseManager`: For managing database concurrency settings.
    - `logging`: For logging operations.

The module utilizes `logging` for logging operations and `sqlalchemy.exc.DatabaseError`
for database related exceptions.
"""

import logging
import multiprocessing

from musigree.exceptions import DatabaseError
from musigree.offline.database.entity_repository import EntityRepository
from musigree.offline.database.offline_transaction import offline_transaction
from musigree.offline.database.relation_repository import RelationRepository
from musigree.offline.loader.loader_base import LoaderBase

log = logging.getLogger(__name__)
"""
The logger for the worker entity deleter module.
"""


async def delete_entities_worker(ids: list[int], current_total: int, total_count: int) -> None:
    """Worker function for deleting entity records from the database.
    This function is designed to be used with ProcessPoolExecutor to perform
    concurrent deletion of entity records.
    Args:
        ids (list[int]): A list of entity IDs to delete.
        current_total (int): The number of entities processed so far.
        total_count (int): The total number of entities to be processed.
    Raises:
        DatabaseError: If there's an error during database operations.
    """

    proc_name = multiprocessing.current_process().name
    """Get the name of the current process."""
    count = 0
    """Counter for the number of entities deleted."""
    end_count = count + len(ids)

    async with offline_transaction():
        """Ensure that database operations are performed within a transaction."""
        entity_repository = EntityRepository()
        """Instance of EntityRepository for database operations on entities."""
        relation_repository = RelationRepository()
        """Instance of RelationRepository for database operations on relations."""
        for entity_id in ids:
            """Iterate through the entity IDs to delete."""
            await delete_single_entity(entity_repository, relation_repository, entity_id)
            count += 1
            if count % LoaderBase.BULK_REPORTING_SIZE == 0 and not count == end_count:
                log.debug(f"[{proc_name}] deleted {count}")

    log.info(f"[{proc_name}] processed {current_total} deleted {count} of {total_count}")
    """Log the progress and number of deleted entities."""

async def delete_single_entity(
    entity_repository: EntityRepository, relation_repository: RelationRepository, entity_id: int
) -> None:
    """Async function to handle entity deletion.
        Args:
            entity_repository (EntityRepository): The repository for entity operations.
            relation_repository (RelationRepository): The repository for relation operations.
            entity_id (int): The ID of the entity to delete.
        Raises:
            DatabaseError: If there's an error during database operations.
        """
    try:
        """Attempt to delete the entity and its relations."""
        await relation_repository.delete_by_entitys(entity_id)
        """Delete the relations associated with the entity."""
        await entity_repository.delete_by_id(entity_id)
        """Delete the entity itself."""
    except DatabaseError:
        """Handle potential database errors."""
        log.error(f"Error in delete_entities_worker for id: {entity_id}")
        raise
