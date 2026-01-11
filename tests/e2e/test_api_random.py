"""End-to-end tests for the random entity API endpoint."""

import pytest
from playwright.async_api import Page

from tests.e2e.end_to_end_utils import APIHelper


@pytest.mark.asyncio
@pytest.mark.parametrize("is_load_offline_data_required", [True], scope="class")
@pytest.mark.parametrize("is_load_runtime_data_required", [True], scope="class")
class TestAPIRandom:
    """Test class for the random entity API endpoint."""

    async def test_get_random_entity_success(
        self,
        page: Page,
        base_url: str,
        server_process: None,
        is_load_offline_data_required: bool,
        is_load_runtime_data_required: bool,
    ) -> None:
        """Test getting a random entity."""
        api_helper = APIHelper(page, base_url)
        response, json_data = await api_helper.get_random_entity()

        assert response.status == 200
        assert json_data is not None
        assert "center" in json_data
        assert isinstance(json_data["center"], str)
        # Format should be "entity_type-entity_id"
        assert "-" in json_data["center"]

    async def test_get_random_entity_multiple_calls(
        self,
        page: Page,
        base_url: str,
        server_process: None,
        is_load_offline_data_required: bool,
        is_load_runtime_data_required: bool,
    ) -> None:
        """Test getting multiple random entities (they may be different)."""
        api_helper = APIHelper(page, base_url)
        response1, json_data1 = await api_helper.get_random_entity()
        response2, json_data2 = await api_helper.get_random_entity()

        assert response1.status == 200
        assert response2.status == 200
        assert json_data1 is not None
        assert json_data2 is not None
        assert "center" in json_data1
        assert "center" in json_data2
