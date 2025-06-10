from unittest.mock import Mock, patch

import pytest
from fastapi import Request
from fastapi.responses import HTMLResponse

from musigree.app.fastapi_ui import (
    router,
    route__index,
    route__entity_type__entity_id,
    UI_DEFAULT_ROLES,
)
from musigree.exceptions import BadRequestError, NotFoundError
from musigree.library.fields.entity_type import EntityType


class TestFastAPIUI:
    """Test cases for the FastAPI UI module."""

    def test_ui_default_roles(self):
        """Test that UI_DEFAULT_ROLES is properly defined."""
        assert isinstance(UI_DEFAULT_ROLES, list)
        assert "Alias" in UI_DEFAULT_ROLES
        assert "Member Of" in UI_DEFAULT_ROLES

    @patch('musigree.app.fastapi_app.templates')
    @patch('musigree.library.cache.role_cache.RoleCache.get_roles_json')
    @patch('musigree.runtime.data_access_layer.role_entry.RoleEntry.get_multiselect_mapping')
    @patch('musigree.utils.parse_request_args')
    @pytest.mark.asyncio
    async def test_route_index_basic(self, mock_parse_args, mock_multiselect, mock_roles_json, mock_templates):
        """Test the basic index route functionality."""
        # Setup mocks
        mock_parse_args.return_value = None
        mock_multiselect.return_value = {"test": "mapping"}
        mock_roles_json.return_value = '{"role1": "data"}'
        mock_templates.TemplateResponse.return_value = HTMLResponse("<html></html>")
        
        # Create mock request
        mock_request = Mock(spec=Request)
        mock_request.base_url = "http://localhost:8000/"
        
        # Call the route
        response = await route__index(mock_request, roles=None, year=None)
        
        # Verify the response
        assert isinstance(response, HTMLResponse)
        mock_templates.TemplateResponse.assert_called_once()
        
        # Verify template context
        call_args = mock_templates.TemplateResponse.call_args
        # Check that request and name are passed as keyword arguments
        assert call_args.kwargs['request'] == mock_request
        assert call_args.kwargs['name'] == 'index.html'
        context = call_args.kwargs['context']
        assert context['title'] == 'Musigree'
        assert context['og_title'] == 'Musigree'
        assert context['original_roles'] == UI_DEFAULT_ROLES
        assert context['original_year'] is None

    @patch('musigree.app.fastapi_app.templates')
    @patch('musigree.library.cache.role_cache.RoleCache.get_roles_json')
    @patch('musigree.runtime.data_access_layer.role_entry.RoleEntry.get_multiselect_mapping')
    @patch('musigree.utils.parse_request_args')
    @pytest.mark.asyncio
    async def test_route_index_with_parameters(self, mock_parse_args, mock_multiselect, mock_roles_json, mock_templates):
        """Test the index route with roles and year parameters."""
        # Setup mocks
        mock_parse_args.return_value = (["Artist", "Album"], 2000)
        mock_multiselect.return_value = {"test": "mapping"}
        mock_roles_json.return_value = '{"role1": "data"}'
        mock_templates.TemplateResponse.return_value = HTMLResponse("<html></html>")
        
        # Create mock request
        mock_request = Mock(spec=Request)
        mock_request.base_url = "http://localhost:8000/"
        
        # Call the route
        response = await route__index(mock_request, roles=["Artist", "Album"], year=2000)
        
        # Verify the response
        assert isinstance(response, HTMLResponse)
        
        # Verify template context
        call_args = mock_templates.TemplateResponse.call_args
        context = call_args.kwargs['context']
        assert context['original_roles'] == ["Artist", "Album"]
        assert context['original_year'] == 2000

    @patch('musigree.app.fastapi_app.templates')
    @patch('musigree.library.cache.role_cache.RoleCache.get_roles_json')
    @patch('musigree.runtime.data_access_layer.role_entry.RoleEntry.get_multiselect_mapping')
    @patch('musigree.runtime.runtime_database_manager.RuntimeDatabaseManager')
    @patch('musigree.utils.parse_request_args')
    @pytest.mark.asyncio
    async def test_route_entity_type_entity_id_success(self, mock_parse_args, mock_db_manager, 
                                                       mock_multiselect, mock_roles_json, mock_templates):
        """Test the entity-specific route with valid parameters."""
        # Setup mocks
        mock_parse_args.return_value = (["Artist"], 2000)
        mock_multiselect.return_value = {"test": "mapping"}
        mock_roles_json.return_value = '{"role1": "data"}'
        mock_templates.TemplateResponse.return_value = HTMLResponse("<html></html>")
        
        # Mock network data
        mock_network_data = {
            "center": {"name": "The Beatles"},
            "nodes": [],
            "edges": []
        }
        mock_db_manager.runtime_database_helper.get_network.return_value = mock_network_data
        
        # Create mock request
        mock_request = Mock(spec=Request)
        mock_request.base_url = "http://localhost:8000/"
        
        # Mock the transaction context manager
        with patch('musigree.app.fastapi_ui.runtime_transaction'):
            response = await route__entity_type__entity_id(
                mock_request, "artist", "123", roles=["Artist"], year=2000
            )
        
        # Verify the response
        assert isinstance(response, HTMLResponse)
        
        # Verify template context - entity route passes context directly as second argument
        call_args = mock_templates.TemplateResponse.call_args
        template_name = call_args[0][0]  # First positional argument
        context = call_args[0][1]  # Second positional argument
        assert template_name == 'index.html'
        assert context['title'] == 'Musigree: The Beatles'
        assert 'The Beatles' in context['og_title']

    @pytest.mark.asyncio
    async def test_route_entity_type_entity_id_bad_entity_type(self):
        """Test the entity route with invalid entity type."""
        mock_request = Mock(spec=Request)
        mock_request.base_url = "http://localhost:8000/"
        
        with pytest.raises(BadRequestError) as exc_info:
            await route__entity_type__entity_id(
                mock_request, "invalid_type", "123", roles=None, year=None
            )
        
        assert "Bad Entity Type" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_route_entity_type_entity_id_bad_entity_id(self):
        """Test the entity route with non-numeric entity ID."""
        mock_request = Mock(spec=Request)
        mock_request.base_url = "http://localhost:8000/"
        
        with pytest.raises(BadRequestError) as exc_info:
            await route__entity_type__entity_id(
                mock_request, "artist", "not_a_number", roles=None, year=None
            )
        
        assert "Bad Entity Id" in str(exc_info.value)

    @patch('musigree.runtime.runtime_database_manager.RuntimeDatabaseManager')
    @patch('musigree.utils.parse_request_args')
    @pytest.mark.asyncio
    async def test_route_entity_type_entity_id_no_network_data(self, mock_parse_args, mock_db_manager):
        """Test the entity route when no network data is found."""
        # Setup mocks
        mock_parse_args.return_value = (None, None)
        mock_db_manager.runtime_database_helper.get_network.return_value = None
        
        mock_request = Mock(spec=Request)
        mock_request.base_url = "http://localhost:8000/"
        
        with patch('musigree.app.fastapi_ui.runtime_transaction'):
            with pytest.raises(NotFoundError) as exc_info:
                await route__entity_type__entity_id(
                    mock_request, "artist", "123", roles=None, year=None
                )
        
        assert "No Network Data" in str(exc_info.value)

    def test_router_exists(self):
        """Test that the router is properly defined."""
        assert router is not None
        # Check that routes are registered
        assert len(router.routes) > 0

    @patch('musigree.app.fastapi_app.templates')
    @patch('musigree.library.cache.role_cache.RoleCache.get_roles_json')
    @patch('musigree.runtime.data_access_layer.role_entry.RoleEntry.get_multiselect_mapping')
    @patch('musigree.utils.parse_request_args')
    @pytest.mark.asyncio
    async def test_route_index_url_generation(self, mock_parse_args, mock_multiselect, mock_roles_json, mock_templates):
        """Test URL generation in the index route."""
        # Setup mocks
        mock_parse_args.return_value = (["Artist"], 2000)
        mock_multiselect.return_value = {"test": "mapping"}
        mock_roles_json.return_value = '{"role1": "data"}'
        mock_templates.TemplateResponse.return_value = HTMLResponse("<html></html>")
        
        mock_request = Mock(spec=Request)
        mock_request.base_url = "http://localhost:8000/"

        _response = await route__index(mock_request, roles=["Artist"], year=2000)
        
        # Verify template context contains URL
        call_args = mock_templates.TemplateResponse.call_args
        context = call_args.kwargs['context']
        assert 'og_url' in context
        assert context['og_url'].startswith('/')

    @patch('musigree.app.fastapi_app.templates')
    @patch('musigree.library.cache.role_cache.RoleCache.get_roles_json')
    @patch('musigree.runtime.data_access_layer.role_entry.RoleEntry.get_multiselect_mapping')
    @patch('musigree.runtime.runtime_database_manager.RuntimeDatabaseManager')
    @patch('musigree.utils.parse_request_args')
    @pytest.mark.asyncio
    async def test_route_entity_url_generation(self, mock_parse_args, mock_db_manager, 
                                               mock_multiselect, mock_roles_json, mock_templates):
        """Test URL generation in the entity route."""
        # Setup mocks
        mock_parse_args.return_value = (["Artist"], 2000)
        mock_multiselect.return_value = {"test": "mapping"}
        mock_roles_json.return_value = '{"role1": "data"}'
        mock_templates.TemplateResponse.return_value = HTMLResponse("<html></html>")
        
        mock_network_data = {
            "center": {"name": "The Beatles"},
            "nodes": [],
            "edges": []
        }
        mock_db_manager.runtime_database_helper.get_network.return_value = mock_network_data
        
        mock_request = Mock(spec=Request)
        mock_request.base_url = "http://localhost:8000/"
        
        with patch('musigree.app.fastapi_ui.runtime_transaction'):
            _response = await route__entity_type__entity_id(
                mock_request, "artist", "123", roles=["Artist"], year=2000
            )
        
        # Verify template context contains URL - entity route passes context directly
        call_args = mock_templates.TemplateResponse.call_args
        context = call_args[0][1]  # Second positional argument
        assert 'og_url' in context
        assert context['og_url'].startswith('/artist/123')

    @pytest.mark.asyncio
    async def test_entity_type_validation(self):
        """Test entity type validation."""
        mock_request = Mock(spec=Request)
        mock_request.base_url = "http://localhost:8000/"
        
        # Valid entity types should work
        valid_types = ["artist", "label", "release"]
        for entity_type in valid_types:
            try:
                # This should not raise for valid types
                EntityType.from_str(entity_type.upper())
            except NotImplementedError:
                # If the type is not implemented, that's okay for this test
                continue
        
        # Invalid entity types should raise BadRequestError
        with pytest.raises(BadRequestError):
            await route__entity_type__entity_id(
                mock_request, "invalid", "123", roles=None, year=None
            ) 