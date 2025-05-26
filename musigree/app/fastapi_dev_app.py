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

from musigree.app.fastapi_app import create_app
from musigree.config import SqliteDevelopmentConfiguration

if __name__ == "__main__":
    # Create SQLite development configuration
    runtime_config = SqliteDevelopmentConfiguration()
    """
    Configuration object for the runtime environment.

    Sets up the configuration for the runtime environment using SQLite.
    """

    # Create FastAPI app
    app = create_app(runtime_config)
    """
    FastAPI application instance.

    Creates a new FastAPI application instance using the specified runtime
    configuration.
    """

    # Load data from tables
    # RuntimeDatabaseManager.runtime_database_helper.load_tables()
    """
    Loads initial data into the runtime database.

    Populates the tables in the runtime database with initial data,
    such as roles, from the pre-configured data sources.
    """

    # Run the Uvicorn development server
    uvicorn.run(app, host="0.0.0.0", port=5000, log_level="info")
    """
    Starts the Uvicorn development server.

    Runs the Uvicorn development server, which listens for incoming HTTP
    requests and serves the Musigree application.
    """
