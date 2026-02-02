"""
This module provides data access functionality for entities within the Musigree offline system.

It defines the `OfflineEntityDataAccess` class, which offers methods for resolving
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

The `OfflineEntityDataAccess` class interacts with `EntityRepository` for database
operations and `CacheManager` for caching. It also uses `TextSearchIndex` for
text search functionality and `LoaderBase` for bulk reporting.

The `Entity` and `Release` classes from `musigree.offline.offline_domain` are used
to represent entities and releases, respectively. `EntityType` is used to
represent the different types of entities.
"""

import logging
import re

from sqlalchemy.exc import IntegrityError

from musigree.constants import BULK_REPORTING_SIZE, CACHE_ENTRY_IS_NULL
from musigree.exceptions import NotFoundError, DatabaseError
from musigree.library.cache.cache_manager import CacheManager
from musigree.library.fields.entity_id import to_entity_label_internal_id
from musigree.library.fields.entity_type import EntityType
from musigree.library.full_text_search.text_search_index import TextSearchIndex
from musigree.library.full_text_search.text_search_utils import normalise_search_content
from musigree.offline.data_access_layer.offline_entity_search import OfflineEntitySearch
from musigree.offline.data_access_layer.offline_master_data_access import OfflineMasterDataAccess
from musigree.offline.data_access_layer.offline_release_data_access import OfflineReleaseDataAccess
from musigree.offline.offline_database.entity_repository import EntityRepository
from musigree.offline.offline_database.token_repository import TokenRepository
from musigree.offline.offline_domain.entity import Entity
from musigree.offline.offline_domain.release import Release

# TODO tidy up
log = logging.getLogger(__name__)
"""
The logger for the OfflineEntityDataAccess module.
"""


