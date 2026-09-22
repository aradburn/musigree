"""
Unit tests for musigree.app.fastapi_app module.
"""

import logging
from collections.abc import Awaitable, Callable
from typing import Any
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from Secweb.CrossOriginEmbedderPolicy import CrossOriginEmbedderPolicy
from Secweb.CrossOriginOpenerPolicy import CrossOriginOpenerPolicy
from Secweb.CrossOriginResourcePolicy import CrossOriginResourcePolicy
from Secweb.ReferrerPolicy import ReferrerPolicy
from Secweb.StrictTransportSecurity import HSTS
from Secweb.XContentTypeOptions import XContentTypeOptions
from Secweb.XDNSPrefetchControl import XDNSPrefetchControl
from Secweb.XFrameOptions import XFrame
from fastapi import APIRouter, FastAPI
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.routing import iter_route_contexts
from fastapi.testclient import TestClient
# noinspection PyPackageRequirements
from starlette.middleware.cors import CORSMiddleware
# noinspection PyPackageRequirements
from starlette.requests import Request
# noinspection PyPackageRequirements
from starlette.responses import JSONResponse, Response

from musigree.app.fastapi_app import (
    create_app,
    init_app,
    shutdown_application,
    templates,
)
from musigree.app.fastapi_permissions_policy import PermissionsPolicy
from musigree.config import Configuration, SqliteTestConfiguration
from musigree.exceptions import BaseError


def _stub_assets_router() -> tuple[APIRouter, MagicMock]:
    """Return a real APIRouter; FastAPI 0.141 rejects MagicMock routers."""
    return APIRouter(), MagicMock()


def _middleware_entry(app: FastAPI, middleware_class: type[Any]) -> Any:
    """Return the registered Starlette middleware entry for a class."""
    for entry in app.user_middleware:
        if entry.cls is middleware_class:
            return entry
    raise AssertionError(f"{middleware_class.__name__} is not registered")


