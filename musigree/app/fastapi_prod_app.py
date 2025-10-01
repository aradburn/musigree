"""
This module defines a production entry point for the Musigree application using FastAPI.

It provides a function, `create_production_app`, to create and configure a
FastAPI application instance suitable for a production environment. This setup
uses the `SqliteProductionConfiguration` for configuration settings, ensuring
that the application is properly configured for deployment.

Key functionalities include:
    - Creating a FastAPI application instance with production settings.
    - Loading initial data into the database tables.
    - Returning the configured FastAPI application instance.

The application configuration is defined in `musigree.config`, and the
database management is handled by `musigree.runtime.runtime_database_manager`.

The `create_app` function from `musigree.app.fastapi_app` is used to create the
FastAPI application instance. The `load_tables` method in
`RuntimeDatabaseManager.runtime_database_helper` is used to populate the
database with initial data.

This module is intended to be used as the main entry point for running the
Musigree application in a production environment. It sets up the necessary
components and returns a ready-to-use FastAPI application.
"""

from fastapi import FastAPI

from musigree.app.fastapi_app import create_app
from musigree.config import SqliteReadOnlyProductionConfiguration


def create_production_app() -> FastAPI:
    """
    Creates and configures a FastAPI application for production.

    This function sets up a FastAPI application instance using the
    `SqliteProductionConfiguration` to ensure it is configured for a
    production environment. It also loads initial data into the database
    tables.

    Returns:
        FastAPI: A configured FastAPI application instance ready for production.
    """
    runtime_config = SqliteReadOnlyProductionConfiguration()
    """
    Configuration object for the runtime environment.

    Sets up the configuration for the runtime environment using SQLite,
    suitable for production use.
    """
    _app = create_app(runtime_config)
    """
    FastAPI application instance.

    Creates a new FastAPI application instance using the specified runtime
    configuration, including settings for the database, cache, and logging.
    """

    return _app


# FastAPI instance for ASGI servers like Uvicorn
app = create_production_app()
"""
The main FastAPI application instance for production.

This is the FastAPI application instance that should be used by ASGI servers
like Uvicorn when running the application in production.
"""
