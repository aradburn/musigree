"""End-to-end tests for the search API endpoint."""

import pytest
from playwright.async_api import Page

from tests.e2e.end_to_end_utils import APIHelper, TEST_SEARCH_STRING


@pytest.mark.asyncio
@pytest.mark.parametrize("is_load_offline_data_required", [True], scope="class")
@pytest.mark.parametrize("is_load_runtime_data_required", [True], scope="class")
class TestAPISearch:
    """Test class for the search API endpoint."""

    async def test_search_entities_success(
        self,
        page: Page,
        base_url: str,
        server_process: None,
        is_load_offline_data_required: bool,
        is_load_runtime_data_required: bool,
    ) -> None:
        """Test searching for entities with a valid search string."""
        api_helper = APIHelper(page, base_url)
        response, json_data = await api_helper.search_entities(TEST_SEARCH_STRING)

        assert response.status == 200
        assert json_data is not None
        # Search results structure may vary, but should be a dict
        assert isinstance(json_data, dict)

    async def test_search_entities_short_string(
        self,
        page: Page,
        base_url: str,
        server_process: None,
        is_load_offline_data_required: bool,
        is_load_runtime_data_required: bool,
    ) -> None:
        """Test searching with a string that's too short (less than 2 characters)."""
        api_helper = APIHelper(page, base_url)
        response, _ = await api_helper.search_entities("a")

        # Should return 422 validation error for string too short
        assert response.status == 422

    async def test_search_entities_long_string(
        self,
        page: Page,
        base_url: str,
        server_process: None,
        is_load_offline_data_required: bool,
        is_load_runtime_data_required: bool,
    ) -> None:
        """Test searching with a string that's too long (more than 20 characters)."""
        api_helper = APIHelper(page, base_url)
        long_string = "a" * 21
        response, _ = await api_helper.search_entities(long_string)

        # Should return 422 validation error for string too long
        assert response.status == 422

    async def test_search_entities_no_results(
        self,
        page: Page,
        base_url: str,
        server_process: None,
        is_load_offline_data_required: bool,
        is_load_runtime_data_required: bool,
    ) -> None:
        """Test searching for entities that don't exist."""
        api_helper = APIHelper(page, base_url)
        response, json_data = await api_helper.search_entities("Entity12345")

        # Should return 200 even if no results found
        assert response.status == 200
        assert json_data is not None

    async def test_search_entities_too_long(
        self,
        page: Page,
        base_url: str,
        server_process: None,
        is_load_offline_data_required: bool,
        is_load_runtime_data_required: bool,
    ) -> None:
        """Test searching for entities that don't exist."""
        api_helper = APIHelper(page, base_url)
        response, json_data = await api_helper.search_entities("NonexistentEntity12345")

        # Should return 422 if search string too long
        assert response.status == 422
        assert json_data is None
