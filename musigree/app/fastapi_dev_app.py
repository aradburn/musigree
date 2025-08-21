"""
This module provides a development entry point for the Musigree application using FastAPI.

It sets up and runs a local development server using Uvicorn, utilizing the
SQLite database for data storage and retrieval. It's intended for development
and testing purposes and should not be used in a production environment.

Key functionalities include:
    - Creating a FastAPI application instance with SQLite configuration.
    - Loading initial data into the database tables.
    - Starting the Uvicorn development server.

The application configuration is defined in `musigree.config`, and the
database management is handled by `musigree.runtime.runtime_database_manager`.

The `create_app` function in `musigree.app.fastapi_app` is used to create the
FastAPI application instance. The `load_tables` method in
`RuntimeDatabaseManager.runtime_database_helper` is used to populate the
database with initial data.
"""

import uvicorn
from fastapi import FastAPI

from musigree.app.fastapi_app import create_app
from musigree.config import SqliteDevelopmentConfiguration


def create_development_app() -> FastAPI:
    """
    Creates and configures a FastAPI application for development.

    This function sets up a FastAPI application instance using the
    `SqliteProductionConfiguration` to ensure it is configured for a
    production environment. It also loads initial data into the database
    tables.

    Returns:
        FastAPI: A configured FastAPI application instance ready for development.
    """
    runtime_config = SqliteDevelopmentConfiguration()
    """
    Configuration object for the runtime environment.

    Sets up the configuration for the runtime environment using SQLite,
    suitable for development use.
    """
    _app = create_app(runtime_config)
    """
    FastAPI application instance.

    Creates a new FastAPI application instance using the specified runtime
    configuration, including settings for the database, cache, and logging.
    """

    return _app


"""
The main FastAPI application instance for development.

This is the FastAPI application instance that should be used by ASGI servers
like Uvicorn when running the application in development.
"""

if __name__ == "__main__":
    # FastAPI instance for ASGI servers like Uvicorn
    app = create_development_app()

    # Run the Uvicorn development server, which listens for incoming HTTP
    # requests and serves the Musigree application.
    uvicorn.run(app, host="0.0.0.0", port=5000, log_level="info")
