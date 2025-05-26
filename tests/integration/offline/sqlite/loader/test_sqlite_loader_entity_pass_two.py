from tests.integration.offline.loader.test_loader_entity_pass_two import (
    TestLoaderEntityPassTwo,
)
from tests.integration.offline.sqlite.sqlite_database_test_case import (
    SqliteDatabaseTestCase,
)


class TestSqliteLoaderEntityPassTwo(SqliteDatabaseTestCase, TestLoaderEntityPassTwo):
    # Run all tests in TestLoaderEntityPassTwo
    pass
