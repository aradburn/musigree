"""End-to-end tests for the label page UI route."""

import pytest
from playwright.async_api import Page

from tests.e2e.end_to_end_utils import BasePage, TEST_INVALID_ENTITY_ID, TEST_NOT_FOUND_ENTITY_ID, \
    TEST_INVALID_ENTITY_ID_STR


@pytest.mark.asyncio
@pytest.mark.parametrize("is_load_offline_data_required", [True], scope="class")
@pytest.mark.parametrize("is_load_runtime_data_required", [True], scope="class")
class TestUILabel:
    """Test class for the label page UI route."""

    async def test_label_page_loads(
        self,
        page: Page,
        base_url: str,
        server_process: None,
        is_load_offline_data_required: bool,
        is_load_runtime_data_required: bool,
    ) -> None:
        """Test that the label page loads successfully for a valid label."""
        # Using a test label ID - adjust if needed based on test data
        label_id = 1
        base_page = BasePage(page, base_url)
        await base_page.navigate(f"/label/{label_id}")

        assert page.url == f"{base_url}/label/{label_id}"
        # Check that the page title contains "Musigree"
        title = await page.title()
        assert "Musigree" in title

    async def test_label_page_contains_expected_content(
        self,
        page: Page,
        base_url: str,
        server_process: None,
        is_load_offline_data_required: bool,
        is_load_runtime_data_required: bool,
    ) -> None:
        """Test that the label page contains expected content."""
        # Using a test label ID - adjust if needed based on test data
        label_id = 1
        base_page = BasePage(page, base_url)
        await base_page.navigate(f"/label/{label_id}")

        # Check that the page has some content
        body_text = await page.locator("body").text_content()
        assert body_text is not None
        assert len(body_text) > 0

    async def test_label_page_with_query_parameters(
        self,
        page: Page,
        base_url: str,
        server_process: None,
        is_load_offline_data_required: bool,
        is_load_runtime_data_required: bool,
    ) -> None:
        """Test that the label page loads with query parameters."""
        # Using a test label ID - adjust if needed based on test data
        label_id = 1
        base_page = BasePage(page, base_url)
        await base_page.navigate(f"/label/{label_id}?roles=Producer&year=1990")

        assert page.url.startswith(f"{base_url}/label/{label_id}")
        title = await page.title()
        assert "Musigree" in title

    async def test_label_page_not_found(
        self,
        page: Page,
        base_url: str,
        server_process: None,
        is_load_offline_data_required: bool,
        is_load_runtime_data_required: bool,
    ) -> None:
        """Test that the label page returns 404 for a non-existent label."""
        response = await page.request.get(f"{base_url}/label/{TEST_NOT_FOUND_ENTITY_ID}")
        assert response.status == 404

    async def test_label_page_invalid_id(
        self,
        page: Page,
        base_url: str,
        server_process: None,
        is_load_offline_data_required: bool,
        is_load_runtime_data_required: bool,
    ) -> None:
        """Test that the label page handles invalid ID format."""
        response = await page.request.get(f"{base_url}/label/{TEST_INVALID_ENTITY_ID}")
        assert response.status == 400

    async def test_label_page_invalid_id_str(
        self,
        page: Page,
        base_url: str,
        server_process: None,
        is_load_offline_data_required: bool,
        is_load_runtime_data_required: bool,
    ) -> None:
        """Test that the label page handles invalid ID format."""
        response = await page.request.get(f"{base_url}/label/{TEST_INVALID_ENTITY_ID_STR}")
        assert response.status == 400
