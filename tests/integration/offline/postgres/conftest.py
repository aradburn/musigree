import pytest
from musigree.config import PostgresTestConfiguration
from musigree.logging_config import setup_logging


@pytest.fixture(scope="class")
def offline_config():
    """Provide the Postgres offline database configuration for tests."""
    offline_config = PostgresTestConfiguration()
    setup_logging(is_testing=True)
    return offline_config