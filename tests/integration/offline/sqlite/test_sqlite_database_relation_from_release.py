from tests.integration.offline.domain.test_database_relation_from_release import (
    TestDatabaseRelationFromRelease,
)
from tests.integration.offline.sqlite.sqlite_database_test_case import (
    SqliteDatabaseTestCase,
)


class TestSqliteDatabaseRelationFromRelease(
    SqliteDatabaseTestCase, TestDatabaseRelationFromRelease
):
    # Run all tests in TestDatabaseRelationFromRelease
    pass
