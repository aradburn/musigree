from musigree.library.fields.entity_type import EntityType
from musigree.runtime.data_access_layer.trellis_node import TrellisNode
from musigree.runtime.runtime_domain.entity import RuntimeEntity


def test_creates_trellis_node_with_valid_data() -> None:
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


def test_checks_equality_of_trellis_nodes() -> None:
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


def test_checks_inequality_of_trellis_nodes() -> None:
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


def test_generates_correct_json_representation() -> None:
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


def test_calculates_correct_parentage() -> None:
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


def test_calculates_correct_neighbors() -> None:
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


def test_hash_functionality() -> None:
    """Test that hash works correctly for TrellisNode instances."""
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

    # Equal nodes should have same hash
    assert hash(node1) == hash(node2)

    # Should be usable in sets and dicts
    node_set = {node1, node2}
    assert len(node_set) == 1

    node_dict = {node1: "value1", node2: "value2"}
    assert len(node_dict) == 1
    assert node_dict[node1] == "value2"


def test_cluster_property_setter() -> None:
    """Test cluster property getter and setter."""
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
    node = TrellisNode(entity)

    # Default cluster should be 0
    assert node.cluster == 0

    # Test setting cluster
    node.cluster = 5
    assert node.cluster == 5

    # Test setting cluster with int
    node.cluster = 7
    assert node.cluster == 7


def test_missing_property_setter() -> None:
    """Test missing property getter and setter."""
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
    node = TrellisNode(entity)

    # Default missing should be 0
    assert node.missing == 0

    # Test setting missing
    node.missing = 3
    assert node.missing == 3

    # Test setting missing with int
    node.missing = 5
    assert node.missing == 5


def test_subgraph_size_property_setter() -> None:
    """Test subgraph_size property getter and setter."""
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
    node = TrellisNode(entity)

    # Default subgraph_size should be None
    assert node.subgraph_size is None

    # Test setting subgraph_size
    node.subgraph_size = 10
    assert node.subgraph_size == 10

    # Test setting subgraph_size with int
    node.subgraph_size = 15
    assert node.subgraph_size == 15


def test_entity_key_property() -> None:
    """Test entity_key property returns correct tuple."""
    entity = RuntimeEntity(
        id=1,
        entity_id=42,
        entity_type=EntityType.LABEL,
        entity_name="Test Label",
        entities={},
        relation_counts={},
        entity_metadata={},
        genres="Electronic",
        styles="Techno",
        countries="Germany",
    )
    node = TrellisNode(entity)

    assert node.entity_key == (42, EntityType.LABEL)


def test_size_property() -> None:
    """Test size property delegates to entity."""
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
    node = TrellisNode(entity)

    # Should delegate to entity.size
    assert node.size == entity.size


def test_distance_property() -> None:
    """Test distance property works correctly."""
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

    # Test default distance
    node1 = TrellisNode(entity)
    assert node1.distance == 0

    # Test custom distance
    node2 = TrellisNode(entity, distance=7)
    assert node2.distance == 7


def test_links_property() -> None:
    """Test links property manipulation."""
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
    node = TrellisNode(entity)

    # Default links should be empty set
    assert node.links == set()

    # Test adding links
    node.links.add("link1")
    node.links.add("link2")
    assert node.links == {"link1", "link2"}


def test_missing_by_page_property() -> None:
    """Test missing_by_page property manipulation."""
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
    node = TrellisNode(entity)

    # Default missing_by_page should be empty dict
    assert node.missing_by_page == {}

    # Test adding missing_by_page data
    node.missing_by_page["page1"] = 5
    node.missing_by_page["page2"] = 3
    assert node.missing_by_page == {"page1": 5, "page2": 3}


def test_json_representation_with_optional_fields() -> None:
    """Test JSON representation includes optional fields when present."""
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

    # Add optional data
    node.cluster = 3
    node.missing_by_page["page1"] = 2
    node.links.add("link1")
    node.links.add("link2")

    json_data = node.as_json()

    expected_json = {
        "distance": 5,
        "id": 1,
        "key": "artist-1",
        "links": ("link1", "link2"),
        "missing": 0,
        "name": "Entity One",
        "size": 0,
        "type": "artist",
        "cluster": 3,
        "missingByPage": {"page1": 2},
    }

    assert json_data == expected_json


def test_json_representation_without_optional_fields() -> None:
    """Test JSON representation excludes optional fields when not present."""
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
    node = TrellisNode(entity)

    json_data = node.as_json()

    # Should not include cluster or missingByPage when they're default/empty
    assert "cluster" not in json_data
    assert "missingByPage" not in json_data


