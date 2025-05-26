from tests.integration.offline.loader.test_loader_role import (
    TestLoaderRole,
)
from tests.integration.offline.sqlite.sqlite_repository_test_case import (
    SqliteRepositoryTestCase,
)


class TestSqliteLoaderRole(SqliteRepositoryTestCase, TestLoaderRole):
    # Run all tests in TestLoaderRole
    pass
