import logging
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport, Request, Response

from musigree.app.fastapi_app import create_app
from musigree.config import (
    PostgresTestConfiguration,
    SqliteTestConfiguration,
    Configuration, SqliteReadOnlyTestConfiguration,
)
from musigree.logging_config import setup_logging

log = logging.getLogger(__name__)


@pytest.fixture(scope="class")
def offline_config() -> Configuration:
    """Provide the Postgres offline database configuration for tests."""
    offline_config = PostgresTestConfiguration()
    setup_logging(is_testing=True)
    return offline_config


@pytest.fixture(scope="class")
def runtime_config() -> Configuration:
    """Provide the Sqlite runtime database configuration for tests."""
    runtime_config = SqliteTestConfiguration()
    setup_logging(is_testing=True)
    return runtime_config


@pytest_asyncio.fixture(scope="class")
async def test_app(runtime_config: Configuration) -> FastAPI:
    """Create a test FastAPI application."""
    print("Creating test_app fixture")
    readonly_config = SqliteReadOnlyTestConfiguration()
    # Make sure we are using the same test sqlite runtime database, we open it in read-0only mode for the FastAPI app.
    readonly_config.SQLITE_RUNTIME_DATABASE_NAME = runtime_config.SQLITE_RUNTIME_DATABASE_NAME
    # Use the value from the runtime_config
    readonly_config.PRODUCTION = runtime_config.PRODUCTION
    readonly_config.DEBUG = runtime_config.DEBUG
    readonly_config.TESTING = runtime_config.TESTING
    readonly_config.CACHE_TYPE = runtime_config.CACHE_TYPE

    # # Close the database engine used for loading the test data before we use the FastAPI app.
    # if (
    #     RuntimeDatabaseManager.runtime_database_helper is not None
    #     and RuntimeDatabaseManager.runtime_database_helper.runtime_async_engine is not None
    # ):
    #     await RuntimeDatabaseManager.runtime_database_helper.runtime_async_engine.dispose(close=True)

    return create_app(readonly_config)


@pytest_asyncio.fixture
async def client(
    offline_database_shutdown: None,
    runtime_database_shutdown: None,
    test_app: FastAPI,
) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client."""
    print("Creating test client")

    async def log_request(request: Request) -> None:
        print(f"Request Event   : {request.method} {request.url}")
        print(f"Request headers : {request.headers}")

    async def log_response(response: Response) -> None:
        request = response.request
        print(f"Response Event  : {request.method} {request.url} - Status {response.status_code}")
        print(f"Response headers: {response.headers}")

    async with LifespanManager(test_app) as manager:
        transport = ASGITransport(app=manager.app)
        async with AsyncClient(transport=transport,
                               base_url="https://musigree.com",
                               event_hooks={
                                   "request": [log_request],
                                   "response": [log_response],
                               },
                               ) as async_client:
            yield async_client
