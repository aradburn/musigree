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
        with patch("musigree.app.fastapi_csp.ContentSecurityPolicy") as mock_csp_middleware:
            # Arrange
            from musigree.app.fastapi_csp import setup_csp_middleware

            app = MagicMock(spec=FastAPI)
            test_config.PRODUCTION = True

            # Act
            setup_csp_middleware(app, test_config)

            # Assert
            app.add_middleware.assert_called_once()
            call_args = app.add_middleware.call_args
            assert call_args[0][0] == mock_csp_middleware
            assert "Option" in call_args[1]
            assert call_args[1]["script_nonce"] is False
            assert call_args[1]["style_nonce"] is False
            assert call_args[1]["report_only"] is False

    def test_setup_csp_middleware_development(
        self,
        test_config: Configuration,
    ) -> None:
        """Test CSP middleware setup for development."""
        with patch("musigree.app.fastapi_csp.ContentSecurityPolicy") as mock_csp_middleware:
            # Arrange
            from musigree.app.fastapi_csp import setup_csp_middleware

            app = MagicMock(spec=FastAPI)
            test_config.PRODUCTION = False

            # Act
            setup_csp_middleware(app, test_config)

            # Assert
            app.add_middleware.assert_called_once()
            call_args = app.add_middleware.call_args
            assert call_args[0][0] == mock_csp_middleware
            assert "Option" in call_args[1]
            assert call_args[1]["script_nonce"] is False
            assert call_args[1]["style_nonce"] is False
            assert call_args[1]["report_only"] is False

    def test_setup_csp_middleware_analytics_umami(
        self,
        test_config: Configuration,
    ) -> None:
        """Test CSP middleware setup with Umami analytics."""
        with patch("musigree.app.fastapi_csp.ContentSecurityPolicy") as mock_csp_middleware:
            # Arrange
            from musigree.app.fastapi_csp import setup_csp_middleware

            app = MagicMock(spec=FastAPI)
            test_config.PRODUCTION = True
            test_config.ANALTICS_TYPE = AnalyticsType.UMAMI

            # Act
            setup_csp_middleware(app, test_config)

            # Assert
            app.add_middleware.assert_called_once()
            call_args = app.add_middleware.call_args
            assert call_args[0][0] == mock_csp_middleware
            csp_options = call_args[1]["Option"]
            # Check that analytics URLs are included in CSP
            assert "script-src" in csp_options
            assert "connect-src" in csp_options

    def test_setup_csp_middleware_analytics_swetrix(
        self,
        test_config: Configuration,
    ) -> None:
        """Test CSP middleware setup with Swetrix analytics."""
        with patch("musigree.app.fastapi_csp.ContentSecurityPolicy") as mock_csp_middleware:
            # Arrange
            from musigree.app.fastapi_csp import setup_csp_middleware

            app = MagicMock(spec=FastAPI)
            test_config.PRODUCTION = True
            test_config.ANALTICS_TYPE = AnalyticsType.SWETRIX

            # Act
            setup_csp_middleware(app, test_config)

            # Assert
            app.add_middleware.assert_called_once()
            call_args = app.add_middleware.call_args
            assert call_args[0][0] == mock_csp_middleware
            csp_options = call_args[1]["Option"]
            # Check that analytics URLs are included in CSP
            assert "script-src" in csp_options
            assert "connect-src" in csp_options
