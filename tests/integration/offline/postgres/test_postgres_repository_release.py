from tests.integration.offline.database.test_repository_release import (
    TestRepositoryRelease,
)
from tests.integration.offline.postgres.postgres_repository_test_case import (
    PostgresRepositoryTestCase,
)


class TestPostgresRepositoryRelease(PostgresRepositoryTestCase, TestRepositoryRelease):
    # Run all tests in TestRepositoryRelease
    pass
