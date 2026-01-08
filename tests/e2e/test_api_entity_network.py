"""End-to-end tests for the entity network API endpoint."""

import pytest
from playwright.async_api import Page

from tests.e2e.end_to_end_utils import (
    APIHelper,
    TEST_ARTIST_ID,
    TEST_ENTITY_TYPE_ARTIST,
    TEST_INVALID_ENTITY_ID, TEST_INVALID_ENTITY_TYPE, TEST_NOT_FOUND_ENTITY_ID, TEST_INVALID_ENTITY_ID_STR,
)


@pytest.mark.asyncio
@pytest.mark.parametrize("is_load_offline_data_required", [True], scope="class")
@pytest.mark.parametrize("is_load_runtime_data_required", [True], scope="class")
class TestAPIEntityNetwork:
    """Test class for the entity network API endpoint."""

    async def test_get_artist_network_success(
        self,
        page: Page,
        base_url: str,
        server_process: None,
        is_load_offline_data_required: bool,
        is_load_runtime_data_required: bool,
    ) -> None:
        """Test getting network graph for a valid artist."""
        api_helper = APIHelper(page, base_url)
        response, json_data = await api_helper.get_entity_network(
            TEST_ENTITY_TYPE_ARTIST, TEST_ARTIST_ID
        )
        assert response.status == 200
        assert json_data is not None
        assert "center" in json_data
        assert "nodes" in json_data
        assert "links" in json_data

    async def test_get_artist_network_with_roles(
        self,
        page: Page,
        base_url: str,
        server_process: None,
        is_load_offline_data_required: bool,
        is_load_runtime_data_required: bool,
    ) -> None:
        """Test getting network graph with role filtering."""
        api_helper = APIHelper(page, base_url)
        response, json_data = await api_helper.get_entity_network(
            TEST_ENTITY_TYPE_ARTIST, TEST_ARTIST_ID, roles=["Producer"]
        )
        assert response.status == 200
        assert json_data is not None

    async def test_get_artist_network_with_year(
        self,
        page: Page,
        base_url: str,
        server_process: None,
        is_load_offline_data_required: bool,
        is_load_runtime_data_required: bool,
    ) -> None:
        """Test getting network graph with year filtering."""
        api_helper = APIHelper(page, base_url)
        response, json_data = await api_helper.get_entity_network(
            TEST_ENTITY_TYPE_ARTIST, TEST_ARTIST_ID, year=1990
        )
        assert response.status == 200
        assert json_data is not None

    async def test_get_entity_network_not_found(
        self,
        page: Page,
        base_url: str,
        server_process: None,
        is_load_offline_data_required: bool,
        is_load_runtime_data_required: bool,
    ) -> None:
        """Test getting network graph for a non-existent entity."""
        api_helper = APIHelper(page, base_url)
        response, json_data = await api_helper.get_entity_network(
            TEST_ENTITY_TYPE_ARTIST, TEST_NOT_FOUND_ENTITY_ID
        )
        # assert response.status == 422

    async def test_get_entity_network_invalid_id(
        self,
        page: Page,
        base_url: str,
        server_process: None,
        is_load_offline_data_required: bool,
        is_load_runtime_data_required: bool,
    ) -> None:
        """Test getting network graph for a non-existent entity."""
        api_helper = APIHelper(page, base_url)
        response, json_data = await api_helper.get_entity_network(
            TEST_ENTITY_TYPE_ARTIST, TEST_INVALID_ENTITY_ID
        )
        assert response.status == 400

    async def test_get_entity_network_invalid_id_str(
        self,
        page: Page,
        base_url: str,
        server_process: None,
        is_load_offline_data_required: bool,
        is_load_runtime_data_required: bool,
    ) -> None:
        """Test getting network graph for a non-existent entity."""
        api_helper = APIHelper(page, base_url)
        response, json_data = await api_helper.get_entity_network(
            TEST_ENTITY_TYPE_ARTIST, TEST_INVALID_ENTITY_ID_STR
        )
        assert response.status == 400

    async def test_get_entity_network_invalid_entity_type(
        self,
        page: Page,
        base_url: str,
        server_process: None,
        is_load_offline_data_required: bool,
        is_load_runtime_data_required: bool,
    ) -> None:
        """Test getting network graph with an invalid entity type."""
        api_helper = APIHelper(page, base_url)
        response, _ = await api_helper.get_entity_network(TEST_INVALID_ENTITY_TYPE, TEST_ARTIST_ID)
        assert response.status == 400  # FastAPI validation error
