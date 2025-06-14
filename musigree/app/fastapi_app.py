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

import atexit
import logging
import sys
from typing import Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import Response
from starlette.staticfiles import StaticFiles

from musigree.config import Configuration
from musigree.constants import TEMPLATES_DIR, PUBLIC_DIR
from musigree.exceptions import (
    BaseError,
    NotFoundError,
)
from musigree.library.cache.cache_manager import CacheManager
from musigree.loader.loader import load_runtime_tables
from musigree.logging_config import setup_logging, shutdown_logging
from musigree.runtime.runtime_database_manager import RuntimeDatabaseManager
from musigree.app.fastapi_security import setup_security_middleware

log = logging.getLogger(__name__)
"""The logger for the application module."""

# Create a global templates variable
templates = Jinja2Templates(directory=TEMPLATES_DIR)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """
    Lifespan context manager for the FastAPI application.

    This function manages the application lifecycle. Code before yield is executed
    on startup, and code after yield is executed on shutdown.

    Args:
        _app: The FastAPI application instance.
    """
    # Code to run on application startup
    yield
    # Code to run on application shutdown
    shutdown_application()


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
    from musigree.app.fastapi_assets import create_assets_router

    # Create a new FastAPI app
    app = FastAPI(
        title="Musigree",
        description="Musigree API for exploring music relationships",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Initialize the app
    init_app(config)

    # Add middleware
    # noinspection PyTypeChecker
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # Configure CORS based on environment
    if config.PRODUCTION:
        # Production: specific origins only
        allowed_origins = [
            "https://musigree.azurewebsites.net",
            "https://www.musigree.com",  # Add your production domain
        ]
        # noinspection PyTypeChecker
        app.add_middleware(
            CORSMiddleware,
            allow_origins=allowed_origins,
            allow_methods=["GET", "POST", "PUT", "DELETE"],
            allow_headers=["Content-Type", "Authorization"],
            allow_credentials=True,
        )
    else:
        # Development: more permissive for local development
        # noinspection PyTypeChecker
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:8080"],
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Setup security middleware (should be added after CORS)
    setup_security_middleware(app, config)

    # Create assets router
    assets_router, assets_templates = create_assets_router(config)

    # Include routers
    app.include_router(api_router, prefix="/api")
    app.include_router(ui_router)
    app.include_router(assets_router)

    app.mount("/public", StaticFiles(directory=PUBLIC_DIR), name="public")

    # Set up exception handlers
    @app.exception_handler(BaseError)
    async def base_error_handler(request: Request, exc: BaseError) -> Response:
        log.warning(f"Error: {exc}")
        if request.url.path.startswith("/api"):
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "success": False,
                    "status": exc.status_code,
                    "message": exc.message,
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

    return app


def shutdown_application():
    """
    Shuts down the application.

    This function is called when the application is being shut down. It
    performs cleanup tasks such as closing database connections, shutting
    down the cache, and shutting down logging.
    """
    from musigree.runtime.runtime_database_manager import RuntimeDatabaseManager

    # Logging may have been shutdown automatically before this point, so we need to reinitialize it again
    setup_logging()
    log.info("######## APPLICATION SHUTDOWN START ########")
    RuntimeDatabaseManager.shutdown_database()
    CacheManager.shutdown_cache()
    shutdown_logging()
    log.info("######## APPLICATION SHUTDOWN DONE ########")


def init_app(config: Configuration):
    """
    Initializes the application.

    This function initializes the application components, including logging,
    caching, and the database.

    Args:
        config: The application configuration object.
    """
    # Setup logging
    setup_logging()

    log.info("")
    log.info("")
    log.info("######  #   # #   ####   ####   ####   ####    ##   #####  #    # ")
    log.info("#     # # #      #    # #    # #    # #    #  #  #  #    # #    # ")
    log.info("#     # #  ####  #      #    # #      #    # #    # #    # ###### ")
    log.info("#     # #      # #      #    # #  ### #####  ###### #####  #    # ")
    log.info("#     # # #    # #    # #    # #    # #   #  #    # #      #    # ")
    log.info("######  #  ####   ####   ####   ####  #    # #    # #      #    # ")
    log.info("")
    log.info("")

    log.info(f"Using runtime configuration: {config.__class__.__name__}")

    # Setup cache
    CacheManager.setup_cache(config)
    cache = CacheManager.get_cache()
    if cache is None:
        log.error("Cache not set")
        sys.exit()
    else:
        log.debug("Clearing cache")
        CacheManager.clear()

    # Setup Database
    RuntimeDatabaseManager.setup_database(config)

    # Load runtime tables
    if not config.TESTING:
        load_runtime_tables(config.DATA_DIR)

    # Shutdown on app exit
    atexit.register(shutdown_application)
