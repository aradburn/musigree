import unittest
from unittest.mock import patch, MagicMock

import musigree.main


class TestMain(unittest.TestCase):
    """Test cases for the main module."""

    @patch('musigree.app.fastapi_dev_app.create_development_app')
    def test_app_creation(self, mock_create_app):
        """Test that the app is created using the development app factory."""
        # Mock the app creation
        mock_app = MagicMock()
        mock_create_app.return_value = mock_app
        
        # Import the module to trigger app creation
        import importlib
        importlib.reload(musigree.main)
        
        # Verify that create_development_app was called
        mock_create_app.assert_called_once()
        
        # Verify that the app variable is set
        self.assertEqual(mock_app, musigree.main.app)

    def test_app_exists(self):
        """Test that the app variable exists in the main module."""
        # The app should be available as a module-level variable
        self.assertTrue(hasattr(musigree.main, 'app'))
        self.assertIsNotNone(musigree.main.app)


if __name__ == "__main__":
    unittest.main() 