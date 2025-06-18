import pytest_asyncio
from musigree.config import SqliteTestConfiguration
from musigree.logging_config import setup_logging


@pytest_asyncio.fixture(scope="session")
async def offline_config():
    """Provide the SQLite offline database configuration for tests."""
    config = SqliteTestConfiguration()
    setup_logging(is_testing=True)
    return config 