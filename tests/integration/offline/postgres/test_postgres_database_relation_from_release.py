from tests.integration.offline.domain.test_database_relation_from_release import (
    TestDatabaseRelationFromRelease,
)
from tests.integration.offline.postgres.postgres_database_test_case import (
    PostgresDatabaseTestCase,
)


class TestPostgresDatabaseRelationFromRelease(
    PostgresDatabaseTestCase, TestDatabaseRelationFromRelease
):
    # Run all tests in TestDatabaseRelationFromRelease
    pass