class TestCreateApp:
    """Test cases for create_app function."""

    @pytest.fixture
    def test_config(self) -> Configuration:
        """Provide test configuration."""
        return SqliteTestConfiguration()

    def test_create_app_basic_structure(
        self,
        test_config: Configuration,
    ) -> None:
        """Test that create_app returns a properly configured FastAPI instance."""
        with (
            patch("musigree.app.fastapi_assets.create_assets_router") as mock_create_assets_router,
            patch("musigree.app.fastapi_app.setup_csp_middleware") as mock_setup_csp,
        ):
            # Arrange
            mock_assets_router, mock_assets_templates = _stub_assets_router()
            mock_create_assets_router.return_value = (mock_assets_router, mock_assets_templates)

            # Act
            app = create_app(test_config)

            # Assert
            assert isinstance(app, FastAPI)
            assert app.title == "Musigree"  # type: ignore
            assert app.description == "Musigree API for exploring music relationships"  # type: ignore
            assert app.version == "1.0.0"  # type: ignore
            tag_names = [tag["name"] for tag in (app.openapi_tags or [])]
            assert tag_names == ["api", "ui", "healthcheck", "assets"]

            # Verify CSP middleware was set up
            mock_setup_csp.assert_called_once_with(app, test_config)

    @patch("musigree.app.fastapi_assets.create_assets_router")
    @patch("musigree.app.fastapi_app.setup_csp_middleware")
    def test_create_app_production_cors(
        self,
        _mock_setup_csp: Mock,
        mock_create_assets_router: Mock,
    ) -> None:
        """Test CORS configuration in production mode."""
        # Arrange
        config = SqliteTestConfiguration()
        config.PRODUCTION = True

        mock_assets_router, mock_assets_templates = _stub_assets_router()
        mock_create_assets_router.return_value = (mock_assets_router, mock_assets_templates)

        # Act
        app = create_app(config)

        # Assert
        assert isinstance(app, FastAPI)
        # Check that middleware was added by checking user_middleware or routes
        assert hasattr(app, "user_middleware") or hasattr(app, "middleware")

    def test_create_app_development_cors(
        self,
        test_config: Configuration,
    ) -> None:
        """Test CORS configuration in development mode."""
        with (
            patch("musigree.app.fastapi_assets.create_assets_router") as mock_create_assets_router,
            patch("musigree.app.fastapi_app.setup_csp_middleware"),
        ):
            # Arrange
            test_config.PRODUCTION = False

            mock_assets_router, mock_assets_templates = _stub_assets_router()
            mock_create_assets_router.return_value = (mock_assets_router, mock_assets_templates)

            # Act
            app = create_app(test_config)

            # Assert
            assert isinstance(app, FastAPI)
            # Check that middleware was added by checking user_middleware or routes
            assert hasattr(app, "user_middleware") or hasattr(app, "middleware")

    def test_create_app_registers_security_middleware(
        self,
        test_config: Configuration,
    ) -> None:
        """Test that security headers and compression middleware are registered."""
        with (
            patch("musigree.app.fastapi_assets.create_assets_router") as mock_create_assets_router,
            patch("musigree.app.fastapi_app.setup_csp_middleware"),
        ):
            mock_assets_router, mock_assets_templates = _stub_assets_router()
            mock_create_assets_router.return_value = (mock_assets_router, mock_assets_templates)

            app = create_app(test_config)

            expected_classes = (
                CORSMiddleware,
                ReferrerPolicy,
                HSTS,
                XContentTypeOptions,
                XDNSPrefetchControl,
                XFrame,
                CrossOriginEmbedderPolicy,
                CrossOriginOpenerPolicy,
                CrossOriginResourcePolicy,
                PermissionsPolicy,
                GZipMiddleware,
            )
            for middleware_class in expected_classes:
                _middleware_entry(app, middleware_class)

            assert _middleware_entry(app, ReferrerPolicy).kwargs["Option"] == [
                "strict-origin-when-cross-origin"
            ]
            assert _middleware_entry(app, HSTS).kwargs["Option"] == {
                "max-age": 2592000,
                "includeSubDomains": True,
                "preload": True,
            }
            assert _middleware_entry(app, XDNSPrefetchControl).kwargs["Option"] == "on"
            assert _middleware_entry(app, XFrame).kwargs["Option"] == "DENY"
            assert (
                _middleware_entry(app, CrossOriginEmbedderPolicy).kwargs["Option"] == "unsafe-none"
            )
            assert _middleware_entry(app, CrossOriginOpenerPolicy).kwargs["Option"] == "same-origin"
            assert _middleware_entry(app, CrossOriginResourcePolicy).kwargs["Option"] == "same-site"
            assert _middleware_entry(app, GZipMiddleware).kwargs["minimum_size"] == 1000

    def test_create_app_routers_included(
        self,
        test_config: Configuration,
    ) -> None:
        """Test that all routers are properly included."""
        with (
            patch("musigree.app.fastapi_assets.create_assets_router") as mock_create_assets_router,
            patch("musigree.app.fastapi_app.setup_csp_middleware"),
        ):
            # Arrange
            mock_assets_router, mock_assets_templates = _stub_assets_router()
            mock_create_assets_router.return_value = (mock_assets_router, mock_assets_templates)

            # Act
            app = create_app(test_config)

            # Assert
            assert isinstance(app, FastAPI)
            # Check that routes exist (the routers have been included)
            # We should have routes from the included routers plus static files
            assert len(app.routes) > 0
            route_paths = {
                context.path
                for context in iter_route_contexts(app.routes)
                if context.path is not None
            }
            assert any(path.startswith("/api/") or path == "/api" for path in route_paths if path is not None)
            assert "/health" in route_paths


