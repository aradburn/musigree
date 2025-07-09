import asyncio
import logging
import pytest
import pytest_asyncio
from sqlalchemy.exc import DatabaseError

from musigree.config import PostgresTestConfiguration, SqliteTestConfiguration
from musigree.constants import ALL_OFFLINE_DATABASE_TABLE_NAMES, ALL_RUNTIME_DATABASE_TABLE_NAMES
from musigree.library.cache.cache_manager import CacheManager
from musigree.loader.loader import load_runtime_tables, load_offline_tables
from musigree.logging_config import setup_logging, shutdown_logging
from musigree.offline.offline_database_manager import OfflineDatabaseManager
from musigree.offline.database.offline_transaction import offline_transaction
from musigree.runtime.runtime_database.runtime_transaction import runtime_transaction
from musigree.runtime.runtime_database_manager import RuntimeDatabaseManager

log = logging.getLogger(__name__)


# Mixin to handle abstract test classes
class NotATest:
    def __init_subclass__(cls):
        cls.__test__ = NotATest not in cls.__bases__


@pytest.fixture(scope="class")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="class")
async def offline_database_setup(offline_config, is_load_offline_data_required):
    setup_logging(is_testing=True)

    """Set up the offline database for testing."""
    log.info("Setting up offline database for tests")

    # Set up cache manager
    CacheManager.setup_cache(offline_config)
    
    # Set up database
    try:
        await OfflineDatabaseManager.setup_database(offline_config)
    except DatabaseError:
        log.error("Error in offline database test setup")
        pytest.fail("Error in offline database test setup")
    
    # Ensure database helper is initialized
    assert OfflineDatabaseManager.offline_database_helper is not None, "Database helper not initialized"
    
    # Drop and recreate tables
    await OfflineDatabaseManager.offline_database_helper.drop_tables(ALL_OFFLINE_DATABASE_TABLE_NAMES)
    await OfflineDatabaseManager.offline_database_helper.create_tables(ALL_OFFLINE_DATABASE_TABLE_NAMES)

    if is_load_offline_data_required:
        log.info("Loading test data into offline database")

        # Load test data
        await load_offline_tables(
            offline_config.DATA_DIR,
            "testinsert",
            is_bulk_inserts=True,
        )
    
    log.info("Offline database setup complete")
    yield
    
    # Teardown
    log.info("Tearing down offline database")
    await OfflineDatabaseManager.shutdown_database()
    CacheManager.shutdown_cache()
    shutdown_logging()


@pytest_asyncio.fixture
async def offline_transaction_fixture():
    """Provide an async transaction context for individual tests."""
    async with offline_transaction() as session:
        yield session
        # Transaction will automatically rollback if not committed


@pytest_asyncio.fixture
async def reset_offline_database():
    """Reset offline database tables to start test with empty tables."""
    if OfflineDatabaseManager.offline_database_helper is not None:
        log.info("Resetting offline database tables")

        await OfflineDatabaseManager.offline_database_helper.drop_tables(ALL_OFFLINE_DATABASE_TABLE_NAMES)
        await OfflineDatabaseManager.offline_database_helper.create_tables(ALL_OFFLINE_DATABASE_TABLE_NAMES)

    yield


@pytest_asyncio.fixture(scope="class")
async def runtime_database_setup(runtime_config, is_load_runtime_data_required):
    setup_logging(is_testing=True)

    """Set up the runtime database for testing."""
    log.info("Setting up runtime database for tests")

    # Set up cache manager
    CacheManager.setup_cache(runtime_config)

    # Set up database
    try:
        await RuntimeDatabaseManager.setup_database(runtime_config)
    except DatabaseError:
        log.error("Error in runtime database test setup")
        pytest.fail("Error in runtime database test setup")

    # Ensure database helper is initialized
    assert RuntimeDatabaseManager.runtime_database_helper is not None, "Database helper not initialized"

    # Drop and recreate tables (excluding role tables)
    await RuntimeDatabaseManager.runtime_database_helper.drop_tables(ALL_RUNTIME_DATABASE_TABLE_NAMES)
    await RuntimeDatabaseManager.runtime_database_helper.create_tables(ALL_RUNTIME_DATABASE_TABLE_NAMES)

    if is_load_runtime_data_required:
        log.info("Loading test data into runtime database")

        # Load test data
        await load_runtime_tables(
            runtime_config.DATA_DIR,
            "testinsert",
        )

    log.info("Runtime database setup complete")
    yield

    # Teardown
    log.info("Tearing down runtime database")
    await RuntimeDatabaseManager.shutdown_database()
    CacheManager.shutdown_cache()
    shutdown_logging()


@pytest_asyncio.fixture
async def runtime_transaction_fixture():
    """Provide an async transaction context for individual tests."""
    async with runtime_transaction() as session:
        yield session
        # Transaction will automatically rollback if not committed


@pytest_asyncio.fixture
async def reset_runtime_database():
    """Reset runtime database tables to start test with empty tables."""
    if RuntimeDatabaseManager.runtime_database_helper is not None:
        log.info("Resetting runtime database tables")

        await RuntimeDatabaseManager.runtime_database_helper.drop_tables(ALL_RUNTIME_DATABASE_TABLE_NAMES)
        await RuntimeDatabaseManager.runtime_database_helper.create_tables(ALL_RUNTIME_DATABASE_TABLE_NAMES)

    yield
    # Function-level cleanup if needed can go here


# @pytest_asyncio.fixture(scope="class")
# async def app_setup(offline_database_setup, runtime_database_setup):
#     offline_config = PostgresTestConfiguration()
#     runtime_config = SqliteTestConfiguration()
#
#     await offline_database_setup(offline_config, True)
#     await runtime_database_setup(runtime_config, True)