class OfflineEntityDataAccess:
    """
    Provides data access functionality for entities within the Musigree offline system.

    This class offers methods for resolving entity and release references, caching
    entity IDs, and managing the text search index.
    """

    @staticmethod
    async def resolve_entity_references(
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
                if not isinstance(entity.entities, dict):
                    continue
                if section not in entity.entities:
                    continue
                for entity_name in entity.entities[section].keys():
                    id_ = await OfflineEntityDataAccess.get_id_by_entity_type_and_entity_name(
                        entity_repository, entity.entity_type, entity_name
                    )
                    if id_:
                        entity.entities[section][entity_name] = id_
                        is_resolved = True
            return is_resolved
        elif entity.entity_type == EntityType.LABEL:
            is_resolved = False
            for section in ("parent_label", "sublabels"):
                if not isinstance(entity.entities, dict):
                    continue
                if section not in entity.entities:
                    continue
                for entity_name in entity.entities[section].keys():
                    id_ = await OfflineEntityDataAccess.get_id_by_entity_type_and_entity_name(
                        entity_repository, entity.entity_type, entity_name
                    )
                    if id_:
                        entity.entities[section][entity_name] = id_
                        is_resolved = True
            return is_resolved
        else:
            raise ValueError

    @staticmethod
    async def resolve_release_references(
        entity_repository: EntityRepository, release: Release
    ) -> bool:
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
        # TODO NOTE: This was removed because it is now done in the runtime section
        # for entry in release.artists:
        #     entity_type = EntityType.ARTIST
        #     entity_id = entry["id"]
        #     id_ = OfflineEntityDataAccess.get_internal_id_by_entity_type_and_entity_id(
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
        #     id_ = OfflineEntityDataAccess.get_internal_id_by_entity_type_and_entity_id(
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
        #             id_ = OfflineEntityDataAccess.get_internal_id_by_entity_type_and_entity_id(
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
        #             id_ = OfflineEntityDataAccess.get_internal_id_by_entity_type_and_entity_id(
        #                 entity_repository, entity_type, entity_id
        #             )
        #             if id_:
        #                 extra_artist_entry["id"] = id_
        #             else:
        #                 extra_artist_entry["id"] = -entity_id
        #             changed = True

        # Resolve labels and companies
        if release.labels is not None:
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
                    id_ = await entity_repository.get_entity_id_by_entity_type_and_entity_name(
                        entity_type, entity_name
                    )
                    entry["id"] = to_entity_label_internal_id(id_)
                    changed = True

        if release.companies is not None:
            for entry in release.companies:
                if "id" in entry:
                    old_id = entry["id"]
                    entry["id"] = to_entity_label_internal_id(old_id)
                    if old_id != entry["id"]:
                        changed = True
                else:
                    entity_type = EntityType.LABEL
                    entity_name = entry["name"]
                    id_ = await entity_repository.get_entity_id_by_entity_type_and_entity_name(
                        entity_type, entity_name
                    )
                    entry["id"] = to_entity_label_internal_id(id_)
                    changed = True

        return changed

    @staticmethod
    async def get_id_by_entity_type_and_entity_name(
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

        # Create the cache key.
        entity_key_str = CacheManager.create_cache_key(
            "entity",
            f"{entity_type.name.lower()}:{entity_name}",
            "id",
        )
        # Get the value from the cache.
        id_str: str | None = await cache.get(entity_key_str)
        # If cache entry was marked as null, return None.
        if id_str == CACHE_ENTRY_IS_NULL:
            return None
        id_: int | None = int(id_str) if id_str is not None else None

        if id_ is None:
            try:
                # Get the internal id from the db.
                internal_id = await entity_repository.get_id_by_entity_type_and_entity_name(
                    entity_type, entity_name
                )

                # Cache the internal id, not entity_id
                if internal_id is not None:
                    await cache.set(entity_key_str, str(internal_id))
                else:
                    await cache.set(entity_key_str, CACHE_ENTRY_IS_NULL)
                id_ = internal_id
            except IntegrityError:
                # Handle potential database errors.
                log.warning(
                    f"get_id_by_entity_type_and_entity_name Integrity Error for id: {entity_key_str}"
                )
                await entity_repository.rollback()
            except DatabaseError:
                # Handle potential database errors.
                log.warning(
                    f"get_id_by_entity_type_and_entity_name Database Error for id: {entity_key_str}"
                )
                await entity_repository.rollback()
            except NotFoundError:
                log.error(
                    f"get_id_from_entity_type_and_entity_name key not found: {entity_key_str}"
                )
                id_ = None
                # Mark the cache entry as null.
                await cache.set(entity_key_str, CACHE_ENTRY_IS_NULL)

        if id_ is None:
            return None
        return id_

    @staticmethod
    async def create_text_search_index(entity_repository: EntityRepository) -> TextSearchIndex:
        """
        Initializes the text search index with entity names and IDs.

        This method iterates through all entities in the database and adds them
        to the text search index.

        Args:
            entity_repository (EntityRepository): The repository for entity database operations.
        Returns:
            TextSearchIndex: The initialized text search index.
        """
        index = TextSearchIndex()
        count = 0
        async for tuple_list in entity_repository.all_ids_and_names():
            for id_, entity_name in tuple_list:
                index.index_entry(id_, entity_name)
                count += 1
                if count % (BULK_REPORTING_SIZE * 100) == 0:
                    log.debug(f"Indexed {count} entities")
        index.reduce_list_to_set()
        index.print_sizes()
        return index

    @staticmethod
    async def find_entity_id_by_entity_type_and_entity_name(
        entity_repository: EntityRepository,
        token_repository: TokenRepository,
        entity_type: EntityType,
        entity_name: str,
    ) -> int | None:
        # Normalize first
        normalised_entity_name = normalise_search_content(entity_name)

        # Try to get from cache first
        cache = CacheManager.get_cache()
        cache_key_str = CacheManager.create_cache_hkey("entity", f"name/{normalised_entity_name}")
        entity_id_str: str | None = await cache.get(cache_key_str)
        if entity_id_str == CACHE_ENTRY_IS_NULL:
            return None
        if entity_id_str is not None:
            return int(entity_id_str)

        # Not found in search results so far
        entity_id_str = CACHE_ENTRY_IS_NULL

        try:
            search_data = await OfflineEntitySearch.search_entities(
                entity_repository, token_repository, normalised_entity_name
            )
            for result_entry in search_data["results"]:
                result_dict: dict[str, str] = dict(result_entry)
                key = result_dict["key"]
                name = result_dict["name"]
                key_parts = key.split("-")
                candidate_entity_type = EntityType.from_str(key_parts[0])

                if candidate_entity_type == entity_type and entity_name == name:
                    entity_id_str = key_parts[1]
                    break

        except NotFoundError as _ex:
            entity_id_str = CACHE_ENTRY_IS_NULL

        # Cache the result
        await cache.set(cache_key_str, entity_id_str)

        if entity_id_str == CACHE_ENTRY_IS_NULL:
            return None

        return int(entity_id_str)

    @staticmethod
    async def process_profile_links(entity_repository: EntityRepository, profile: str) -> str:
        # Process all embedded profile links to add either missing entity_id or entity_name
        # There maybe multiple links
        # [a12345] -> [a12345=Artist Name]
        # [a=Artist Name] -> [a12345=Artist Name]
        # [l7890] -> [l7890=Label Name]
        # [l=Label Name] -> [l7890=Label Name]
        # [l7890=Label Name]
        # [m2775] -> [m2775=Master Record Title]
        # [r2775] -> [r2775=Release Title]
        # e.g. "Classic Techno label from Detroit, USA.\r\n[b]Label owner:[/b] [a=Carl Craig].\r\n" ->
        #      "Classic Techno label from Detroit, USA.\r\n[b]Label owner:[/b] [a871=Carl Craig].\r\n"
        # e.g. # [m2775] -> [m2775=Warp10+3 Remixes]
        #
        # Uses:
        # id -> name = entity_repository.get_entity_name_by_id()
        # name -> id = entity_repository.get_entity_id_by_entity_type_and_entity_name()
        # master_id -> master_title OfflineMasterDataAccess.get_master_title_from_master_id(master_id)
        # release_id -> release_title OfflineReleaseDataAccess.get_release_title_from_release_id(release_id)

        # Map prefix to EntityType
        prefix_to_type = {
            "a": EntityType.ARTIST,
            "l": EntityType.LABEL,
        }

        # Pattern to ref_match: [prefixid], [prefix=Name], or [prefixid=Name]
        # prefix is a single letter (a, l, m, or r), id is digits, Name can contain any characters except ]
        pattern = r"\[([alrm])(\d*)(?:=([^\]]+))?\]"

        async def process_match(ref_match: re.Match[str]) -> str:
            prefix = ref_match.group(1)
            entity_id: int | None
            entity_id_str = ref_match.group(2)  # Can be empty
            entity_name = ref_match.group(3)  # Can be None

            # Handle master references: [mid] -> [mid=Master Title]
            if prefix == "m":
                # Case 1: [mid=Title] - already complete, return as is
                if entity_id_str and entity_name:
                    return ref_match.group(0)

                # Case 2: [mid] - need to get master title
                if entity_id_str and not entity_name:
                    try:
                        master_id = int(entity_id_str)
                        master_title = (
                            await OfflineMasterDataAccess.get_master_title_from_master_id(master_id)
                        )
                        return f"[m{master_id}={master_title}]"
                    except NotFoundError:
                        log.error(f"process_profile_links: master not found for m{entity_id_str}")
                        # Return original if master not found
                        return ref_match.group(0)

                # Case 3: [m=value] - check if value is numeric ID
                if not entity_id_str and entity_name:
                    # Check if entity_name is numeric (malformed reference like [m=34567])
                    try:
                        master_id = int(entity_name)
                        log.debug(f"master_id (from malformed ref): {master_id}")

                        master_title = (
                            await OfflineMasterDataAccess.get_master_title_from_master_id(master_id)
                        )
                        return f"[m{master_id}={master_title}]"
                    except ValueError:
                        # Not numeric, name lookup not supported
                        log.error(
                            f"process_profile_links: master id lookup from name not supported for m={entity_name}"
                        )
                        return ref_match.group(0)
                    except NotFoundError:
                        log.error(f"process_profile_links: master not found for m{entity_name}")
                        # Transform malformed ref to correct format even if not found
                        return f"[m{int(entity_name)}]"

                # Fallback: return original
                return ref_match.group(0)

            # Handle release references: [rid] -> [rid=Release Title]
            if prefix == "r":
                # Case 1: [rid=Title] - already complete, return as is
                if entity_id_str and entity_name:
                    return ref_match.group(0)

                # Case 2: [rid] - need to get release title
                if entity_id_str and not entity_name:
                    try:
                        release_id = int(entity_id_str)
                        release_title = (
                            await OfflineReleaseDataAccess.get_release_title_from_release_id(
                                release_id
                            )
                        )
                        return f"[r{release_id}={release_title}]"
                    except NotFoundError:
                        log.error(f"process_profile_links: release not found for r{entity_id_str}")
                        # Return original if release not found
                        return ref_match.group(0)

                # Case 3: [r=value] - check if value is numeric ID
                if not entity_id_str and entity_name:
                    # Check if entity_name is numeric (malformed reference like [r=1234])
                    try:
                        release_id = int(entity_name)
                        log.debug(f"release_id (from malformed ref): {release_id}")

                        release_title = (
                            await OfflineReleaseDataAccess.get_release_title_from_release_id(
                                release_id
                            )
                        )
                        return f"[r{release_id}={release_title}]"
                    except ValueError:
                        # Not numeric, name lookup not supported
                        log.error(
                            f"process_profile_links: release id lookup from name not supported for r={entity_name}"
                        )
                        return ref_match.group(0)
                    except NotFoundError:
                        log.error(f"process_profile_links: release not found for r{entity_name}")
                        # Transform malformed ref to correct format even if not found
                        return f"[r{int(entity_name)}]"

                # Fallback: return original
                return ref_match.group(0)

            # Handle entity references (artist and label)
            entity_type = prefix_to_type.get(prefix)
            if entity_type is None:
                # Unknown prefix, return original
                return ref_match.group(0)

            # Case 1: [prefixid=Name] - already complete, return as is
            if entity_id_str and entity_name:
                return ref_match.group(0)

            # Case 2: [prefixid] - need to get name
            if entity_id_str and not entity_name:
                try:
                    entity_id = int(entity_id_str)
                    entity = await entity_repository.get_by_entity_id_and_entity_type(
                        entity_id, entity_type
                    )
                    return f"[{prefix}{entity_id}={entity.entity_name}]"
                except NotFoundError:
                    log.error(
                        f"process_profile_links: entity not found for {prefix}{entity_id_str}"
                    )
                    # Return original if entity not found
                    return ref_match.group(0)

            # Case 3: [prefix=Name] - need to get entity_id
            if not entity_id_str and entity_name:
                token_repository = TokenRepository()

                candidate_entity_id = (
                    await OfflineEntityDataAccess.find_entity_id_by_entity_type_and_entity_name(
                        entity_repository,
                        token_repository,
                        entity_type,
                        entity_name,
                    )
                )
                # entity_id = await entity_repository.get_entity_id_by_entity_type_and_entity_name(
                #     entity_type, entity_name
                # )
                if candidate_entity_id is not None:
                    return f"[{prefix}{candidate_entity_id}={entity_name}]"
                else:
                    log.error(
                        f"process_profile_links: entity_id not found for {prefix}={entity_name}"
                    )
                    # Return original if entity_id not found
                    return ref_match.group(0)

            # Fallback: return original
            return ref_match.group(0)

        # Find all matches and process them sequentially
        matches = list(re.finditer(pattern, profile))
        if not matches:
            return profile

        # Process all matches first to get replacements, then apply from end to start
        # to preserve indices when replacing
        replacements: list[tuple[re.Match[str], str]] = []
        for match in matches:
            replacement = await process_match(match)
            replacements.append((match, replacement))

        # Apply replacements from end to start to preserve indices
        result = profile
        for match, replacement in reversed(replacements):
            result = result[: match.start()] + replacement + result[match.end() :]

        return result

    @staticmethod
    async def get_by_entity_id_and_entity_type(
        entity_repository: EntityRepository, entity_id: int, entity_type: EntityType
    ) -> Entity:
        entity = await entity_repository.get_by_entity_id_and_entity_type(entity_id, entity_type)
        if entity is not None and entity.entity_metadata is not None:
            profile: str | None = entity.entity_metadata.get("profile", "")
            if profile is not None and profile:
                updated_profile = await OfflineEntityDataAccess.process_profile_links(
                    entity_repository, profile
                )
                entity.entity_metadata["profile"] = updated_profile
        return entity

    @staticmethod
    async def get_entity_name_by_id(entity_repository: EntityRepository, id_: int) -> str | None:
        cache = CacheManager.get_cache()

        # Create the cache key.
        entity_key_str = CacheManager.create_cache_key("entity", str(id_), "name")

        name: str | None = await cache.get(entity_key_str)
        if name == CACHE_ENTRY_IS_NULL:
            return None

        if name is None:
            try:
                name = await entity_repository.get_entity_name_by_id(id_)
                if name is not None:
                    await cache.set(entity_key_str, name)
                else:
                    # Mark the cache entry as null.
                    await cache.set(entity_key_str, CACHE_ENTRY_IS_NULL)
            except NotFoundError:
                log.error(f"get_entity_name_by_id id not found: {id_}")
                name = None
                # Mark the cache entry as null.
                await cache.set(entity_key_str, CACHE_ENTRY_IS_NULL)

        return name
