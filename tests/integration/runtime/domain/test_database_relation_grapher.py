import logging

from musigree import utils
from musigree.library.fields.entity_type import EntityType
from musigree.runtime.data_access_layer.relation_grapher import RelationGrapher
from musigree.runtime.runtime_database.runtime_database_helper import (
    RuntimeDatabaseHelper,
)
from musigree.runtime.runtime_database.runtime_entity_repository import (
    RuntimeEntityRepository,
)
from musigree.runtime.runtime_database.runtime_relation_repository import (
    RuntimeRelationRepository,
)
from musigree.runtime.runtime_database.runtime_transaction import runtime_transaction
from tests.integration.runtime.database.runtime_database_test_case import (
    RuntimeDatabaseTestCase,
)

log = logging.getLogger(__name__)


class TestDatabaseRelationGrapher(RuntimeDatabaseTestCase):
    """
    Problematic networks:

        - 296570: 306 nodes, 13688 links,
        - 1946151: unbalanced
        - 491160: bifurcated dense alias networks

    """

    def test___call___01(self):
        # GIVEN
        entity_type = EntityType.ARTIST
        entity_name = "Seefeel"

        # WHEN
        with runtime_transaction():
            entity_repository = RuntimeEntityRepository()
            relation_repository = RuntimeRelationRepository()
            artist = entity_repository.get_by_type_and_name(entity_type, entity_name)
            log.debug(f"artist: {artist}")
            roles = ["Alias", "Member Of"]
            grapher = RelationGrapher(
                center_entity=artist,
                degree=1,
                link_ratio=RuntimeDatabaseHelper.LINK_RATIO,
                max_nodes=RuntimeDatabaseHelper.MAX_NODES,
                role_names=roles,
            )
            network = grapher.get_relation_graph(entity_repository, relation_repository)
            actual = utils.normalize_dict(network)
            log.debug(f"network: {actual}")

        # THEN
        expected_network = {
            "center": {"key": "artist-2239", "name": "Seefeel"},
            "links": [
                {
                    "key": "artist-115880-member-of-artist-2239",
                    "role": "Member Of",
                    "source": "artist-115880",
                    "target": "artist-2239",
                },
                {
                    "key": "artist-41103-member-of-artist-2239",
                    "role": "Member Of",
                    "source": "artist-41103",
                    "target": "artist-2239",
                },
                {
                    "key": "artist-489350-member-of-artist-2239",
                    "role": "Member Of",
                    "source": "artist-489350",
                    "target": "artist-2239",
                },
                {
                    "key": "artist-51674-member-of-artist-2239",
                    "role": "Member Of",
                    "source": "artist-51674",
                    "target": "artist-2239",
                },
                {
                    "key": "artist-66803-member-of-artist-2239",
                    "role": "Member Of",
                    "source": "artist-66803",
                    "target": "artist-2239",
                },
            ],
            "nodes": [
                {
                    "distance": 0,
                    "id": 2239,
                    "key": "artist-2239",
                    "links": [
                        "artist-115880-member-of-artist-2239",
                        "artist-41103-member-of-artist-2239",
                        "artist-489350-member-of-artist-2239",
                        "artist-51674-member-of-artist-2239",
                        "artist-66803-member-of-artist-2239",
                    ],
                    "missing": 0,
                    "name": "Seefeel",
                    "size": 5,
                    "type": "artist",
                },
                {
                    "cluster": 2,
                    "distance": 1,
                    "id": 41103,
                    "key": "artist-41103",
                    "links": ["artist-41103-member-of-artist-2239"],
                    "missing": 1,
                    "name": "Mark Van Hoen",
                    "size": 0,
                    "type": "artist",
                },
                {
                    "cluster": 1,
                    "distance": 1,
                    "id": 51674,
                    "key": "artist-51674",
                    "links": ["artist-51674-member-of-artist-2239"],
                    "missing": 3,
                    "name": "Mark Clifford",
                    "size": 0,
                    "type": "artist",
                },
                {
                    "distance": 1,
                    "id": 66803,
                    "key": "artist-66803",
                    "links": ["artist-66803-member-of-artist-2239"],
                    "missing": 0,
                    "name": "Daren Seymour",
                    "size": 0,
                    "type": "artist",
                },
                {
                    "distance": 1,
                    "id": 115880,
                    "key": "artist-115880",
                    "links": ["artist-115880-member-of-artist-2239"],
                    "missing": 0,
                    "name": "Sarah Peacock",
                    "size": 0,
                    "type": "artist",
                },
                {
                    "distance": 1,
                    "id": 489350,
                    "key": "artist-489350",
                    "links": ["artist-489350-member-of-artist-2239"],
                    "missing": 0,
                    "name": "Justin Fletcher",
                    "size": 0,
                    "type": "artist",
                },
            ],
        }
        expected = utils.normalize_dict(expected_network)
        self.assertEqual(expected, actual)

    def test___call___02(self):
        # GIVEN
        entity_type = EntityType.ARTIST
        entity_name = "Justin Fletcher"

        # WHEN
        with runtime_transaction():
            entity_repository = RuntimeEntityRepository()
            relation_repository = RuntimeRelationRepository()
            artist = entity_repository.get_by_type_and_name(entity_type, entity_name)
            log.debug(f"artist: {artist}")
            roles = ["Alias", "Member Of"]
            grapher = RelationGrapher(
                center_entity=artist,
                degree=2,
                link_ratio=RuntimeDatabaseHelper.LINK_RATIO,
                max_nodes=5,
                role_names=roles,
            )
            network = grapher.get_relation_graph(entity_repository, relation_repository)
            actual = utils.normalize_dict(network)
            log.debug(f"network: {actual}")

        expected_network = {
            "center": {"key": "artist-489350", "name": "Justin Fletcher"},
            "links": [
                {
                    "key": "artist-115880-member-of-artist-2239",
                    "role": "Member Of",
                    "source": "artist-115880",
                    "target": "artist-2239",
                },
                {
                    "key": "artist-41103-member-of-artist-2239",
                    "role": "Member Of",
                    "source": "artist-41103",
                    "target": "artist-2239",
                },
                {
                    "key": "artist-489350-member-of-artist-2239",
                    "role": "Member Of",
                    "source": "artist-489350",
                    "target": "artist-2239",
                },
                {
                    "key": "artist-51674-member-of-artist-2239",
                    "role": "Member Of",
                    "source": "artist-51674",
                    "target": "artist-2239",
                },
                {
                    "key": "artist-66803-member-of-artist-2239",
                    "role": "Member Of",
                    "source": "artist-66803",
                    "target": "artist-2239",
                },
            ],
            "nodes": [
                {
                    "distance": 1,
                    "id": 2239,
                    "key": "artist-2239",
                    "links": [
                        "artist-115880-member-of-artist-2239",
                        "artist-41103-member-of-artist-2239",
                        "artist-489350-member-of-artist-2239",
                        "artist-51674-member-of-artist-2239",
                        "artist-66803-member-of-artist-2239",
                    ],
                    "missing": 0,
                    "name": "Seefeel",
                    "size": 5,
                    "type": "artist",
                },
                {
                    "cluster": 2,
                    "distance": 2,
                    "id": 41103,
                    "key": "artist-41103",
                    "links": ["artist-41103-member-of-artist-2239"],
                    "missing": 1,
                    "name": "Mark Van Hoen",
                    "size": 0,
                    "type": "artist",
                },
                {
                    "cluster": 1,
                    "distance": 2,
                    "id": 51674,
                    "key": "artist-51674",
                    "links": ["artist-51674-member-of-artist-2239"],
                    "missing": 3,
                    "name": "Mark Clifford",
                    "size": 0,
                    "type": "artist",
                },
                {
                    "distance": 2,
                    "id": 66803,
                    "key": "artist-66803",
                    "links": ["artist-66803-member-of-artist-2239"],
                    "missing": 0,
                    "name": "Daren Seymour",
                    "size": 0,
                    "type": "artist",
                },
                {
                    "distance": 2,
                    "id": 115880,
                    "key": "artist-115880",
                    "links": ["artist-115880-member-of-artist-2239"],
                    "missing": 0,
                    "name": "Sarah Peacock",
                    "size": 0,
                    "type": "artist",
                },
                {
                    "distance": 0,
                    "id": 489350,
                    "key": "artist-489350",
                    "links": ["artist-489350-member-of-artist-2239"],
                    "missing": 0,
                    "name": "Justin Fletcher",
                    "size": 0,
                    "type": "artist",
                },
            ],
        }
        expected = utils.normalize_dict(expected_network)
        self.assertEqual(expected, actual)

    def test___call___03(self):
        # GIVEN
        entity_type = EntityType.ARTIST
        entity_name = "Justin Fletcher"

        # WHEN
        with runtime_transaction():
            entity_repository = RuntimeEntityRepository()
            relation_repository = RuntimeRelationRepository()
            artist = entity_repository.get_by_type_and_name(entity_type, entity_name)
            roles = ["Alias", "Member Of"]
            grapher = RelationGrapher(
                center_entity=artist,
                degree=2,
                link_ratio=2,
                max_nodes=RuntimeDatabaseHelper.MAX_NODES,
                role_names=roles,
            )
            network = grapher.get_relation_graph(entity_repository, relation_repository)
            actual = utils.normalize_dict(network)

        # THEN
        expected_network = {
            "center": {"key": "artist-489350", "name": "Justin Fletcher"},
            "links": [
                {
                    "key": "artist-115880-member-of-artist-2239",
                    "role": "Member Of",
                    "source": "artist-115880",
                    "target": "artist-2239",
                },
                {
                    "key": "artist-41103-member-of-artist-2239",
                    "role": "Member Of",
                    "source": "artist-41103",
                    "target": "artist-2239",
                },
                {
                    "key": "artist-489350-member-of-artist-2239",
                    "role": "Member Of",
                    "source": "artist-489350",
                    "target": "artist-2239",
                },
                {
                    "key": "artist-51674-member-of-artist-2239",
                    "role": "Member Of",
                    "source": "artist-51674",
                    "target": "artist-2239",
                },
                {
                    "key": "artist-66803-member-of-artist-2239",
                    "role": "Member Of",
                    "source": "artist-66803",
                    "target": "artist-2239",
                },
            ],
            "nodes": [
                {
                    "distance": 1,
                    "id": 2239,
                    "key": "artist-2239",
                    "links": [
                        "artist-115880-member-of-artist-2239",
                        "artist-41103-member-of-artist-2239",
                        "artist-489350-member-of-artist-2239",
                        "artist-51674-member-of-artist-2239",
                        "artist-66803-member-of-artist-2239",
                    ],
                    "missing": 0,
                    "name": "Seefeel",
                    "size": 5,
                    "type": "artist",
                },
                {
                    "cluster": 2,
                    "distance": 2,
                    "id": 41103,
                    "key": "artist-41103",
                    "links": ["artist-41103-member-of-artist-2239"],
                    "missing": 1,
                    "name": "Mark Van Hoen",
                    "size": 0,
                    "type": "artist",
                },
                {
                    "cluster": 1,
                    "distance": 2,
                    "id": 51674,
                    "key": "artist-51674",
                    "links": ["artist-51674-member-of-artist-2239"],
                    "missing": 3,
                    "name": "Mark Clifford",
                    "size": 0,
                    "type": "artist",
                },
                {
                    "distance": 2,
                    "id": 66803,
                    "key": "artist-66803",
                    "links": ["artist-66803-member-of-artist-2239"],
                    "missing": 0,
                    "name": "Daren Seymour",
                    "size": 0,
                    "type": "artist",
                },
                {
                    "distance": 2,
                    "id": 115880,
                    "key": "artist-115880",
                    "links": ["artist-115880-member-of-artist-2239"],
                    "missing": 0,
                    "name": "Sarah Peacock",
                    "size": 0,
                    "type": "artist",
                },
                {
                    "distance": 0,
                    "id": 489350,
                    "key": "artist-489350",
                    "links": ["artist-489350-member-of-artist-2239"],
                    "missing": 0,
                    "name": "Justin Fletcher",
                    "size": 0,
                    "type": "artist",
                },
            ],
        }
        expected = utils.normalize_dict(expected_network)
        self.assertEqual(expected, actual)

    def test___call___04(self):
        """
        Missing count takes into account structural roles: members,
        aliases, groups, sublabels, parent labels, etc.
        """
        # GIVEN
        entity_id = 489350
        entity_type = EntityType.ARTIST

        # WHEN
        with runtime_transaction():
            entity_repository = RuntimeEntityRepository()
            relation_repository = RuntimeRelationRepository()
            artist = entity_repository.get_by_entity_id_and_entity_type(
                entity_id, entity_type
            )
            roles = ["Alias", "Member Of"]
            grapher = RelationGrapher(
                center_entity=artist,
                degree=12,
                link_ratio=RuntimeDatabaseHelper.LINK_RATIO,
                max_nodes=RuntimeDatabaseHelper.MAX_NODES,
                role_names=roles,
            )
            network = grapher.get_relation_graph(entity_repository, relation_repository)
            actual = utils.normalize_dict(network)

        expected_network = {
            "center": {"key": "artist-489350", "name": "Justin Fletcher"},
            "links": [
                {
                    "key": "artist-115880-member-of-artist-2239",
                    "role": "Member Of",
                    "source": "artist-115880",
                    "target": "artist-2239",
                },
                {
                    "key": "artist-1920-alias-artist-51674",
                    "role": "Alias",
                    "source": "artist-1920",
                    "target": "artist-51674",
                },
                {
                    "key": "artist-231-alias-artist-1920",
                    "role": "Alias",
                    "source": "artist-231",
                    "target": "artist-1920",
                },
                {
                    "key": "artist-231-alias-artist-51674",
                    "role": "Alias",
                    "source": "artist-231",
                    "target": "artist-51674",
                },
                {
                    "key": "artist-3490-alias-artist-41103",
                    "role": "Alias",
                    "source": "artist-3490",
                    "target": "artist-41103",
                },
                {
                    "key": "artist-41103-member-of-artist-2239",
                    "role": "Member Of",
                    "source": "artist-41103",
                    "target": "artist-2239",
                },
                {
                    "key": "artist-489350-member-of-artist-2239",
                    "role": "Member Of",
                    "source": "artist-489350",
                    "target": "artist-2239",
                },
                {
                    "key": "artist-51674-member-of-artist-1656080",
                    "role": "Member Of",
                    "source": "artist-51674",
                    "target": "artist-1656080",
                },
                {
                    "key": "artist-51674-member-of-artist-2239",
                    "role": "Member Of",
                    "source": "artist-51674",
                    "target": "artist-2239",
                },
                {
                    "key": "artist-66803-member-of-artist-2239",
                    "role": "Member Of",
                    "source": "artist-66803",
                    "target": "artist-2239",
                },
            ],
            "nodes": [
                {
                    "cluster": 1,
                    "distance": 3,
                    "id": 231,
                    "key": "artist-231",
                    "links": [
                        "artist-231-alias-artist-1920",
                        "artist-231-alias-artist-51674",
                    ],
                    "missing": 0,
                    "name": "Woodenspoon",
                    "size": 0,
                    "type": "artist",
                },
                {
                    "cluster": 1,
                    "distance": 3,
                    "id": 1920,
                    "key": "artist-1920",
                    "links": [
                        "artist-1920-alias-artist-51674",
                        "artist-231-alias-artist-1920",
                    ],
                    "missing": 0,
                    "name": "Disjecta",
                    "size": 0,
                    "type": "artist",
                },
                {
                    "distance": 1,
                    "id": 2239,
                    "key": "artist-2239",
                    "links": [
                        "artist-115880-member-of-artist-2239",
                        "artist-41103-member-of-artist-2239",
                        "artist-489350-member-of-artist-2239",
                        "artist-51674-member-of-artist-2239",
                        "artist-66803-member-of-artist-2239",
                    ],
                    "missing": 0,
                    "name": "Seefeel",
                    "size": 5,
                    "type": "artist",
                },
                {
                    "cluster": 2,
                    "distance": 3,
                    "id": 3490,
                    "key": "artist-3490",
                    "links": ["artist-3490-alias-artist-41103"],
                    "missing": 0,
                    "name": "Locust",
                    "size": 0,
                    "type": "artist",
                },
                {
                    "cluster": 2,
                    "distance": 2,
                    "id": 41103,
                    "key": "artist-41103",
                    "links": [
                        "artist-3490-alias-artist-41103",
                        "artist-41103-member-of-artist-2239",
                    ],
                    "missing": 0,
                    "name": "Mark Van Hoen",
                    "size": 0,
                    "type": "artist",
                },
                {
                    "cluster": 1,
                    "distance": 2,
                    "id": 51674,
                    "key": "artist-51674",
                    "links": [
                        "artist-1920-alias-artist-51674",
                        "artist-231-alias-artist-51674",
                        "artist-51674-member-of-artist-1656080",
                        "artist-51674-member-of-artist-2239",
                    ],
                    "missing": 0,
                    "name": "Mark Clifford",
                    "size": 0,
                    "type": "artist",
                },
                {
                    "distance": 2,
                    "id": 66803,
                    "key": "artist-66803",
                    "links": ["artist-66803-member-of-artist-2239"],
                    "missing": 0,
                    "name": "Daren Seymour",
                    "size": 0,
                    "type": "artist",
                },
                {
                    "distance": 2,
                    "id": 115880,
                    "key": "artist-115880",
                    "links": ["artist-115880-member-of-artist-2239"],
                    "missing": 0,
                    "name": "Sarah Peacock",
                    "size": 0,
                    "type": "artist",
                },
                {
                    "distance": 0,
                    "id": 489350,
                    "key": "artist-489350",
                    "links": ["artist-489350-member-of-artist-2239"],
                    "missing": 0,
                    "name": "Justin Fletcher",
                    "size": 0,
                    "type": "artist",
                },
                {
                    "distance": 3,
                    "id": 1656080,
                    "key": "artist-1656080",
                    "links": ["artist-51674-member-of-artist-1656080"],
                    "missing": 0,
                    "name": "Cliffordandcalix",
                    "size": 1,
                    "type": "artist",
                },
            ],
        }
        expected = utils.normalize_dict(expected_network)
        self.assertEqual(expected, actual)

    def test___call___05(self):
        # GIVEN
        entity_type = EntityType.LABEL
        entity_name = "Lab Studio, Berlin"

        # WHEN
        with runtime_transaction():
            entity_repository = RuntimeEntityRepository()
            relation_repository = RuntimeRelationRepository()
            label = entity_repository.get_by_type_and_name(entity_type, entity_name)
            print(f"label: {label}")
            roles = ["Recorded At"]
            grapher = RelationGrapher(
                center_entity=label,
                degree=2,
                link_ratio=RuntimeDatabaseHelper.LINK_RATIO,
                max_nodes=RuntimeDatabaseHelper.MAX_NODES,
                role_names=roles,
            )
            network = grapher.get_relation_graph(entity_repository, relation_repository)
            actual = utils.normalize_dict(network)

        # THEN
        expected_network = {
            "center": {"key": "artist-489350", "name": "Justin Fletcher"},
            "links": [
                {
                    "key": "artist-115880-member-of-artist-2239",
                    "role": "Member Of",
                    "source": "artist-115880",
                    "target": "artist-2239",
                },
                {
                    "key": "artist-1920-alias-artist-51674",
                    "role": "Alias",
                    "source": "artist-1920",
                    "target": "artist-51674",
                },
                {
                    "key": "artist-231-alias-artist-1920",
                    "role": "Alias",
                    "source": "artist-231",
                    "target": "artist-1920",
                },
                {
                    "key": "artist-231-alias-artist-51674",
                    "role": "Alias",
                    "source": "artist-231",
                    "target": "artist-51674",
                },
                {
                    "key": "artist-3490-alias-artist-41103",
                    "role": "Alias",
                    "source": "artist-3490",
                    "target": "artist-41103",
                },
                {
                    "key": "artist-41103-member-of-artist-2239",
                    "role": "Member Of",
                    "source": "artist-41103",
                    "target": "artist-2239",
                },
                {
                    "key": "artist-489350-member-of-artist-2239",
                    "role": "Member Of",
                    "source": "artist-489350",
                    "target": "artist-2239",
                },
                {
                    "key": "artist-51674-member-of-artist-1656080",
                    "role": "Member Of",
                    "source": "artist-51674",
                    "target": "artist-1656080",
                },
                {
                    "key": "artist-51674-member-of-artist-2239",
                    "role": "Member Of",
                    "source": "artist-51674",
                    "target": "artist-2239",
                },
                {
                    "key": "artist-66803-member-of-artist-2239",
                    "role": "Member Of",
                    "source": "artist-66803",
                    "target": "artist-2239",
                },
            ],
            "nodes": [
                {
                    "cluster": 1,
                    "distance": 3,
                    "id": 231,
                    "key": "artist-231",
                    "links": [
                        "artist-231-alias-artist-1920",
                        "artist-231-alias-artist-51674",
                    ],
                    "missing": 0,
                    "name": "Woodenspoon",
                    "size": 0,
                    "type": "artist",
                },
                {
                    "cluster": 1,
                    "distance": 3,
                    "id": 1920,
                    "key": "artist-1920",
                    "links": [
                        "artist-1920-alias-artist-51674",
                        "artist-231-alias-artist-1920",
                    ],
                    "missing": 0,
                    "name": "Disjecta",
                    "size": 0,
                    "type": "artist",
                },
                {
                    "distance": 1,
                    "id": 2239,
                    "key": "artist-2239",
                    "links": [
                        "artist-115880-member-of-artist-2239",
                        "artist-41103-member-of-artist-2239",
                        "artist-489350-member-of-artist-2239",
                        "artist-51674-member-of-artist-2239",
                        "artist-66803-member-of-artist-2239",
                    ],
                    "missing": 0,
                    "name": "Seefeel",
                    "size": 5,
                    "type": "artist",
                },
                {
                    "cluster": 2,
                    "distance": 3,
                    "id": 3490,
                    "key": "artist-3490",
                    "links": ["artist-3490-alias-artist-41103"],
                    "missing": 0,
                    "name": "Locust",
                    "size": 0,
                    "type": "artist",
                },
                {
                    "cluster": 2,
                    "distance": 2,
                    "id": 41103,
                    "key": "artist-41103",
                    "links": [
                        "artist-3490-alias-artist-41103",
                        "artist-41103-member-of-artist-2239",
                    ],
                    "missing": 0,
                    "name": "Mark Van Hoen",
                    "size": 0,
                    "type": "artist",
                },
                {
                    "cluster": 1,
                    "distance": 2,
                    "id": 51674,
                    "key": "artist-51674",
                    "links": [
                        "artist-1920-alias-artist-51674",
                        "artist-231-alias-artist-51674",
                        "artist-51674-member-of-artist-1656080",
                        "artist-51674-member-of-artist-2239",
                    ],
                    "missing": 0,
                    "name": "Mark Clifford",
                    "size": 0,
                    "type": "artist",
                },
                {
                    "distance": 2,
                    "id": 66803,
                    "key": "artist-66803",
                    "links": ["artist-66803-member-of-artist-2239"],
                    "missing": 0,
                    "name": "Daren Seymour",
                    "size": 0,
                    "type": "artist",
                },
                {
                    "distance": 2,
                    "id": 115880,
                    "key": "artist-115880",
                    "links": ["artist-115880-member-of-artist-2239"],
                    "missing": 0,
                    "name": "Sarah Peacock",
                    "size": 0,
                    "type": "artist",
                },
                {
                    "distance": 0,
                    "id": 489350,
                    "key": "artist-489350",
                    "links": ["artist-489350-member-of-artist-2239"],
                    "missing": 0,
                    "name": "Justin Fletcher",
                    "size": 0,
                    "type": "artist",
                },
                {
                    "distance": 3,
                    "id": 1656080,
                    "key": "artist-1656080",
                    "links": ["artist-51674-member-of-artist-1656080"],
                    "missing": 0,
                    "name": "Cliffordandcalix",
                    "size": 1,
                    "type": "artist",
                },
            ],
        }
        expected = utils.normalize_dict(expected_network)
        self.assertEqual(expected, actual)
