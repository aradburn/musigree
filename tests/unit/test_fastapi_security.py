"""
Unit tests for FastAPI security middleware and utilities.
"""
from typing import cast
from unittest.mock import Mock, AsyncMock

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient
from starlette.types import Message, Scope, Receive, Send

from musigree.app.fastapi_security import (
    SecurityHeadersMiddleware,
    validate_environment_variables,
    setup_security_middleware
)
from musigree.config import SqliteProductionConfiguration, SqliteDevelopmentConfiguration, Configuration


class TestSecurityHeadersMiddleware:
    """Test cases for SecurityHeadersMiddleware."""

    @pytest.fixture
    def app(self) -> FastAPI:
        """Create a test FastAPI app."""
        app = FastAPI()
        
        @app.get("/test")
        async def test_endpoint() -> dict[str, str]:
            return {"message": "test"}
        
        return app

    @pytest.fixture
    def production_app(self, app: FastAPI) -> FastAPI:
        """Create app with production security middleware."""
        # noinspection PyTypeChecker
        app.add_middleware(SecurityHeadersMiddleware, is_production=True)
        return app

    @pytest.fixture
    def development_app(self, app: FastAPI) -> FastAPI:
        """Create app with development security middleware."""
        # noinspection PyTypeChecker
        app.add_middleware(SecurityHeadersMiddleware, is_production=False)
        return app

    def test_production_security_headers(self, production_app: FastAPI) -> None:
        """Test that production security headers are correctly applied."""
        client = TestClient(production_app)
        response = client.get("/test")
        
        assert response.status_code == 200
        
        # Check security headers (case-insensitive)
        headers = {k.lower(): v for k, v in response.headers.items()}
        
        assert headers["x-content-type-options"] == "nosniff"
        assert headers["x-frame-options"] == "DENY"
        assert headers["x-xss-protection"] == "1; mode=block"
        assert headers["referrer-policy"] == "strict-origin-when-cross-origin"
        assert "permissions-policy" in headers
        
        # Production-specific headers
        assert "strict-transport-security" in headers
        assert "max-age=31536000" in headers["strict-transport-security"]
        assert "content-security-policy" in headers
        assert "default-src 'self'" in headers["content-security-policy"]

    def test_development_security_headers(self, development_app: FastAPI) -> None:
        """Test that development security headers are correctly applied."""
        client = TestClient(development_app)
        response = client.get("/test")
        
        assert response.status_code == 200
        
        # Check basic security headers (case-insensitive)
        headers = {k.lower(): v for k, v in response.headers.items()}
        
        assert headers["x-content-type-options"] == "nosniff"
        assert headers["x-frame-options"] == "DENY"
        assert headers["x-xss-protection"] == "1; mode=block"
        
        # Development should not have HSTS
        assert "strict-transport-security" not in headers
        
        # Development CSP should be more permissive
        assert "content-security-policy" in headers
        csp = headers["content-security-policy"]
        assert "unsafe-inline" in csp
        assert "localhost" in csp

    @pytest.mark.asyncio
    async def test_middleware_asgi_flow(self) -> None:
        """Test the ASGI middleware flow."""
        # Create a mock ASGI app
        mock_app = AsyncMock()
        
        middleware = SecurityHeadersMiddleware(app=mock_app, is_production=True)
        
        # Mock ASGI scope for HTTP request
        scope: Scope = {
            "type": "http",
            "method": "GET",
            "path": "/test",
        }
        
        # Mock receive and send
        receive = AsyncMock()
        
        # Track sent messages
        sent_messages: list[Message] = []
        
        async def mock_send(message: Message) -> None:
            sent_messages.append(message)
        
        # Mock the app to send a response
        async def mock_app_call(_scope: Scope, _receive: Receive, send: Send) -> None:
            await send({
                "type": "http.response.start",
                "status": 200,
                "headers": [(b"content-type", b"application/json")],
            })
            await send({
                "type": "http.response.body",
                "body": b'{"message": "test"}',
            })
        
        mock_app.side_effect = mock_app_call
        
        # Call the middleware
        await middleware(scope, receive, mock_send)
        
        # Verify mock_app was called
        mock_app.assert_called_once()
        
        # Verify headers were added
        assert len(sent_messages) == 2
        response_start = sent_messages[0]
        assert response_start["type"] == "http.response.start"
        
        # Convert headers to dict for easier checking
        headers_dict = {name.decode(): value.decode() for name, value in response_start["headers"]}
        
        assert "x-content-type-options" in headers_dict
        assert headers_dict["x-content-type-options"] == "nosniff"
        assert "x-frame-options" in headers_dict
        assert headers_dict["x-frame-options"] == "DENY"

    @pytest.mark.asyncio
    async def test_middleware_non_http_passthrough(self) -> None:
        """Test that non-HTTP requests pass through unchanged."""
        mock_app = AsyncMock()
        middleware = SecurityHeadersMiddleware(app=mock_app, is_production=True)
        
        # WebSocket scope
        scope: Scope = {"type": "websocket"}
        receive = AsyncMock()
        send = AsyncMock()
        
        await middleware(scope, receive, send)
        
        # Verify the app was called with original parameters
        mock_app.assert_called_once_with(scope, receive, send)


