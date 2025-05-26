import unittest

from musigree.config import (
    SqliteTestConfiguration,
    PostgresTestConfiguration,
    PostgresProductionConfiguration,
)
from musigree.constants import DatabaseType


class TestConfiguration(unittest.TestCase):
    def test_SqliteTestConfiguration(self):
        config = SqliteTestConfiguration()
        self.assertIsNotNone(config)

    def test_SqliteTestConfiguration_get_testing(self):
        config = SqliteTestConfiguration()
        self.assertTrue(config.TESTING)

    def test_SqliteTestConfiguration_get_database(self):
        config = SqliteTestConfiguration()
        self.assertEqual(DatabaseType.SQLITE, config.DATABASE)

    # def test_SqliteTestConfiguration_set(self):
    #     config = SqliteTestConfiguration()
    #     with self.assertRaises(ValidationError) as ctx:
    #         config.TESTING = False
    #     self.assertEqual(
    #         "'SqliteTestConfiguration' object does not support item assignment",
    #         str(ctx.exception),
    #     )

    def test_PostgresTestConfiguration(self):
        config = PostgresTestConfiguration()
        self.assertIsNotNone(config)

    def test_PostgresTestConfiguration_get_testing(self):
        config = PostgresTestConfiguration()
        self.assertTrue(config.TESTING)

    def test_PostgresTestConfiguration_get_database(self):
        config = PostgresTestConfiguration()
        self.assertEqual(DatabaseType.POSTGRES, config.DATABASE)

    # def test_PostgresTestConfiguration_set(self):
    #     config = PostgresTestConfiguration()
    #     with self.assertRaises(ValidationError) as ctx:
    #         config.TESTING = False
    #     self.assertEqual(
    #         "'PostgresTestConfiguration' object does not support item assignment",
    #         str(ctx.exception),
    #     )

    def test_PostgresProductionConfiguration(self):
        config = PostgresProductionConfiguration()
        self.assertIsNotNone(config)

    def test_PostgresProductionConfiguration_get_testing(self):
        config = PostgresProductionConfiguration()
        self.assertFalse(config.TESTING)

    def test_PostgresProductionConfiguration_get_database(self):
        config = PostgresProductionConfiguration()
        self.assertEqual(DatabaseType.POSTGRES, config.DATABASE)

    # def test_PostgresProductionConfiguration_set(self):
    #     config = PostgresProductionConfiguration()
    #     with self.assertRaises(ValidationError) as ctx:
    #         config.TESTING = False
    #     self.assertEqual(
    #         "'PostgresProductionConfiguration' object does not support item assignment",
    #         str(ctx.exception),
    #     )
