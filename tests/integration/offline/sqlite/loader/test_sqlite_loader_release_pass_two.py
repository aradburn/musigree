from tests.integration.offline.loader.test_loader_release_pass_two import (
    TestLoaderReleasePassTwo,
)
from tests.integration.offline.sqlite.sqlite_database_test_case import (
    SqliteDatabaseTestCase,
)


class TestSqliteLoaderReleasePassTwo(SqliteDatabaseTestCase, TestLoaderReleasePassTwo):
    # Run all tests in TestLoaderReleasePassTwo
    pass
