import logging
from typing import cast, Any

from sqlalchemy.exc import IntegrityError

from musigree.constants import CACHE_ENTRY_IS_NULL
from musigree.exceptions import NotFoundError, DatabaseError
from musigree.library.cache.cache_manager import CacheManager
from musigree.library.fields.entity_type import EntityType
from musigree.logging_config import LOGGING_TRACE
from musigree.offline.domain.entity import Entity
from musigree.runtime.runtime_database.runtime_entity_repository import (
    RuntimeEntityRepository,
)
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
        id_str: str | None = cache.get(entity_key_str)
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
                cache.set(entity_key_str, str(internal_id))
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
                cache.set(entity_key_str, CACHE_ENTRY_IS_NULL)

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

        name: str | None = cache.get(entity_key_str)
        if name == CACHE_ENTRY_IS_NULL:
            return None

        if name is None:
            try:
                name = await entity_repository.get_entity_name_by_id(id_)
                if name is not None:
                    cache.set(entity_key_str, name)
                else:
                    # Mark the cache entry as null.
                    cache.set(entity_key_str, CACHE_ENTRY_IS_NULL)
            except NotFoundError:
                if LOGGING_TRACE:
                    log.debug(f"get_entity_name_by_id id not found: {id_}")
                name = None
                # Mark the cache entry as null.
                cache.set(entity_key_str, CACHE_ENTRY_IS_NULL)

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
