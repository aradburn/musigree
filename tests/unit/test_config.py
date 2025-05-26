import unittest
import os

from musigree.config import (
    SqliteTestConfiguration,
    PostgresTestConfiguration,
    PostgresDevelopmentConfiguration,
)
from musigree.constants import DatabaseType, ThreadingModel, CacheType


class TestPydanticConfig(unittest.TestCase):

    def test_pydantic_sqlite_test_config(self):
        """Test that the new pydantic-settings classes work correctly."""
        config = SqliteTestConfiguration()

        # Test basic settings
        self.assertFalse(config.PRODUCTION)
        self.assertTrue(config.DEBUG)
        self.assertTrue(config.TESTING)
        self.assertEqual(config.DATABASE, DatabaseType.SQLITE)
        self.assertEqual(config.THREADING_MODEL, ThreadingModel.THREAD)
        self.assertEqual(config.CACHE_TYPE, CacheType.MEMORY)

        # Test SQLite-specific settings
        self.assertTrue(
            "musigree_offline_" in str(config.SQLITE_OFFLINE_DATABASE_NAME)
        )
        self.assertTrue(
            "musigree_runtime_" in str(config.SQLITE_RUNTIME_DATABASE_NAME)
        )

        # Test that the DB names contain the random string
        self.assertTrue("_test.db" in str(config.SQLITE_OFFLINE_DATABASE_NAME))
        self.assertTrue("_test.db" in str(config.SQLITE_RUNTIME_DATABASE_NAME))

    def test_pydantic_postgres_test_config(self):
        """Test that the new pydantic-settings PostgresTestConfig works correctly."""
        config = PostgresTestConfiguration()

        self.assertFalse(config.PRODUCTION)
        self.assertTrue(config.DEBUG)
        self.assertTrue(config.TESTING)
        self.assertEqual(config.DATABASE, DatabaseType.POSTGRES)
        self.assertEqual(config.THREADING_MODEL, ThreadingModel.PROCESS)
        self.assertEqual(config.CACHE_TYPE, CacheType.MEMORY)

        # Test PostgreSQL-specific settings
        self.assertEqual(
            config.POSTGRES_OFFLINE_DATABASE_NAME, "test_offline_musigree"
        )
        self.assertEqual(
            config.POSTGRES_RUNTIME_DATABASE_NAME, "test_runtime_musigree"
        )

    def test_pydantic_postgres_dev_config(self):
        """Test that the new pydantic-settings PostgresDevelopmentConfig works correctly."""
        config = PostgresDevelopmentConfiguration()

        self.assertFalse(config.PRODUCTION)
        self.assertTrue(config.DEBUG)
        self.assertFalse(config.TESTING)
        self.assertEqual(config.DATABASE, DatabaseType.POSTGRES)
        self.assertEqual(config.THREADING_MODEL, ThreadingModel.PROCESS)
        self.assertEqual(config.CACHE_TYPE, CacheType.REDIS)

        # Test PostgreSQL-specific settings
        self.assertEqual(config.POSTGRES_DATABASE_USERNAME, "musigree")
        self.assertEqual(config.POSTGRES_DATABASE_PASSWORD, "musigree")
        self.assertEqual(config.POSTGRES_DATABASE_HOST, "localhost")
        self.assertEqual(config.POSTGRES_DATABASE_PORT, 5432)
        self.assertEqual(config.POSTGRES_OFFLINE_DATABASE_NAME, "musigree_dev")

    def test_pydantic_env_override(self):
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
            self.assertEqual(config.POSTGRES_DATABASE_USERNAME, "test_user")
            self.assertEqual(config.POSTGRES_DATABASE_PASSWORD, "test_pass")

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