def test_equality_with_different_types() -> None:
    """Test equality comparison with non-TrellisNode objects."""
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
    node = TrellisNode(entity)

    # Should not be equal to non-TrellisNode objects
    assert node != "string"
    assert node != 42
    assert node is not None
    assert node != {}
    assert node != []


def test_complex_parentage_calculation() -> None:
    """Test parentage calculation with multiple levels of parents."""
    # Create entities
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
        entity_type=EntityType.ARTIST,
        entity_name="Entity Three",
        entities={},
        relation_counts={},
        entity_metadata={},
        genres="Rock",
        styles="Pop",
        countries="USA",
    )
    entity4 = RuntimeEntity(
        id=4,
        entity_id=4,
        entity_type=EntityType.ARTIST,
        entity_name="Entity Four",
        entities={},
        relation_counts={},
        entity_metadata={},
        genres="Rock",
        styles="Pop",
        countries="USA",
    )

    # Create nodes
    node1 = TrellisNode(entity1)  # grandparent
    node2 = TrellisNode(entity2)  # parent
    node3 = TrellisNode(entity3)  # another parent
    node4 = TrellisNode(entity4)  # child

    # Set up parent-child relationships
    # node1 -> node2 -> node4
    # node3 -> node4
    node2._parents.add(node1)
    node4._parents.add(node2)
    node4._parents.add(node3)

    # Test parentage calculation
    parentage = node4.get_parentage()
    expected_parentage = frozenset([node1, node2, node3, node4])
    assert parentage == expected_parentage

    # Test caching - should return same object
    parentage2 = node4.get_parentage()
    assert parentage is parentage2


def test_complex_neighbors_calculation() -> None:
    """Test neighbors calculation with all types of relationships."""
    # Create entities
    entities = []
    for i in range(1, 6):
        entities.append(
            RuntimeEntity(
                id=i,
                entity_id=i,
                entity_type=EntityType.ARTIST,
                entity_name=f"Entity {i}",
                entities={},
                relation_counts={},
                entity_metadata={},
                genres="Rock",
                styles="Pop",
                countries="USA",
            )
        )

    # Create nodes
    nodes = [TrellisNode(entity) for entity in entities]
    center_node = nodes[0]
    parent_node = nodes[1]
    child_node = nodes[2]
    sibling_node1 = nodes[3]
    sibling_node2 = nodes[4]

    # Set up relationships
    center_node._parents.add(parent_node)
    center_node._children.add(child_node)
    center_node._siblings.add(sibling_node1)
    center_node._siblings.add(sibling_node2)

    # Test neighbors calculation
    neighbors = center_node.get_neighbors()
    expected_neighbors = {parent_node, child_node, sibling_node1, sibling_node2}
    assert neighbors == expected_neighbors


def test_get_neighbors_empty_relationships() -> None:
    """Test get_neighbors when node has no relationships."""
    entity = RuntimeEntity(
        id=1,
        entity_id=1,
        entity_type=EntityType.ARTIST,
        entity_name="Isolated Entity",
        entities={},
        relation_counts={},
        entity_metadata={},
        genres="Rock",
        styles="Pop",
        countries="USA",
    )
    node = TrellisNode(entity)

    # Should return empty set when no relationships exist
    assert node.get_neighbors() == set()


def test_get_parentage_no_parents() -> None:
    """Test get_parentage when node has no parents."""
    entity = RuntimeEntity(
        id=1,
        entity_id=1,
        entity_type=EntityType.ARTIST,
        entity_name="Root Entity",
        entities={},
        relation_counts={},
        entity_metadata={},
        genres="Rock",
        styles="Pop",
        countries="USA",
    )
    node = TrellisNode(entity)

    # Should return frozenset containing only itself
    parentage = node.get_parentage()
    assert parentage == frozenset([node])


def test_children_siblings_parents_properties() -> None:
    """Test that children, siblings, and parents properties return correct sets."""
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
    node = TrellisNode(entity)

    # Should all be empty sets initially
    assert node.children == set()
    assert node.siblings == set()
    assert node.parents == set()

    # Should be modifiable
    other_entity = RuntimeEntity(
        id=2,
        entity_id=2,
        entity_type=EntityType.ARTIST,
        entity_name="Other",
        entities={},
        relation_counts={},
        entity_metadata={},
        genres="Rock",
        styles="Pop",
        countries="USA",
    )
    other_node = TrellisNode(other_entity)

    node.children.add(other_node)
    node.siblings.add(other_node)
    node.parents.add(other_node)

    assert other_node in node.children
    assert other_node in node.siblings
    assert other_node in node.parents
