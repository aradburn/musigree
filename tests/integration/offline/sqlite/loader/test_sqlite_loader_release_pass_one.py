from tests.integration.offline.loader.test_loader_release_pass_one import (
    TestLoaderReleasePassOne,
)
from tests.integration.offline.sqlite.sqlite_database_test_case import (
    SqliteDatabaseTestCase,
)


class TestSqliteLoaderReleasePassOne(SqliteDatabaseTestCase, TestLoaderReleasePassOne):
    # Run all tests in TestLoaderReleasePassOne
    pass
