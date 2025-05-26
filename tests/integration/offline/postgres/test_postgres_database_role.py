from tests.integration.offline.database.test_database_role import TestDatabaseRole
from tests.integration.offline.postgres.postgres_database_test_case import (
    PostgresDatabaseTestCase,
)


class TestPostgresDatabaseRole(PostgresDatabaseTestCase, TestDatabaseRole):
    # Run all tests in TestDatabaseRole
    pass