class TestEnvironmentValidation:
    """Test cases for environment variable validation."""

    def test_validate_environment_variables_development(self) -> None:
        """Test that development config passes validation."""
        config = SqliteDevelopmentConfiguration()
        # Should not raise any exception
        validate_environment_variables(config)

    def test_validate_environment_variables_production_sqlite(self) -> None:
        """Test that production SQLite config passes validation."""
        config = SqliteProductionConfiguration()
        # Should not raise any exception for SQLite
        validate_environment_variables(config)

    def test_validate_environment_variables_missing_postgres_vars(self) -> None:
        """Test that missing PostgreSQL environment variables raise error."""
        # Create a mock PostgreSQL production config with missing variables
        database_mock = Mock()
        database_mock.value = "postgres"
        
        config = Mock()
        config.PRODUCTION = True
        config.DATABASE = database_mock
        config.POSTGRES_DATABASE_USERNAME = None
        config.POSTGRES_DATABASE_PASSWORD = None
        config.POSTGRES_DATABASE_HOST = None
        config.POSTGRES_DATABASE_PORT = None
        config.POSTGRES_OFFLINE_DATABASE_NAME = None

        with pytest.raises(ValueError) as excinfo:
            validate_environment_variables(cast(Configuration, config))
        
        assert "Required environment variables for production are missing" in str(excinfo.value)
        assert "POSTGRES_DATABASE_USERNAME" in str(excinfo.value)


class TestSetupSecurityMiddleware:
    """Test cases for setup_security_middleware function."""

    def test_setup_security_middleware_development(self) -> None:
        """Test security middleware setup for development."""
        app = Mock()
        config = SqliteDevelopmentConfiguration()
        
        # Should not raise any exception
        setup_security_middleware(app, config)
        
        # Verify middleware was added
        app.add_middleware.assert_called_once()
        call_args = app.add_middleware.call_args
        assert call_args[0][0] == SecurityHeadersMiddleware
        assert call_args[1]["is_production"] == False

    def test_setup_security_middleware_production(self) -> None:
        """Test security middleware setup for production."""
        app = Mock()
        config = SqliteProductionConfiguration()
        
        # Should not raise any exception
        setup_security_middleware(app, config)
        
        # Verify middleware was added
        app.add_middleware.assert_called_once()
        call_args = app.add_middleware.call_args
        assert call_args[0][0] == SecurityHeadersMiddleware
        assert call_args[1]["is_production"] == True

    def test_setup_security_middleware_validates_environment(self) -> None:
        """Test that setup_security_middleware validates environment variables."""
        app = Mock()
        
        # Create a mock config that will fail validation
        database_mock = Mock()
        database_mock.value = "postgres"
        
        config = Mock()
        config.PRODUCTION = True
        config.DATABASE = database_mock
        config.POSTGRES_DATABASE_USERNAME = None
        config.POSTGRES_DATABASE_PASSWORD = None
        config.POSTGRES_DATABASE_HOST = None
        config.POSTGRES_DATABASE_PORT = None
        config.POSTGRES_OFFLINE_DATABASE_NAME = None

        with pytest.raises(ValueError):
            setup_security_middleware(app, cast(Configuration, config))
        
        # Middleware should not be added if validation fails
        app.add_middleware.assert_not_called() 