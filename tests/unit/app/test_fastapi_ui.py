from unittest.mock import Mock, patch, AsyncMock

import pytest
from fastapi import Request
from fastapi.responses import HTMLResponse

from musigree.app.fastapi_dependencies import UI_DEFAULT_ROLES
from musigree.app.fastapi_ui import (
    router,
    route__index,
    route__entity_type__entity_id,
)
from musigree.exceptions import BadRequestError, NotFoundError
from musigree.library.fields.entity_type import EntityType


def _create_mock_base_url(url_string: str) -> Mock:
    """Create a mock base_url that supports the replace() method."""
    mock_url = Mock()
    # noinspection HttpUrlsUsage
    mock_url.replace.return_value = url_string.replace("http://", "https://")
    return mock_url


class TestFastAPIUI:
    """Test cases for the FastAPI UI module."""

    def test_ui_default_roles(self) -> None:
        """Test that UI_DEFAULT_ROLES is properly defined."""
        assert isinstance(UI_DEFAULT_ROLES, list)
        assert "Alias" in UI_DEFAULT_ROLES
        assert "Member Of" in UI_DEFAULT_ROLES

    @patch("musigree.app.fastapi_app.templates")
    @patch("musigree.library.cache.role_cache.RoleCache.get_roles_json")
    @patch("musigree.runtime.data_access_layer.role_entry.RoleEntry.get_multiselect_mapping")
    @pytest.mark.asyncio
    async def test_route_index_basic(
        self,
        mock_multiselect: Mock,
        mock_roles_json: Mock,
        mock_templates: Mock,
    ) -> None:
        """Test the basic index route functionality."""
        # Setup mocks
        mock_multiselect.return_value = {"test": "mapping"}
        mock_roles_json.return_value = '{"role1": "data"}'
        mock_templates.TemplateResponse.return_value = HTMLResponse("<html></html>")

        # Create mock request
        mock_request = Mock(spec=Request)
        mock_request.base_url = _create_mock_base_url("http://localhost:8000/")

        # Call the route with UI_DEFAULT_ROLES since that's what gets set when no roles are provided
        response = await route__index(mock_request, roles=UI_DEFAULT_ROLES, year=None)

        # Verify the response
        assert isinstance(response, HTMLResponse)
        mock_templates.TemplateResponse.assert_called_once()

        # Verify template context
        call_args = mock_templates.TemplateResponse.call_args
        # Check that request and name are passed as keyword arguments
        assert call_args.kwargs["request"] == mock_request
        assert call_args.kwargs["name"] == "index.html"
        context = call_args.kwargs["context"]
        assert context["title"] == "Musigree - Explore Music Connections, an Interactive Map of Artists, Bands & Labels"
        assert context["og_title"] == "Musigree - An Interactive Map of Artists, Bands & Labels"
        assert context["original_roles"] == UI_DEFAULT_ROLES
        assert context["original_year"] is None

    @patch("musigree.app.fastapi_app.templates")
    @patch("musigree.library.cache.role_cache.RoleCache.get_roles_json")
    @patch("musigree.runtime.data_access_layer.role_entry.RoleEntry.get_multiselect_mapping")
    @pytest.mark.asyncio
    async def test_route_index_with_parameters(
        self,
        mock_multiselect: Mock,
        mock_roles_json: Mock,
        mock_templates: Mock,
    ) -> None:
        """Test the index route with roles and year parameters."""
        # Setup mocks
        mock_multiselect.return_value = {"test": "mapping"}
        mock_roles_json.return_value = '{"role1": "data"}'
        mock_templates.TemplateResponse.return_value = HTMLResponse("<html></html>")

        # Create mock request
        mock_request = Mock(spec=Request)
        mock_request.base_url = _create_mock_base_url("http://localhost:8000/")

        # Call the route
        response = await route__index(mock_request, roles=["Artist", "Album"], year=2000)

        # Verify the response
        assert isinstance(response, HTMLResponse)

        # Verify template context
        call_args = mock_templates.TemplateResponse.call_args
        context = call_args.kwargs["context"]
        assert context["original_roles"] == ["Artist", "Album"]
        assert context["original_year"] == 2000

    @patch("musigree.app.fastapi_app.templates")
    @patch("musigree.library.cache.role_cache.RoleCache.get_roles_json")
    @patch("musigree.runtime.data_access_layer.role_entry.RoleEntry.get_multiselect_mapping")
    @patch("musigree.runtime.runtime_database_manager.RuntimeDatabaseManager")
    @pytest.mark.asyncio
    async def test_route_entity_type_entity_id_success(
        self,
        mock_db_manager: Mock,
        mock_multiselect: Mock,
        mock_roles_json: Mock,
        mock_templates: Mock,
    ) -> None:
        """Test the entity route with valid parameters."""
        # Setup mocks
        mock_multiselect.return_value = {"test": "mapping"}
        mock_roles_json.return_value = '{"role1": "data"}'
        mock_templates.TemplateResponse.return_value = HTMLResponse("<html></html>")

        mock_network_data = {
            "center": {"name": "The Beatles"},
            "nodes": [],
            "edges": [],
        }
        # Create a mock runtime_database_helper with get_network method
        mock_helper = Mock()
        mock_helper.get_network = AsyncMock(return_value=mock_network_data)
        mock_db_manager.runtime_database_helper = mock_helper

        # Create mock request
        mock_request = Mock(spec=Request)
        mock_request.base_url = _create_mock_base_url("http://localhost:8000/")

        # Mock the transaction context manager
        mock_transaction = AsyncMock()
        mock_transaction.__aenter__ = AsyncMock(return_value=None)
        mock_transaction.__aexit__ = AsyncMock(return_value=None)
        with patch("musigree.app.fastapi_ui.runtime_transaction", return_value=mock_transaction):
            response = await route__entity_type__entity_id(
                mock_request, EntityType.ARTIST, 123, roles=["Artist"], year=2000
            )

        # Verify the response
        assert isinstance(response, HTMLResponse)

        # Verify template context
        call_args = mock_templates.TemplateResponse.call_args
        assert call_args[0][0] == mock_request
        assert call_args.kwargs["name"] == "index.html"
        context = call_args.kwargs["context"]
        assert context["title"] == "Musigree: The Beatles"
        assert "The Beatles" in context["og_title"]

    def test_get_entity_type_invalid(self) -> None:
        """Test the get_entity_type dependency with invalid entity type."""
        from musigree.app.fastapi_dependencies import get_entity_type

        with pytest.raises(BadRequestError) as exc_info:
            get_entity_type("invalid_type")

        assert "Bad Entity Type" in str(exc_info.value)

    def test_get_entity_id_invalid(self) -> None:
        """Test the get_entity_id dependency with non-numeric entity ID."""
        from musigree.app.fastapi_dependencies import get_entity_id

        with pytest.raises(BadRequestError) as exc_info:
            get_entity_id("not_a_number")

        assert "Bad Entity Id" in str(exc_info.value)

    @patch("musigree.runtime.runtime_database_manager.RuntimeDatabaseManager")
    @pytest.mark.asyncio
    async def test_route_entity_type_entity_id_no_network_data(self, mock_db_manager: Mock) -> None:
        """Test the entity route when no network data is found."""
        # Setup mocks
        mock_helper = Mock()
        mock_helper.get_network = AsyncMock(return_value=None)
        mock_db_manager.runtime_database_helper = mock_helper

        mock_request = Mock(spec=Request)
        mock_request.base_url = _create_mock_base_url("http://localhost:8000/")

        # Mock the transaction context manager
        mock_transaction = AsyncMock()
        mock_transaction.__aenter__ = AsyncMock(return_value=None)
        mock_transaction.__aexit__ = AsyncMock(return_value=None)
        with patch("musigree.app.fastapi_ui.runtime_transaction", return_value=mock_transaction):
            with pytest.raises(NotFoundError) as exc_info:
                await route__entity_type__entity_id(
                    mock_request, EntityType.ARTIST, 123, roles=[], year=None
                )

        assert "No Network Data" in str(exc_info.value)

    def test_router_exists(self) -> None:
        """Test that the router is properly defined."""
        assert router is not None
        # Check that routes are registered
        assert len(router.routes) > 0

    @patch("musigree.app.fastapi_app.templates")
    @patch("musigree.library.cache.role_cache.RoleCache.get_roles_json")
    @patch("musigree.runtime.data_access_layer.role_entry.RoleEntry.get_multiselect_mapping")
    @pytest.mark.asyncio
    async def test_route_index_url_generation(
        self,
        mock_multiselect: Mock,
        mock_roles_json: Mock,
        mock_templates: Mock,
    ) -> None:
        """Test URL generation in the index route."""
        # Setup mocks
        mock_multiselect.return_value = {"test": "mapping"}
        mock_roles_json.return_value = '{"role1": "data"}'
        mock_templates.TemplateResponse.return_value = HTMLResponse("<html></html>")

        mock_request = Mock(spec=Request)
        mock_request.base_url = _create_mock_base_url("http://localhost:8000/")

        _response = await route__index(mock_request, roles=["Artist"], year=2000)

        # Verify template context contains URL
        call_args = mock_templates.TemplateResponse.call_args
        context = call_args.kwargs["context"]
        assert "og_url" in context
        # og_url should be the application_url (https://localhost:8000) without trailing slash
        assert "https://localhost:8000" in context["og_url"]

    @patch("musigree.app.fastapi_app.templates")
    @patch("musigree.library.cache.role_cache.RoleCache.get_roles_json")
    @patch("musigree.runtime.data_access_layer.role_entry.RoleEntry.get_multiselect_mapping")
    @patch("musigree.runtime.runtime_database_manager.RuntimeDatabaseManager")
    @pytest.mark.asyncio
    async def test_route_entity_url_generation(
        self,
        mock_db_manager: Mock,
        mock_multiselect: Mock,
        mock_roles_json: Mock,
        mock_templates: Mock,
    ) -> None:
        """Test URL generation in the entity route."""
        # Setup mocks
        mock_multiselect.return_value = {"test": "mapping"}
        mock_roles_json.return_value = '{"role1": "data"}'
        mock_templates.TemplateResponse.return_value = HTMLResponse("<html></html>")

        mock_network_data = {
            "center": {"name": "The Beatles"},
            "nodes": [],
            "edges": [],
        }
        mock_helper = Mock()
        mock_helper.get_network = AsyncMock(return_value=mock_network_data)
        mock_db_manager.runtime_database_helper = mock_helper

        mock_request = Mock(spec=Request)
        mock_request.base_url = _create_mock_base_url("http://localhost:8000/")

        # Mock the transaction context manager
        mock_transaction = AsyncMock()
        mock_transaction.__aenter__ = AsyncMock(return_value=None)
        mock_transaction.__aexit__ = AsyncMock(return_value=None)
        with patch("musigree.app.fastapi_ui.runtime_transaction", return_value=mock_transaction):
            _response = await route__entity_type__entity_id(
                mock_request, EntityType.ARTIST, 123, roles=["Artist"], year=2000
            )

        # Verify template context contains URL
        call_args = mock_templates.TemplateResponse.call_args
        context = call_args.kwargs["context"]
        assert "og_url" in context
        assert "/artist/123" in context["og_url"]
        assert "roles=Artist" in context["og_url"]
        assert "year=2000" in context["og_url"]

    def test_entity_type_validation(self) -> None:
        """Test entity type validation via dependency function."""
        from musigree.app.fastapi_dependencies import get_entity_type

        # Valid entity types should work
        valid_types = ["artist", "label"]
        for entity_type in valid_types:
            # This should not raise for valid types
            result = get_entity_type(entity_type)
            assert result is not None

        # Invalid entity types should raise BadRequestError
        with pytest.raises(BadRequestError):
            get_entity_type("invalid")
