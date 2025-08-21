"""
Unit tests for the ReleaseDataAccess class.

This module contains comprehensive unit tests for the ReleaseDataAccess class,
which provides data access functionality for releases in the Musigree offline system.
It tests the creation and population of EntityDetailsIndex from release data.
"""

from typing import AsyncGenerator
from unittest.mock import Mock, patch

import pytest

from musigree.offline.data_access_layer.release_data_access import ReleaseDataAccess
from musigree.offline.database.release_repository import ReleaseRepository
from musigree.runtime.data_access_layer.entity_details_index import EntityDetailsIndex


async def async_iterator(items: list) -> AsyncGenerator:
    """Helper function to create async iterator from list."""
    for item in items:
        yield item


class TestCreateEntityDetailsIndex:
    """Test class for create_entity_details_index method."""

    @patch("musigree.offline.data_access_layer.release_data_access.EntityDetailsIndex")
    @pytest.mark.asyncio
    async def test_create_entity_details_index_empty_repository(
        self, mock_entity_details_index_class: Mock
    ) -> None:
        """Test create_entity_details_index with empty repository."""
        # Setup
        mock_repository = Mock(spec=ReleaseRepository)
        mock_repository.all.return_value = async_iterator([])

        mock_index = Mock(spec=EntityDetailsIndex)
        mock_entity_details_index_class.return_value = mock_index

        # Test
        result = await ReleaseDataAccess.create_entity_details_index(mock_repository)

        # Assertions
        mock_entity_details_index_class.assert_called_once()
        assert result == mock_index

    @patch("musigree.offline.data_access_layer.release_data_access.EntityDetailsIndex")
    @pytest.mark.asyncio
    async def test_create_entity_details_index_single_release_with_country(
        self, mock_entity_details_index_class: Mock
    ) -> None:
        """Test create_entity_details_index with a single release containing country data."""
        # Setup
        mock_repository = Mock(spec=ReleaseRepository)

        # Create a mock release with country, artists, and labels
        mock_release = Mock()
        mock_release.country = "US"
        mock_release.artists = [{"id": "artist1", "name": "Artist One"}]
        mock_release.labels = [{"id": "label1", "name": "Label One"}]
        mock_release.genres = None
        mock_release.styles = None

        mock_repository.all.return_value = async_iterator([mock_release])

        mock_index = Mock(spec=EntityDetailsIndex)
        mock_entity_details_index_class.return_value = mock_index

        # Test
        result = await ReleaseDataAccess.create_entity_details_index(mock_repository)

        # Assertions
        mock_entity_details_index_class.assert_called_once()
        mock_index.index_country.assert_any_call("artist1", "US")
        mock_index.index_country.assert_any_call("label1", "US")
        assert mock_index.index_country.call_count == 2
        assert result == mock_index

    @patch("musigree.offline.data_access_layer.release_data_access.EntityDetailsIndex")
    @pytest.mark.asyncio
    async def test_create_entity_details_index_single_release_with_genres(
        self, mock_entity_details_index_class: Mock
    ) -> None:
        """Test create_entity_details_index with a single release containing genre data."""
        # Setup
        mock_repository = Mock(spec=ReleaseRepository)

        # Create a mock release with genres
        mock_release = Mock()
        mock_release.country = None
        mock_release.artists = [{"id": "artist1", "name": "Artist One"}]
        mock_release.labels = [{"id": "label1", "name": "Label One"}]
        mock_release.genres = ["Rock", "Pop"]
        mock_release.styles = None

        mock_repository.all.return_value = async_iterator([mock_release])

        mock_index = Mock(spec=EntityDetailsIndex)
        mock_entity_details_index_class.return_value = mock_index

        # Test
        result = await ReleaseDataAccess.create_entity_details_index(mock_repository)

        # Assertions
        mock_entity_details_index_class.assert_called_once()
        # Should index both genres for both artist and label
        mock_index.index_genre.assert_any_call("artist1", "Rock")
        mock_index.index_genre.assert_any_call("artist1", "Pop")
        mock_index.index_genre.assert_any_call("label1", "Rock")
        mock_index.index_genre.assert_any_call("label1", "Pop")
        assert mock_index.index_genre.call_count == 4
        assert result == mock_index

    @patch("musigree.offline.data_access_layer.release_data_access.EntityDetailsIndex")
    @pytest.mark.asyncio
    async def test_create_entity_details_index_single_release_with_styles(
        self, mock_entity_details_index_class: Mock
    ) -> None:
        """Test create_entity_details_index with a single release containing style data."""
        # Setup
        mock_repository = Mock(spec=ReleaseRepository)

        # Create a mock release with styles
        mock_release = Mock()
        mock_release.country = None
        mock_release.artists = [{"id": "artist1", "name": "Artist One"}]
        mock_release.labels = [{"id": "label1", "name": "Label One"}]
        mock_release.genres = None
        mock_release.styles = ["Alternative Rock", "Indie Pop"]

        mock_repository.all.return_value = async_iterator([mock_release])

        mock_index = Mock(spec=EntityDetailsIndex)
        mock_entity_details_index_class.return_value = mock_index

        # Test
        result = await ReleaseDataAccess.create_entity_details_index(mock_repository)

        # Assertions
        mock_entity_details_index_class.assert_called_once()
        # Should index both styles for both artist and label
        mock_index.index_style.assert_any_call("artist1", "Alternative Rock")
        mock_index.index_style.assert_any_call("artist1", "Indie Pop")
        mock_index.index_style.assert_any_call("label1", "Alternative Rock")
        mock_index.index_style.assert_any_call("label1", "Indie Pop")
        assert mock_index.index_style.call_count == 4
        assert result == mock_index

    @patch("musigree.offline.data_access_layer.release_data_access.EntityDetailsIndex")
    @pytest.mark.asyncio
    async def test_create_entity_details_index_release_without_id_in_artists(
        self, mock_entity_details_index_class: Mock
    ) -> None:
        """Test create_entity_details_index with release where artists don't have id."""
        # Setup
        mock_repository = Mock(spec=ReleaseRepository)

        # Create a mock release with artists missing id
        mock_release = Mock()
        mock_release.country = "US"
        mock_release.artists = [{"name": "Artist One"}]  # No id field
        mock_release.labels = [{"id": "label1", "name": "Label One"}]
        mock_release.genres = None
        mock_release.styles = None

        mock_repository.all.return_value = async_iterator([mock_release])

        mock_index = Mock(spec=EntityDetailsIndex)
        mock_entity_details_index_class.return_value = mock_index

        # Test
        result = await ReleaseDataAccess.create_entity_details_index(mock_repository)

        # Assertions
        mock_entity_details_index_class.assert_called_once()
        # Should only index country for label, not artist (missing id)
        mock_index.index_country.assert_called_once_with("label1", "US")
        assert result == mock_index

    @patch("musigree.offline.data_access_layer.release_data_access.EntityDetailsIndex")
    @pytest.mark.asyncio
    async def test_create_entity_details_index_release_without_id_in_labels(
        self, mock_entity_details_index_class: Mock
    ) -> None:
        """Test create_entity_details_index with release where labels don't have id."""
        # Setup
        mock_repository = Mock(spec=ReleaseRepository)

        # Create a mock release with labels missing id
        mock_release = Mock()
        mock_release.country = "US"
        mock_release.artists = [{"id": "artist1", "name": "Artist One"}]
        mock_release.labels = [{"name": "Label One"}]  # No id field
        mock_release.genres = None
        mock_release.styles = None

        mock_repository.all.return_value = async_iterator([mock_release])

        mock_index = Mock(spec=EntityDetailsIndex)
        mock_entity_details_index_class.return_value = mock_index

        # Test
        result = await ReleaseDataAccess.create_entity_details_index(mock_repository)

        # Assertions
        mock_entity_details_index_class.assert_called_once()
        # Should only index country for artist, not label (missing id)
        mock_index.index_country.assert_called_once_with("artist1", "US")
        assert result == mock_index

    @patch("musigree.offline.data_access_layer.release_data_access.EntityDetailsIndex")
    @pytest.mark.asyncio
    async def test_create_entity_details_index_non_list_artists(
        self, mock_entity_details_index_class: Mock
    ) -> None:
        """Test create_entity_details_index with release where artists is not a list."""
        # Setup
        mock_repository = Mock(spec=ReleaseRepository)

        # Create a mock release with artists as non-list
        mock_release = Mock()
        mock_release.country = "US"
        mock_release.artists = "Not a list"
        mock_release.labels = [{"id": "label1", "name": "Label One"}]
        mock_release.genres = None
        mock_release.styles = None

        mock_repository.all.return_value = async_iterator([mock_release])

        mock_index = Mock(spec=EntityDetailsIndex)
        mock_entity_details_index_class.return_value = mock_index

        # Test
        result = await ReleaseDataAccess.create_entity_details_index(mock_repository)

        # Assertions
        mock_entity_details_index_class.assert_called_once()
        # Should only index country for label, not artist (not a list)
        mock_index.index_country.assert_called_once_with("label1", "US")
        assert result == mock_index

    @patch("musigree.offline.data_access_layer.release_data_access.EntityDetailsIndex")
    @pytest.mark.asyncio
    async def test_create_entity_details_index_non_list_labels(
        self, mock_entity_details_index_class: Mock
    ) -> None:
        """Test create_entity_details_index with release where labels is not a list."""
        # Setup
        mock_repository = Mock(spec=ReleaseRepository)

        # Create a mock release with labels as non-list
        mock_release = Mock()
        mock_release.country = "US"
        mock_release.artists = [{"id": "artist1", "name": "Artist One"}]
        mock_release.labels = "Not a list"
        mock_release.genres = None
        mock_release.styles = None

        mock_repository.all.return_value = async_iterator([mock_release])

        mock_index = Mock(spec=EntityDetailsIndex)
        mock_entity_details_index_class.return_value = mock_index

        # Test
        result = await ReleaseDataAccess.create_entity_details_index(mock_repository)

        # Assertions
        mock_entity_details_index_class.assert_called_once()
        # Should only index country for artist, not label (not a list)
        mock_index.index_country.assert_called_once_with("artist1", "US")
        assert result == mock_index

    @patch("musigree.offline.data_access_layer.release_data_access.EntityDetailsIndex")
    @patch("musigree.offline.data_access_layer.release_data_access.LoaderBase")
    @pytest.mark.asyncio
    async def test_create_entity_details_index_bulk_reporting(
        self, mock_loader_base: Mock, mock_entity_details_index_class: Mock
    ) -> None:
        """Test create_entity_details_index with bulk reporting."""
        # Setup
        mock_repository = Mock(spec=ReleaseRepository)
        mock_loader_base.BULK_REPORTING_SIZE = 10

        # Create multiple mock releases to trigger bulk reporting
        mock_releases = []
        for _ in range(1005):  # Just over 1000 to trigger reporting
            mock_release = Mock()
            mock_release.country = None
            mock_release.artists = []
            mock_release.labels = []
            mock_release.genres = None
            mock_release.styles = None
            mock_releases.append(mock_release)

        mock_repository.all.return_value = async_iterator(mock_releases)

        mock_index = Mock(spec=EntityDetailsIndex)
        mock_entity_details_index_class.return_value = mock_index

        # Test
        with patch(
            "musigree.offline.data_access_layer.release_data_access.log"
        ) as mock_log:
            result = await ReleaseDataAccess.create_entity_details_index(
                mock_repository
            )

        # Assertions
        mock_entity_details_index_class.assert_called_once()
        # Should log progress at 1000 and final count
        assert mock_log.debug.call_count >= 2
        assert result == mock_index

    @patch("musigree.offline.data_access_layer.release_data_access.EntityDetailsIndex")
    @pytest.mark.asyncio
    async def test_create_entity_details_index_complete_release_data(
        self, mock_entity_details_index_class: Mock
    ) -> None:
        """Test create_entity_details_index with complete release data."""
        # Setup
        mock_repository = Mock(spec=ReleaseRepository)

        # Create a mock release with all data fields
        mock_release = Mock()
        mock_release.country = "UK"
        mock_release.artists = [
            {"id": "artist1", "name": "Artist One"},
            {"id": "artist2", "name": "Artist Two"},
        ]
        mock_release.labels = [{"id": "label1", "name": "Label One"}]
        mock_release.genres = ["Electronic", "Ambient"]
        mock_release.styles = ["Downtempo", "Chillout"]

        mock_repository.all.return_value = async_iterator([mock_release])

        mock_index = Mock(spec=EntityDetailsIndex)
        mock_entity_details_index_class.return_value = mock_index

        # Test
        result = await ReleaseDataAccess.create_entity_details_index(mock_repository)

        # Assertions
        mock_entity_details_index_class.assert_called_once()

        # Check country indexing
        mock_index.index_country.assert_any_call("artist1", "UK")
        mock_index.index_country.assert_any_call("artist2", "UK")
        mock_index.index_country.assert_any_call("label1", "UK")
        assert mock_index.index_country.call_count == 3

        # Check genre indexing
        mock_index.index_genre.assert_any_call("artist1", "Electronic")
        mock_index.index_genre.assert_any_call("artist1", "Ambient")
        mock_index.index_genre.assert_any_call("artist2", "Electronic")
        mock_index.index_genre.assert_any_call("artist2", "Ambient")
        mock_index.index_genre.assert_any_call("label1", "Electronic")
        mock_index.index_genre.assert_any_call("label1", "Ambient")
        assert mock_index.index_genre.call_count == 6

        # Check style indexing
        mock_index.index_style.assert_any_call("artist1", "Downtempo")
        mock_index.index_style.assert_any_call("artist1", "Chillout")
        mock_index.index_style.assert_any_call("artist2", "Downtempo")
        mock_index.index_style.assert_any_call("artist2", "Chillout")
        mock_index.index_style.assert_any_call("label1", "Downtempo")
        mock_index.index_style.assert_any_call("label1", "Chillout")
        assert mock_index.index_style.call_count == 6

        assert result == mock_index
