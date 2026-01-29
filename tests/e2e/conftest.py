"""Pytest configuration and fixtures for end-to-end tests."""
import logging
import multiprocessing
import socket
import time
from pathlib import Path
from typing import Generator, AsyncGenerator

import pytest
import uvicorn

from musigree.app.fastapi_app import create_app
from musigree.config import Configuration, SqliteReadOnlyTestConfiguration
from musigree.constants import CacheType
from musigree.logging_config import TEST_LOGGING_CONFIG
from tests.e2e.end_to_end_utils import TEST_SERVER_BASE_URL, TEST_SERVER_BASE_PORT

log = logging.getLogger(__name__)


def run_server(runtime_db_path: str) -> None:
    """Run the FastAPI server in a separate process.

    Args:
        runtime_db_path: Path to the runtime database.
    """
    readonly_config = SqliteReadOnlyTestConfiguration()
    # Override runtime database path
    readonly_config.SQLITE_RUNTIME_DATABASE_NAME = Path(runtime_db_path)
    readonly_config.PRODUCTION = True
    readonly_config.DEBUG = True
    readonly_config.TESTING = True
    readonly_config.CACHE_TYPE = CacheType.REDIS

    app = create_app(readonly_config)

    # uvicorn.run(app, host="0.0.0.0", port=TEST_SERVER_BASE_PORT, log_level="trace", access_log=True)
    uvicorn.run(app, host="0.0.0.0", port=TEST_SERVER_BASE_PORT, log_level="debug", log_config=TEST_LOGGING_CONFIG,
                access_log=True)


def is_server_ready(host: str = "localhost", port: int = TEST_SERVER_BASE_PORT, timeout: float = 1.0) -> bool:
    """Check if the server is ready to accept connections."""
    # noinspection PyBroadException
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False


@pytest.fixture(scope="class")
def server_process(
    runtime_config: Configuration,
    offline_database_setup: AsyncGenerator[None, None],
    runtime_database_setup: AsyncGenerator[None, None],
    offline_database_shutdown: None,
    runtime_database_shutdown: None,
) -> Generator[multiprocessing.Process, None, None]:
    """Start the FastAPI server in a background process.

    Uses the same configuration as the test fixtures to ensure the server
    connects to the same databases that were set up by the test fixtures.

    Args:
        runtime_config: The runtime database configuration from the test fixtures.
        :param offline_database_shutdown:
        :param runtime_database_shutdown:
        :param runtime_config:
        :param runtime_database_setup:
        :param offline_database_setup:
    """
    # Get runtime_database paths from the configs
    runtime_db_path = str(runtime_config.SQLITE_RUNTIME_DATABASE_NAME)

    process = multiprocessing.Process(
        target=run_server,
        args=(runtime_db_path,),
        daemon=True,
    )
    process.start()

    # Wait for server to be ready
    max_attempts = 30
    for _attempt in range(max_attempts):
        if is_server_ready():
            log.info("Server is ready")
            break
        time.sleep(0.5)
    else:
        pytest.fail("Server failed to start within timeout")

    yield process

    # Cleanup: terminate the server process
    process.terminate()
    process.join(timeout=5)
    if process.is_alive():
        process.kill()


@pytest.fixture(scope="session")
def base_url() -> str:
    """Provide the base URL for the test server."""
    return TEST_SERVER_BASE_URL


# Reuse runtime_database fixtures from integration tests
pytest_plugins = ["tests.integration.app.conftest"]