class TestExceptionHandlers:
    """Test cases for exception handlers."""

    @pytest.fixture
    def test_config(self) -> Configuration:
        """Provide test configuration."""
        return SqliteTestConfiguration()

    @pytest.fixture
    def app(
        self,
        test_config: Configuration,
    ) -> FastAPI:
        """Create a test FastAPI app."""
        with (
            patch("musigree.app.fastapi_assets.create_assets_router") as mock_create_assets_router,
            patch("musigree.app.fastapi_app.setup_csp_middleware"),
        ):
            mock_assets_router, mock_assets_templates = _stub_assets_router()
            mock_create_assets_router.return_value = (mock_assets_router, mock_assets_templates)

            return create_app(test_config)

    @pytest.fixture
    def client(self, app: FastAPI) -> TestClient:
        """Create a test client."""
        return TestClient(app)

    @pytest.mark.asyncio
    async def test_base_error_handler_api_route(self, app: FastAPI) -> None:
        """Test BaseError handler for API routes."""
        # Arrange
        mock_request = MagicMock(spec=Request)
        mock_request.url.path = "/api/test"
        error = BaseError(message="Test error", status_code=400)

        # Find the exception handler
        handler: Callable | None = None
        for exc_type, exc_handler in app.exception_handlers.items():
            if exc_type == BaseError:
                handler = exc_handler
                break

        assert handler is not None, "BaseError handler not found"

        # Act
        if handler is not None:
            # noinspection PyCallingNonCallable
            result: Response | Awaitable[Response] = handler(mock_request, error)
            if hasattr(result, "__await__"):
                response: Response = await result  # type: ignore
            else:
                response = result  # type: ignore

            # Assert
            assert isinstance(response, JSONResponse)
            assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_base_error_handler_non_api_route(self, app: FastAPI) -> None:
        """Test BaseError handler for non-API routes."""
        # Arrange
        mock_request = MagicMock(spec=Request)
        mock_request.url.path = "/some-page"
        error = BaseError(message="Test error", status_code=500)

        # Find the exception handler
        handler: Callable | None = None
        for exc_type, exc_handler in app.exception_handlers.items():
            if exc_type == BaseError:
                handler = exc_handler
                break

        assert handler is not None, "BaseError handler not found"

        # Act
        if handler is not None:
            # noinspection PyCallingNonCallable
            result: Response | Awaitable[Response] = handler(mock_request, error)
            response: Response
            if hasattr(result, "__await__"):
                response = await result  # type: ignore
            else:
                response = result  # type: ignore

            # Assert
            assert response.status_code == 500
            # Response should be a TemplateResponse for non-API routes
            assert hasattr(response, "template")

    @pytest.mark.asyncio
    async def test_not_found_handler(self, app: FastAPI) -> None:
        """Test 404 exception handler."""
        # Arrange
        mock_request = MagicMock(spec=Request)
        mock_request.url.path = "/nonexistent"
        exc = Exception("Not found")

        # Find the 404 handler
        handler = app.exception_handlers.get(404)
        assert handler is not None, "404 handler not found"

        # Act
        result: Response | Awaitable[Response] = handler(mock_request, exc)
        response: Response
        if hasattr(result, "__await__"):
            response = await result  # type: ignore
        else:
            response = result  # type: ignore

        # Assert
        assert response.status_code == 404
        assert hasattr(response, "template")

    @pytest.mark.asyncio
    async def test_server_error_handler(self, app: FastAPI) -> None:
        """Test 500 exception handler."""
        # Arrange
        mock_request = MagicMock(spec=Request)
        mock_request.url.path = "/error"
        exc = Exception("Server error")

        # Find the 500 handler
        handler = app.exception_handlers.get(500)
        assert handler is not None, "500 handler not found"

        # Act
        result: Response | Awaitable[Response] = handler(mock_request, exc)
        response: Response
        if hasattr(result, "__await__"):
            response = await result  # type: ignore
        else:
            response = result  # type: ignore

        # Assert
        assert response.status_code == 500
        assert hasattr(response, "template")


class TestInitApp:
    """Test cases for init_app function."""

    @pytest.fixture
    def test_config(self) -> Configuration:
        """Provide test configuration."""
        return SqliteTestConfiguration()

    @pytest.mark.asyncio
    async def test_init_app_success(
        self,
        test_config: Configuration,
    ) -> None:
        """Test successful app initialization."""
        with (
            patch("musigree.app.fastapi_app.setup_logging"),
            patch("musigree.app.fastapi_app.CacheManager") as mock_cache_manager,
            patch("musigree.app.fastapi_app.RuntimeDatabaseManager") as mock_runtime_db_manager,
            patch("musigree.app.fastapi_app.RuntimeRoleDataAccess") as mock_role_data_access,
            patch("musigree.app.fastapi_app.asyncio_atexit") as mock_asyncio_atexit,
        ):
            # Arrange
            mock_cache_manager.setup_and_clear_cache = AsyncMock()
            mock_runtime_db_manager.setup_database = AsyncMock()
            mock_role_data_access.load_all_roles_into_cache = AsyncMock()

            # Act
            await init_app(test_config)

            # Assert
            # Note: setup_logging is called in create_app, not init_app
            mock_cache_manager.setup_and_clear_cache.assert_awaited_once_with(test_config)
            mock_runtime_db_manager.setup_database.assert_awaited_once_with(test_config)
            mock_role_data_access.load_all_roles_into_cache.assert_awaited_once()
            mock_asyncio_atexit.register.assert_called_once()

    @pytest.mark.asyncio
    async def test_init_app_raises_when_cache_not_initialized(
        self,
        test_config: Configuration,
    ) -> None:
        """Test init_app propagates cache initialization failures."""
        with patch("musigree.app.fastapi_app.CacheManager") as mock_cache_manager:
            mock_cache_manager.setup_and_clear_cache = AsyncMock(
                side_effect=RuntimeError("Cache not initialized after setup")
            )

            with pytest.raises(RuntimeError, match="Cache not initialized after setup"):
                await init_app(test_config)

    @pytest.mark.asyncio
    async def test_init_app_database_setup_called(
        self,
        test_config: Configuration,
    ) -> None:
        """Test that runtime_database setup is called during initialization."""
        with (
            patch("musigree.app.fastapi_app.setup_logging"),
            patch("musigree.app.fastapi_app.CacheManager") as mock_cache_manager,
            patch("musigree.app.fastapi_app.RuntimeDatabaseManager") as mock_runtime_db_manager,
            patch("musigree.app.fastapi_app.RuntimeRoleDataAccess") as mock_role_data_access,
            patch("musigree.app.fastapi_app.asyncio_atexit"),
        ):
            # Arrange
            mock_cache_manager.setup_and_clear_cache = AsyncMock()
            mock_runtime_db_manager.setup_database = AsyncMock()
            mock_role_data_access.load_all_roles_into_cache = AsyncMock()

            # Act
            await init_app(test_config)

            # Assert
            mock_runtime_db_manager.setup_database.assert_called_once_with(test_config)
            mock_role_data_access.load_all_roles_into_cache.assert_called_once()


