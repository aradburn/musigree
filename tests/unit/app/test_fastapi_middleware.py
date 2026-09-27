"""
Unit tests for musigree.app.fastapi_middleware module.
"""

from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send

from musigree.app.fastapi_middleware import add_app_middleware


class _HeaderMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        await self.app(scope, receive, send)


class TestAddAppMiddleware:
    """Test cases for add_app_middleware."""

    def test_registers_middleware_class_with_kwargs(self) -> None:
        """Test that middleware is registered with constructor kwargs."""
        app = FastAPI()

        add_app_middleware(app, GZipMiddleware, minimum_size=1000)

        assert len(app.user_middleware) == 1
        assert app.user_middleware[0].cls is GZipMiddleware
        assert app.user_middleware[0].kwargs["minimum_size"] == 1000

    def test_registers_middleware_class_without_kwargs(self) -> None:
        """Test that middleware can be registered with no extra options."""
        app = FastAPI()

        add_app_middleware(app, _HeaderMiddleware)

        assert len(app.user_middleware) == 1
        assert app.user_middleware[0].cls is _HeaderMiddleware
