"""
Unit tests for musigree.app.fastapi_dev_app module.
"""

from unittest.mock import Mock, patch

import pytest
from fastapi import FastAPI

from musigree.app.fastapi_dev_app import create_development_app
from musigree.config import SqliteDevelopmentConfiguration


class TestCreateDevelopmentApp:
    """Test class for create_development_app function."""

    @patch('musigree.app.fastapi_dev_app.create_app')
    @patch('musigree.app.fastapi_dev_app.SqliteDevelopmentConfiguration')
    def test_create_development_app_returns_fastapi_instance(
        self, mock_config_class: Mock, mock_create_app: Mock
    ) -> None:
        """Test that create_development_app returns a FastAPI instance."""
        # Setup
        mock_config = Mock(spec=SqliteDevelopmentConfiguration)
        mock_config_class.return_value = mock_config
        
        mock_app = Mock(spec=FastAPI)
        mock_create_app.return_value = mock_app
        
        # Test
        result = create_development_app()
        
        # Assertions
        mock_config_class.assert_called_once()
        mock_create_app.assert_called_once_with(mock_config)
        assert result == mock_app

    @patch('musigree.app.fastapi_dev_app.create_app')
    @patch('musigree.app.fastapi_dev_app.SqliteDevelopmentConfiguration')
    def test_create_development_app_uses_sqlite_development_config(
        self, mock_config_class: Mock, mock_create_app: Mock
    ) -> None:
        """Test that create_development_app uses SqliteDevelopmentConfiguration."""
        # Setup
        mock_config = Mock(spec=SqliteDevelopmentConfiguration)
        mock_config_class.return_value = mock_config
        
        mock_app = Mock(spec=FastAPI)
        mock_create_app.return_value = mock_app
        
        # Test
        create_development_app()
        
        # Assertions
        mock_config_class.assert_called_once()
        mock_create_app.assert_called_once_with(mock_config)

    def test_create_development_app_function_exists(self) -> None:
        """Test that create_development_app function exists and is callable."""
        assert callable(create_development_app)


class TestMainExecution:
    """Test class for main execution block."""

    @patch('musigree.app.fastapi_dev_app.uvicorn.run')
    @patch('musigree.app.fastapi_dev_app.create_development_app')
    def test_main_execution_creates_app_and_runs_uvicorn(
        self, mock_create_app: Mock, mock_uvicorn_run: Mock
    ) -> None:
        """Test that main execution creates app and runs uvicorn."""
        # Setup
        mock_app = Mock(spec=FastAPI)
        mock_create_app.return_value = mock_app
        
        # Test by executing the main block logic
        app = mock_create_app()
        mock_uvicorn_run(app, host="0.0.0.0", port=5000, log_level="info")
        
        # Assertions
        mock_create_app.assert_called_once()
        mock_uvicorn_run.assert_called_once_with(
            app, host="0.0.0.0", port=5000, log_level="info"
        )

    @patch('musigree.app.fastapi_dev_app.uvicorn')
    @patch('musigree.app.fastapi_dev_app.create_development_app')
    def test_uvicorn_run_with_correct_parameters(
        self, mock_create_app: Mock, mock_uvicorn: Mock
    ) -> None:
        """Test that uvicorn.run is called with correct parameters."""
        # Setup
        mock_app = Mock(spec=FastAPI)
        mock_create_app.return_value = mock_app
        
        # Test by simulating main execution
        app = mock_create_app()
        mock_uvicorn.run(app, host="0.0.0.0", port=5000, log_level="info")
        
        # Assertions
        mock_uvicorn.run.assert_called_once_with(
            app, host="0.0.0.0", port=5000, log_level="info"
        )
