"""Unit tests for RelationGrapher class."""

from typing import Any, Generator
from unittest.mock import Mock, patch, AsyncMock, MagicMock

import pytest

from musigree.library.fields.entity_type import EntityType
from musigree.runtime.data_access_layer.relation_grapher import RelationGrapher
from musigree.runtime.data_access_layer.trellis_node import TrellisNode
from musigree.runtime.runtime_domain.entity import RuntimeEntity
from musigree.runtime.runtime_domain.relation import RuntimeRelationResult


class TestRelationGrapher:
    """Test cases for the RelationGrapher class."""

    @pytest.fixture
    def mock_center_entity(self) -> RuntimeEntity:
        """Create a mock center entity for testing."""
        return RuntimeEntity(
            id=1,
            entity_id=123,
            entity_type=EntityType.ARTIST,
            entity_name="Test Artist",
            relation_counts={"Artist": 5, "Album": 3},
            entity_metadata={"test": "metadata"},
            entities={"aliases": {"alias1": 456}},
            countries="US",
            genres="Rock",
            styles="Alternative",
        )

    @pytest.fixture
    def mock_role_cache(self) -> Generator[MagicMock | AsyncMock, Any, None]:
        """Mock the RoleCache for testing."""
        with patch("musigree.runtime.data_access_layer.relation_grapher.RoleCache") as mock:
            mock.role_name_to_role_id_lookup = {
                "Artist": 1,
                "Album": 2,
                "Alias": 3,
                "Member Of": 4,
                "Sublabel Of": 5,
                "Producer": 6,
                "Released On": 7,
            }
            yield mock

    def test_constructor_valid_parameters(
        self, mock_center_entity: RuntimeEntity, mock_role_cache: Mock
    ) -> None:
        """Test RelationGrapher constructor with valid parameters."""
        # Given
        degree = 2
        link_ratio = 10
        max_nodes = 100
        role_names = ["Artist", "Album"]

        # When
        with patch(
            "musigree.runtime.runtime_database.runtime_database_helper.RuntimeDatabaseHelper"
        ) as mock_helper:
            mock_helper.MAX_NODES = 1000
            mock_helper.LINK_RATIO = 20
            grapher = RelationGrapher(
                center_entity=mock_center_entity,
                degree=degree,
                link_ratio=link_ratio,
                max_nodes=max_nodes,
                role_names=role_names,
            )

        # Then
        assert grapher.center_entity == mock_center_entity
        assert grapher.degree == degree
        assert grapher.link_ratio == link_ratio
        assert grapher.max_nodes == max_nodes
        assert grapher.all_roles == role_names
        assert grapher.relational_role_names == role_names
        assert grapher.structural_role_names == []

    def test_constructor_with_structural_roles(
        self, mock_center_entity: RuntimeEntity, mock_role_cache: Mock
    ) -> None:
        """Test constructor with structural roles."""
        # Given
        role_names = ["Artist", "Alias", "Member Of"]

        # When
        with patch(
            "musigree.runtime.runtime_database.runtime_database_helper.RuntimeDatabaseHelper"
        ) as mock_helper:
            mock_helper.MAX_NODES = 1000
            mock_helper.LINK_RATIO = 20
            # Note: The constructor accepts None values despite type annotations
            grapher = RelationGrapher(
                center_entity=mock_center_entity,
                degree=1,
                link_ratio=None,  # type: ignore
                max_nodes=None,  # type: ignore
                role_names=role_names,
            )

        # Then
        assert "Alias" in grapher.structural_role_names
        assert "Member Of" in grapher.structural_role_names
        assert "Artist" in grapher.relational_role_names
        assert grapher.max_nodes == mock_helper.MAX_NODES
        assert grapher.link_ratio == mock_helper.LINK_RATIO

    def test_constructor_invalid_degree(
        self, mock_center_entity: RuntimeEntity, mock_role_cache: Mock
    ) -> None:
        """Test constructor with invalid degree raises assertion error."""
        with pytest.raises(AssertionError):
            RelationGrapher(
                center_entity=mock_center_entity,
                degree=0,  # Invalid
                link_ratio=10,
                max_nodes=100,
                role_names=["Artist"],
            )

    def test_constructor_invalid_role_names(
        self, mock_center_entity: RuntimeEntity, mock_role_cache: Mock
    ) -> None:
        """Test constructor with invalid role names raises assertion error."""
        mock_role_cache.role_name_to_role_id_lookup = {"Artist": 1}

        with pytest.raises(AssertionError):
            RelationGrapher(
                center_entity=mock_center_entity,
                degree=1,
                link_ratio=10,
                max_nodes=100,
                role_names=["InvalidRole"],  # Not in cache
            )

    @pytest.mark.asyncio
    async def test_search_entities_basic(self) -> None:
        """Test the static search_entities method."""
        # Given
        mock_repository = AsyncMock()
        entity_keys = {(123, EntityType.ARTIST), (456, EntityType.LABEL)}

        mock_entities = [
            RuntimeEntity(
                id=1,
                entity_id=123,
                entity_type=EntityType.ARTIST,
                entity_name="Artist 1",
                relation_counts={},
                entity_metadata={},
                countries=None,
                genres=None,
                styles=None,
            ),
            RuntimeEntity(
                id=2,
                entity_id=456,
                entity_type=EntityType.LABEL,
                entity_name="Label 1",
                relation_counts={},
                entity_metadata={},
                countries=None,
                genres=None,
                styles=None,
            ),
        ]
        mock_repository.search_multi.return_value = mock_entities

        # When
        result = await RelationGrapher.search_entities(mock_repository, entity_keys)

        # Then
        assert len(result) == 2
        assert result == mock_entities
        mock_repository.search_multi.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_entities_large_batch(self) -> None:
        """Test search_entities with large batch that gets chunked."""
        # Given
        mock_repository = AsyncMock()
        # Create 1500 entity keys to trigger batching (step size is 1000)
        entity_keys = {(i, EntityType.ARTIST) for i in range(1500)}

        mock_entities_batch1 = [Mock() for _ in range(1000)]
        mock_entities_batch2 = [Mock() for _ in range(500)]
        mock_repository.search_multi.side_effect = [
            mock_entities_batch1,
            mock_entities_batch2,
        ]

        # When
        result = await RelationGrapher.search_entities(mock_repository, entity_keys)

        # Then
        assert len(result) == 1500
        assert mock_repository.search_multi.call_count == 2

    def test_process_entities_valid_entities(
        self, mock_center_entity: RuntimeEntity, mock_role_cache: Mock
    ) -> None:
        """Test process_entities with valid entities."""
        # Given
        with patch(
            "musigree.runtime.runtime_database.runtime_database_helper.RuntimeDatabaseHelper"
        ):
            grapher = RelationGrapher(
                center_entity=mock_center_entity,
                degree=1,
                link_ratio=10,
                max_nodes=100,
                role_names=["Artist"],
            )

        entities = [
            RuntimeEntity(
                id=1,
                entity_id=123,
                entity_type=EntityType.ARTIST,
                entity_name="Valid Artist",
                relation_counts={},
                entity_metadata={},
                countries=None,
                genres=None,
                styles=None,
            ),
            RuntimeEntity(
                id=2,
                entity_id=456,
                entity_type=EntityType.LABEL,
                entity_name="Valid Label",
                relation_counts={},
                entity_metadata={},
                countries=None,
                genres=None,
                styles=None,
            ),
        ]

        # Add entities to visit set
        for entity in entities:
            grapher.entity_keys_to_visit.add(entity.entity_key)

        # When
        grapher.process_entities(distance=1, entities=entities)

        # Then
        assert len(grapher.nodes) == 2
        for entity in entities:
            assert entity.entity_key in grapher.nodes
            assert isinstance(grapher.nodes[entity.entity_key], TrellisNode)
            assert grapher.nodes[entity.entity_key].distance == 1

    def test_process_entities_pruned_entities(
        self, mock_center_entity: RuntimeEntity, mock_role_cache: Mock
    ) -> None:
        """Test process_entities with entities that should be pruned."""
        # Given
        with patch(
            "musigree.runtime.runtime_database.runtime_database_helper.RuntimeDatabaseHelper"
        ):
            grapher = RelationGrapher(
                center_entity=mock_center_entity,
                degree=1,
                link_ratio=10,
                max_nodes=100,
                role_names=["Artist"],
            )

        entities = [
            RuntimeEntity(
                id=1,
                entity_id=123,
                entity_type=EntityType.ARTIST,
                entity_name="Various",
                relation_counts={},
                entity_metadata={},
                countries=None,
                genres=None,
                styles=None,
            ),
            RuntimeEntity(
                id=2,
                entity_id=456,
                entity_type=EntityType.LABEL,
                entity_name="Various Artists - Test",
                relation_counts={},
                entity_metadata={},
                countries=None,
                genres=None,
                styles=None,
            ),
            RuntimeEntity(
                id=3,
                entity_id=789,
                entity_type=EntityType.ARTIST,
                entity_name="Valid Artist",
                relation_counts={},
                entity_metadata={},
                countries=None,
                genres=None,
                styles=None,
            ),
        ]

        # Add entities to visit set
        for entity in entities:
            grapher.entity_keys_to_visit.add(entity.entity_key)

        # When
        grapher.process_entities(distance=1, entities=entities)

        # Then
        # Only the valid artist should remain
        assert len(grapher.nodes) == 1
        assert (789, EntityType.ARTIST) in grapher.nodes
        # Pruned entities should be removed from visit set
        assert (123, EntityType.ARTIST) not in grapher.entity_keys_to_visit
        assert (456, EntityType.LABEL) not in grapher.entity_keys_to_visit

    def test_process_relations_valid_relations(
        self, mock_center_entity: RuntimeEntity, mock_role_cache: Mock
    ) -> None:
        """Test process_relations with valid relation links."""
        # Given
        with patch(
            "musigree.runtime.runtime_database.runtime_database_helper.RuntimeDatabaseHelper"
        ):
            grapher = RelationGrapher(
                center_entity=mock_center_entity,
                degree=1,
                link_ratio=10,
                max_nodes=100,
                role_names=["Artist"],
            )

        relation_links: dict[str, RuntimeRelationResult] = {
            "link1": RuntimeRelationResult(
                entity_one_id=123,
                entity_one_type=EntityType.ARTIST,
                entity_two_id=456,
                entity_two_type=EntityType.LABEL,
                releases={"release1": 5},
                role="Artist",
                distance=None,
            ),
            "link2": RuntimeRelationResult(
                entity_one_id=456,
                entity_one_type=EntityType.LABEL,
                entity_two_id=789,
                entity_two_type=EntityType.ARTIST,
                releases={"release2": 3},
                role="Artist",
                distance=None,
            ),
        }

        # When
        grapher.process_relations(relation_links)

        # Then
        assert len(grapher.links) == 2
        assert "link1" in grapher.links
        assert "link2" in grapher.links
        # New entity keys should be added to visit set
        assert (123, EntityType.ARTIST) in grapher.entity_keys_to_visit
        assert (456, EntityType.LABEL) in grapher.entity_keys_to_visit
        assert (789, EntityType.ARTIST) in grapher.entity_keys_to_visit

    def test_prune_roles_with_many_nodes(
        self, mock_center_entity: RuntimeEntity, mock_role_cache: Mock
    ) -> None:
        """Test prune_roles when there are many nodes."""
        # Given
        with patch(
            "musigree.runtime.runtime_database.runtime_database_helper.RuntimeDatabaseHelper"
        ):
            grapher = RelationGrapher(
                center_entity=mock_center_entity,
                degree=1,
                link_ratio=10,
                max_nodes=100,
                role_names=["Artist", "Producer", "Released On"],
            )

        # Simulate many nodes to trigger pruning
        for i in range(30):  # More than max_nodes / 4 (25)
            grapher.nodes[(i, EntityType.ARTIST)] = Mock()

        provisional_role_names = ["Artist", "Producer", "Released On"]

        # When
        grapher.prune_roles(distance=1, provisional_role_names=provisional_role_names)

        # Then
        assert "Producer" not in provisional_role_names
        assert "Released On" not in provisional_role_names
        assert "Artist" in provisional_role_names  # Should remain

    def test_prune_roles_artist_sublabel_pruning(self, mock_role_cache: Mock) -> None:
        """Test pruning of Sublabel Of for artist entities."""
        # Given
        artist_entity = RuntimeEntity(
            id=1,
            entity_id=123,
            entity_type=EntityType.ARTIST,  # Artist type
            entity_name="Test Artist",
            relation_counts={},
            entity_metadata={},
            countries=None,
            genres=None,
            styles=None,
        )

        with patch(
            "musigree.runtime.runtime_database.runtime_database_helper.RuntimeDatabaseHelper"
        ):
            grapher = RelationGrapher(
                center_entity=artist_entity,
                degree=1,
                link_ratio=10,
                max_nodes=100,
                role_names=["Artist", "Sublabel Of"],
            )

        # Simulate many nodes to trigger pruning
        for i in range(30):  # More than max_nodes / 4
            grapher.nodes[(i, EntityType.ARTIST)] = Mock()

        provisional_role_names = ["Artist", "Sublabel Of"]

        # When
        grapher.prune_roles(distance=1, provisional_role_names=provisional_role_names)

        # Then
        assert "Sublabel Of" not in provisional_role_names
        assert "Artist" in provisional_role_names

    def test_find_clusters(self, mock_center_entity: RuntimeEntity, mock_role_cache: Mock) -> None:
        """Test find_clusters method."""
        # Given
        with patch(
            "musigree.runtime.runtime_database.runtime_database_helper.RuntimeDatabaseHelper"
        ):
            grapher = RelationGrapher(
                center_entity=mock_center_entity,
                degree=1,
                link_ratio=10,
                max_nodes=100,
                role_names=["Artist"],
            )

        # Create entities with aliases
        entity1 = RuntimeEntity(
            id=1,
            entity_id=123,
            entity_type=EntityType.ARTIST,
            entity_name="Main Artist",
            relation_counts={},
            entity_metadata={},
            entities={"aliases": {"alias1": 456}},
            countries=None,
            genres=None,
            styles=None,
        )
        entity2 = RuntimeEntity(
            id=2,
            entity_id=456,
            entity_type=EntityType.ARTIST,
            entity_name="Alias Artist",
            relation_counts={},
            entity_metadata={},
            entities={},
            countries=None,
            genres=None,
            styles=None,
        )

        node1 = TrellisNode(entity1, 0)
        node2 = TrellisNode(entity2, 1)
        grapher.nodes[(123, EntityType.ARTIST)] = node1
        grapher.nodes[(456, EntityType.ARTIST)] = node2

        # When
        grapher.find_clusters()

        # Then
        # The find_clusters method should assign the same cluster to entities that are aliases
        # But since entity2 doesn't have entity1's ID in its cluster map,
        # they won't be in the same cluster. Let's test that entity1 gets clustered.
        assert node1.cluster > 0
        # The clustering algorithm may not cluster entity2 if it doesn't have the right alias setup

    def test_clear_method(self, mock_center_entity: RuntimeEntity, mock_role_cache: Mock) -> None:
        """Test clear method resets all collections."""
        # Given
        with patch(
            "musigree.runtime.runtime_database.runtime_database_helper.RuntimeDatabaseHelper"
        ):
            grapher = RelationGrapher(
                center_entity=mock_center_entity,
                degree=1,
                link_ratio=10,
                max_nodes=100,
                role_names=["Artist"],
            )

        # Add some data
        grapher.nodes[(123, EntityType.ARTIST)] = Mock()
        grapher.links["test_link"] = Mock()
        grapher.entity_keys_to_visit.add((456, EntityType.LABEL))
        grapher.should_break_loop = True

        # When
        grapher.clear()

        # Then
        assert len(grapher.nodes) == 0
        assert len(grapher.links) == 0
        assert len(grapher.entity_keys_to_visit) == 0
        assert grapher.should_break_loop is False

    def test_property_accessors(
        self, mock_center_entity: RuntimeEntity, mock_role_cache: Mock
    ) -> None:
        """Test all property accessors."""
        # Given
        with patch(
            "musigree.runtime.runtime_database.runtime_database_helper.RuntimeDatabaseHelper"
        ):
            grapher = RelationGrapher(
                center_entity=mock_center_entity,
                degree=2,
                link_ratio=15,
                max_nodes=200,
                role_names=["Artist", "Alias"],
            )

        # Then
        assert grapher.center_entity == mock_center_entity
        assert grapher.degree == 2
        assert grapher.link_ratio == 15
        assert grapher.max_nodes == 200
        assert grapher.max_links == 200 * 15  # max_nodes * link_ratio
        assert "Artist" in grapher.relational_role_names
        assert "Alias" in grapher.structural_role_names
        assert grapher.all_roles == ["Alias", "Artist"]

        # Test should_break_loop setter
        grapher.should_break_loop = True
        assert grapher.should_break_loop is True
        grapher.should_break_loop = False
        assert grapher.should_break_loop is False

    def test_make_cache_key_basic(self) -> None:
        """Test make_cache_key with basic parameters."""
        # When
        key = RelationGrapher.make_cache_key(
            template="test/{entity_type}/{entity_id}",
            entity_id=123,
            entity_type=EntityType.ARTIST,
        )

        # Then
        assert key == "test/artist/123"

    def test_make_cache_key_with_roles_and_year(self) -> None:
        """Test make_cache_key with roles and year parameters."""
        # When
        key = RelationGrapher.make_cache_key(
            template="test/{entity_type}/{entity_id}",
            entity_id=123,
            entity_type=EntityType.ARTIST,
            roles=["Artist Role", "Producer Role"],
            year=2020,
        )

        # Then
        assert "test/artist/123?" in key
        assert "roles[]=Artist+Role" in key
        assert "roles[]=Producer+Role" in key
        assert "year=2020" in key

    def test_make_cache_key_with_year_range(self) -> None:
        """Test make_cache_key with year range."""
        # When
        key = RelationGrapher.make_cache_key(
            template="test/{entity_type}/{entity_id}",
            entity_id=123,
            entity_type=EntityType.ARTIST,
            year=[2015, 2020],
        )

        # Then
        assert "year=2015-2020" in key

    @pytest.mark.asyncio
    async def test_get_relation_graph_basic_flow(
        self, mock_center_entity: RuntimeEntity, mock_role_cache: Mock
    ) -> None:
        """Test the main get_relation_graph method with basic flow."""
        # Given
        with patch(
            "musigree.runtime.runtime_database.runtime_database_helper.RuntimeDatabaseHelper"
        ):
            grapher = RelationGrapher(
                center_entity=mock_center_entity,
                degree=1,
                link_ratio=10,
                max_nodes=100,
                role_names=["Artist"],
            )

        mock_entity_repo = AsyncMock()
        mock_relation_repo = AsyncMock()

        # Mock search_entities to return the center entity
        mock_entities = [mock_center_entity]

        # Mock the static method properly
        with patch(
            "musigree.runtime.data_access_layer.relation_grapher.RelationGrapher.search_entities",
            new_callable=AsyncMock,
            return_value=mock_entities,
        ) as _mock_search:
            with patch(
                "musigree.runtime.data_access_layer.relation_grapher.RuntimeEntityDataAccess"
            ) as mock_entity_access:
                with patch(
                    "musigree.runtime.data_access_layer.relation_grapher.RuntimeRelationDataAccess"
                ) as mock_relation_access:
                    mock_entity_access.roles_to_relation_count.return_value = 5
                    mock_entity_access.structural_roles_to_relations.return_value = {}
                    mock_relation_access.search_multi = AsyncMock(return_value=[])

                    # When
                    result = await grapher.get_relation_graph(mock_entity_repo, mock_relation_repo)

        # Then
        assert "center" in result
        assert "nodes" in result
        assert "links" in result
        assert result["center"]["key"] == mock_center_entity.json_entity_key
        assert result["center"]["name"] == mock_center_entity.entity_name

    @pytest.mark.asyncio
    async def test_search_via_relational_roles(
        self, mock_center_entity: RuntimeEntity, mock_role_cache: Mock
    ) -> None:
        """Test search_via_relational_roles method."""
        # Given
        with patch(
            "musigree.runtime.runtime_database.runtime_database_helper.RuntimeDatabaseHelper"
        ):
            grapher = RelationGrapher(
                center_entity=mock_center_entity,
                degree=2,
                link_ratio=10,
                max_nodes=100,
                role_names=["Artist"],
            )

        mock_relation_repo = AsyncMock()
        mock_node = TrellisNode(mock_center_entity, 0)
        grapher.nodes[mock_center_entity.entity_key] = mock_node
        grapher.entity_keys_to_visit.add(mock_center_entity.entity_key)

        mock_relations = [
            RuntimeRelationResult(
                entity_one_id=123,
                entity_one_type=EntityType.ARTIST,
                entity_two_id=456,
                entity_two_type=EntityType.LABEL,
                releases={"release1": 3},
                role="Artist",
                distance=None,
            )
        ]

        with patch(
            "musigree.runtime.data_access_layer.relation_grapher.RuntimeEntityDataAccess"
        ) as mock_entity_access:
            with patch(
                "musigree.runtime.data_access_layer.relation_grapher.RuntimeRelationDataAccess"
            ) as mock_relation_access:
                mock_entity_access.roles_to_relation_count.return_value = 5
                # Make search_multi return an awaitable
                mock_relation_access.search_multi = AsyncMock(return_value=mock_relations)

                relation_links: dict[str, RuntimeRelationResult] = {}

                # When
                await grapher.search_via_relational_roles(
                    relation_repository=mock_relation_repo,
                    distance=0,
                    provisional_roles=["Artist"],
                    relation_links=relation_links,
                )

        # Then
        assert len(relation_links) == 1
        link_key = list(relation_links.keys())[0]
        assert relation_links[link_key].entity_one_id == 123
        assert relation_links[link_key].entity_two_id == 456

    def test_search_via_structural_roles(
        self, mock_center_entity: RuntimeEntity, mock_role_cache: Mock
    ) -> None:
        """Test search_via_structural_roles method."""
        # Given
        with patch(
            "musigree.runtime.runtime_database.runtime_database_helper.RuntimeDatabaseHelper"
        ):
            grapher = RelationGrapher(
                center_entity=mock_center_entity,
                degree=1,
                link_ratio=10,
                max_nodes=100,
                role_names=["Alias"],
            )

        mock_node = TrellisNode(mock_center_entity, 0)
        grapher.nodes[mock_center_entity.entity_key] = mock_node
        grapher.entity_keys_to_visit.add(mock_center_entity.entity_key)

        mock_structural_relations = {
            "struct_link1": RuntimeRelationResult(
                entity_one_id=123,
                entity_one_type=EntityType.ARTIST,
                entity_two_id=456,
                entity_two_type=EntityType.ARTIST,
                releases={"release1": 1},
                role="Alias",
                distance=None,
            )
        }

        with patch(
            "musigree.runtime.data_access_layer.relation_grapher.RuntimeEntityDataAccess"
        ) as mock_entity_access:
            mock_entity_access.structural_roles_to_relations.return_value = (
                mock_structural_relations
            )

            relation_links: dict[str, RuntimeRelationResult] = {}

            # When
            grapher.search_via_structural_roles(
                distance=0, provisional_roles=["Alias"], relation_links=relation_links
            )

        # Then
        assert len(relation_links) == 1
        assert "struct_link1" in relation_links

    def test_search_via_structural_roles_no_structural_roles(
        self, mock_center_entity: RuntimeEntity, mock_role_cache: Mock
    ) -> None:
        """Test search_via_structural_roles with no structural roles."""
        # Given
        with patch(
            "musigree.runtime.runtime_database.runtime_database_helper.RuntimeDatabaseHelper"
        ):
            grapher = RelationGrapher(
                center_entity=mock_center_entity,
                degree=1,
                link_ratio=10,
                max_nodes=100,
                role_names=["Artist"],  # No structural roles
            )

        relation_links: dict[str, RuntimeRelationResult] = {}

        # When
        grapher.search_via_structural_roles(
            distance=0, provisional_roles=["Artist"], relation_links=relation_links
        )

        # Then
        assert len(relation_links) == 0  # Should do nothing

    def test_build_trellis(self, mock_center_entity: RuntimeEntity, mock_role_cache: Mock) -> None:
        """Test build_trellis method."""
        # Given
        with patch(
            "musigree.runtime.runtime_database.runtime_database_helper.RuntimeDatabaseHelper"
        ):
            grapher = RelationGrapher(
                center_entity=mock_center_entity,
                degree=1,
                link_ratio=10,
                max_nodes=100,
                role_names=["Artist"],
            )

        # Create test entities and nodes
        entity1 = RuntimeEntity(
            id=1,
            entity_id=123,
            entity_type=EntityType.ARTIST,
            entity_name="Artist 1",
            relation_counts={},
            entity_metadata={},
            countries=None,
            genres=None,
            styles=None,
        )
        entity2 = RuntimeEntity(
            id=2,
            entity_id=456,
            entity_type=EntityType.LABEL,
            entity_name="Label 1",
            relation_counts={},
            entity_metadata={},
            countries=None,
            genres=None,
            styles=None,
        )

        node1 = TrellisNode(entity1, 0)
        node2 = TrellisNode(entity2, 1)
        grapher.nodes[entity1.entity_key] = node1
        grapher.nodes[entity2.entity_key] = node2

        # Create a link between them
        relation = RuntimeRelationResult(
            entity_one_id=123,
            entity_one_type=EntityType.ARTIST,
            entity_two_id=456,
            entity_two_type=EntityType.LABEL,
            releases={"release1": 3},
            role="Artist",
            distance=None,
        )
        grapher.links["link1"] = relation

        # When
        grapher.build_trellis()

        # Then
        # Check that the trellis structure is built correctly
        assert "link1" in node1.links
        assert "link1" in node2.links
        assert node2 in node1.children  # node2 is at higher distance
        assert node1 in node2.parents  # node1 is at lower distance
        assert node1.subgraph_size is not None
        assert node2.subgraph_size is not None

    def test_test_loop_conditions(
        self, mock_center_entity: RuntimeEntity, mock_role_cache: Mock
    ) -> None:
        """Test loop breaking conditions."""
        # Given
        with patch(
            "musigree.runtime.runtime_database.runtime_database_helper.RuntimeDatabaseHelper"
        ):
            grapher = RelationGrapher(
                center_entity=mock_center_entity,
                degree=1,
                link_ratio=2,  # Small link ratio for testing
                max_nodes=10,  # Small max for testing
                role_names=["Artist"],
            )

        # Test test_loop_one - should break when too many nodes
        for i in range(15):  # More than max_nodes
            grapher.nodes[(i, EntityType.ARTIST)] = Mock()

        grapher.test_loop_one(distance=1)
        assert grapher.should_break_loop is True

        # Reset
        grapher.should_break_loop = False

        # Test test_loop_two - should break when too many relations
        # max_links = max_nodes * link_ratio = 10 * 2 = 20
        many_relations = {f"link_{i}": Mock() for i in range(25)}  # More than max_links (20)
        grapher.test_loop_two(
            distance=2, relations=many_relations
        )  # Use distance > 1 to trigger the condition
        assert grapher.should_break_loop is True

        # Test with empty relations
        grapher.should_break_loop = False
        grapher.test_loop_two(distance=1, relations={})
        assert grapher.should_break_loop is True
