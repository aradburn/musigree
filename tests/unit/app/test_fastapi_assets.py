"""
Unit tests for the FastAPI assets module.

This module contains comprehensive unit tests for the fastapi_assets module,
which handles static asset serving and template asset URL resolution for both
development and production environments.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, mock_open, patch

import pytest
from fastapi import APIRouter
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from musigree.app.fastapi_assets import create_assets_router
from musigree.config import SqliteTestConfiguration


class TestCreateAssetsRouter:
    """Test class for create_assets_router function."""
    
    @patch('musigree.app.fastapi_assets.templates')
    def test_create_assets_router_development(self, mock_templates):
        """Test create_assets_router in development mode."""
        # Setup
        config = SqliteTestConfiguration()
        config.PRODUCTION = False
        
        mock_templates.env.globals.update = Mock()
        
        # Test
        router, templates = create_assets_router(config)
        
        # Assertions
        assert isinstance(router, APIRouter)
        assert templates == mock_templates
        
        # Verify templates globals were updated
        mock_templates.env.globals.update.assert_called_once()
        call_args = mock_templates.env.globals.update.call_args[0][0]
        assert 'asset' in call_args
        assert 'is_production' in call_args
        assert call_args['is_production'] is False
    
    @patch('musigree.app.fastapi_assets.templates')
    @patch('musigree.app.fastapi_assets.FRONTEND_DIR')
    @patch('musigree.app.fastapi_assets.StaticFiles')
    @patch('builtins.open', new_callable=mock_open)
    def test_create_assets_router_production(self, mock_file, mock_static_files, mock_frontend_dir, mock_templates):
        """Test create_assets_router in production mode."""
        # Setup
        config = SqliteTestConfiguration()
        config.PRODUCTION = True
        
        mock_templates.env.globals.update = Mock()
        mock_frontend_dir.__truediv__ = Mock(return_value=Path("/fake/frontend/dist"))
        mock_static_files.return_value = Mock()
        
        # Mock manifest file content
        manifest_content = {
            "main.js": {"file": "assets/main-abcd1234.js"},
            "main.css": {"file": "assets/main-efgh5678.css"}
        }
        mock_file.return_value.read.return_value = json.dumps(manifest_content)
        
        # Test
        router, templates = create_assets_router(config)
        
        # Assertions
        assert isinstance(router, APIRouter)
        assert templates == mock_templates
        
        # Verify file was opened for manifest
        mock_file.assert_called()
        
        # Verify StaticFiles was called
        mock_static_files.assert_called_once()
        
        # Verify templates globals were updated
        mock_templates.env.globals.update.assert_called_once()
        call_args = mock_templates.env.globals.update.call_args[0][0]
        assert 'asset' in call_args
        assert 'is_production' in call_args
        assert call_args['is_production'] is True
    
    @patch('musigree.app.fastapi_assets.templates')
    @patch('musigree.app.fastapi_assets.FRONTEND_DIR')
    @patch('musigree.app.fastapi_assets.StaticFiles')
    def test_create_assets_router_production_manifest_not_found(self, mock_static_files, mock_frontend_dir, mock_templates):
        """Test create_assets_router when manifest file is not found."""
        # Setup
        config = SqliteTestConfiguration()
        config.PRODUCTION = True
        
        mock_templates.env.globals.update = Mock()
        mock_frontend_dir.__truediv__ = Mock(return_value=Path("/fake/frontend/dist"))
        mock_static_files.return_value = Mock()
        
        # Test and Assert
        with patch('builtins.open', side_effect=OSError("File not found")):
            with pytest.raises(OSError, match="Manifest file not found"):
                create_assets_router(config)
    
    @patch('musigree.app.fastapi_assets.templates')
    @patch.dict(os.environ, {"VITE_ORIGIN": "http://custom:3000"})
    def test_create_assets_router_custom_vite_origin(self, mock_templates):
        """Test create_assets_router with custom VITE_ORIGIN."""
        # Setup
        config = SqliteTestConfiguration()
        config.PRODUCTION = False
        
        mock_templates.env.globals.update = Mock()
        
        # Test
        router, templates = create_assets_router(config)
        
        # Verify the asset function uses custom origin
        call_args = mock_templates.env.globals.update.call_args[0][0]
        asset_func = call_args['asset']
        
        # Test the asset function
        result = asset_func("test.js")
        assert result == "http://custom:3000/assets/test.js"
    
    @patch('musigree.app.fastapi_assets.templates')
    @patch.dict(os.environ, {}, clear=True)
    def test_create_assets_router_default_vite_origin(self, mock_templates):
        """Test create_assets_router with default VITE_ORIGIN."""
        # Setup
        config = SqliteTestConfiguration()
        config.PRODUCTION = False
        
        mock_templates.env.globals.update = Mock()
        
        # Test
        router, templates = create_assets_router(config)
        
        # Verify the asset function uses default origin
        call_args = mock_templates.env.globals.update.call_args[0][0]
        asset_func = call_args['asset']
        
        # Test the asset function
        result = asset_func("test.js")
        assert result == "http://localhost:5173/assets/test.js"


class TestDevAssetFunction:
    """Test class for the dev_asset function behavior."""
    
    @patch('musigree.app.fastapi_assets.templates')
    @patch('musigree.app.fastapi_assets.log')
    def test_dev_asset_function_logging(self, mock_log, mock_templates):
        """Test that dev_asset function logs correctly."""
        # Setup
        config = SqliteTestConfiguration()
        config.PRODUCTION = False
        
        mock_templates.env.globals.update = Mock()
        
        # Test
        router, templates = create_assets_router(config)
        
        # Get the asset function
        call_args = mock_templates.env.globals.update.call_args[0][0]
        asset_func = call_args['asset']
        
        # Call the function
        result = asset_func("styles/main.css")
        
        # Verify logging
        mock_log.debug.assert_called_with("dev asset: styles/main.css")
        assert result == "http://localhost:5173/assets/styles/main.css"
    
    @patch('musigree.app.fastapi_assets.templates')
    def test_dev_asset_function_various_paths(self, mock_templates):
        """Test dev_asset function with various file paths."""
        # Setup
        config = SqliteTestConfiguration()
        config.PRODUCTION = False
        
        mock_templates.env.globals.update = Mock()
        
        # Test
        router, templates = create_assets_router(config)
        
        # Get the asset function
        call_args = mock_templates.env.globals.update.call_args[0][0]
        asset_func = call_args['asset']
        
        # Test various paths
        test_cases = [
            ("main.js", "http://localhost:5173/assets/main.js"),
            ("styles/app.css", "http://localhost:5173/assets/styles/app.css"),
            ("images/logo.png", "http://localhost:5173/assets/images/logo.png"),
            ("fonts/roboto.woff2", "http://localhost:5173/assets/fonts/roboto.woff2"),
        ]
        
        for input_path, expected_output in test_cases:
            result = asset_func(input_path)
            assert result == expected_output


class TestProdAssetFunction:
    """Test class for the prod_asset function behavior."""
    
    @patch('musigree.app.fastapi_assets.templates')
    @patch('musigree.app.fastapi_assets.FRONTEND_DIR')
    @patch('musigree.app.fastapi_assets.StaticFiles')
    @patch('builtins.open', new_callable=mock_open)
    @patch('musigree.app.fastapi_assets.log')
    def test_prod_asset_function_logging(self, mock_log, mock_file, mock_static_files, mock_frontend_dir, mock_templates):
        """Test that prod_asset function logs correctly."""
        # Setup
        config = SqliteTestConfiguration()
        config.PRODUCTION = True
        
        mock_templates.env.globals.update = Mock()
        mock_frontend_dir.__truediv__ = Mock(return_value=Path("/fake/frontend/dist"))
        mock_static_files.return_value = Mock()
        
        # Mock manifest file content
        manifest_content = {
            "main.js": {"file": "assets/main-abcd1234.js"}
        }
        mock_file.return_value.read.return_value = json.dumps(manifest_content)
        
        # Test
        router, templates = create_assets_router(config)
        
        # Get the asset function
        call_args = mock_templates.env.globals.update.call_args[0][0]
        asset_func = call_args['asset']
        
        # Call the function
        result = asset_func("main.js")
        
        # Verify logging
        mock_log.debug.assert_called_with("prod asset: main.js")
        assert result == "/assets/assets/main-abcd1234.js"
    
    @patch('musigree.app.fastapi_assets.templates')
    @patch('musigree.app.fastapi_assets.FRONTEND_DIR')
    @patch('musigree.app.fastapi_assets.StaticFiles')
    @patch('builtins.open', new_callable=mock_open)
    def test_prod_asset_function_various_paths(self, mock_file, mock_static_files, mock_frontend_dir, mock_templates):
        """Test prod_asset function with various file paths."""
        # Setup
        config = SqliteTestConfiguration()
        config.PRODUCTION = True
        
        mock_templates.env.globals.update = Mock()
        mock_frontend_dir.__truediv__ = Mock(return_value=Path("/fake/frontend/dist"))
        mock_static_files.return_value = Mock()
        
        # Mock manifest file content
        manifest_content = {
            "main.js": {"file": "assets/main-abcd1234.js"},
            "styles/app.css": {"file": "assets/styles/app-efgh5678.css"},
            "images/logo.png": {"file": "assets/images/logo-ijkl9012.png"}
        }
        mock_file.return_value.read.return_value = json.dumps(manifest_content)
        
        # Test
        router, templates = create_assets_router(config)
        
        # Get the asset function
        call_args = mock_templates.env.globals.update.call_args[0][0]
        asset_func = call_args['asset']
        
        # Test various paths
        test_cases = [
            ("main.js", "/assets/assets/main-abcd1234.js"),
            ("styles/app.css", "/assets/assets/styles/app-efgh5678.css"),
            ("images/logo.png", "/assets/assets/images/logo-ijkl9012.png"),
        ]
        
        for input_path, expected_output in test_cases:
            result = asset_func(input_path)
            assert result == expected_output


class TestAssetRouterEndpoints:
    """Test class for asset router endpoints."""
    
    @patch('musigree.app.fastapi_assets.templates')
    def test_context_endpoint_exists(self, mock_templates):
        """Test that the context endpoint is created."""
        # Setup
        config = SqliteTestConfiguration()
        config.PRODUCTION = False
        
        mock_templates.env.globals.update = Mock()
        
        # Test
        router, templates = create_assets_router(config)
        
        # Verify router has routes
        assert len(router.routes) > 0
        
        # Find the context route
        context_route = None
        for route in router.routes:
            if hasattr(route, 'path') and route.path == "/context":
                context_route = route
                break
        
        assert context_route is not None
        assert "GET" in context_route.methods
    
    @patch('musigree.app.fastapi_assets.templates')
    @patch('musigree.app.fastapi_assets.FRONTEND_DIR')
    @patch('musigree.app.fastapi_assets.StaticFiles')
    def test_static_files_mount_production(self, mock_static_files, mock_frontend_dir, mock_templates):
        """Test that static files are mounted in production."""
        # Setup
        config = SqliteTestConfiguration()
        config.PRODUCTION = True
        
        mock_templates.env.globals.update = Mock()
        mock_frontend_dir.__truediv__ = Mock(return_value=Path("/fake/frontend/dist"))
        mock_static_files.return_value = Mock()
        
        # Mock manifest file to avoid OSError
        with patch('builtins.open', mock_open(read_data='{"main.js": {"file": "main.js"}}')):
            # Test
            router, templates = create_assets_router(config)
        
        # Verify StaticFiles was called (indicating static files were mounted)
        mock_static_files.assert_called_once()
        
        # Verify router has routes
        assert len(router.routes) > 0
    
    @patch('musigree.app.fastapi_assets.templates')
    def test_no_static_files_mount_development(self, mock_templates):
        """Test that static files are not mounted in development."""
        # Setup
        config = SqliteTestConfiguration()
        config.PRODUCTION = False
        
        mock_templates.env.globals.update = Mock()
        
        # Test
        router, templates = create_assets_router(config)
        
        # In development, should only have the context endpoint, no static file mounts
        route_paths = [getattr(route, 'path', None) for route in router.routes]
        static_routes = [path for path in route_paths if path and path.startswith('/assets')]
        assert len(static_routes) == 0


class TestLogging:
    """Test class for logging behavior."""
    
    def test_logger_exists(self):
        """Test that the module logger is properly configured."""
        from musigree.app.fastapi_assets import log
        
        assert log.name == "musigree.app.fastapi_assets"
    
    @patch('musigree.app.fastapi_assets.log')
    @patch('musigree.app.fastapi_assets.templates')
    @patch('musigree.app.fastapi_assets.StaticFiles')
    def test_production_flag_logging(self, mock_static_files, mock_templates, mock_log):
        """Test that production flag is logged."""
        # Setup
        config = SqliteTestConfiguration()
        config.PRODUCTION = True
        
        mock_templates.env.globals.update = Mock()
        mock_static_files.return_value = Mock()
        
        # Mock manifest file to avoid OSError
        with patch('builtins.open', mock_open(read_data='{"main.js": {"file": "main.js"}}')):
            with patch('musigree.app.fastapi_assets.FRONTEND_DIR'):
                # Test
                create_assets_router(config)
        
        # Verify logging
        mock_log.info.assert_called_with("is_production: True")
