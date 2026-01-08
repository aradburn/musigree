"""Common utilities and helper classes for end-to-end tests."""

from typing import Any

from playwright.async_api import APIResponse, Page

# Test constants
TEST_ARTIST_ID = 2239  # Seefeel
TEST_ARTIST_NAME = "Seefeel"
TEST_ENTITY_TYPE_ARTIST = "artist"
TEST_ENTITY_TYPE_LABEL = "label"
TEST_SEARCH_STRING = "Seefeel"
TEST_NOT_FOUND_ENTITY_ID = 999999999
TEST_INVALID_ENTITY_ID = -1
TEST_INVALID_ENTITY_ID_STR = "bad_string"
TEST_INVALID_ENTITY_TYPE = "invalid_type"

# Base URL for the test server
TEST_SERVER_BASE_PORT = 5050
TEST_SERVER_BASE_URL = f"http://localhost:{TEST_SERVER_BASE_PORT}"


class BasePage:
    """Base class for page interactions."""

    def __init__(self, page: Page, base_url: str) -> None:
        """Initialize the base page.

        Args:
            page: The Playwright page object.
            base_url: The base URL for the application.
        """
        self.page = page
        self.base_url = base_url

    async def navigate(self, path: str) -> None:
        """Navigate to a specific path.

        Args:
            path: The path to navigate to (relative to base_url).
        """
        url = f"{self.base_url}{path}"
        await self.page.goto(url, timeout=180000, wait_until="networkidle")

    async def get_response(self, path: str) -> APIResponse:
        """Make a GET request and return the response.

        Args:
            path: The path to request (relative to base_url).

        Returns:
            The API response object.
        """
        url = f"{self.base_url}{path}"
        response = await self.page.request.get(url)
        return response

    async def get_json(self, path: str) -> dict[str, Any]:
        """Make a GET request and return the JSON response.

        Args:
            path: The path to request (relative to base_url).

        Returns:
            The JSON response as a dictionary.
        """
        response = await self.get_response(path)
        json_data: Any = await response.json()
        assert isinstance(json_data, dict)
        return json_data


class APIHelper:
    """Helper class for API endpoint testing."""

    def __init__(self, page: Page, base_url: str) -> None:
        """Initialize the API helper.

        Args:
            page: The Playwright page object.
            base_url: The base URL for the application.
        """
        self.page = page
        self.base_url = base_url
        self.page.set_default_timeout(180000)

    async def get_entity_details(
        self, entity_type: str, entity_id: int | str
    ) -> tuple[APIResponse, dict[str, Any] | None]:
        """Get entity details from the API.

        Args:
            entity_type: The type of entity (e.g., 'artist', 'label').
            entity_id: The ID of the entity.

        Returns:
            A tuple of (response, json_data).
        """
        path = f"/api/{entity_type}/details/{entity_id}"
        response = await self.page.request.get(f"{self.base_url}{path}")
        json_data = await response.json() if response.ok else None
        return response, json_data

    async def get_entity_network(
        self,
        entity_type: str,
        entity_id: int | str,
        roles: list[str] | None = None,
        year: int | None = None,
    ) -> tuple[APIResponse, dict[str, Any] | None]:
        """Get entity network from the API.

        Args:
            entity_type: The type of entity (e.g., 'artist', 'label').
            entity_id: The ID of the entity.
            roles: Optional list of roles to filter by.
            year: Optional year to filter by.

        Returns:
            A tuple of (response, json_data).
        """
        path = f"/api/{entity_type}/network/{entity_id}"
        params: list[str] = []
        if roles:
            params.append(f"roles={','.join(roles)}")
        if year:
            params.append(f"year={year}")
        if params:
            path += "?" + "&".join(params)
        response = await self.page.request.get(f"{self.base_url}{path}")
        json_data = await response.json() if response.ok else None
        return response, json_data

    async def get_entity_relations(
        self, entity_type: str, entity_id: int | str
    ) -> tuple[APIResponse, dict[str, Any] | None]:
        """Get entity relations from the API.

        Args:
            entity_type: The type of entity (e.g., 'artist', 'label').
            entity_id: The ID of the entity.

        Returns:
            A tuple of (response, json_data).
        """
        path = f"/api/{entity_type}/relations/{entity_id}"
        response = await self.page.request.get(f"{self.base_url}{path}")
        json_data = await response.json() if response.ok else None
        return response, json_data

    async def search_entities(
        self, search_string: str
    ) -> tuple[APIResponse, dict[str, Any] | None]:
        """Search for entities.

        Args:
            search_string: The search string.

        Returns:
            A tuple of (response, json_data).
        """
        path = f"/api/search/{search_string}"
        response = await self.page.request.get(f"{self.base_url}{path}")
        json_data = await response.json() if response.ok else None
        return response, json_data

    async def get_random_entity(self) -> tuple[APIResponse, dict[str, Any] | None]:
        """Get a random entity from the API.

        Returns:
            A tuple of (response, json_data).
        """
        path = "/api/random"
        response = await self.page.request.get(f"{self.base_url}{path}", timeout=180000)
        json_data = await response.json() if response.ok else None
        return response, json_data

    async def get_roles(self) -> tuple[APIResponse, dict[str, Any] | None]:
        """Get all roles from the API.

        Returns:
            A tuple of (response, json_data).
        """
        path = "/api/roles"
        response = await self.page.request.get(f"{self.base_url}{path}")
        json_data = await response.json() if response.ok else None
        return response, json_data
