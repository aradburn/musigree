from tests.integration.offline.database.test_repository_relation import (
    TestRepositoryRelation,
)
from tests.integration.offline.sqlite.sqlite_repository_test_case import (
    SqliteRepositoryTestCase,
)


class TestSqliteRepositoryRelation(SqliteRepositoryTestCase, TestRepositoryRelation):
    # Run all tests in TestRepositoryRelation
    pass
