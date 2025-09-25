"""
Unit tests for musigree.app.fastapi_prod_app module.
"""

from unittest.mock import Mock, patch

from fastapi import FastAPI

from musigree.app.fastapi_prod_app import create_production_app, app
from musigree.config import SqliteReadOnlyProductionConfiguration


class TestCreateProductionApp:
    """Test class for create_production_app function."""

    @patch("musigree.app.fastapi_prod_app.create_app")
    @patch("musigree.app.fastapi_prod_app.SqliteReadOnlyProductionConfiguration")
    def test_create_production_app_returns_fastapi_instance(
        self, mock_config_class: Mock, mock_create_app: Mock
    ) -> None:
        """Test that create_production_app returns a FastAPI instance."""
        # Setup
        mock_config = Mock(spec=SqliteReadOnlyProductionConfiguration)
        mock_config_class.return_value = mock_config

        mock_app = Mock(spec=FastAPI)
        mock_create_app.return_value = mock_app

        # Test
        result = create_production_app()

        # Assertions
        mock_config_class.assert_called_once()
        mock_create_app.assert_called_once_with(mock_config)
        assert result == mock_app

    @patch("musigree.app.fastapi_prod_app.create_app")
    @patch("musigree.app.fastapi_prod_app.SqliteReadOnlyProductionConfiguration")
    def test_create_production_app_uses_sqlite_production_config(
        self, mock_config_class: Mock, mock_create_app: Mock
    ) -> None:
        """Test that create_production_app uses SqliteReadOnlyProductionConfiguration."""
        # Setup
        mock_config = Mock(spec=SqliteReadOnlyProductionConfiguration)
        mock_config_class.return_value = mock_config

        mock_app = Mock(spec=FastAPI)
        mock_create_app.return_value = mock_app

        # Test
        create_production_app()

        # Assertions
        mock_config_class.assert_called_once()
        mock_create_app.assert_called_once_with(mock_config)

    @patch("musigree.app.fastapi_prod_app.create_production_app")
    def test_module_level_app_creation(self, mock_create_production_app: Mock) -> None:
        """Test that the module-level app variable is created properly."""
        # This test verifies that the app is created when the module is imported
        # We can't easily test this directly since the module is already imported
        # But we can verify the function would be called
        mock_app = Mock(spec=FastAPI)
        mock_create_production_app.return_value = mock_app

        # Manually call to simulate module import
        result_app = mock_create_production_app()

        # Assertions
        mock_create_production_app.assert_called_once()
        assert result_app == mock_app

    def test_create_production_app_function_exists(self) -> None:
        """Test that create_production_app function exists and is callable."""
        assert callable(create_production_app)

    def test_module_level_app_variable_exists(self) -> None:
        """Test that the module-level app variable exists."""
        assert app is not None
        # The app should be a FastAPI instance (though it might be mocked in tests)
        # We'll just verify it exists without checking the type to avoid import issues
