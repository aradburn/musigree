from typing import AsyncGenerator

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

from musigree.app.fastapi_app import create_app
from musigree.config import (
    PostgresTestConfiguration,
    SqliteTestConfiguration,
    Configuration,
)
from musigree.logging_config import setup_logging


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


async def create_test_app() -> FastAPI:
    """Create a test FastAPI application with minimal setup for testing."""
    print("Creating test FastAPI application")
    config = SqliteTestConfiguration()

    # Create a FastAPI app for testing
    app = create_app(config)

    return app


@pytest_asyncio.fixture
async def test_app() -> FastAPI:
    """Create a test FastAPI application."""
    print("Creating test_app fixture")
    return await create_test_app()


@pytest_asyncio.fixture
async def client(test_app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client."""
    print("Creating test client")
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
        yield ac
