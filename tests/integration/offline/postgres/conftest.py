import pytest_asyncio
from musigree.config import PostgresTestConfiguration
from musigree.logging_config import setup_logging


@pytest_asyncio.fixture(scope="session")
async def offline_config():
    """Provide the Postgres offline database configuration for tests."""
    config = PostgresTestConfiguration()
    setup_logging(is_testing=True)
    return config 