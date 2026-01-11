"""End-to-end tests for the entity details API endpoint."""

import pytest
from playwright.async_api import Page

from tests.e2e.end_to_end_utils import (
    APIHelper,
    TEST_ARTIST_ID,
    TEST_ENTITY_TYPE_ARTIST,
    TEST_INVALID_ENTITY_ID, TEST_NOT_FOUND_ENTITY_ID, TEST_INVALID_ENTITY_TYPE, TEST_INVALID_ENTITY_ID_STR,
)


@pytest.mark.asyncio
@pytest.mark.parametrize("is_load_offline_data_required", [True], scope="class")
@pytest.mark.parametrize("is_load_runtime_data_required", [True], scope="class")
class TestAPIEntityDetails:
    """Test class for the entity details API endpoint."""

    async def test_get_artist_details_success(
        self,
        page: Page,
        base_url: str,
        server_process: None,
        is_load_offline_data_required: bool,
        is_load_runtime_data_required: bool,
    ) -> None:
        """Test getting entity details for a valid artist."""
        api_helper = APIHelper(page, base_url)
        response, json_data = await api_helper.get_entity_details(
            TEST_ENTITY_TYPE_ARTIST, TEST_ARTIST_ID
        )
        assert response.status == 200
        assert json_data is not None
        assert "id" in json_data
        assert "type" in json_data
        assert "name" in json_data
        assert "metadata" in json_data
        assert "entities" in json_data
        assert "relation_counts" in json_data
        assert json_data["id"] == TEST_ARTIST_ID
        assert json_data["type"] == "artist"

    async def test_get_entity_details_not_found(
        self,
        page: Page,
        base_url: str,
        server_process: None,
        is_load_offline_data_required: bool,
        is_load_runtime_data_required: bool,
    ) -> None:
        """Test getting entity details for a non-existent entity."""
        api_helper = APIHelper(page, base_url)
        response, json_data = await api_helper.get_entity_details(
            TEST_ENTITY_TYPE_ARTIST, TEST_NOT_FOUND_ENTITY_ID
        )
        assert response.status == 404

    async def test_get_entity_details_invalid_entity_type(
        self,
        page: Page,
        base_url: str,
        server_process: None,
        is_load_offline_data_required: bool,
        is_load_runtime_data_required: bool,
    ) -> None:
        """Test getting entity details with an invalid entity type."""
        api_helper = APIHelper(page, base_url)
        response, _ = await api_helper.get_entity_details(TEST_INVALID_ENTITY_TYPE, TEST_ARTIST_ID)
        assert response.status == 400  # FastAPI validation error

    async def test_get_entity_details_invalid_entity_id(
        self,
        page: Page,
        base_url: str,
        server_process: None,
        is_load_offline_data_required: bool,
        is_load_runtime_data_required: bool,
    ) -> None:
        """Test getting entity details with an invalid entity ID (non-numeric)."""
        api_helper = APIHelper(page, base_url)
        response, _ = await api_helper.get_entity_details(TEST_ENTITY_TYPE_ARTIST, TEST_INVALID_ENTITY_ID)
        assert response.status == 400

    async def test_get_entity_details_invalid_entity_id_str(
        self,
        page: Page,
        base_url: str,
        server_process: None,
        is_load_offline_data_required: bool,
        is_load_runtime_data_required: bool,
    ) -> None:
        """Test getting entity details with an invalid entity ID (non-numeric)."""
        api_helper = APIHelper(page, base_url)
        response, _ = await api_helper.get_entity_details(TEST_ENTITY_TYPE_ARTIST, TEST_INVALID_ENTITY_ID_STR)
        assert response.status == 400
