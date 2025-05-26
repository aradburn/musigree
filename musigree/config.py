import logging
import os
from pathlib import Path
from typing import Optional

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

# KEYS for backward compatibility
# PRODUCTION_KEY = "PRODUCTION"
# DEBUG_KEY = "DEBUG"
# TESTING_KEY = "TESTING"
# DATA_DIR_KEY = "DATA_DIR"
# DATABASE_KEY = "DATABASE"
# POSTGRES_DATABASE_USERNAME_KEY = "POSTGRES_DATABASE_USERNAME"
# POSTGRES_DATABASE_PASSWORD_KEY = "POSTGRES_DATABASE_PASSWORD"
# POSTGRES_DATABASE_HOST_KEY = "POSTGRES_DATABASE_HOST"
# POSTGRES_DATABASE_PORT_KEY = "POSTGRES_DATABASE_PORT"
# POSTGRES_OFFLINE_DATABASE_NAME_KEY = "POSTGRES_OFFLINE_DATABASE_NAME"
# POSTGRES_RUNTIME_DATABASE_NAME_KEY = "POSTGRES_RUNTIME_DATABASE_NAME"
# POSTGRES_ROOT_KEY = "POSTGRES_ROOT"
# POSTGRES_OFFLINE_DATA_KEY = "POSTGRES_OFFLINE_DATA"
# POSTGRES_RUNTIME_DATA_KEY = "POSTGRES_RUNTIME_DATA"
# APPLICATION_ROOT_KEY = "APPLICATION_ROOT"
# THREADING_MODEL_KEY = "THREADING_MODEL"
# CACHE_TYPE_KEY = "CACHE_TYPE"
# SQLITE_OFFLINE_DATABASE_NAME_KEY = "SQLITE_OFFLINE_DATABASE_NAME"
# SQLITE_RUNTIME_DATABASE_NAME_KEY = "SQLITE_RUNTIME_DATABASE_NAME"


class Configuration(BaseSettings):
    """Base configuration class using pydantic-settings."""

    model_config = SettingsConfigDict(
        env_prefix="MUSIGREE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        strict=True,
        # frozen=True,
    )

    # Common settings
    PRODUCTION: bool = False
    DEBUG: bool = True
    TESTING: bool = False
    DATA_DIR: Path = ROOT_DIR / "musigree" / "data"
    DATABASE: DatabaseType = DatabaseType.SQLITE
    APPLICATION_ROOT: str = "http://localhost"
    THREADING_MODEL: ThreadingModel = ThreadingModel.THREAD
    CACHE_TYPE: CacheType = CacheType.FILESYSTEM

    # PostgreSQL settings
    POSTGRES_DATABASE_USERNAME: Optional[str] = None
    POSTGRES_DATABASE_PASSWORD: Optional[str] = None
    POSTGRES_DATABASE_HOST: Optional[str] = None
    POSTGRES_DATABASE_PORT: Optional[int] = None
    POSTGRES_OFFLINE_DATABASE_NAME: Optional[str] = None
    POSTGRES_RUNTIME_DATABASE_NAME: Optional[str] = None
    POSTGRES_ROOT: Optional[str] = None
    POSTGRES_OFFLINE_DATA: Optional[Path] = None
    POSTGRES_RUNTIME_DATA: Optional[Path] = None

    # SQLite settings
    SQLITE_OFFLINE_DATABASE_NAME: Optional[Path] = None
    SQLITE_RUNTIME_DATABASE_NAME: Optional[Path] = None


