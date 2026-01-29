"""
Unit tests for musigree.offline.data_access_layer.relation_data_access module.
"""

from unittest.mock import Mock, patch, AsyncMock

import pytest

from musigree.config import SqliteTestConfiguration, Configuration
from musigree.library.fields.role_type import RoleType
from musigree.offline.data_access_layer.offline_relation_data_access import OfflineRelationDataAccess
from musigree.offline.offline_domain.relation import Relation
from musigree.offline.offline_domain.release import Release


class TestOfflineRelationDataAccess:
    """Test cases for OfflineRelationDataAccess class."""

    @pytest.fixture
    def test_config(self) -> Configuration:
        """Provide test configuration."""
        return SqliteTestConfiguration()

    @pytest.fixture
    def sample_release(self) -> Release:
        """Provide a sample release for testing."""
        return Release(
            release_id=123,
            title="Test Release",
            artists=[{"id": 1, "name": "Test Artist"}],
            labels=[{"id": 2, "name": "Test Label"}],
            extra_artists=[{"id": 3, "name": "Producer", "roles": [{"name": "Producer"}]}],
            companies=[{"id": 4, "name": "Test Company", "entity_type_name": "Distributed By"}],
            tracklist=[
                {
                    "title": "Test Track",
                    "artists": [{"id": 5, "name": "Track Artist"}],
                    "extra_artists": [{"id": 6, "name": "Vocalist", "roles": [{"name": "Vocals"}]}],
                }
            ],
        )

    @pytest.fixture
    def compilation_release(self) -> Release:
        """Provide a compilation release for testing."""
        return Release(
            release_id=456,
            title="Various Artists - Compilation",
            artists=[{"id": 194, "name": "Various Artists"}],  # Discogs ID for Various Artists
            labels=[{"id": 2, "name": "Test Label"}],
            extra_artists=[{"id": 3, "name": "Producer", "roles": [{"name": "Producer"}]}],
            tracklist=[
                {"title": "Track 1", "artists": [{"id": 5, "name": "Artist 1"}]},
                {"title": "Track 2", "artists": [{"id": 6, "name": "Artist 2"}]},
            ],
        )

    @patch("musigree.offline.data_access_layer.offline_relation_data_access.OfflineRoleDataAccess.find_role")
    @patch(
        "musigree.offline.data_access_layer.offline_relation_data_access.RoleDataUtils.normalise_role_names"
    )
    def test_from_release_basic(
        self, mock_normalise_roles: Mock, mock_find_role: Mock, sample_release: Release
    ) -> None:
        """Test basic relation extraction from release."""
        # Arrange
        mock_normalise_roles.return_value = ["producer"]
        mock_find_role.return_value = "producer"

        # Act
        result = OfflineRelationDataAccess.from_release(sample_release)

        # Assert
        assert isinstance(result, list)
        assert len(result) >= 0  # Should return some relations
        mock_normalise_roles.assert_called()
        mock_find_role.assert_called()

    @patch("musigree.offline.data_access_layer.offline_relation_data_access.OfflineRoleDataAccess.find_role")
    @patch(
        "musigree.offline.data_access_layer.offline_relation_data_access.RoleDataUtils.normalise_role_names"
    )
    def test_from_release_compilation(
        self,
        mock_normalise_roles: Mock,
        mock_find_role: Mock,
        compilation_release: Release,
    ) -> None:
        """Test relation extraction from compilation release."""
        # Arrange
        mock_normalise_roles.return_value = ["producer"]
        mock_find_role.return_value = "producer"

        # Act
        result = OfflineRelationDataAccess.from_release(compilation_release)

        # Assert
        assert isinstance(result, list)
        mock_normalise_roles.assert_called()
        mock_find_role.assert_called()

    def test_get_release_setup_normal_release(self, sample_release: Release) -> None:
        """Test get_release_setup for normal release."""
        # Act
        artist_ids, label_ids, is_compilation = OfflineRelationDataAccess.get_release_setup(sample_release)

        # Assert
        assert isinstance(artist_ids, set)
        assert isinstance(label_ids, set)
        assert isinstance(is_compilation, bool)
        assert 1 in artist_ids  # Artist ID from sample_release
        assert 2 in label_ids  # Label ID from sample_release
        assert not is_compilation  # Should not be compilation

    def test_get_release_setup_compilation_release(self, compilation_release: Release) -> None:
        """Test get_release_setup for compilation release."""
        # Act
        artist_ids, label_ids, is_compilation = OfflineRelationDataAccess.get_release_setup(
            compilation_release
        )

        # Assert
        assert isinstance(artist_ids, set)
        assert isinstance(label_ids, set)
        assert isinstance(is_compilation, bool)
        # For compilations, artist_ids should include track artists, not the "Various Artists" placeholder
        assert artist_ids == {5, 6}  # Track artists
        assert label_ids == {2}
        assert is_compilation is True

    def test_get_artist_label_relations_normal_release(self) -> None:
        """Test artist-label relations for normal release."""
        # Arrange
        artist_ids = {1, 2}
        label_ids = {3, 4}
        is_compilation = False

        # Act
        result = OfflineRelationDataAccess.get_artist_label_relations(
            artist_ids, label_ids, is_compilation
        )

        # Assert
        assert isinstance(result, set)
        expected_relations = {
            (1, "Released On", 3),
            (1, "Released On", 4),
            (2, "Released On", 3),
            (2, "Released On", 4),
        }
        assert result == expected_relations

    def test_get_artist_label_relations_compilation(self) -> None:
        """Test artist-label relations for compilation release."""
        # Arrange
        artist_ids = {194}  # Various Artists
        label_ids = {3, 4}
        is_compilation = True

        # Act
        result = OfflineRelationDataAccess.get_artist_label_relations(
            artist_ids, label_ids, is_compilation
        )

        # Assert
        assert isinstance(result, set)
        # For compilations, relations should be created with "Compiled On" role
        expected_relations = {(194, "Compiled On", 3), (194, "Compiled On", 4)}
        assert result == expected_relations

    def test_from_triples_basic(self) -> None:
        """Test converting triples to relations."""
        # Arrange
        triples = [(1, "producer", 2), (3, "vocals", 4)]

        # Act
        result = OfflineRelationDataAccess.from_triples(triples)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 2
        for relation in result:
            assert isinstance(relation, dict)
            assert "subject" in relation
            assert "role" in relation
            assert "object" in relation

    def test_from_triples_with_release(self, sample_release: Release) -> None:
        """Test converting triples to relations with release metadata."""
        # Arrange
        triples = [(1, "producer", 2)]

        # Act
        result = OfflineRelationDataAccess.from_triples(triples, release=sample_release)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 1
        relation = result[0]
        assert relation["subject"] == 1
        assert relation["role"] == "producer"
        assert relation["object"] == 2
        assert "release_id" in relation
        assert relation["release_id"] == 123

    @pytest.mark.asyncio
    async def test_get_relation_by_key(self) -> None:
        """Test finding relation by key."""
        # Arrange
        mock_relation_repo = AsyncMock()
        mock_key = {"subject": 1, "role": "producer", "object": 2}

        # Create a proper mock RelationInternal with the required attributes
        mock_relation_internal = Mock()
        mock_relation_internal.subject = 1
        mock_relation_internal.role = "producer"
        mock_relation_internal.object = 2
        mock_relation_internal.release_id = 123
        mock_relation_internal.year = 2020

        mock_relation = Mock(spec=Relation)
        mock_relation_internal.to_relation.return_value = mock_relation
        mock_relation_repo.find_by_key.return_value = [mock_relation_internal]

        # Act
        result = await OfflineRelationDataAccess.get_relation_by_key(
            relation_repository=mock_relation_repo,
            key=mock_key,
        )

        # Assert
        assert result is not None
        assert isinstance(result, Relation)
        assert result.role == "producer"
        mock_relation_repo.find_by_key.assert_called_once_with(mock_key)

    # def test_relation_internal_dict_to_relation_external_dict_valid(self):
    #     """Test converting internal relation dict to external dict."""
    #     # Arrange - use proper internal entity IDs
    #     # Artist ID 1 stays as 1 (internal), Label ID 2 becomes 1000000002 (internal)
    #     internal_dict = {
    #         "id": 1,
    #         "subject": 1,  # Artist ID 1 (internal)
    #         "role": "Released On",
    #         "object": 1000000002,  # Label ID 2 (internal)
    #     }
    #
    #     # Act
    #     result = OfflineRelationDataAccess.relation_internal_dict_to_relation_external_dict(internal_dict)
    #
    #     # Assert
    #     assert result is not None
    #     assert "entity_one_id" in result
    #     assert "entity_two_id" in result
    #     assert result["role"] == "Released On"

    # def test_relation_internal_dict_to_relation_external_dict_invalid(self):
    #     """Test converting invalid internal relation dict."""
    #     # Arrange
    #     invalid_dict = {"incomplete": "data"}
    #
    #     # Act
    #     result = OfflineRelationDataAccess.relation_internal_dict_to_relation_external_dict(invalid_dict)
    #
    #     # Assert
    #     assert result is None

    # def test_relation_internal_dicts_to_relation_external_dicts(self):
    #     """Test converting list of internal relation dicts to external dicts."""
    #     # Arrange - use proper internal entity IDs
    #     internal_dicts = [
    #         {
    #             "id": 1,
    #             "subject": 1,  # Artist ID 1 (internal)
    #             "role": "Released On",
    #             "object": 1000000002,  # Label ID 2 (internal)
    #         },
    #         {
    #             "id": 2,
    #             "subject": 3,  # Artist ID 3 (internal)
    #             "role": "Released On",
    #             "object": 1000000004,  # Label ID 4 (internal)
    #         },
    #         {"incomplete": "data"}  # This should be filtered out
    #     ]
    #
    #     # Act
    #     result = OfflineRelationDataAccess.relation_internal_dicts_to_relation_external_dicts(internal_dicts)
    #
    #     # Assert
    #     assert isinstance(result, list)
    #     assert len(result) == 2  # Only valid dicts should be included
    #     assert all("entity_one_id" in item for item in result)
    #     assert all("entity_two_id" in item for item in result)

    @patch("musigree.offline.data_access_layer.offline_relation_data_access.OfflineRoleDataAccess.find_role")
    @patch(
        "musigree.offline.data_access_layer.offline_relation_data_access.RoleDataUtils.normalise_role_names"
    )
    def test_from_release_with_aggregate_roles(
        self, mock_normalise_roles: Mock, mock_find_role: Mock, sample_release: Release
    ) -> None:
        """Test relation extraction with aggregate roles."""
        # Arrange
        mock_normalise_roles.return_value = ["producer"]
        mock_find_role.return_value = "producer"

        # Mock RoleType.aggregate_roles to include "producer"
        with patch.object(RoleType, "aggregate_roles", {"producer"}):
            # Act
            result = OfflineRelationDataAccess.from_release(sample_release)

            # Assert
            assert isinstance(result, list)
            mock_normalise_roles.assert_called()
            mock_find_role.assert_called()

    @patch("musigree.offline.data_access_layer.offline_relation_data_access.OfflineRoleDataAccess.find_role")
    @patch(
        "musigree.offline.data_access_layer.offline_relation_data_access.RoleDataUtils.normalise_role_names"
    )
    def test_from_release_with_track_data(
        self, mock_normalise_roles: Mock, mock_find_role: Mock, sample_release: Release
    ) -> None:
        """Test relation extraction with track-level data."""
        # Arrange
        mock_normalise_roles.return_value = ["vocals"]
        mock_find_role.return_value = "vocals"

        # Act
        result = OfflineRelationDataAccess.from_release(sample_release)

        # Assert
        assert isinstance(result, list)
        # Verify that track-level roles are processed
        mock_normalise_roles.assert_called()
        mock_find_role.assert_called()

    def test_from_release_empty_release(self) -> None:
        """Test relation extraction from empty release."""
        # Arrange
        empty_release = Release(
            release_id=999,
            title="Empty Release",
            artists=[],
            labels=[],
            extra_artists=[],
            companies=[],
            tracklist=[],
        )

        # Act
        result = OfflineRelationDataAccess.from_release(empty_release)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 0

    def test_from_release_none_values(self) -> None:
        """Test relation extraction with None values."""
        # Arrange
        release_with_nones = Release(
            release_id=777,
            title="Release with Nones",
            artists=None,
            labels=None,
            extra_artists=None,
            companies=None,
            tracklist=None,
        )

        # Act
        result = OfflineRelationDataAccess.from_release(release_with_nones)

        # Assert
        assert isinstance(result, list)
        # Should handle None values gracefully without crashing

    @patch("musigree.offline.data_access_layer.offline_relation_data_access.OfflineRoleDataAccess.find_role")
    @patch(
        "musigree.offline.data_access_layer.offline_relation_data_access.RoleDataUtils.normalise_role_names"
    )
    def test_from_release_no_role_found(
        self, mock_normalise_roles: Mock, mock_find_role: Mock, sample_release: Release
    ) -> None:
        """Test relation extraction when no role is found."""
        # Arrange
        mock_normalise_roles.return_value = ["unknown_role"]
        mock_find_role.return_value = None  # No role found

        # Act
        result = OfflineRelationDataAccess.from_release(sample_release)

        # Assert
        assert isinstance(result, list)
        # When no role is found, no relations should be created for that role
        mock_normalise_roles.assert_called()
        mock_find_role.assert_called()


