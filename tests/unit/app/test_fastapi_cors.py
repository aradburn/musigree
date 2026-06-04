"""
Unit tests for musigree.app.fastapi_cors module.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
# noinspection PyPackageRequirements
from starlette.requests import Request
# noinspection PyPackageRequirements
from starlette.responses import Response

from musigree.app.fastapi_cors import (
    CustomCORSPreflightMiddleware,
    PreflightLoggerMiddleware,
)


class TestCustomCORSPreflightMiddleware:
    """Test cases for CustomCORSPreflightMiddleware."""

    def test_init_defaults(self) -> None:
        """Test middleware init with default allow_credentials and max_age."""
        app = MagicMock()
        mw = CustomCORSPreflightMiddleware(
            app,
            allow_origins=["https://example.com"],
            allow_methods=["GET", "POST"],
            allow_headers=["Content-Type"],
        )
        assert mw.allowed_origins == ["https://example.com"]
        assert mw.allowed_methods == ["GET", "POST"]
        assert mw.allowed_headers == ["Content-Type"]
        assert mw.allow_credentials is True
        assert mw.max_age == 600

    def test_init_empty_lists_default(self) -> None:
        """Test middleware init with None uses empty lists."""
        app = MagicMock()
        mw = CustomCORSPreflightMiddleware(app)
        assert mw.allowed_origins == []
        assert mw.allowed_methods == []
        assert mw.allowed_headers == []

    def test_is_origin_allowed_true(self) -> None:
        """Test _is_origin_allowed when origin is in list."""
        app = MagicMock()
        mw = CustomCORSPreflightMiddleware(app, allow_origins=["https://allowed.com"])
        assert mw._is_origin_allowed("https://allowed.com") is True

    def test_is_origin_allowed_false(self) -> None:
        """Test _is_origin_allowed when origin is not in list."""
        app = MagicMock()
        mw = CustomCORSPreflightMiddleware(app, allow_origins=["https://allowed.com"])
        assert mw._is_origin_allowed("https://other.com") is False

    @pytest.mark.asyncio
    async def test_dispatch_options_allowed_origin(self) -> None:
        """Test OPTIONS request with allowed origin returns 204 and CORS headers."""
        app = MagicMock()
        mw = CustomCORSPreflightMiddleware(
            app,
            allow_origins=["https://example.com"],
            allow_methods=["GET"],
            allow_headers=["Authorization"],
            allow_credentials=True,
            max_age=300,
        )
        request = MagicMock(spec=Request)
        request.method = "OPTIONS"
        request.headers = {"origin": "https://example.com"}
        call_next = AsyncMock(return_value=Response())

        response = await mw.dispatch(request, call_next)

        assert response.status_code == 204
        assert response.headers["Access-Control-Allow-Origin"] == "https://example.com"
        assert "GET" in response.headers["Access-Control-Allow-Methods"]
        assert "Authorization" in response.headers["Access-Control-Allow-Headers"]
        assert response.headers["Access-Control-Max-Age"] == "300"
        assert response.headers["Access-Control-Allow-Credentials"] == "true"
        call_next.assert_not_called()

    @pytest.mark.asyncio
    async def test_dispatch_options_disallowed_origin(self) -> None:
        """Test OPTIONS request with disallowed origin returns 400."""
        app = MagicMock()
        mw = CustomCORSPreflightMiddleware(app, allow_origins=["https://example.com"])
        request = MagicMock(spec=Request)
        request.method = "OPTIONS"
        request.headers = {"origin": "https://evil.com"}
        call_next = AsyncMock(return_value=Response())

        response = await mw.dispatch(request, call_next)

        assert response.status_code == 400
        call_next.assert_not_called()

    @pytest.mark.asyncio
    async def test_dispatch_get_with_origin_adds_cors_headers(self) -> None:
        """Test GET request with allowed origin adds CORS headers to response."""
        app = MagicMock()
        mw = CustomCORSPreflightMiddleware(app, allow_origins=["https://example.com"])
        request = MagicMock(spec=Request)
        request.method = "GET"
        request.headers = {"origin": "https://example.com"}
        downstream = Response(content=b"ok")
        call_next = AsyncMock(return_value=downstream)

        response = await mw.dispatch(request, call_next)

        call_next.assert_called_once_with(request)
        assert response.headers["Access-Control-Allow-Origin"] == "https://example.com"
        assert response.headers["Access-Control-Allow-Credentials"] == "true"

    @pytest.mark.asyncio
    async def test_dispatch_get_no_origin_passes_through(self) -> None:
        """Test GET request without origin passes through without CORS headers."""
        app = MagicMock()
        mw = CustomCORSPreflightMiddleware(app, allow_origins=["https://example.com"])
        request = MagicMock(spec=Request)
        request.method = "GET"
        request.headers = {}
        downstream = Response(content=b"ok")
        call_next = AsyncMock(return_value=downstream)

        response = await mw.dispatch(request, call_next)

        call_next.assert_called_once_with(request)
        assert "Access-Control-Allow-Origin" not in response.headers


class TestPreflightLoggerMiddleware:
    """Test cases for PreflightLoggerMiddleware."""

    @pytest.mark.asyncio
    async def test_dispatch_options_calls_call_next(self) -> None:
        """Test OPTIONS request is passed to call_next and response returned."""
        app = MagicMock()
        mw = PreflightLoggerMiddleware(app)
        request = MagicMock(spec=Request)
        request.method = "OPTIONS"
        request.url = MagicMock(path="/api")
        request.headers = {"origin": "https://x.com", "access-control-request-method": "GET"}
        downstream = Response(status_code=204)
        call_next = AsyncMock(return_value=downstream)

        response = await mw.dispatch(request, call_next)

        call_next.assert_called_once_with(request)
        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_dispatch_non_options_passes_through(self) -> None:
        """Test non-OPTIONS request passes through without logging."""
        app = MagicMock()
        mw = PreflightLoggerMiddleware(app)
        request = MagicMock(spec=Request)
        request.method = "GET"
        downstream = Response(content=b"ok")
        call_next = AsyncMock(return_value=downstream)

        response = await mw.dispatch(request, call_next)

        call_next.assert_called_once_with(request)
        assert response.body == b"ok"
