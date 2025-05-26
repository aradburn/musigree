from tests.integration.offline.loader.test_loader_entity_pass_one import (
    TestLoaderEntityPassOne,
)
from tests.integration.offline.sqlite.sqlite_database_test_case import (
    SqliteDatabaseTestCase,
)


class TestSqliteLoaderEntityPassOne(SqliteDatabaseTestCase, TestLoaderEntityPassOne):
    # Run all tests in TestLoaderEntityPassOne
    pass
