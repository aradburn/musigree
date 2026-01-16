import logging
from pathlib import Path
from typing import Any

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from musigree import utils
from musigree.constants import (
    ROOT_DIR,
    OFFLINE_DATABASE,
    RUNTIME_DATABASE,
    TEST_DIR,
    DatabaseType,
    ThreadingModel,
    CacheType,
)

log = logging.getLogger(__name__)


class Configuration(BaseSettings):
    """Base configuration class using pydantic-settings."""

    model_config = SettingsConfigDict(
        extra="ignore",
        strict=True,
        # frozen=True,
    )

    # Common settings
    PRODUCTION: bool = False
    IS_READ_ONLY: bool = False
    DEBUG: bool = True
    TESTING: bool = False
    DATA_DIR: Path = ROOT_DIR / "musigree" / "data"
    DATABASE: DatabaseType = DatabaseType.SQLITE
    APPLICATION_ROOT: str = "http://localhost"
    THREADING_MODEL: ThreadingModel = ThreadingModel.THREAD
    CACHE_TYPE: CacheType = CacheType.MEMORY

    # PostgreSQL settings
    POSTGRES_DATABASE_USERNAME: str | None = None
    POSTGRES_DATABASE_PASSWORD: str | None = None
    POSTGRES_DATABASE_HOST: str | None = None
    POSTGRES_DATABASE_PORT: int | None = None
    POSTGRES_OFFLINE_DATABASE_NAME: str | None = None
    POSTGRES_RUNTIME_DATABASE_NAME: str | None = None
    POSTGRES_ROOT: str | None = None
    POSTGRES_OFFLINE_DATA: Path | None = None
    POSTGRES_RUNTIME_DATA: Path | None = None

    # SQLite settings
    SQLITE_OFFLINE_DATABASE_NAME: Path | None = None
    SQLITE_RUNTIME_DATABASE_NAME: Path | None = None

    # Redis settings
    REDIS_USERNAME: str | None = None
    REDIS_PASSWORD: str | None = None
    REDIS_HOST: str | None = None
    REDIS_PORT: int | None = None


class PostgresProductionConfiguration(Configuration):
    """Production configuration for PostgreSQL database."""

    PRODUCTION: bool = True
    DEBUG: bool = False
    TESTING: bool = False
    DATA_DIR: Path = ROOT_DIR / "musigree" / "data"
    DATABASE: DatabaseType = DatabaseType.POSTGRES
    APPLICATION_ROOT: str = "https://musigree.azurewebsites.net/"
    THREADING_MODEL: ThreadingModel = ThreadingModel.PROCESS
    CACHE_TYPE: CacheType = CacheType.REDIS

    # Use default None values for tests, but prefer env vars when available
    # (modify Field default with default_factory to use os.getenv at runtime)
    POSTGRES_DATABASE_USERNAME: str | None = Field(
        default=None,
        description="PostgreSQL database username from environment variable",
    )
    POSTGRES_DATABASE_PASSWORD: str | None = Field(
        default=None,
        description="PostgreSQL database password from environment variable",
    )
    POSTGRES_DATABASE_HOST: str | None = Field(
        default=None, description="PostgreSQL database host from environment variable"
    )
    POSTGRES_DATABASE_PORT: int | None = Field(
        default=None, description="PostgreSQL database port from environment variable"
    )
    POSTGRES_OFFLINE_DATABASE_NAME: str | None = Field(
        default=None,
        description="PostgreSQL offline database name from environment variable",
    )
    REDIS_USERNAME: str | None = Field(
        default=None,
        description="Redis username from environment variable",
    )
    REDIS_PASSWORD: str | None = Field(
        default=None,
        description="Redis password from environment variable",
    )
    REDIS_HOST: str | None = Field(default=None, description="Redis host from environment variable")
    REDIS_PORT: int | None = Field(default=None, description="Redis port from environment variable")


class PostgresDevelopmentConfiguration(Configuration):
    """Development configuration for PostgreSQL database."""

    PRODUCTION: bool = False
    DEBUG: bool = True
    TESTING: bool = False
    DATA_DIR: Path = ROOT_DIR / "musigree" / "data"
    DATABASE: DatabaseType = DatabaseType.POSTGRES
    APPLICATION_ROOT: str = "http://localhost"
    THREADING_MODEL: ThreadingModel = ThreadingModel.PROCESS
    CACHE_TYPE: CacheType = CacheType.REDIS

    # PostgreSQL settings with defaults
    POSTGRES_DATABASE_USERNAME: str = "musigree"
    POSTGRES_DATABASE_PASSWORD: str = "musigree"
    POSTGRES_DATABASE_HOST: str = "localhost"
    POSTGRES_DATABASE_PORT: int = 5432
    POSTGRES_OFFLINE_DATABASE_NAME: str = "musigree_dev"
    REDIS_USERNAME: str = ""
    REDIS_PASSWORD: str = ""
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379


