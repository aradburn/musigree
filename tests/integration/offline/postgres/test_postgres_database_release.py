from tests.integration.offline.database.test_database_release import (
    TestDatabaseRelease,
)
from tests.integration.offline.postgres.postgres_database_test_case import (
    PostgresDatabaseTestCase,
)


class TestPostgresDatabaseRelease(PostgresDatabaseTestCase, TestDatabaseRelease):
    # Run all tests in TestDatabaseRelease
    pass
