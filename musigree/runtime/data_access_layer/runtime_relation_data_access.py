import logging
from typing import Any

from musigree.library.cache.role_cache import RoleCache
from musigree.offline.offline_domain.relation import RelationDB
from musigree.runtime.runtime_database.runtime_relation_repository import (
    RuntimeRelationRepository,
)
from musigree.runtime.runtime_domain.runtime_relation import (
    RuntimeRelation,
    RuntimeRelationInternal,
    to_runtime_relation_db_dict,
)

log = logging.getLogger(__name__)


class RuntimeRelationDataAccess:
    @classmethod
    async def search_multi(
        cls,
        *,
        relation_repository: RuntimeRelationRepository,
        ids: list[int],
        role_names: list[str],
    ) -> list[RuntimeRelation]:
        """
        Searches for relations involving multiple entities and specific roles.

        This method takes a list of entity keys and role names, and returns
        all relations that involve any of the specified entities in any of
        the specified roles.

        Args:
            relation_repository: The repository to use for runtime_database operations.
            ids: List of ids to search for.
            role_names: List of role names to filter by.

        Returns:
            list[RuntimeRelation]: List of relations matching the criteria.
        """
        assert ids
        assert role_names

        relation_internals: list[RuntimeRelationInternal] = []

        role_ids: list[int] = [
            RoleCache.role_name_to_role_id_lookup[role_name] for role_name in role_names
        ]

        for _id in ids:
            entity_relations = await relation_repository.find_by_entity_and_roles(_id, role_ids)
            # log.debug(f"    found entity_relations: {entity_relations}")
            relation_internals.extend(entity_relations)

        # Group relation_internals by link_key
        relations_map: dict[str, list[RuntimeRelationInternal]] = {}
        for relation_internal in relation_internals:
            key = relation_internal.link_key
            if key in relations_map:
                relation_internal_list = relations_map[key]
            else:
                relation_internal_list = []
            relation_internal_list.append(relation_internal)
            relations_map.update({key: relation_internal_list})

        relations: list[RuntimeRelation] = []
        for relation_internals in relations_map.values():
            relation = RuntimeRelation.from_relation_internals(relation_internals)
            relations.append(relation)

        # log.debug(f"    -> relations: {relations}")
        return relations

    # def search_bimulti(
    #     self,
    #     lh_entities: list[tuple[int, EntityType]],
    #     rh_entities: list[tuple[int, EntityType]],
    #     role_names: list[str] = None,
    #     year=None,
    #     verbose=True,
    # ) -> List[Relation]:
    #     lh_artist_ids = []
    #     lh_label_ids = []
    #     rh_artist_ids = []
    #     rh_label_ids = []
    #     for entity_id, entity_type in lh_entities:
    #         if entity_type == EntityType.ARTIST:
    #             lh_artist_ids.append(entity_id)
    #         else:
    #             lh_label_ids.append(entity_id)
    #     for entity_id, entity_type in rh_entities:
    #         if entity_type == EntityType.ARTIST:
    #             rh_artist_ids.append(entity_id)
    #         else:
    #             rh_label_ids.append(entity_id)
    #     relations: List[Relation] = []
    #     if lh_artist_ids:
    #         lh_type = EntityType.ARTIST
    #         lh_ids = lh_artist_ids
    #         if rh_artist_ids:
    #             rh_type = EntityType.ARTIST
    #             rh_ids = rh_artist_ids
    #             results1 = self.find_by_type_and_ids_and_role_names(
    #                 lh_type, lh_ids, rh_type, rh_ids, role_names
    #             )
    #             relations.extend(results1)
    #         if rh_label_ids:
    #             rh_type = EntityType.LABEL
    #             rh_ids = rh_label_ids
    #             results2 = self.find_by_type_and_ids_and_role_names(
    #                 lh_type, lh_ids, rh_type, rh_ids, role_names
    #             )
    #             relations.extend(results2)
    #     if lh_label_ids:
    #         lh_type = EntityType.LABEL
    #         lh_ids = lh_label_ids
    #         if rh_artist_ids:
    #             rh_type = EntityType.ARTIST
    #             rh_ids = rh_artist_ids
    #             results3 = self.find_by_type_and_ids_and_role_names(
    #                 lh_type, lh_ids, rh_type, rh_ids, role_names
    #             )
    #             relations.extend(results3)
    #         if rh_label_ids:
    #             rh_type = EntityType.LABEL
    #             rh_ids = rh_label_ids
    #             results4 = self.find_by_type_and_ids_and_role_names(
    #                 lh_type, lh_ids, rh_type, rh_ids, role_names
    #             )
    #             relations.extend(results4)
    #     return relations
    #     # for query in queries:
    #     #     log.debug(f"search_bimulti query: {query}")
    #     #     relations.extend(query)
    #     # relation_links = {relation.link_key: relation for relation in relations}
    #     # log.debug(f"relation_links: {relation_links}")
    #     # return relation_links

    @staticmethod
    def get_runtime_relation_dicts_from_relations(
        relation_dbs: list[RelationDB],
    ) -> list[dict[str, Any]]:
        from musigree.runtime.runtime_database_manager import RuntimeDatabaseManager

        assert RuntimeDatabaseManager.runtime_database_helper is not None
        runtime_relation_dict_list: list[dict[str, Any]] = []
        for relation_db in relation_dbs:
            runtime_relation_dict = to_runtime_relation_db_dict(relation_db)
            runtime_relation_dict_list.append(runtime_relation_dict)
        return runtime_relation_dict_list
