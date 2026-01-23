"""
Unit tests for musigree.app.fastapi_csp module.
"""

from unittest.mock import Mock, MagicMock, patch

import pytest
from fastapi import FastAPI

from musigree.config import SqliteTestConfiguration, Configuration
from musigree.constants import AnalyticsType


class TestCSPMiddleware:
    """Test cases for CSP middleware setup."""

    @pytest.fixture
    def test_config(self) -> Configuration:
        """Provide test configuration."""
        return SqliteTestConfiguration()

    @patch("musigree.app.fastapi_csp.ContentSecurityPolicy")
    def test_setup_csp_middleware_production(
        self,
        mock_csp_middleware: Mock,
        test_config: Configuration,
    ) -> None:
        """Test CSP middleware setup for production."""
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

    @patch("musigree.app.fastapi_csp.ContentSecurityPolicy")
    def test_setup_csp_middleware_development(
        self,
        mock_csp_middleware: Mock,
        test_config: Configuration,
    ) -> None:
        """Test CSP middleware setup for development."""
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

    @patch("musigree.app.fastapi_csp.ContentSecurityPolicy")
    def test_setup_csp_middleware_analytics_umami(
        self,
        mock_csp_middleware: Mock,
        test_config: Configuration,
    ) -> None:
        """Test CSP middleware setup with Umami analytics."""
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

    @patch("musigree.app.fastapi_csp.ContentSecurityPolicy")
    def test_setup_csp_middleware_analytics_swetrix(
        self,
        mock_csp_middleware: Mock,
        test_config: Configuration,
    ) -> None:
        """Test CSP middleware setup with Swetrix analytics."""
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
