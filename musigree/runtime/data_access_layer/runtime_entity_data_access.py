import logging
import re
from typing import cast, Any

from sqlalchemy.exc import IntegrityError

from musigree.constants import CACHE_ENTRY_IS_NULL
from musigree.exceptions import NotFoundError, DatabaseError
from musigree.library.cache.cache_manager import CacheManager
from musigree.library.fields.entity_type import EntityType
from musigree.library.full_text_search.text_search_utils import normalise_search_content
from musigree.logging_config import LOGGING_TRACE
from musigree.offline.domain.entity import Entity
from musigree.runtime.runtime_database.runtime_entity_repository import (
    RuntimeEntityRepository,
)
from musigree.runtime.runtime_database.token_repository import TokenRepository
from musigree.runtime.runtime_domain.entity import RuntimeEntity, to_runtime_entity_dict
from musigree.runtime.runtime_domain.relation import RuntimeRelationResult

log = logging.getLogger(__name__)


class RuntimeEntityDataAccess:
    @staticmethod
    def roles_to_relation_count(entity: RuntimeEntity, roles: list[str]) -> int:
        count = 0
        relation_counts = entity.relation_counts or {}
        for role in roles:
            if role == "Alias":
                if "aliases" in entity.entities:
                    count += len(cast(dict, entity.entities["aliases"]))
            elif role == "Member Of":
                if "groups" in entity.entities:
                    count += len(cast(dict, entity.entities["groups"]))
                if "members" in entity.entities:
                    count += len(cast(dict, entity.entities["members"]))
            elif role == "Sublabel Of":
                if "parent_label" in entity.entities:
                    count += len(cast(dict, entity.entities["parent_label"]))
                if "sublabels" in entity.entities:
                    count += len(cast(dict, entity.entities["sublabels"]))
            else:
                count += relation_counts.get(role, 0)
        # log.debug(
        #     f"roles_to_relation_count entity: {entity} roles: {roles} -> {count})"
        # )
        return count

    @staticmethod
    def structural_roles_to_relations(
        entity: RuntimeEntity, roles: list[str]
    ) -> dict[str, RuntimeRelationResult]:
        log.debug(f"            structural_roles_to_relations entity_id: {entity.entity_id}")
        # log.debug(f"            structural_roles_to_relations entities: {entity.entities}")
        log.debug(f"            structural_roles_to_relations roles: {roles}")
        relations: dict[str, RuntimeRelationResult] = {}
        if entity.entity_type == EntityType.ARTIST:
            role = "Alias"
            if role in roles and "aliases" in entity.entities:
                for entity_id in entity.entities["aliases"].values():
                    if not entity_id:
                        continue
                    ids = sorted((entity_id, entity.entity_id))
                    relation = RuntimeRelationResult(
                        entity_one_id=ids[0],
                        entity_one_type=entity.entity_type,
                        entity_two_id=ids[1],
                        entity_two_type=entity.entity_type,
                        releases=None,
                        role=role,
                        distance=None,
                    )
                    relations[relation.link_key] = relation
            role = "Member Of"
            if role in roles:
                if "groups" in entity.entities:
                    for entity_id in entity.entities["groups"].values():
                        if not entity_id:
                            continue
                        relation = RuntimeRelationResult(
                            entity_one_id=entity.entity_id,
                            entity_one_type=entity.entity_type,
                            entity_two_id=entity_id,
                            entity_two_type=entity.entity_type,
                            releases=None,
                            role=role,
                            distance=None,
                        )
                        relations[relation.link_key] = relation
                if "members" in entity.entities:
                    for entity_id in entity.entities["members"].values():
                        if not entity_id:
                            continue
                        relation = RuntimeRelationResult(
                            entity_one_id=entity_id,
                            entity_one_type=entity.entity_type,
                            entity_two_id=entity.entity_id,
                            entity_two_type=entity.entity_type,
                            releases=None,
                            role=role,
                            distance=None,
                        )
                        relations[relation.link_key] = relation
        elif entity.entity_type == EntityType.LABEL and "Sublabel Of" in roles:
            role = "Sublabel Of"
            if "parent_label" in entity.entities:
                for entity_id in entity.entities["parent_label"].values():
                    if not entity_id:
                        continue
                    relation = RuntimeRelationResult(
                        entity_one_id=entity.entity_id,
                        entity_one_type=entity.entity_type,
                        entity_two_id=entity_id,
                        entity_two_type=entity.entity_type,
                        releases=None,
                        role=role,
                        distance=None,
                    )
                    relations[relation.link_key] = relation
            if "sublabels" in entity.entities:
                for entity_id in entity.entities["sublabels"].values():
                    if not entity_id:
                        continue
                    relation = RuntimeRelationResult(
                        entity_one_id=entity_id,
                        entity_one_type=entity.entity_type,
                        entity_two_id=entity.entity_id,
                        entity_two_type=entity.entity_type,
                        releases=None,
                        role=role,
                        distance=None,
                    )
                    relations[relation.link_key] = relation
        log.debug(
            f"            structural_roles_to_relations relations size: {len(relations.items())}"
        )
        return relations

    @staticmethod
    async def get_id_by_entity_type_and_entity_name(
        entity_repository: RuntimeEntityRepository,
        entity_type: EntityType,
        entity_name: str,
    ) -> int | None:
        """
        Retrieves the internal ID of an entity based on its type and name.

        This method first checks the cache for the entity ID. If not found, it
        queries the database and updates the cache.

        Args:
            entity_repository (RuntimeEntityRepository): The repository for entity database operations.
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
        id_: int | None = int(id_str) if id_str else None
        # If cache entry was marked as null, return None.
        if id_ == CACHE_ENTRY_IS_NULL:
            return None

        if id_ is None:
            try:
                # Get the internal id from the db.
                internal_id = await entity_repository.get_id_by_entity_type_and_entity_name(
                    entity_type, entity_name
                )

                # Cache the internal id, not entity_id
                await cache.set(entity_key_str, str(internal_id))
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
                if LOGGING_TRACE:
                    log.debug(
                        f"get_id_from_entity_type_and_entity_name key not found: {entity_key_str}"
                    )
                id_ = None
                # Mark the cache entry as null.
                await cache.set(entity_key_str, CACHE_ENTRY_IS_NULL)

        if id_ is None:
            return None
        return int(id_)

    @staticmethod
    async def get_entity_name_by_id(
        entity_repository: RuntimeEntityRepository, id_: int
    ) -> str | None:
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
                if LOGGING_TRACE:
                    log.debug(f"get_entity_name_by_id id not found: {id_}")
                name = None
                # Mark the cache entry as null.
                await cache.set(entity_key_str, CACHE_ENTRY_IS_NULL)

        return name

    @staticmethod
    def get_runtime_entity_dicts_from_entities(entity_list: list[Entity]) -> list[dict[str, Any]]:
        from musigree.runtime.runtime_database_manager import RuntimeDatabaseManager

        assert RuntimeDatabaseManager.runtime_database_helper is not None
        assert RuntimeDatabaseManager.runtime_database_helper.entity_details_index is not None

        runtime_entity_dict_list: list[dict[str, Any]] = []

        for entity in entity_list:
            runtime_entity_dict = to_runtime_entity_dict(
                RuntimeDatabaseManager.runtime_database_helper.entity_details_index, entity
            )
            runtime_entity_dict_list.append(runtime_entity_dict)

        return runtime_entity_dict_list

    @staticmethod
    async def find_entity_id_by_entity_type_and_entity_name(
        entity_repository: RuntimeEntityRepository,
        token_repository: TokenRepository,
        entity_type: EntityType,
        entity_name: str,
    ) -> int | None:
        from musigree.runtime.data_access_layer.runtime_entity_search import RuntimeEntitySearch

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
            search_data = await RuntimeEntitySearch.search_entities(
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
    async def process_profile_links(
        entity_repository: RuntimeEntityRepository, profile: str
    ) -> str:
        # Process all embedded profile links to add either missing entity_id or entity_name
        # There maybe multiple links
        # [a12345] -> [a12345=Artist Name]
        # [a=Artist Name] -> [a12345=Artist Name]
        # [l7890] -> [l7890=Label Name]
        # [l=Label Name] -> [l7890=Label Name]
        # [l7890=Label Name]
        # e.g. "Classic Techno label from Detroit, USA.\r\n[b]Label owner:[/b] [a=Carl Craig].\r\n" ->
        #      "Classic Techno label from Detroit, USA.\r\n[b]Label owner:[/b] [a871=Carl Craig].\r\n"
        # id -> name = entity_repository.get_entity_name_by_id()
        # name -> id = entity_repository.get_entity_id_by_entity_type_and_entity_name()

        # Map prefix to EntityType
        prefix_to_type = {
            "a": EntityType.ARTIST,
            "l": EntityType.LABEL,
        }

        # Pattern to match: [prefixid], [prefix=Name], or [prefixid=Name]
        # prefix is a single letter (a or l), id is digits, Name can contain any characters except ]
        pattern = r"\[([al])(\d*)(?:=([^\]]+))?\]"

        async def process_match(match: re.Match[str]) -> str:
            prefix = match.group(1)
            entity_id: int | None
            entity_id_str = match.group(2)  # Can be empty
            entity_name = match.group(3)  # Can be None

            entity_type = prefix_to_type.get(prefix)
            if entity_type is None:
                # Unknown prefix, return original
                return match.group(0)

            # Case 1: [prefixid=Name] - already complete, return as is
            if entity_id_str and entity_name:
                return match.group(0)

            # Case 2: [prefixid] - need to get name
            if entity_id_str and not entity_name:
                try:
                    entity_id = int(entity_id_str)
                    log.debug(f"entity_id: {entity_id}")
                    log.debug(f"entity_type: {entity_type}")

                    entity = await entity_repository.get_by_entity_id_and_entity_type(
                        entity_id, entity_type
                    )
                    return f"[{prefix}{entity_id}={entity.entity_name}]"
                except NotFoundError:
                    if LOGGING_TRACE:
                        log.debug(
                            f"process_profile_links: entity not found for {prefix}{entity_id_str}"
                        )
                    # Return original if entity not found
                    return match.group(0)

            # Case 3: [prefix=Name] - need to get entity_id
            if not entity_id_str and entity_name:
                log.debug(f"entity_type: {entity_type}")
                log.debug(f"entity_name: {entity_name}")

                token_repository = TokenRepository()

                candidate_entity_id = (
                    await RuntimeEntityDataAccess.find_entity_id_by_entity_type_and_entity_name(
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
                    if LOGGING_TRACE:
                        log.debug(
                            f"process_profile_links: entity_id not found for {prefix}={entity_name}"
                        )
                    # Return original if entity_id not found
                    return match.group(0)

            # Fallback: return original
            return match.group(0)

        # Find all matches and process them sequentially
        matches = list(re.finditer(pattern, profile))
        if not matches:
            return profile

        # Process all matches first to get replacements, then apply from end to start
        # to preserve indices when replacing
        replacements: list[tuple[re.Match[str], str]] = []
        for match in matches:
            log.debug(f"match1: {match}")
            replacement = await process_match(match)
            log.debug(f"replacement1: {replacement}")
            replacements.append((match, replacement))

        # Apply replacements from end to start to preserve indices
        result = profile
        for match, replacement in reversed(replacements):
            log.debug(f"match2: {match}")
            log.debug(f"replacement2: {replacement}")
            result = result[: match.start()] + replacement + result[match.end() :]

        return result

    @staticmethod
    async def get_by_entity_id_and_entity_type(
        entity_repository: RuntimeEntityRepository, entity_id: int, entity_type: EntityType
    ) -> RuntimeEntity:
        entity = await entity_repository.get_by_entity_id_and_entity_type(entity_id, entity_type)
        if entity is not None and entity.entity_metadata is not None:
            profile: str | None = entity.entity_metadata.get("profile", "")
            log.debug(f"profile: {profile}")
            if profile is not None and profile:
                log.debug(f"profile: {profile}")
                updated_profile = await RuntimeEntityDataAccess.process_profile_links(
                    entity_repository, profile
                )
                entity.entity_metadata["profile"] = updated_profile
                log.debug(f"updated_profile: {updated_profile}")
        return entity
