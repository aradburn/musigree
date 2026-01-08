"""End-to-end tests for the artist page UI route."""

import pytest
from playwright.async_api import Page

from tests.e2e.end_to_end_utils import BasePage, TEST_ARTIST_ID, TEST_INVALID_ENTITY_ID, TEST_NOT_FOUND_ENTITY_ID, \
    TEST_INVALID_ENTITY_ID_STR


@pytest.mark.asyncio
@pytest.mark.parametrize("is_load_offline_data_required", [True], scope="class")
@pytest.mark.parametrize("is_load_runtime_data_required", [True], scope="class")
class TestUIArtist:
    """Test class for the artist page UI route."""

    async def test_artist_page_loads(
        self,
        page: Page,
        base_url: str,
        server_process: None,
        is_load_offline_data_required: bool,
        is_load_runtime_data_required: bool,
    ) -> None:
        """Test that the artist page loads successfully for a valid artist."""
        base_page = BasePage(page, base_url)
        await base_page.navigate(f"/artist/{TEST_ARTIST_ID}")

        assert page.url == f"{base_url}/artist/{TEST_ARTIST_ID}"
        # Check that the page title contains "Musigree"
        title = await page.title()
        assert "Musigree" in title

    async def test_artist_page_contains_expected_content(
        self,
        page: Page,
        base_url: str,
        server_process: None,
        is_load_offline_data_required: bool,
        is_load_runtime_data_required: bool,
    ) -> None:
        """Test that the artist page contains expected content."""
        base_page = BasePage(page, base_url)
        await base_page.navigate(f"/artist/{TEST_ARTIST_ID}")

        # Check that the page has some content
        body_text = await page.locator("body").text_content()
        assert body_text is not None
        assert len(body_text) > 0

    async def test_artist_page_with_query_parameters(
        self,
        page: Page,
        base_url: str,
        server_process: None,
        is_load_offline_data_required: bool,
        is_load_runtime_data_required: bool,
    ) -> None:
        """Test that the artist page loads with query parameters."""
        base_page = BasePage(page, base_url)
        await base_page.navigate(f"/artist/{TEST_ARTIST_ID}?roles=Producer&year=1990")

        assert page.url.startswith(f"{base_url}/artist/{TEST_ARTIST_ID}")
        title = await page.title()
        assert "Musigree" in title

    async def test_artist_page_not_found(
        self,
        page: Page,
        base_url: str,
        server_process: None,
        is_load_offline_data_required: bool,
        is_load_runtime_data_required: bool,
    ) -> None:
        """Test that the artist page returns 404 for a non-existent artist."""
        response = await page.request.get(f"{base_url}/artist/{TEST_NOT_FOUND_ENTITY_ID}")
        assert response.status == 404

    async def test_artist_page_invalid_id(
        self,
        page: Page,
        base_url: str,
        server_process: None,
        is_load_offline_data_required: bool,
        is_load_runtime_data_required: bool,
    ) -> None:
        """Test that the artist page handles invalid ID format."""
        response = await page.request.get(f"{base_url}/artist/{TEST_INVALID_ENTITY_ID}")
        assert response.status == 400

    async def test_artist_page_invalid_id_str(
        self,
        page: Page,
        base_url: str,
        server_process: None,
        is_load_offline_data_required: bool,
        is_load_runtime_data_required: bool,
    ) -> None:
        """Test that the artist page handles invalid ID format."""
        response = await page.request.get(f"{base_url}/artist/{TEST_INVALID_ENTITY_ID_STR}")
        assert response.status == 400
