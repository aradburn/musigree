import pytest
from musigree.config import SqliteTestConfiguration
from musigree.logging_config import setup_logging


@pytest.fixture(scope="class")
def offline_config():
    """Provide the SQLite offline database configuration for tests."""
    offline_config = SqliteTestConfiguration()
    setup_logging(is_testing=True)
    return offline_config