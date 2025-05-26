"""
This module defines the `WorkerEntityUpdater` class, which is a worker process
responsible for updating or inserting entity records in the Musigree offline
database.

It utilizes `multiprocessing` to enable concurrent updating and insertion of
entities, improving the efficiency of the data loading process. The
`WorkerEntityUpdater` handles updating existing entity records with new
information, as well as inserting new entity records if they do not already
exist in the database.

Key functionalities include:
    - **Concurrent Updating/Inserting**: Employs `multiprocessing.Process` to
      perform update and insert operations concurrently, speeding up the
      processing of large numbers of entities.
    - **Batch Processing**: Processes a list of entity data (`bulk_updates`) in
      a single run, minimizing database interactions.
    - **Database Transactions**: Uses `offline_transaction` to ensure that each
      update or insert operation is atomic, maintaining data integrity.
    - **Error Handling**: Implements error handling using `try...except` blocks
      to catch `NotFoundError` and `DatabaseError` exceptions and handle them
      appropriately.
    - **Entity Access**: Uses `EntityRepository` to access and update or insert
      entity data.
    - **Reference Resolution**: Resolves entity references (e.g., aliases,
      groups, members) within the entity data.
    - **Process Initialization**: Handles the initialization of the database
      helper in each worker process when concurrency is enabled.
    - **Change Detection**: Uses `DeepDiff` to detect changes between the
      existing entity and the new data, only updating fields that have changed.
    - **Search Content Normalization**: Normalizes entity names for full-text
      search.
    - **Logging**: Provides detailed logging of the update and insertion
      process, including the number of updated and inserted entities.

The `WorkerEntityUpdater` class interacts with the following components:
    - `multiprocessing.Process`: The base class for creating worker processes.
    - `OfflineDatabaseHelper`: For managing database connections and
      initialization in a concurrent environment.
    - `EntityRepository`: For database operations related to entities.
    - `Entity`: The domain object representing an entity.
    - `EntityTable`: For accessing the entity table definition.
    - `DeepDiff`: For comparing the existing entity with the new data.
    - `normalise_search_content`: A function for normalizing search content.
    - `offline_transaction`: A decorator for managing database transactions.
    - `OfflineDatabaseManager`: For managing database concurrency settings.
    - `logging`: For logging operations.
    - `NotFoundError`: Used for handling the not found exception.
    - `DatabaseError`: Used for handling the database exception.
    - `LOGGING_TRACE`: Used to check if trace logging is activated.

The module utilizes `logging` for logging operations, `multiprocessing` for
process management, `sqlalchemy.exc.DatabaseError` for database
related exception and `pprint` for pretty print the diff between entities. It
interacts with `musigree.offline.database` for database related operations,
`musigree.library.full_text_search` for text normalization and
`musigree.offline.offline_database_manager` for managing concurrency.
"""

import logging
import multiprocessing
import pprint
from typing import Any

from deepdiff import DeepDiff

from musigree.exceptions import DatabaseError, NotFoundError
from musigree.library.full_text_search.text_search_utils import (
    normalise_search_content,
)
from musigree.logging_config import LOGGING_TRACE
from musigree.offline.database.offline_database_helper import OfflineDatabaseHelper
from musigree.offline.database.entity_repository import EntityRepository
from musigree.offline.database.entity_table import EntityTable
from musigree.offline.database.offline_transaction import offline_transaction
from musigree.offline.domain.entity import Entity
from musigree.offline.offline_database_manager import OfflineDatabaseManager

log = logging.getLogger(__name__)
"""
The logger for the WorkerEntityUpdater module.
"""


