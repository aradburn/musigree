from tests.integration.runtime.data_access_layer.test_runtime_entity_search import (
    TestRuntimeEntitySearch,
)
from tests.integration.runtime.sqlite.sqlite_runtime_database_test_case import (
    SqliteRuntimeDatabaseTestCase,
)


class TestSqliteRuntimeEntitySearch(
    SqliteRuntimeDatabaseTestCase, TestRuntimeEntitySearch
):
    # Run all tests in TestRuntimeEntitySearch
    pass
