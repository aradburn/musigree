"""
Unit tests for musigree.app.fastapi_csp module.
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI

from musigree.config import Configuration, SqliteTestConfiguration
from musigree.constants import AnalyticsType


class TestCSPMiddleware:
    """Test cases for CSP middleware setup."""

    @pytest.fixture
    def test_config(self) -> Configuration:
        """Provide test configuration."""
        return SqliteTestConfiguration()

    def test_setup_csp_middleware_production(
        self,
        test_config: Configuration,
    ) -> None:
        """Test CSP middleware setup for production."""
        with patch("musigree.app.fastapi_csp.Content_Security_Policy") as mock_csp:
            # Arrange
            from musigree.app.fastapi_csp import setup_csp_middleware

            app = MagicMock(spec=FastAPI)
            test_config.PRODUCTION = True

            # Act
            setup_csp_middleware(app, test_config)

            # Assert
            mock_csp.assert_called_once()
            assert mock_csp.call_args.args[0] is app
            assert mock_csp.call_args.kwargs["script_nonce_flag"] is False
            assert mock_csp.call_args.kwargs["style_nonce_flag"] is False
            assert mock_csp.call_args.kwargs["report_only"] is False
            assert "default-src" in mock_csp.call_args.kwargs["options"]

    def test_setup_csp_middleware_development(
        self,
        test_config: Configuration,
    ) -> None:
        """Test CSP middleware setup for development."""
        with patch("musigree.app.fastapi_csp.Content_Security_Policy") as mock_csp:
            # Arrange
            from musigree.app.fastapi_csp import setup_csp_middleware

            app = MagicMock(spec=FastAPI)
            test_config.PRODUCTION = False

            # Act
            setup_csp_middleware(app, test_config)

            # Assert
            mock_csp.assert_called_once()
            assert mock_csp.call_args.args[0] is app
            assert mock_csp.call_args.kwargs["script_nonce_flag"] is False
            assert mock_csp.call_args.kwargs["style_nonce_flag"] is False
            assert mock_csp.call_args.kwargs["report_only"] is False
            assert "http://localhost:5173" in mock_csp.call_args.kwargs["options"]["script-src"]

    def test_setup_csp_middleware_analytics_umami(
        self,
        test_config: Configuration,
    ) -> None:
        """Test CSP middleware setup with Umami analytics."""
        with patch("musigree.app.fastapi_csp.Content_Security_Policy") as mock_csp:
            # Arrange
            from musigree.app.fastapi_csp import setup_csp_middleware

            app = MagicMock(spec=FastAPI)
            test_config.PRODUCTION = True
            test_config.ANALTICS_TYPE = AnalyticsType.UMAMI

            # Act
            setup_csp_middleware(app, test_config)

            # Assert
            mock_csp.assert_called_once()
            csp_options = mock_csp.call_args.kwargs["options"]
            assert "https://umami.musigree.com " in csp_options["script-src"]
            assert "https://umami.musigree.com " in csp_options["connect-src"]

    def test_setup_csp_middleware_analytics_swetrix(
        self,
        test_config: Configuration,
    ) -> None:
        """Test CSP middleware setup with Swetrix analytics."""
        with patch("musigree.app.fastapi_csp.Content_Security_Policy") as mock_csp:
            # Arrange
            from musigree.app.fastapi_csp import setup_csp_middleware

            app = MagicMock(spec=FastAPI)
            test_config.PRODUCTION = True
            test_config.ANALTICS_TYPE = AnalyticsType.SWETRIX

            # Act
            setup_csp_middleware(app, test_config)

            # Assert
            mock_csp.assert_called_once()
            csp_options = mock_csp.call_args.kwargs["options"]
            assert (
                "https://swetrix.org/swetrix.js https://cdn.jsdelivr.net/gh/Swetrix/ "
                in csp_options["script-src"]
            )
            assert "https://swetrix-api.musigree.com/ " in csp_options["connect-src"]
