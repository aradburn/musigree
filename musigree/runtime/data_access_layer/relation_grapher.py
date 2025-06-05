import logging
from abc import ABC
from collections import OrderedDict

from musigree import utils
from musigree.library.cache.role_cache import RoleCache
from musigree.library.fields.entity_type import EntityType
from musigree.runtime.data_access_layer.runtime_entity_data_access import (
    RuntimeEntityDataAccess,
)
from musigree.runtime.data_access_layer.runtime_relation_data_access import (
    RuntimeRelationDataAccess,
)
from musigree.runtime.data_access_layer.trellis_node import TrellisNode
from musigree.runtime.runtime_database.runtime_entity_repository import (
    RuntimeEntityRepository,
)
from musigree.runtime.runtime_database.runtime_relation_repository import (
    RuntimeRelationRepository,
)
from musigree.runtime.runtime_domain.entity import RuntimeEntity
from musigree.runtime.runtime_domain.relation import RuntimeRelationResult

log = logging.getLogger(__name__)


class RelationGrapher(ABC):
    # CLASS VARIABLES

    __slots__ = (
        "should_break_loop",
        "center_entity",
        "degree",
        "entity_keys_to_visit",
        "link_ratio",
        "links",
        "max_nodes",
        "nodes",
        "relational_role_names",
        "structural_role_names",
    )

    roles_to_prune = [
        "Released On",
        "Compiled On",
        "Producer",
        "Remix",
        "DJ Mix",
        "Written-By",
    ]

    entities_to_prune = [
        "Various",
        "Not On Label",
        "Self Released",
        "Self-Released",
    ]

    # INITIALIZER

    def __init__(
        self,
        center_entity: RuntimeEntity,
        degree: int,
        link_ratio: int,
        max_nodes: int,
        role_names: list[str],
    ):
        from musigree.runtime.runtime_database.runtime_database_helper import (
            RuntimeDatabaseHelper,
        )

        log.debug(
            f"RelationGrapher for {center_entity.entity_type}-{center_entity.entity_name}"
        )
        self.center_entity = center_entity
        degree = int(degree)
        assert degree > 0
        self.degree = degree
        if max_nodes is not None:
            max_nodes = int(max_nodes)
            assert max_nodes > 0
        else:
            max_nodes = RuntimeDatabaseHelper.MAX_NODES
        self.max_nodes = max_nodes
        if link_ratio is not None:
            link_ratio = int(link_ratio)
            assert link_ratio > 0
        else:
            link_ratio = RuntimeDatabaseHelper.LINK_RATIO
        self.link_ratio = link_ratio
        self.structural_role_names: list[str] = []
        self.relational_role_names: list[str] = []
        if role_names:
            # if isinstance(role_names, str):
            #     role_names = (role_names,)
            # elif not isinstance(role_names, collections_abc.Iterable):
            #     role_names = (role_names,)
            # role_names = tuple(role_names)
            assert all(
                _ in RoleCache.role_name_to_role_id_lookup.keys() for _ in role_names
            )
            for role_name in role_names:
                if role_name in ("Alias", "Sublabel Of", "Member Of"):
                    self.structural_role_names.append(role_name)
                else:
                    self.relational_role_names.append(role_name)
        # self.structural_role_names = tuple(structural_role_names)
        # self.relational_role_names = tuple(relational_role_names)
        self.nodes: OrderedDict[tuple[int, EntityType], TrellisNode] = OrderedDict()
        self.links: dict[str, RuntimeRelationResult] = {}
        self.should_break_loop = False
        self.entity_keys_to_visit = set[tuple[int, EntityType]]()

    def get_relation_graph(
        self,
        entity_repository: RuntimeEntityRepository,
        relation_repository: RuntimeRelationRepository,
    ):
        log.debug(f"Searching around {self.center_entity.entity_name}...")
        log.debug(f"  {len(self.structural_role_names)} structural_role_names")
        log.debug(f"  {len(self.relational_role_names)}relational_role_names")
        provisional_role_names = self.relational_role_names
        # provisional_roles = list(self.relational_role_names)
        self.report_search_start()
        self.clear()
        self.entity_keys_to_visit.add(self.center_entity.entity_key)
        for distance in range(self.degree + 1):
            self.report_search_loop_start(distance)
            if len(self.entity_keys_to_visit) > self.max_nodes:
                break
            log.debug(f"        Search for {len(self.entity_keys_to_visit)} entities")
            entities = self.search_entities(
                entity_repository, self.entity_keys_to_visit
            )
            log.debug(f"        Search found {len(entities)} entities")
            relations: dict[str, RuntimeRelationResult] = {}
            self.process_entities(distance, entities)
            if (
                not self.entity_keys_to_visit
                or self.should_break_loop
                or len(entities) > self.max_nodes
            ):
                break
            self.test_loop_one(distance)
            self.prune_roles(distance, provisional_role_names)
            if not self.should_break_loop:
                self.search_via_structural_roles(
                    distance, provisional_role_names, relations
                )
                self.search_via_relational_roles(
                    relation_repository=relation_repository,
                    distance=distance,
                    provisional_roles=provisional_role_names,
                    relation_links=relations,
                )
            self.test_loop_two(distance, relations)
            self.entity_keys_to_visit.clear()
            self.process_relations(relations)
        self.build_trellis()
        # self.cross_reference(distance)
        # pages = self.partition_trellis(distance)
        # self.page_entities(pages)
        self.find_clusters()
        for node in self.nodes.values():
            expected_count = RuntimeEntityDataAccess.roles_to_relation_count(
                node.entity, self.all_roles
            )
            node.missing = expected_count - len(node.links)
        # log.debug(f"self.links: {self.links}")
        # log.debug(f"self.nodes: {self.nodes}")
        json_links = tuple(
            link.as_json()
            for key, link in sorted(self.links.items(), key=lambda x: x[0])
        )
        json_nodes = tuple(
            node.as_json()
            for key, node in sorted(self.nodes.items(), key=lambda x: x[0])
        )
        network = {
            "center": {
                "key": self.center_entity.json_entity_key,
                "name": self.center_entity.entity_name,
            },
            "links": json_links,
            "nodes": json_nodes,
        }
        return network

    @staticmethod
    def search_entities(
        entity_repository: RuntimeEntityRepository,
        entity_keys_to_visit: set[tuple[int, EntityType]],
    ) -> list[RuntimeEntity]:
        # log.debug(f"        Retrieving entities keys: {entity_keys_to_visit}")
        entities: list[RuntimeEntity] = []
        entity_keys_to_visit_list = list(entity_keys_to_visit)
        stop = len(entity_keys_to_visit_list)
        step = 1000
        for start in range(0, stop, step):
            entity_key_slice = entity_keys_to_visit_list[start : start + step]
            found = entity_repository.search_multi(entity_key_slice)
            entities.extend(found)
            log.debug(f"            {start + 1}-{min(start + step, stop)} of {stop}")
        return entities

    def search_via_relational_roles(
        self,
        *,
        relation_repository: RuntimeRelationRepository,
        distance: int,
        provisional_roles: list[str],
        relation_links: dict[str, RuntimeRelationResult],
    ):
        for entity_key in sorted(self.entity_keys_to_visit):
            node = self.nodes.get(entity_key)
            if not node:
                continue
            entity = node.entity
            relational_count = RuntimeEntityDataAccess.roles_to_relation_count(
                entity, provisional_roles
            )
            if 0 < distance and self.max_links < relational_count:
                self.entity_keys_to_visit.remove(entity_key)
                log.debug(
                    f"            Pre-pruned {entity.entity_name} [{relational_count}]"
                )
        if provisional_roles and distance < self.degree:
            log.debug("        Retrieving relational relations")
            keys = sorted(self.entity_keys_to_visit)
            step = 500
            stop = len(keys)
            for start in range(0, stop, step):
                key_slice = keys[start : start + step]
                # log.debug(
                #     f"            {start + 1}-{min(start + step, stop)} of {stop}"
                # )
                relation_results = RuntimeRelationDataAccess.search_multi(
                    relation_repository=relation_repository,
                    entity_keys=key_slice,
                    role_names=provisional_roles,
                )
                # log.debug(f"                relation_results: {relation_results}")
                for relation in relation_results:
                    relation_links[relation.link_key] = RuntimeRelationResult(
                        id=relation.id,
                        entity_one_id=relation.entity_one_id,
                        entity_one_type=relation.entity_one_type,
                        entity_two_id=relation.entity_two_id,
                        entity_two_type=relation.entity_two_type,
                        releases=relation.releases,
                        role=relation.role,
                        distance=None,
                    )

    # PRIVATE METHODS

    def find_clusters(self):
        cluster_count = 0
        cluster_map = {}
        for node in sorted(
            self.nodes.values(),
            key=lambda x: len(x.entity.entities.get("aliases", {})),
            reverse=True,
        ):
            entity = node.entity
            aliases = entity.entities.get("aliases", {})
            if not aliases:
                continue
            if entity.entity_id not in cluster_map:
                cluster_count += 1
                cluster_map[entity.entity_id] = cluster_count
                for _, alias_id in aliases.items():
                    cluster_map[alias_id] = cluster_count
            cluster = cluster_map[entity.entity_id]
            if cluster is not None:
                node.cluster = cluster

    @staticmethod
    def group_trellis(trellis):
        trellis_nodes_by_distance = OrderedDict()
        for trellis_node in trellis.values():
            if trellis_node.distance not in trellis_nodes_by_distance:
                trellis_nodes_by_distance[trellis_node.distance] = set()
            trellis_nodes_by_distance[trellis_node.distance].add(trellis_node)
        return trellis_nodes_by_distance

    def build_trellis(self):
        for link_key, relation in tuple(self.links.items()):
            if (
                relation.entity_one_key not in self.nodes
                or relation.entity_two_key not in self.nodes
            ):
                self.links.pop(link_key)
                continue
            source_node = self.nodes[relation.entity_one_key]
            source_node.links.add(link_key)
            target_node = self.nodes[relation.entity_two_key]
            target_node.links.add(link_key)
            if source_node.distance == target_node.distance:
                source_node.siblings.add(target_node)
                target_node.siblings.add(source_node)
            elif source_node.distance < target_node.distance:
                source_node.children.add(target_node)
                target_node.parents.add(source_node)
            elif target_node.distance < source_node.distance:
                target_node.children.add(source_node)
                source_node.parents.add(target_node)
        self.recurse_trellis(self.nodes[self.center_entity.entity_key])
        for node_key, node in self.nodes.items():
            if node.subgraph_size is None:
                self.nodes.pop(node_key)
        for link_key, relation in tuple(self.links.items()):
            if (
                relation.entity_one_key not in self.nodes
                or relation.entity_two_key not in self.nodes
            ):
                self.links.pop(link_key)
                continue
        log.debug(
            f"    Built trellis: {len(self.nodes)} nodes / {len(self.links)} links"
        )

    @staticmethod
    def find_trellis_distance(trellis_nodes_by_distance, threshold):
        log.debug(f"        Maximum depth: {max(trellis_nodes_by_distance)}")
        log.debug(f"        Subgraph threshold: {threshold}")
        distancewise_average_subgraph_size = {}
        for distance, trellis_nodes in trellis_nodes_by_distance.items():
            trellis_nodes_by_distance[distance] = sorted(
                trellis_nodes,
                key=lambda x: x.entity_key,
            )
            sizes = sorted(_.subgraph_size for _ in trellis_nodes)
            geometric = sum(sizes) ** (1.0 / len(sizes))
            distancewise_average_subgraph_size[distance] = geometric
            log.debug(f"            At distance {distance}: {geometric} geometric mean")
        winning_distance = 0
        pairs = ((a, d) for d, a in distancewise_average_subgraph_size.items())
        pairs = sorted(pairs, reverse=True)
        for average, distance in pairs:
            log.debug(f"                Testing {average} @ distance {distance}")
            if average < threshold:
                winning_distance = distance
                break
        log.debug(f"            Winning distance: {winning_distance}")
        if (winning_distance + 1) < (len(distancewise_average_subgraph_size) / 2):
            winning_distance += 1
            log.debug(f"            Promoting winning distance: {winning_distance}")
        return winning_distance

    def clear(self):
        self.nodes.clear()
        self.links.clear()
        self.entity_keys_to_visit.clear()
        self.should_break_loop = False

    def prune_roles(self, distance: int, provisional_role_names: list[str]) -> None:
        if distance > 0 and len(self.nodes) > self.max_nodes / 4:
            for role_name in self.roles_to_prune:
                if role_name in provisional_role_names:
                    log.debug(f"            Pruned {role_name} role")
                    provisional_role_names.remove(role_name)
            if self.center_entity.entity_type == EntityType.ARTIST:
                if "Sublabel Of" in provisional_role_names:
                    log.debug(f'            Pruned "Sublabel Of" role')
                    provisional_role_names.remove("Sublabel Of")

    def process_entities(self, distance: int, entities: list[RuntimeEntity]):
        for entity in sorted(entities, key=lambda x: x.entity_key):
            if not all([entity.entity_id, entity.entity_name]):
                self.entity_keys_to_visit.remove(entity.entity_key)
                continue
            if entity.entity_name in self.entities_to_prune:
                self.entity_keys_to_visit.remove(entity.entity_key)
                continue
            if entity.entity_name.startswith("Various Artists"):
                self.entity_keys_to_visit.remove(entity.entity_key)
                continue
            entity_key = entity.entity_key
            if entity_key not in self.nodes:
                # log.debug(f"        add TrellisNode for entity: {entity_key}")
                self.nodes[entity_key] = TrellisNode(entity, distance)

    def process_relations(
        self, relation_links: dict[str, RuntimeRelationResult]
    ) -> None:
        log.debug(f"    process {len(relation_links)} relation_links")
        for link_key, relation in sorted(relation_links.items()):
            # log.debug(f"        link_key: {link_key}")
            # log.debug(f"        relation: {relation}")

            if not relation.entity_one_id or not relation.entity_two_id:
                # log.debug(f"        skip: {relation}")
                continue
            entity_one_key = relation.entity_one_key
            entity_two_key = relation.entity_two_key
            if entity_one_key not in self.nodes:
                # log.debug(f"        add entity_one_key: {entity_one_key}")
                self.entity_keys_to_visit.add(entity_one_key)
            if entity_two_key not in self.nodes:
                # log.debug(f"        add entity_two_key: {entity_two_key}")
                self.entity_keys_to_visit.add(entity_two_key)
            self.links[link_key] = relation
        # log.debug(f"        entity_keys_to_visit: {self.entity_keys_to_visit}")

    def recurse_trellis(self, node):
        # noinspection PySetFunctionToLiteral
        traversed_keys = set([node.entity_key])
        for child in node.children:
            traversed_keys.update(self.recurse_trellis(child))
        node.subgraph_size = len(traversed_keys)
        # log.debug(f"{'    ' * node.distance}{node.entity.entity_name}: {node.subgraph_size}")
        return traversed_keys

    def report_search_loop_start(self, distance) -> None:
        to_visit_count = len(self.entity_keys_to_visit)
        log.debug(f"    At distance {distance}:")
        log.debug(f"        {len(self.nodes)} old nodes")
        log.debug(f"        {len(self.links)} old links")
        log.debug(f"        {to_visit_count} new nodes")

    def report_search_start(self) -> None:
        log.debug(f"    Max nodes: {self.max_nodes}")
        log.debug(f"    Max links: {self.max_links}")
        log.debug(f"    {len(self.all_roles)} Roles")

    # noinspection PyUnusedLocal
    def search_via_structural_roles(
        self,
        distance,
        provisional_roles,
        relation_links: dict[str, RuntimeRelationResult],
    ) -> None:
        if not self.structural_role_names:
            return
        log.debug("        Retrieving structural relations")
        for entity_key in sorted(self.entity_keys_to_visit):
            # log.debug(f"            entity_key: {entity_key}")
            node = self.nodes.get(entity_key)
            # log.debug(f"            node: {node}")
            if not node:
                # log.debug(f"            ...skipped")
                continue
            entity = node.entity
            # log.debug(f"            entity: {entity}")
            # log.debug(f"            relations: {relations}")
            relation_links.update(
                RuntimeEntityDataAccess.structural_roles_to_relations(
                    entity, self.structural_role_names
                )
            )

    def test_loop_one(self, distance) -> None:
        if distance > 0:
            if len(self.nodes) >= self.max_nodes:
                log.debug("        Max nodes: exiting next search loop.")
                self.should_break_loop = True

    def test_loop_two(self, distance, relations: dict) -> None:
        if not relations:
            self.should_break_loop = True
        if len(relations) >= self.max_links * 3:
            log.debug("        Max links: exiting next search loop.")
            self.should_break_loop = True
        if distance > 1:
            if len(relations) >= self.max_links:
                log.debug("        Max links: exiting next search loop.")
                self.should_break_loop = True

    # PUBLIC METHODS

    @classmethod
    def make_cache_key(
        cls, template, entity_id: int, entity_type: EntityType, roles=None, year=None
    ) -> str:
        entity_type_str = entity_type.name.lower()
        key = template.format(entity_id=entity_id, entity_type=entity_type_str)
        if roles or year:
            parts = []
            if roles:
                roles = (utils.WORD_PATTERN.sub("+", _) for _ in roles)
                roles = ("roles[]={}".format(_) for _ in roles)
                roles = "&".join(sorted(roles))
                parts.append(roles)
            if year:
                if isinstance(year, int):
                    year = f"year={year}"
                else:
                    year = "-".join(str(_) for _ in year)
                    year = f"year={year}"
                parts.append(year)
            query_string = "&".join(parts)
            key = f"{key}?{query_string}"
        # key = f"musigree:{key}"
        # log.debug(f"  cache key: {key}")
        return key

    # PUBLIC PROPERTIES

    @property
    def all_roles(self) -> list[str]:
        return self.structural_role_names + self.relational_role_names

    # @property
    # def should_break_loop(self):
    #     return self.should_break_loop
    #
    # @should_break_loop.setter
    # def should_break_loop(self, expr):
    #     self.should_break_loop = bool(expr)
    #
    # @property
    # def center_entity(self):
    #     return self.center_entity
    #
    # @property
    # def degree(self):
    #     return self.degree
    #
    # @property
    # def entity_keys_to_visit(self):
    #     return self.entity_keys_to_visit
    #
    # @property
    # def link_ratio(self):
    #     return self.link_ratio
    #
    # @property
    # def links(self):
    #     return self.links

    @property
    def max_links(self) -> int:
        return self.max_nodes * self.link_ratio

    # @property
    # def max_nodes(self):
    #     return self.max_nodes
    #
    # @property
    # def nodes(self):
    #     return self.nodes
    #
    # @property
    # def relational_roles(self):
    #     return self.relational_roles
    #
    # @property
    # def structural_roles(self):
    #     return self.structural_roles
