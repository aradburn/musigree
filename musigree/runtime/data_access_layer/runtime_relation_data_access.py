import logging

from musigree.library.cache.role_cache import RoleCache
from musigree.library.fields.entity_id import to_entity_internal_id
from musigree.library.fields.entity_type import EntityType
from musigree.runtime.runtime_database.runtime_relation_repository import (
    RuntimeRelationRepository,
)
from musigree.runtime.runtime_domain.relation import RuntimeRelation, RuntimeRelationInternal

log = logging.getLogger(__name__)


class RuntimeRelationDataAccess:
    @classmethod
    async def search_multi(
        cls,
        *,
        relation_repository: RuntimeRelationRepository,
        entity_keys: list[tuple[int, EntityType]],
        role_names: list[str],
    ) -> list[RuntimeRelation]:
        """
        Searches for relations involving multiple entities and specific roles.

        This method takes a list of entity keys and role names, and returns
        all relations that involve any of the specified entities in any of
        the specified roles.

        Args:
            relation_repository: The repository to use for database operations.
            entity_keys: List of (entity_id, entity_type) tuples to search for.
            role_names: List of role names to filter by.

        Returns:
            list[RuntimeRelation]: List of relations matching the criteria.
        """
        assert entity_keys
        assert role_names

        relation_internals: list[RuntimeRelationInternal] = []

        role_ids: list[int] = [
            RoleCache.role_name_to_role_id_lookup[role_name] for role_name in role_names
        ]

        for entity_id, entity_type in entity_keys:
            _id = to_entity_internal_id(entity_id, entity_type)
            # entity = entity_repository.get_by_entity_id_and_entity_type(
            #     entity_id, entity_type
            # )
            # log.debug(f"find_by_entity_and_roles: {_id} {role_ids}")
            entity_relations = await relation_repository.find_by_entity_and_roles(
                _id, role_ids
            )
            # log.debug(f"    found entity_relations: {entity_relations}")
            relation_internals.extend(entity_relations)

        relations = []
        for relation_internal in relation_internals:
            if relation_internal is not None:
                relation = relation_internal.to_relation()
                if relation is not None:
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