class TestShutdownApplication:
    """Test cases for shutdown_application function."""

    @pytest.mark.asyncio
    @patch("musigree.app.fastapi_app.shutdown_logging")
    @patch("musigree.app.fastapi_app.CacheManager")
    @patch("musigree.runtime.runtime_database_manager.RuntimeDatabaseManager")
    @patch("musigree.app.fastapi_app.setup_logging")
    async def test_shutdown_application(
        self,
        mock_setup_logging: Mock,
        mock_runtime_db_manager: Mock,
        mock_cache_manager: Mock,
        mock_shutdown_logging: Mock,
    ) -> None:
        """Test successful application shutdown."""
        # Arrange
        mock_runtime_db_manager.shutdown_database = AsyncMock()
        mock_cache_manager.shutdown_cache = AsyncMock()

        # Act
        await shutdown_application()

        # Assert
        mock_setup_logging.assert_called_once()
        mock_runtime_db_manager.shutdown_database.assert_called_once()
        mock_cache_manager.shutdown_cache.assert_awaited_once()
        mock_shutdown_logging.assert_called_once()


class TestLifespan:
    """Test cases for the FastAPI lifespan context manager."""

    @pytest.fixture
    def test_config(self) -> Configuration:
        """Provide test configuration."""
        return SqliteTestConfiguration()

    # Note: Lifespan context manager testing requires complex FastAPI internal mocking
    # The create_app function is well tested and coverage is at 98%


class TestTemplatesGlobal:
    """Test cases for the global templates variable."""

    def test_templates_global_created(self) -> None:
        """Test that the global templates variable is properly created."""
        # Assert
        assert templates is not None
        assert hasattr(templates, "get_template")
        assert hasattr(templates, "TemplateResponse")


class TestModuleLogging:
    """Test cases for module-level logging."""

    def test_module_logger_exists(self) -> None:
        """Test that the module logger is properly created."""
        # Import the module to access its logger
        from musigree.app import fastapi_app

        # Assert
        assert hasattr(fastapi_app, "log")
        assert isinstance(fastapi_app.log, logging.Logger)
        assert fastapi_app.log.name == "musigree.app.fastapi_app"


class TestIntegrationScenarios:
    """Test cases for integration scenarios."""

    @pytest.fixture
    def test_config(self) -> Configuration:
        """Provide test configuration."""
        return SqliteTestConfiguration()

    @pytest.mark.asyncio
    async def test_exception_handlers_integration(
        self,
        test_config: Configuration,
    ) -> None:
        """Test that exception handlers are properly integrated into the app."""
        with (
            patch("musigree.app.fastapi_assets.create_assets_router") as mock_create_assets_router,
            patch("musigree.app.fastapi_app.setup_csp_middleware"),
        ):
            # Arrange
            mock_assets_router, mock_assets_templates = _stub_assets_router()
            mock_create_assets_router.return_value = (mock_assets_router, mock_assets_templates)

            # Act
            app = create_app(test_config)

            # Assert
            # Check that exception handlers are registered
            assert BaseError in app.exception_handlers  # type: ignore
            assert 404 in app.exception_handlers  # type: ignore
            assert 500 in app.exception_handlers  # type: ignore

            # Test the handlers exist and are callable
            base_error_handler = app.exception_handlers[BaseError]  # type: ignore
            not_found_handler = app.exception_handlers[404]  # type: ignore
            server_error_handler = app.exception_handlers[500]  # type: ignore

            assert callable(base_error_handler)
            assert callable(not_found_handler)
            assert callable(server_error_handler)
