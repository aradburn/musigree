"""
This module defines the FastAPI application for Musigree.

It provides functions to create a FastAPI application instance with
appropriate configuration, middleware, and route handlers. It also includes
initialization logic for the database and cache.

Key functionalities include:
    - Creating a FastAPI application instance
    - Configuring middleware for compression and CORS
    - Registering routers for API endpoints and UI routes
    - Initializing the database and cache
    - Handling application shutdown
    - Error handling through exception handlers

The module uses the following components:
    - FastAPI: For creating the web application
    - Starlette: For HTTP responses and middleware
    - musigree.config: For application configuration
    - musigree.exceptions: For custom exception handling
    - musigree.library.cache.cache_manager: For caching
    - musigree.logging_config: For logging configuration
    - musigree.runtime.runtime_database_manager: For database management
"""

import logging
import sys
from contextlib import asynccontextmanager
from typing import Any

import asyncio_atexit  # type: ignore
from fastapi import FastAPI, Request
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import Response
from starlette.staticfiles import StaticFiles

from musigree.app.fastapi_cors import PreflightLoggerMiddleware, CustomCORSPreflightMiddleware
from musigree.app.fastapi_security import setup_security_middleware
from musigree.config import Configuration
from musigree.constants import (
    TEMPLATES_DIR,
    PUBLIC_DIR,
    FRONTEND_DIR,
)
from musigree.exceptions import (
    BaseError,
    NotFoundError,
)
from musigree.library.cache.cache_manager import CacheManager
from musigree.logging_config import setup_logging, shutdown_logging
from musigree.runtime.data_access_layer.runtime_role_data_access import (
    RuntimeRoleDataAccess,
)
from musigree.runtime.runtime_database_manager import RuntimeDatabaseManager
from musigree.utils import log_banner

log = logging.getLogger(__name__)
"""The logger for the application module."""

# Create a global templates variable
templates = Jinja2Templates(directory=TEMPLATES_DIR)


