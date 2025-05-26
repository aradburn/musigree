"""
This module provides data access functionality for entities within the Musigree offline system.

It defines the `EntityDataAccess` class, which offers methods for resolving
entity and release references, caching entity IDs, and managing the text search
index. It is designed to be used during the offline data loading process.

Key functionalities include:
    - Resolving entity references: replacing entity names with internal IDs
      within entity and release data structures.
    - Resolving release references: updating label and company information to
      use internal IDs.
    - Caching entity IDs for fast lookup based on entity type and name.
    - Initializing the text search index with entity names and IDs.
    - Handling cases where entities are not found in the database.
    - Logging of debug and error messages during the data access operations.

The `EntityDataAccess` class interacts with `EntityRepository` for database
operations and `CacheManager` for caching. It also uses `TextSearchIndex` for
text search functionality and `LoaderBase` for bulk reporting.

The `Entity` and `Release` classes from `musigree.offline.domain` are used
to represent entities and releases, respectively. `EntityType` is used to
represent the different types of entities.
"""

import logging

from musigree.exceptions import NotFoundError
from musigree.library.cache.cache_manager import CacheManager
from musigree.library.fields.entity_id import to_entity_label_internal_id
from musigree.library.fields.entity_type import EntityType
from musigree.library.full_text_search.text_search_index import TextSearchIndex
from musigree.logging_config import LOGGING_TRACE
from musigree.offline.database.entity_repository import EntityRepository
from musigree.offline.domain.entity import Entity
from musigree.offline.domain.release import Release
from musigree.offline.loader.loader_base import LoaderBase

# TODO tidy up
log = logging.getLogger(__name__)
"""
The logger for the EntityDataAccess module.
"""


