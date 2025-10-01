import os

from musigree.config import (
    SqliteTestConfiguration,
    PostgresTestConfiguration,
    PostgresDevelopmentConfiguration,
    PostgresProductionConfiguration,
)
from musigree.constants import DatabaseType, ThreadingModel, CacheType


def test_pydantic_sqlite_test_config() -> None:
    """Test that the new pydantic-settings classes work correctly."""
    config = SqliteTestConfiguration()

    # Test basic settings
    assert not config.PRODUCTION
    assert config.DEBUG
    assert config.TESTING
    assert config.DATABASE == DatabaseType.SQLITE
    assert config.THREADING_MODEL == ThreadingModel.THREAD
    assert config.CACHE_TYPE == CacheType.MEMORY

    # Test SQLite-specific settings
    assert "musigree_offline_" in str(config.SQLITE_OFFLINE_DATABASE_NAME)
    assert "musigree_runtime_" in str(config.SQLITE_RUNTIME_DATABASE_NAME)

    # Test that the DB names contain the random string
    assert "_test.db" in str(config.SQLITE_OFFLINE_DATABASE_NAME)
    assert "_test.db" in str(config.SQLITE_RUNTIME_DATABASE_NAME)


def test_pydantic_postgres_test_config() -> None:
    """Test that the new pydantic-settings PostgresTestConfig works correctly."""
    config = PostgresTestConfiguration()

    assert not config.PRODUCTION
    assert config.DEBUG
    assert config.TESTING
    assert config.DATABASE == DatabaseType.POSTGRES
    assert config.THREADING_MODEL == ThreadingModel.PROCESS
    assert config.CACHE_TYPE == CacheType.MEMORY

    # Test PostgreSQL-specific settings
    assert config.POSTGRES_OFFLINE_DATABASE_NAME == "test_offline_musigree"
    assert config.POSTGRES_RUNTIME_DATABASE_NAME == "test_runtime_musigree"


def test_pydantic_postgres_dev_config() -> None:
    """Test that the new pydantic-settings PostgresDevelopmentConfig works correctly."""
    config = PostgresDevelopmentConfiguration()

    assert not config.PRODUCTION
    assert config.DEBUG
    assert not config.TESTING
    assert config.DATABASE == DatabaseType.POSTGRES
    assert config.THREADING_MODEL == ThreadingModel.PROCESS
    assert config.CACHE_TYPE == CacheType.REDIS

    # Test PostgreSQL-specific settings
    assert config.POSTGRES_DATABASE_USERNAME == "musigree"
    assert config.POSTGRES_DATABASE_PASSWORD == "musigree"
    assert config.POSTGRES_DATABASE_HOST == "localhost"
    assert config.POSTGRES_DATABASE_PORT == 5432
    assert config.POSTGRES_OFFLINE_DATABASE_NAME == "musigree_dev"


def test_pydantic_env_override() -> None:
    """Test that environment variables can override the pydantic-settings."""
    # Save original env vars if they exist
    orig_username = os.environ.get("MUSIGREE_POSTGRES_DATABASE_USERNAME")
    orig_password = os.environ.get("MUSIGREE_POSTGRES_DATABASE_PASSWORD")

    try:
        # Set test environment variables
        os.environ["MUSIGREE_POSTGRES_DATABASE_USERNAME"] = "test_user"
        os.environ["MUSIGREE_POSTGRES_DATABASE_PASSWORD"] = "test_pass"

        # Create a new config instance to pick up the env vars
        config = PostgresDevelopmentConfiguration()

        # Test that env vars override defaults
        assert config.POSTGRES_DATABASE_USERNAME == "test_user"
        assert config.POSTGRES_DATABASE_PASSWORD == "test_pass"

    finally:
        # Restore original env vars or remove test ones
        if orig_username:
            os.environ["MUSIGREE_POSTGRES_DATABASE_USERNAME"] = orig_username
        else:
            os.environ.pop("MUSIGREE_POSTGRES_DATABASE_USERNAME", None)

        if orig_password:
            os.environ["MUSIGREE_POSTGRES_DATABASE_PASSWORD"] = orig_password
        else:
            os.environ.pop("MUSIGREE_POSTGRES_DATABASE_PASSWORD", None)


def test_sqlite_test_configuration() -> None:
    """Test that SqliteTestConfiguration can be instantiated."""
    config = SqliteTestConfiguration()
    assert config is not None


def test_sqlite_test_configuration_get_testing() -> None:
    """Test that SqliteTestConfiguration has TESTING set to True."""
    config = SqliteTestConfiguration()
    assert config.TESTING


def test_sqlite_test_configuration_get_database() -> None:
    """Test that SqliteTestConfiguration has DATABASE set to SQLITE."""
    config = SqliteTestConfiguration()
    assert config.DATABASE == DatabaseType.SQLITE


def test_postgres_production_configuration() -> None:
    """Test that PostgresProductionConfiguration can be instantiated."""
    config = PostgresProductionConfiguration()
    assert config is not None


def test_postgres_production_configuration_get_testing() -> None:
    """Test that PostgresProductionConfiguration has TESTING set to False."""
    config = PostgresProductionConfiguration()
    assert not config.TESTING


def test_postgres_production_configuration_get_database() -> None:
    """Test that PostgresProductionConfiguration has DATABASE set to POSTGRES."""
    config = PostgresProductionConfiguration()
    assert config.DATABASE == DatabaseType.POSTGRES