def create_app(config: Configuration) -> FastAPI:
    """
    Creates and configures the FastAPI application.

    This function is a factory for creating the FastAPI application instance. It
    initializes the application, sets up the database and cache, registers
    routers, and configures error handling.

    Args:
        config: The application configuration object.

    Returns:
        FastAPI: The configured FastAPI application instance.
    """
    from musigree.app.fastapi_api import router as api_router
    from musigree.app.fastapi_ui import router as ui_router
    from musigree.app.fastapi_healthcheck import router as healthcheck_router
    from musigree.app.fastapi_assets import create_assets_router

    # Setup logging
    setup_logging(is_testing=config.TESTING)

    log_banner()

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> Any:
        """
        Lifespan context manager for the FastAPI application.

        This function manages the application lifecycle. Code before yield is executed
        on startup, and code after yield is executed on shutdown.

        Args:
            _app: The FastAPI application instance.
        """
        # Code to run on application startup

        # Initialize the app
        log.info("######## APPLICATION LIFESPAN STARTUP ########")
        await init_app(config)

        yield

        # Code to run on application shutdown
        log.info("######## APPLICATION LIFESPAN SHUTDOWN ########")
        await shutdown_application()

    # Create a new FastAPI app
    app = FastAPI(
        debug=config.DEBUG,
        title="Musigree",
        description="Musigree API for exploring music relationships",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Add middleware

    # Configure CORS based on environment
    if config.PRODUCTION:
        # Production: specific origins only
        allowed_origins = [
            "https://www.musigree.com",
            "https://musigree.com",
            "https://umami.musigree.com",
            "https://swetrix.org/swetrix.js",
            "https://cdn.jsdelivr.net/gh/Swetrix/",
        ]
        log.info("Configuring CORS for production")
        log.debug(f"Allowed origins: {allowed_origins}")

        app.add_middleware(
            CORSMiddleware,
            allow_origins=allowed_origins,
            allow_methods=["GET,HEAD,POST,OPTIONS"],
            allow_headers=["Content-Type"],
            allow_credentials=False,
        )
        app.add_middleware(
            CustomCORSPreflightMiddleware,
            allow_origins=allowed_origins,
            allow_methods=["GET,HEAD,POST,OPTIONS"],
            allow_headers=["Content-Type"],
            allow_credentials=False,
        )
        app.add_middleware(PreflightLoggerMiddleware)

    else:
        # Development: more permissive for local development
        # noinspection PyTypeChecker
        allowed_origins = [
            "http://localhost:5000",
            "http://localhost:5173",
            "http://localhost:8080",
            "http://127.0.0.1:5000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:8080",
            "https://swetrix.org/swetrix.js",
            "https://cdn.jsdelivr.net/gh/Swetrix/",
        ]
        log.info("Configuring CORS for development")
        log.debug(f"Allowed origins: {allowed_origins}")
        app.add_middleware(
            CORSMiddleware,
            allow_origins=allowed_origins,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Setup security middleware (should be added after CORS)
    setup_security_middleware(app, config)

    # noinspection PyTypeChecker
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # Create assets router
    assets_router, assets_templates = create_assets_router(config)

    # Include routers
    app.mount("/prodassets", StaticFiles(directory=FRONTEND_DIR / "dist"), name="prodassets")
    app.include_router(assets_router)
    app.include_router(api_router, prefix="/api")
    app.include_router(ui_router)
    app.include_router(healthcheck_router)
    app.mount("/", StaticFiles(directory=PUBLIC_DIR), name="public")

    # Set up exception handlers
    @app.exception_handler(BaseError)
    async def base_error_handler(request: Request, exc: BaseError) -> Response:
        if request.url.path.startswith("/api/"):
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "success": False,
                    "status": exc.status_code,
                    "message": exc.message,
                },
            )
        elif request.url.path.startswith("/health/"):
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "success": False,
                    "status": exc.status_code,
                    "message": "Bad healthcheck endpoint",
                },
            )
        else:
            # For non-API routes, return an HTML response
            return templates.TemplateResponse(
                request=request,
                name="error.html",
                context={"error": exc},
                status_code=exc.status_code,
            )

    # noinspection PyUnusedLocal
    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc: Any) -> Response:
        if request.url.path.startswith("/api/"):
            return JSONResponse(
                status_code=404,
                content={
                    "success": False,
                    "status": 404,
                    "message": "Bad API endpoint",
                },
            )
        elif request.url.path.startswith("/health/"):
            return JSONResponse(
                status_code=404,
                content={
                    "success": False,
                    "status": 404,
                    "message": "Bad healthcheck endpoint",
                },
            )
        else:
            error = NotFoundError(message="Not Found")
            return templates.TemplateResponse(
                request=request,
                name="error.html",
                context={"error": error},
                status_code=error.status_code,
            )

    # noinspection PyUnusedLocal
    @app.exception_handler(500)
    async def server_error_handler(request: Request, exc: Any) -> Response:
        error = BaseError(message="Server Error")
        return templates.TemplateResponse(
            request=request,
            name="error.html",
            context={"error": error},
            status_code=error.status_code,
        )

    # Custom exception handler
    @app.exception_handler(Exception)
    async def custom_exception_handler(_request: Request, exc: Exception) -> Response:
        log.error(f"Unhandled exception: {exc}")
        return JSONResponse(
            status_code=500,
            content={"message": "An internal server error occurred."},
        )

    return app


async def shutdown_application() -> None:
    """
    Shuts down the application.

    This function is called when the application is being shut down. It
    performs cleanup tasks such as closing database connections, shutting
    down the cache, and shutting down logging.
    """
    from musigree.runtime.runtime_database_manager import RuntimeDatabaseManager

    # Logging may have been shutdown automatically before this point, so we need to reinitialize it again
    setup_logging()
    log.info("######## APPLICATION SHUTDOWN BEGIN ########")
    await RuntimeDatabaseManager.shutdown_database()
    await CacheManager.shutdown_cache()
    shutdown_logging()
    log.info("######## APPLICATION SHUTDOWN END ########")


async def init_app(config: Configuration) -> None:
    """
    Initializes the application.

    This function initializes the application components, including logging,
    caching, and the database.

    Args:
        config: The application configuration object.
    """

    log.info("######## APPLICATION STARTUP BEGIN ########")
    log.info(f"Using runtime configuration: {config.__class__.__name__}")

    # Setup cache
    await CacheManager.setup_cache(config)
    cache = CacheManager.get_cache()
    if cache is None:
        log.error("Cache not set")
        sys.exit()
    else:
        log.debug("Clearing cache")
        await CacheManager.clear()

    # Setup Database
    await RuntimeDatabaseManager.setup_database(config)

    log.info("Database setup OK")

    # Load role cache in memory
    await RuntimeRoleDataAccess.load_all_roles_into_cache()

    log.info("Loaded all roles OK")

    # Shutdown on app exit
    asyncio_atexit.register(shutdown_application)

    log.info("######## APPLICATION STARTUP END ########")
