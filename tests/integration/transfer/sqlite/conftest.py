import pytest
from musigree.config import SqliteTestConfiguration, Configuration
from musigree.logging_config import setup_logging


@pytest.fixture(scope="class")
def offline_config() -> Configuration:
    """Provide the Sqlite offline database configuration for tests."""
    offline_config = SqliteTestConfiguration()
    setup_logging(is_testing=True)
    return offline_config


@pytest.fixture(scope="class")
def runtime_config() -> Configuration:
    """Provide the Sqlite runtime database configuration for tests."""
    runtime_config = SqliteTestConfiguration()
    setup_logging(is_testing=True)
    return runtime_config
