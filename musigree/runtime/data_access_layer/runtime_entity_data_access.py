import logging
from typing import cast

from musigree.exceptions import NotFoundError
from musigree.library.cache.cache_manager import CacheManager
from musigree.library.fields.entity_type import EntityType
from musigree.logging_config import LOGGING_TRACE
from musigree.runtime.runtime_database.runtime_entity_repository import (
    RuntimeEntityRepository,
)
from musigree.runtime.runtime_domain.entity import RuntimeEntity
from musigree.runtime.runtime_domain.relation import RuntimeRelationResult

log = logging.getLogger(__name__)


class RuntimeEntityDataAccess:
    CACHE_ENTRY_IS_NULL = "___"
    CACHE_KEY_SEPARATOR = "_"

    @staticmethod
    def roles_to_relation_count(entity: RuntimeEntity, roles) -> int:
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
        entity: RuntimeEntity, roles
    ) -> dict[str, RuntimeRelationResult]:
        # log.debug(f"            structural_roles_to_relations entity: {self}")
        # log.debug(
        #     f"            structural_roles_to_relations entities: {self.entities}"
        # )
        # log.debug(f"            structural_roles_to_relations roles: {roles}")
        relations: dict[str, RuntimeRelationResult] = {}
        if entity.entity_type == EntityType.ARTIST:
            role = "Alias"
            if role in roles and "aliases" in entity.entities:
                for entity_id in entity.entities["aliases"].values():
                    if not entity_id:
                        continue
                    ids = sorted((entity_id, entity.entity_id))
                    relation = RuntimeRelationResult(
                        id=0,
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
                            id=0,
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
                            id=0,
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
                        id=0,
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
                        id=0,
                        entity_one_id=entity_id,
                        entity_one_type=entity.entity_type,
                        entity_two_id=entity.entity_id,
                        entity_two_type=entity.entity_type,
                        releases=None,
                        role=role,
                        distance=None,
                    )
                    relations[relation.link_key] = relation
        # log.debug(f"            structural_roles_to_relations relations: {relations}")
        return relations

    @staticmethod
    async def get_id_by_entity_type_and_entity_name(
        entity_repository: RuntimeEntityRepository,
        entity_type: EntityType,
        entity_name: str,
    ) -> int | None:
        cache = CacheManager.get_cache()

        entity_key_str = (
            f"{entity_name}{RuntimeEntityDataAccess.CACHE_KEY_SEPARATOR}{entity_type}"
        )

        id_ = cache.get(entity_key_str)
        if id_ == RuntimeEntityDataAccess.CACHE_ENTRY_IS_NULL:
            return None

        # if entity_id is not None:
        #     log.debug(f"cache hit for {key_str}")
        if id_ is None:
            # log.debug(f"not cached, try db")
            try:
                int_id = await entity_repository.get_id_by_entity_type_and_entity_name(
                    entity_type, entity_name
                )
                # Store the internal id, not entity_id
                cache.set(entity_key_str, int_id)
                # log.debug(f"cache set for {key_str} -> {int_id}")
                id_ = int_id

            except NotFoundError:
                if LOGGING_TRACE:
                    log.debug(
                        f"get_id_from_entity_type_and_entity_name key not found: {entity_key_str}"
                    )
                id_ = None
                cache.set(entity_key_str, RuntimeEntityDataAccess.CACHE_ENTRY_IS_NULL)

        return id_
