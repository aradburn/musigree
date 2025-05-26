from tests.integration.offline.database.test_database_relation import (
    TestDatabaseRelation,
)
from tests.integration.offline.sqlite.sqlite_database_test_case import (
    SqliteDatabaseTestCase,
)


class TestSqliteDatabaseRelation(SqliteDatabaseTestCase, TestDatabaseRelation):
    # Run all tests in TestDatabaseRelation
    pass