class WorkerEntityUpdater(multiprocessing.Process):
    """
    A worker process for updating or inserting entity records.

    This class extends `multiprocessing.Process` to perform concurrent
    update and insert operations on entity records.
    """

    def __init__(self, bulk_updates: list[dict[str, Any]], processed_count: int):
        """
        Initializes the WorkerEntityUpdater.

        Args:
            bulk_updates (list[dict[str, Any]]): A list of entity data to update or insert.
            processed_count (int): The number of entities processed so far.
        """
        super().__init__()
        """Call the constructor of the parent class."""
        self.bulk_updates = bulk_updates
        """The list of entity data to update or insert."""
        self.processed_count = processed_count
        """The number of entities processed so far."""

    def run(self):
        """
        Executes the entity update/insert process.

        This method performs the following steps:
            1. Initializes the database helper if concurrency is enabled.
            2. Iterates through the list of entity data.
            3. For each entity data, starts a database transaction.
            4. Attempts to retrieve the existing entity from the database.
            5. If the entity exists, compares it with the new data using DeepDiff.
            6. Updates the entity with any changed fields.
            7. If the entity does not exist, creates a new entity.
            8. Handles `NotFoundError` and `DatabaseError` exceptions.
            9. Logs the progress and number of entities updated and inserted.
        """
        proc_name = self.name
        """Get the name of the current process."""
        updated_count = 0
        """Counter for the number of entities updated."""
        inserted_count = 0
        """Counter for the number of entities inserted."""

        if OfflineDatabaseManager.get_concurrency_count() > 1:
            """Check if concurrency is enabled."""
            OfflineDatabaseHelper.initialize()
            """Initialize the database helper."""

        for data in self.bulk_updates:
            """Iterate over the entity data."""
            with offline_transaction():
                """Ensure that database operations are performed within a transaction."""
                entity_repository = EntityRepository()
                """Instance of EntityRepository for database operations on entities."""
                updated_entity = Entity(**data)
                """Create a new Entity object from the data."""
                try:
                    """Attempt to update the entity."""
                    if LOGGING_TRACE:
                        """Log if trace logging is enabled."""
                        log.debug(
                            f"update: {updated_entity.entity_id}-{updated_entity.entity_type}"
                        )

                    db_entity = entity_repository.get_by_entity_id_and_entity_type(
                        updated_entity.entity_id, updated_entity.entity_type
                    )
                    """Retrieve the existing entity from the database."""

                    is_changed = False
                    """Flag to check if any changes were made."""
                    update_payload = {}
                    """Dictionary to store the update payload."""

                    if db_entity.entity_name != updated_entity.entity_name:
                        """Check if the entity name has changed."""
                        # Update name
                        db_entity.entity_name = updated_entity.entity_name
                        update_payload[EntityTable.entity_name.key] = (
                            db_entity.entity_name
                        )
                        """Update the entity name."""

                        # Update search_content
                        db_entity.search_content = normalise_search_content(
                            updated_entity.entity_name
                        )
                        update_payload[EntityTable.search_content.key] = (
                            db_entity.search_content
                        )
                        """Update the search content."""
                        is_changed = True
                        """Set the changed flag."""

                    # Update metadata
                    differences = DeepDiff(
                        db_entity,
                        updated_entity,
                        include_paths=[
                            "entity_metadata",
                        ],
                        ignore_numeric_type_changes=True,
                    )
                    """Compare the entity metadata."""
                    diff = pprint.pformat(differences)
                    """Format the diff for logging."""
                    if diff != "{}":
                        """If there are any differences."""
                        if LOGGING_TRACE:
                            """Log the differences if trace logging is enabled."""
                            log.debug(f"diff: {diff}")
                        # log.debug(f"db_entity     : {db_entity}")
                        # log.debug(f"updated_entity: {updated_entity}")

                        db_entity.entity_metadata = updated_entity.entity_metadata
                        """Update the entity metadata."""

                        update_payload[EntityTable.entity_metadata.key] = (
                            db_entity.entity_metadata
                        )
                        """Add the metadata to the update payload."""
                        is_changed = True
                        """Set the changed flag."""

                    if is_changed:
                        """If any changes were made, update the entity."""
                        entity_repository.update(db_entity.id, update_payload)
                        """Update the entity."""
                        entity_repository.commit()
                        """Commit the transaction."""
                        updated_count += 1
                        """Increment the updated count."""
                except NotFoundError:
                    """Handle the case where the entity is not found."""
                    # log.debug(
                    #     f"New insert in WorkerEntityUpdater: {updated_entity.entity_id}-{updated_entity.entity_type}"
                    # )
                    try:
                        """Attempt to create a new entity."""
                        entity_repository.create(updated_entity)
                        """Create the entity."""
                        entity_repository.commit()
                        """Commit the transaction."""
                        inserted_count += 1
                        """Increment the inserted count."""
                    except DatabaseError as e:
                        """Handle database errors."""
                        log.exception("Error in WorkerEntityUpdater worker")
                        raise e
                except DatabaseError as e:
                    """Handle database errors."""
                    log.exception("Error in WorkerEntityUpdater", e)
                    raise e

        log.info(
            f"[{proc_name}] processed_count: {self.processed_count}, "
            + f"updated: {updated_count}, inserted: {inserted_count}"
        )
        """Log the number of entities processed, updated, and inserted."""
