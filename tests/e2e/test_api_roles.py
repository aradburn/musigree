"""End-to-end tests for the roles API endpoint."""

import pytest
from playwright.async_api import Page

from tests.e2e.end_to_end_utils import APIHelper


@pytest.mark.asyncio
@pytest.mark.parametrize("is_load_offline_data_required", [True], scope="class")
@pytest.mark.parametrize("is_load_runtime_data_required", [True], scope="class")
class TestAPIRoles:
    """Test class for the roles API endpoint."""

    async def test_get_roles_success(
        self,
        page: Page,
        base_url: str,
        server_process: None,
        is_load_offline_data_required: bool,
        is_load_runtime_data_required: bool,
    ) -> None:
        """Test getting all available roles."""
        api_helper = APIHelper(page, base_url)
        response, json_data = await api_helper.get_roles()

        assert response.status == 200
        assert json_data is not None
        assert "roles" in json_data
        assert isinstance(json_data["roles"], list)
        assert len(json_data["roles"]) > 0

    async def test_get_roles_structure(
        self,
        page: Page,
        base_url: str,
        server_process: None,
        is_load_offline_data_required: bool,
        is_load_runtime_data_required: bool,
    ) -> None:
        """Test that roles have the expected structure."""
        api_helper = APIHelper(page, base_url)
        response, json_data = await api_helper.get_roles()

        assert response.status == 200
        assert json_data is not None
        roles = json_data["roles"]
        # Each role should be a string or have a specific structure
        for role in roles:
            assert isinstance(role, str) or isinstance(role, dict)
