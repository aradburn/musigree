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
    # Use the SQLite development configuration
    runtime_config = SqliteDevelopmentConfiguration()

    # Create FastAPI app using the specified runtime configuration.
    app = create_app(runtime_config)

    # Run the Uvicorn development server, which listens for incoming HTTP
    # requests and serves the Musigree application.
    uvicorn.run(app, host="0.0.0.0", port=5000, log_level="info")
