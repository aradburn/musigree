"""End-to-end tests for the index page UI route."""
import pytest
from playwright.async_api import Page

from tests.e2e.end_to_end_utils import BasePage


@pytest.mark.asyncio
@pytest.mark.parametrize("is_load_offline_data_required", [True], scope="class")
@pytest.mark.parametrize("is_load_runtime_data_required", [True], scope="class")
class TestUIIndex:
    """Test class for the index page UI route."""

    async def test_index_page_loads(
        self,
        page: Page,
        base_url: str,
        server_process: None,
        is_load_offline_data_required: bool,
        is_load_runtime_data_required: bool,
    ) -> None:
        """Test that the index page loads successfully."""
        base_page = BasePage(page, base_url)
        await base_page.navigate("/")

        assert page.url == f"{base_url}/"
        # Check that the page title contains "Musigree"
        title = await page.title()
        assert "Musigree" in title

    @pytest.mark.asyncio
    async def test_index_page_contains_expected_content(
        self,
        page: Page,
        base_url: str,
        server_process: None,
        is_load_offline_data_required: bool,
        is_load_runtime_data_required: bool,
    ) -> None:
        """Test that the index page contains expected content."""
        base_page = BasePage(page, base_url)
        await base_page.navigate("/")

        # Check that the page has some content
        body_text = await page.locator("body").text_content()
        assert body_text is not None
        assert len(body_text) > 0

    @pytest.mark.asyncio
    async def test_index_page_with_query_parameters(
        self,
        page: Page,
        base_url: str,
        server_process: None,
        is_load_offline_data_required: bool,
        is_load_runtime_data_required: bool,
    ) -> None:
        """Test that the index page loads with query parameters."""
        base_page = BasePage(page, base_url)
        await base_page.navigate("/?roles=Producer&year=1990")

        assert page.url.startswith(f"{base_url}/")
        title = await page.title()
        assert "Musigree" in title

    @pytest.mark.asyncio
    async def test_index_page_response_status(
        self,
        page: Page,
        base_url: str,
        server_process: None,
        is_load_offline_data_required: bool,
        is_load_runtime_data_required: bool,
    ) -> None:
        """Test that the index page returns a 200 status code."""
        response = await page.request.get(f"{base_url}/")
        assert response.status == 200