class EntityDataAccess:
    """
    Provides data access functionality for entities within the Musigree offline system.

    This class offers methods for resolving entity and release references, caching
    entity IDs, and managing the text search index.

    Attributes:
        CACHE_ENTRY_IS_NULL (str): A string used to represent a null entry in the cache.
        CACHE_KEY_SEPARATOR (str): A string used to separate parts of a cache key.
    """

    CACHE_ENTRY_IS_NULL = "___"
    """
    A string used to represent a null entry in the cache.

    This is used to indicate that an entity was looked up and not found, so
    future lookups can be avoided.
    """
    CACHE_KEY_SEPARATOR = "_"
    """
    A string used to separate parts of a cache key.

    This is used to create unique cache keys for different entity types and names.
    """

    @staticmethod
    def resolve_entity_references(
        entity_repository: EntityRepository, entity: Entity
    ) -> bool:
        """
        Resolves entity references within an entity's data structure.

        This method replaces entity names with their corresponding internal IDs
        in the `entities` attribute of an `Entity` object. It handles aliases,
        groups, and members for artists, and parent labels and sublabels for
        labels.

        Args:
            entity_repository (EntityRepository): The repository for entity database operations.
            entity (Entity): The entity object to resolve references in.

        Returns:
            bool: True if any references were resolved, False otherwise.

        Raises:
            ValueError: If the entity type is not ARTIST or LABEL.
        """
        if not entity.entities:
            return False

        if entity.entity_type == EntityType.ARTIST:
            is_resolved = False
            for section in ("aliases", "groups", "members"):
                if section not in entity.entities:
                    continue
                for entity_name in entity.entities[section].keys():
                    id_ = EntityDataAccess.get_id_by_entity_type_and_entity_name(
                        entity_repository, entity.entity_type, entity_name
                    )
                    if id_:
                        entity.entities[section][entity_name] = id_
                        is_resolved = True
            return is_resolved
        elif entity.entity_type == EntityType.LABEL:
            is_resolved = False
            for section in ("parent_label", "sublabels"):
                if section not in entity.entities:
                    continue
                for entity_name in entity.entities[section].keys():
                    id_ = EntityDataAccess.get_id_by_entity_type_and_entity_name(
                        entity_repository, entity.entity_type, entity_name
                    )
                    if id_:
                        entity.entities[section][entity_name] = id_
                        is_resolved = True
            return is_resolved
        else:
            raise ValueError("Bad entity_type")

    @staticmethod
    def resolve_release_references(
        entity_repository: EntityRepository, release: Release
    ):
        """
        Resolves release references within a release's data structure.

        This method updates label and company information in a `Release` object
        to use internal IDs instead of names.

        Args:
            entity_repository (EntityRepository): The repository for entity database operations.
            release (Release): The release object to resolve references in.

        Returns:
            bool: True if any references were resolved, False otherwise.
        """
        changed = False
        # NOTE: This was removed because it is now done in the runtime section
        # for entry in release.artists:
        #     entity_type = EntityType.ARTIST
        #     entity_id = entry["id"]
        #     id_ = EntityDataAccess.get_internal_id_by_entity_type_and_entity_id(
        #         entity_repository, entity_type, entity_id
        #     )
        #     if id_:
        #         entry["id"] = id_
        #     else:
        #         entry["id"] = -entity_id
        #     changed = True

        # for entry in release.extra_artists:
        #     entity_type = EntityType.ARTIST
        #     entity_id = entry["id"]
        #     id_ = EntityDataAccess.get_internal_id_by_entity_type_and_entity_id(
        #         entity_repository, entity_type, entity_id
        #     )
        #     if id_:
        #         entry["id"] = id_
        #     else:
        #         entry["id"] = -entity_id
        #     changed = True
        #
        # for entry in release.tracklist:
        #     if "artists" in entry:
        #         artists_list = entry["artists"]
        #         for artist_entry in artists_list:
        #             entity_type = EntityType.ARTIST
        #             entity_id = artist_entry["id"]
        #             id_ = EntityDataAccess.get_internal_id_by_entity_type_and_entity_id(
        #                 entity_repository, entity_type, entity_id
        #             )
        #             if id_:
        #                 artist_entry["id"] = id_
        #             else:
        #                 artist_entry["id"] = -entity_id
        #             changed = True
        #     if "extra_artists" in entry:
        #         extra_artists_list = entry["extra_artists"]
        #         for extra_artist_entry in extra_artists_list:
        #             entity_type = EntityType.ARTIST
        #             entity_id = extra_artist_entry["id"]
        #             id_ = EntityDataAccess.get_internal_id_by_entity_type_and_entity_id(
        #                 entity_repository, entity_type, entity_id
        #             )
        #             if id_:
        #                 extra_artist_entry["id"] = id_
        #             else:
        #                 extra_artist_entry["id"] = -entity_id
        #             changed = True

        for entry in release.labels:
            if "id" in entry:
                old_id = entry["id"]
                entry["id"] = to_entity_label_internal_id(old_id)
                if old_id != entry["id"]:
                    changed = True
            else:
                # Look up label name to get the id
                entity_type = EntityType.LABEL
                entity_name = entry["name"]
                id_ = entity_repository.get_entity_id_by_entity_type_and_entity_name(
                    entity_type, entity_name
                )
                entry["id"] = to_entity_label_internal_id(id_)
                changed = True

        for entry in release.companies:
            if "id" in entry:
                old_id = entry["id"]
                entry["id"] = to_entity_label_internal_id(old_id)
                if old_id != entry["id"]:
                    changed = True
            else:
                entity_type = EntityType.LABEL
                entity_name = entry["name"]
                id_ = entity_repository.get_entity_id_by_entity_type_and_entity_name(
                    entity_type, entity_name
                )
                entry["id"] = to_entity_label_internal_id(id_)
                changed = True

        return changed

    @staticmethod
    def get_id_by_entity_type_and_entity_name(
        entity_repository: EntityRepository,
        entity_type: EntityType,
        entity_name: str,
    ) -> int | None:
        """
        Retrieves the internal ID of an entity based on its type and name.

        This method first checks the cache for the entity ID. If not found, it
        queries the database and updates the cache.

        Args:
            entity_repository (EntityRepository): The repository for entity database operations.
            entity_type (EntityType): The type of the entity (e.g., ARTIST, LABEL).
            entity_name (str): The name of the entity.

        Returns:
            int | None: The internal ID of the entity, or None if not found.
        """
        cache = CacheManager.get_cache()
        """Get an instance of the cache."""

        entity_key_str = (
            f"{entity_name}{EntityDataAccess.CACHE_KEY_SEPARATOR}{entity_type}"
        )
        """Create the cache key."""

        id_ = cache.get(entity_key_str)
        """Get the value from the cache."""
        if id_ == EntityDataAccess.CACHE_ENTRY_IS_NULL:
            return None
        """If cache entry was marked as null, return None."""

        if id_ is None:
            try:
                int_id = entity_repository.get_id_by_entity_type_and_entity_name(
                    entity_type, entity_name
                )
                """Get the internal id from the db."""
                # Store the internal id, not entity_id
                cache.set(entity_key_str, int_id)
                """Cache the internal id."""
                id_ = int_id

            except NotFoundError:
                if LOGGING_TRACE:
                    log.debug(
                        f"get_id_from_entity_type_and_entity_name key not found: {entity_key_str}"
                    )
                id_ = None
                cache.set(entity_key_str, EntityDataAccess.CACHE_ENTRY_IS_NULL)
                """Mark the cache entry as null."""

        return id_

    @staticmethod
    def init_text_search_index(
        entity_repository: EntityRepository, index: TextSearchIndex
    ) -> None:
        """
        Initializes the text search index with entity names and IDs.

        This method iterates through all entities in the database and adds them
        to the text search index.

        Args:
            entity_repository (EntityRepository): The repository for entity database operations.
            index (TextSearchIndex): The text search index to initialize.
        """
        count = 0
        for id_, entity_name in entity_repository.all_ids_and_names():
            index.index_entry(id_, entity_name)
            count += 1
            if count % (LoaderBase.BULK_REPORTING_SIZE * 100) == 0:
                log.debug(f"Indexed {count} entities")
        index.reduce_list_to_set()
        index.print_sizes()