class PostgresTestConfiguration(Configuration):
    """Test configuration for PostgreSQL database."""

    PRODUCTION: bool = False
    DEBUG: bool = True
    TESTING: bool = True
    DATA_DIR: Path = TEST_DIR / "data"
    DATABASE: DatabaseType = DatabaseType.POSTGRES
    APPLICATION_ROOT: str = "http://localhost"
    THREADING_MODEL: ThreadingModel = ThreadingModel.PROCESS
    CACHE_TYPE: CacheType = CacheType.MEMORY

    # PostgreSQL test settings
    POSTGRES_OFFLINE_DATABASE_NAME: str = "test_offline_musigree"
    POSTGRES_RUNTIME_DATABASE_NAME: str = "test_runtime_musigree"
    POSTGRES_ROOT: str = "/usr/lib/postgresql/18"

    def __init__(self, **data: Any) -> None:
        # Generate random strings before init
        self._offline_random_string = utils.get_random_string(5)
        self._runtime_random_string = utils.get_random_string(5)

        # Dynamically set the database names
        data["POSTGRES_OFFLINE_DATA"] = (
            TEST_DIR / OFFLINE_DATABASE / f"musigree_offline_{self._offline_random_string}_test"
        )
        data["POSTGRES_RUNTIME_DATA"] = (
            TEST_DIR / RUNTIME_DATABASE / f"musigree_runtime_{self._runtime_random_string}_test"
        )

        super().__init__(**data)


class SqliteProductionConfiguration(Configuration):
    """Production configuration for SQLite database."""

    PRODUCTION: bool = True
    DEBUG: bool = False
    TESTING: bool = False
    DATA_DIR: Path = ROOT_DIR / "musigree" / "data"
    DATABASE: DatabaseType = DatabaseType.SQLITE
    APPLICATION_ROOT: str = "http://localhost"
    THREADING_MODEL: ThreadingModel = ThreadingModel.THREAD
    CACHE_TYPE: CacheType = CacheType.REDIS

    # SQLite settings
    SQLITE_OFFLINE_DATABASE_NAME: Path = ROOT_DIR / OFFLINE_DATABASE / "musigree_offline_prod.db"
    SQLITE_RUNTIME_DATABASE_NAME: Path = ROOT_DIR / RUNTIME_DATABASE / "musigree_runtime_prod.db"

    # Redis cache
    REDIS_USERNAME: str | None = Field(
        default=None,
        description="Redis username from environment variable",
    )
    REDIS_PASSWORD: str | None = Field(
        default=None,
        description="Redis password from environment variable",
    )
    REDIS_HOST: str | None = Field(default=None, description="Redis host from environment variable")
    REDIS_PORT: int | None = Field(default=None, description="Redis port from environment variable")


class SqliteDevelopmentConfiguration(Configuration):
    """Development configuration for SQLite database."""

    PRODUCTION: bool = False
    DEBUG: bool = True
    TESTING: bool = False
    DATA_DIR: Path = ROOT_DIR / "musigree" / "data"
    DATABASE: DatabaseType = DatabaseType.SQLITE
    APPLICATION_ROOT: str = "http://localhost"
    THREADING_MODEL: ThreadingModel = ThreadingModel.THREAD
    CACHE_TYPE: CacheType = CacheType.REDIS

    # SQLite settings
    SQLITE_OFFLINE_DATABASE_NAME: Path = ROOT_DIR / OFFLINE_DATABASE / "musigree_offline_dev.db"
    SQLITE_RUNTIME_DATABASE_NAME: Path = ROOT_DIR / RUNTIME_DATABASE / "musigree_runtime_dev.db"

    # Redis cache settings
    REDIS_USERNAME: str = ""
    REDIS_PASSWORD: str = ""
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379


class SqliteTestConfiguration(Configuration):
    """Test configuration for SQLite database."""

    PRODUCTION: bool = False
    DEBUG: bool = True
    TESTING: bool = True
    DATA_DIR: Path = TEST_DIR / "data"
    DATABASE: DatabaseType = DatabaseType.SQLITE
    APPLICATION_ROOT: str = "http://localhost"
    THREADING_MODEL: ThreadingModel = ThreadingModel.THREAD
    CACHE_TYPE: CacheType = CacheType.MEMORY

    # Cache generated random strings
    _offline_random_string: str | None = None
    _runtime_random_string: str | None = None

    # Generate placeholders to satisfy pydantic validation
    SQLITE_OFFLINE_DATABASE_NAME: Path | None = None
    SQLITE_RUNTIME_DATABASE_NAME: Path | None = None

    def __init__(self, **data: Any) -> None:
        # Generate random strings before init
        self._offline_random_string = utils.get_random_string(5)
        self._runtime_random_string = utils.get_random_string(5)

        # Dynamically set the database names
        data["SQLITE_OFFLINE_DATABASE_NAME"] = (
            TEST_DIR / OFFLINE_DATABASE / f"musigree_offline_{self._offline_random_string}_test.db"
        )
        data["SQLITE_RUNTIME_DATABASE_NAME"] = (
            TEST_DIR / RUNTIME_DATABASE / f"musigree_runtime_{self._runtime_random_string}_test.db"
        )

        super().__init__(**data)


class PostgresReadOnlyProductionConfiguration(PostgresProductionConfiguration):
    IS_READ_ONLY: bool = True


class PostgresReadOnlyDevelopmentConfiguration(PostgresDevelopmentConfiguration):
    IS_READ_ONLY: bool = True


class PostgresReadOnlyTestConfiguration(PostgresTestConfiguration):
    IS_READ_ONLY: bool = True


class SqliteReadOnlyProductionConfiguration(SqliteProductionConfiguration):
    IS_READ_ONLY: bool = True


class SqliteReadOnlyDevelopmentConfiguration(SqliteDevelopmentConfiguration):
    IS_READ_ONLY: bool = True


class SqliteReadOnlyTestConfiguration(SqliteTestConfiguration):
    IS_READ_ONLY: bool = True