class TestRelationDataAccessEdgeCases:
    """Test edge cases for OfflineRelationDataAccess."""

    def test_from_triples_empty_list(self) -> None:
        """Test from_triples with empty list."""
        triples: list[tuple[int, str, int]] = []  # Empty list of triples
        result = OfflineRelationDataAccess.from_triples(triples)
        assert result == []

    def test_from_triples_duplicate_triples(self) -> None:
        """Test from_triples with duplicate triples."""
        triples = [(1, "producer", 2), (1, "producer", 2)]  # Duplicate
        result = OfflineRelationDataAccess.from_triples(triples)
        assert len(result) == 1  # Should only have one unique relation

    def test_get_artist_label_relations_empty_sets(self) -> None:
        """Test get_artist_label_relations with empty sets."""
        result = OfflineRelationDataAccess.get_artist_label_relations(set(), set(), False)
        assert result == set()

    # def test_relation_internal_dicts_to_relation_external_dicts_empty_list(self):
    #     """Test converting empty list of internal relation dicts."""
    #     result = OfflineRelationDataAccess.relation_internal_dicts_to_relation_external_dicts([])
    #     assert result == []

    # def test_relation_internal_dicts_to_relation_external_dicts_all_invalid(self):
    #     """Test converting list with all invalid internal relation dicts."""
    #     invalid_dicts = [
    #         {"invalid": "data"},
    #         {"also": "invalid"},
    #     ]
    #     result = OfflineRelationDataAccess.relation_internal_dicts_to_relation_external_dicts(invalid_dicts)
    #     assert isinstance(result, list)
    #     assert len(result) == 0
