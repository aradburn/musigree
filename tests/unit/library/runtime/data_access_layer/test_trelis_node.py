from musigree.library.fields.entity_type import EntityType
from musigree.runtime.data_access_layer.trellis_node import TrellisNode
from musigree.runtime.runtime_domain.entity import RuntimeEntity


def test_creates_trellis_node_with_valid_data():
    entity = RuntimeEntity(
        id=1,
        entity_id=1,
        entity_type=EntityType.ARTIST,
        entity_name="Entity One",
        entities={},
        relation_counts={},
        entity_metadata={},
        genres="Rock",
        styles="Pop",
        countries="USA",
    )
    node = TrellisNode(entity, distance=5)
    assert node.entity == entity
    assert node.distance == 5
    assert node.children == set()
    assert node.cluster == 0
    assert node.links == set()
    assert node.missing == 0
    assert node.missing_by_page == {}
    assert node.parents == set()
    assert node.siblings == set()
    assert node.subgraph_size is None


def test_checks_equality_of_trellis_nodes():
    entity1 = RuntimeEntity(
        id=1,
        entity_id=1,
        entity_type=EntityType.ARTIST,
        entity_name="Entity One",
        entities={},
        relation_counts={},
        entity_metadata={},
        genres="Rock",
        styles="Pop",
        countries="USA",
    )
    entity2 = RuntimeEntity(
        id=1,
        entity_id=1,
        entity_type=EntityType.ARTIST,
        entity_name="Entity One",
        entities={},
        relation_counts={},
        entity_metadata={},
        genres="Rock",
        styles="Pop",
        countries="USA",
    )
    node1 = TrellisNode(entity1)
    node2 = TrellisNode(entity2)
    assert node1 == node2


def test_checks_inequality_of_trellis_nodes():
    entity1 = RuntimeEntity(
        id=1,
        entity_id=1,
        entity_type=EntityType.ARTIST,
        entity_name="Entity One",
        entities={},
        relation_counts={},
        entity_metadata={},
        genres="Rock",
        styles="Pop",
        countries="USA",
    )
    entity2 = RuntimeEntity(
        id=2,
        entity_id=2,
        entity_type=EntityType.LABEL,
        entity_name="Entity Two",
        entities={},
        relation_counts={},
        entity_metadata={},
        genres="Rock",
        styles="Pop",
        countries="USA",
    )
    node1 = TrellisNode(entity1)
    node2 = TrellisNode(entity2)
    assert node1 != node2


def test_generates_correct_json_representation():
    entity = RuntimeEntity(
        id=1,
        entity_id=1,
        entity_type=EntityType.ARTIST,
        entity_name="Entity One",
        entities={},
        relation_counts={},
        entity_metadata={},
        genres="Rock",
        styles="Pop",
        countries="USA",
    )
    node = TrellisNode(entity, distance=5)
    expected_json = {
        "distance": 5,
        "id": 1,
        "key": "artist-1",
        "links": (),
        "missing": 0,
        "name": "Entity One",
        "size": 0,
        "type": "artist",
    }
    assert node.as_json() == expected_json


def test_calculates_correct_parentage():
    entity1 = RuntimeEntity(
        id=1,
        entity_id=1,
        entity_type=EntityType.ARTIST,
        entity_name="Entity One",
        entities={},
        relation_counts={},
        entity_metadata={},
        genres="Rock",
        styles="Pop",
        countries="USA",
    )
    entity2 = RuntimeEntity(
        id=2,
        entity_id=2,
        entity_type=EntityType.ARTIST,
        entity_name="Entity Two",
        entities={},
        relation_counts={},
        entity_metadata={},
        genres="Rock",
        styles="Pop",
        countries="USA",
    )
    node1 = TrellisNode(entity1)
    node2 = TrellisNode(entity2)
    node2._parents.add(node1)
    assert node2.get_parentage() == frozenset([node1, node2])


def test_calculates_correct_neighbors():
    entity1 = RuntimeEntity(
        id=1,
        entity_id=1,
        entity_type=EntityType.ARTIST,
        entity_name="Entity One",
        entities={},
        relation_counts={},
        entity_metadata={},
        genres="Rock",
        styles="Pop",
        countries="USA",
    )
    entity2 = RuntimeEntity(
        id=2,
        entity_id=2,
        entity_type=EntityType.ARTIST,
        entity_name="Entity Two",
        entities={},
        relation_counts={},
        entity_metadata={},
        genres="Rock",
        styles="Pop",
        countries="USA",
    )
    entity3 = RuntimeEntity(
        id=3,
        entity_id=3,
        entity_type=EntityType.LABEL,
        entity_name="Entity Three",
        entities={},
        relation_counts={},
        entity_metadata={},
        genres="Rock",
        styles="Pop",
        countries="USA",
    )
    node1 = TrellisNode(entity1)
    node2 = TrellisNode(entity2)
    node3 = TrellisNode(entity3)
    node2._parents.add(node1)
    node2._siblings.add(node3)
    assert node2.get_neighbors() == {node1, node3}
