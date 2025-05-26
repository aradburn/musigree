from tests.integration.offline.database.test_database_release import (
    TestDatabaseRelease,
)
from tests.integration.offline.sqlite.sqlite_database_test_case import (
    SqliteDatabaseTestCase,
)


class TestSqliteDatabaseRelease(SqliteDatabaseTestCase, TestDatabaseRelease):
    # Run all tests in TestDatabaseRelease
    pass
