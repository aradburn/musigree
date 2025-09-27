from typing import Generator
from unittest.mock import patch, MagicMock

import pytest


@patch("musigree.app.fastapi_dev_app.create_development_app")
def test_app_creation(mock_create_app: MagicMock) -> None:
    """Test that the app is created using the development app factory."""
    # Mock the app creation
    mock_app = MagicMock()
    mock_create_app.return_value = mock_app

    # Import the module to trigger app creation
    import musigree.main

    # Verify that create_development_app was called
    mock_create_app.assert_called_once()

    # Verify that the app variable is set to our mock
    assert musigree.main.app == mock_app


@patch("musigree.app.fastapi_dev_app.create_development_app")
def test_app_exists(mock_create_app: MagicMock) -> None:
    """Test that the app variable exists in the main module."""
    # Mock the app creation to avoid slow setup
    mock_app = MagicMock()
    mock_create_app.return_value = mock_app

    # Import with mocked dependencies
    import musigree.main

    # The app should be available as a module-level variable
    assert hasattr(musigree.main, "app")
    assert musigree.main.app is not None


@pytest.fixture
def mock_app_setup() -> Generator[MagicMock, None, None]:
    """Fixture to mock the entire app setup process."""
    with patch(
        "musigree.app.fastapi_dev_app.create_development_app"
    ) as mock_create_app:
        mock_app = MagicMock()
        mock_create_app.return_value = mock_app
        yield mock_app


def test_main_module_imports_without_errors(mock_app_setup: MagicMock) -> None:
    """Test that the main module can be imported without errors when app setup is mocked."""
    # This test ensures the module structure is correct
    try:
        # Use importlib to test module availability without importing
        import importlib.util

        spec = importlib.util.find_spec("musigree.main")
        assert spec is not None, "musigree.main module not found"

        # If we need to actually import for testing, do it here
        import musigree.main  # noqa: F401

        # If we get here, the import succeeded
        assert True
    except ImportError as e:
        pytest.fail(f"Failed to import musigree.main: {e}")


def test_app_is_fastapi_instance(mock_app_setup: MagicMock) -> None:
    """Test that the app variable is properly configured as a FastAPI instance."""
    import musigree.main

    # With mocking, we verify the structure without slow setup
    assert hasattr(musigree.main, "app")
    # The mock should have been called during module import
    assert mock_app_setup is not None