class PostgresProductionConfiguration(Configuration):
    """Production configuration for PostgreSQL database."""

    PRODUCTION: bool = True
    DEBUG: bool = True
    TESTING: bool = False
    DATA_DIR: Path = ROOT_DIR / "musigree" / "data"
    DATABASE: DatabaseType = DatabaseType.POSTGRES
    APPLICATION_ROOT: str = "https://musigree.azurewebsites.net/"
    THREADING_MODEL: ThreadingModel = ThreadingModel.PROCESS
    CACHE_TYPE: CacheType = CacheType.FILESYSTEM

    # Use default None values for tests, but prefer env vars when available
    # (modify Field default with default_factory to use os.getenv at runtime)
    POSTGRES_DATABASE_USERNAME: Optional[str] = Field(
        default=None,
        description="PostgreSQL database username from environment variable",
    )
    POSTGRES_DATABASE_PASSWORD: Optional[str] = Field(
        default=None,
        description="PostgreSQL database password from environment variable",
    )
    POSTGRES_DATABASE_HOST: Optional[str] = Field(
        default=None, description="PostgreSQL database host from environment variable"
    )
    POSTGRES_DATABASE_PORT: Optional[int] = Field(
        default=None, description="PostgreSQL database port from environment variable"
    )
    POSTGRES_OFFLINE_DATABASE_NAME: Optional[str] = Field(
        default=None,
        description="PostgreSQL offline database name from environment variable",
    )

    def model_post_init(self, __context):
        """Set values from environment variables if not provided in constructor."""
        if self.POSTGRES_DATABASE_USERNAME is None:
            self.POSTGRES_DATABASE_USERNAME = os.getenv("MUSIGREE_DATABASE_USERNAME")
        if self.POSTGRES_DATABASE_PASSWORD is None:
            self.POSTGRES_DATABASE_PASSWORD = os.getenv("MUSIGREE_DATABASE_PASSWORD")
        if self.POSTGRES_DATABASE_HOST is None:
            self.POSTGRES_DATABASE_HOST = os.getenv("MUSIGREE_DATABASE_HOST")
        if self.POSTGRES_DATABASE_PORT is None:
            port_str = os.getenv("MUSIGREE_DATABASE_PORT")
            self.POSTGRES_DATABASE_PORT = int(port_str) if port_str else None
        if self.POSTGRES_OFFLINE_DATABASE_NAME is None:
            self.POSTGRES_OFFLINE_DATABASE_NAME = os.getenv("MUSIGREE_DATABASE_NAME")


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
    POSTGRES_ROOT: str = "/usr/lib/postgresql/17"

    def __init__(self, **data):
        # Generate random strings before init
        self._offline_random_string = utils.get_random_string(5)
        self._runtime_random_string = utils.get_random_string(5)

        # Dynamically set the database names
        data["POSTGRES_OFFLINE_DATA"] = (
            TEST_DIR
            / OFFLINE_DATABASE
            / f"musigree_offline_{self._offline_random_string}_test"
        )
        data["POSTGRES_RUNTIME_DATA"] = (
            TEST_DIR
            / RUNTIME_DATABASE
            / f"musigree_runtime_{self._runtime_random_string}_test"
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
    CACHE_TYPE: CacheType = CacheType.FILESYSTEM

    # SQLite settings
    SQLITE_OFFLINE_DATABASE_NAME: Path = (
        ROOT_DIR / OFFLINE_DATABASE / "musigree_offline_prod.db"
    )
    SQLITE_RUNTIME_DATABASE_NAME: Path = (
        ROOT_DIR / RUNTIME_DATABASE / "musigree_runtime_prod.db"
    )


class SqliteDevelopmentConfiguration(Configuration):
    """Development configuration for SQLite database."""

    PRODUCTION: bool = False
    DEBUG: bool = True
    TESTING: bool = False
    DATA_DIR: Path = ROOT_DIR / "musigree" / "data"
    DATABASE: DatabaseType = DatabaseType.SQLITE
    APPLICATION_ROOT: str = "http://localhost"
    THREADING_MODEL: ThreadingModel = ThreadingModel.THREAD
    CACHE_TYPE: CacheType = CacheType.FILESYSTEM

    # SQLite settings
    SQLITE_OFFLINE_DATABASE_NAME: Path = (
        ROOT_DIR / OFFLINE_DATABASE / "musigree_offline_dev.db"
    )
    SQLITE_RUNTIME_DATABASE_NAME: Path = (
        ROOT_DIR / RUNTIME_DATABASE / "musigree_runtime_dev.db"
    )


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
    _offline_random_string: Optional[str] = None
    _runtime_random_string: Optional[str] = None

    # Generate placeholders to satisfy pydantic validation
    SQLITE_OFFLINE_DATABASE_NAME: Path = None
    SQLITE_RUNTIME_DATABASE_NAME: Path = None

    def __init__(self, **data):
        # Generate random strings before init
        self._offline_random_string = utils.get_random_string(5)
        self._runtime_random_string = utils.get_random_string(5)

        # Dynamically set the database names
        data["SQLITE_OFFLINE_DATABASE_NAME"] = (
            TEST_DIR
            / OFFLINE_DATABASE
            / f"musigree_offline_{self._offline_random_string}_test.db"
        )
        data["SQLITE_RUNTIME_DATABASE_NAME"] = (
            TEST_DIR
            / RUNTIME_DATABASE
            / f"musigree_runtime_{self._runtime_random_string}_test.db"
        )

        super().__init__(**data)


# Compatibility layer for backward compatibility

# class Configuration:
#     """Base compatibility class for backward compatibility with the old Configuration class."""
#     def __init__(self, data: Dict[str, Any]):
#         config_data = {
#             key: value
#             for key, value in data.items()
#             if not key.startswith("_") and not callable(value)
#         }
#         self._data = config_data
#
#     def __getitem__(self, key):
#         return self._data[key]
#
#     def __len__(self):
#         return len(self._data)
#
#     def __iter__(self):
#         return iter(self._data)
#
#
# class PostgresProductionConfiguration(Configuration):
#     """Compatibility class for PostgresProductionConfiguration."""
#     PRODUCTION = True
#     DEBUG = True
#     TESTING = False
#     DATA_DIR = ROOT_DIR / "musigree" / "data"
#     DATABASE = DatabaseType.POSTGRES
#     POSTGRES_DATABASE_USERNAME = os.getenv("MUSIGREE_DATABASE_USERNAME")
#     POSTGRES_DATABASE_PASSWORD = os.getenv("MUSIGREE_DATABASE_PASSWORD")
#     POSTGRES_DATABASE_HOST = os.getenv("MUSIGREE_DATABASE_HOST")
#     POSTGRES_DATABASE_PORT = os.getenv("MUSIGREE_DATABASE_PORT")
#     POSTGRES_OFFLINE_DATABASE_NAME = os.getenv("MUSIGREE_DATABASE_NAME")
#     APPLICATION_ROOT = "https://musigree.azurewebsites.net/"
#     THREADING_MODEL = ThreadingModel.PROCESS
#     CACHE_TYPE = CacheType.FILESYSTEM
#
#     def __init__(self):
#         # Use the new pydantic config
#         config = PostgresProductionConfig()
#         # Convert to dict and pass to base Configuration
#         super().__init__(config.model_dump())
#
#
# class PostgresDevelopmentConfiguration(Configuration):
#     """Compatibility class for PostgresDevelopmentConfiguration."""
#     PRODUCTION = False
#     DEBUG = True
#     TESTING = False
#     DATA_DIR = ROOT_DIR / "musigree" / "data"
#     DATABASE = DatabaseType.POSTGRES
#     POSTGRES_DATABASE_USERNAME = "musigree"
#     POSTGRES_DATABASE_PASSWORD = "musigree"
#     POSTGRES_DATABASE_HOST = "localhost"
#     POSTGRES_DATABASE_PORT = 5432
#     POSTGRES_OFFLINE_DATABASE_NAME = "musigree_dev"
#     APPLICATION_ROOT = "http://localhost"
#     THREADING_MODEL = ThreadingModel.PROCESS
#     CACHE_TYPE = CacheType.REDIS
#
#     def __init__(self):
#         # Use the new pydantic config
#         config = PostgresDevelopmentConfig()
#         # Convert to dict and pass to base Configuration
#         super().__init__(config.model_dump())
#
#
# class PostgresTestConfiguration(Configuration):
#     """Compatibility class for PostgresTestConfiguration."""
#     PRODUCTION = False
#     DEBUG = True
#     TESTING = True
#     DATA_DIR = TEST_DIR / "data"
#     DATABASE = DatabaseType.POSTGRES
#     POSTGRES_OFFLINE_DATABASE_NAME = "test_offline_musigree"
#     POSTGRES_RUNTIME_DATABASE_NAME = "test_runtime_musigree"
#     POSTGRES_ROOT = "/usr/lib/postgresql/17"
#     POSTGRES_OFFLINE_DATA = TEST_DIR / OFFLINE_DATABASE
#     POSTGRES_RUNTIME_DATA = TEST_DIR / RUNTIME_DATABASE
#     APPLICATION_ROOT = "http://localhost"
#     THREADING_MODEL = ThreadingModel.PROCESS
#     CACHE_TYPE = CacheType.MEMORY
#
#     def __init__(self):
#         # Use the new pydantic config
#         config = PostgresTestConfig()
#         # Convert to dict and pass to base Configuration
#         super().__init__(config.model_dump())
#
#
# class SqliteProductionConfiguration(Configuration):
#     """Compatibility class for SqliteProductionConfiguration."""
#     PRODUCTION = True
#     DEBUG = False
#     TESTING = False
#     DATA_DIR = ROOT_DIR / "musigree" / "data"
#     DATABASE = DatabaseType.SQLITE
#     SQLITE_OFFLINE_DATABASE_NAME = (
#         ROOT_DIR / OFFLINE_DATABASE / "musigree_offline_prod.db"
#     )
#     SQLITE_RUNTIME_DATABASE_NAME = (
#         ROOT_DIR / RUNTIME_DATABASE / "musigree_runtime_prod.db"
#     )
#     APPLICATION_ROOT = "http://localhost"
#     THREADING_MODEL = ThreadingModel.THREAD
#     CACHE_TYPE = CacheType.FILESYSTEM
#
#     def __init__(self):
#         # Use the new pydantic config
#         config = SqliteProductionConfig()
#         # Convert to dict and pass to base Configuration
#         super().__init__(config.model_dump())
#
#
# class SqliteDevelopmentConfiguration(Configuration):
#     """Compatibility class for SqliteDevelopmentConfiguration."""
#     PRODUCTION = False
#     DEBUG = True
#     TESTING = False
#     DATA_DIR = ROOT_DIR / "musigree" / "data"
#     DATABASE = DatabaseType.SQLITE
#     SQLITE_OFFLINE_DATABASE_NAME = (
#         ROOT_DIR / OFFLINE_DATABASE / "musigree_offline_dev.db"
#     )
#     SQLITE_RUNTIME_DATABASE_NAME = (
#         ROOT_DIR / RUNTIME_DATABASE / "musigree_runtime_dev.db"
#     )
#     APPLICATION_ROOT = "http://localhost"
#     THREADING_MODEL = ThreadingModel.THREAD
#     CACHE_TYPE = CacheType.FILESYSTEM
#
#     def __init__(self):
#         # Use the new pydantic config
#         config = SqliteDevelopmentConfig()
#         # Convert to dict and pass to base Configuration
#         super().__init__(config.model_dump())
#
#
# class SqliteTestConfiguration(Configuration):
#     """Compatibility class for SqliteTestConfiguration."""
#     PRODUCTION = False
#     DEBUG = True
#     TESTING = True
#     DATA_DIR = TEST_DIR / "data"
#     DATABASE = DatabaseType.SQLITE
#     APPLICATION_ROOT = "http://localhost"
#     THREADING_MODEL = ThreadingModel.THREAD
#     CACHE_TYPE = CacheType.MEMORY
#
#     def __init__(self):
#         # Use the new pydantic config
#         config = SqliteTestConfig()
#         # Convert to dict and pass to base Configuration
#         super().__init__(config.model_dump())
