from tests.integration.runtime.data_access_layer.test_runtime_entity_data_access import (
    TestRuntimeEntityDataAccess,
)
from tests.integration.runtime.sqlite.sqlite_runtime_database_test_case import (
    SqliteRuntimeDatabaseTestCase,
)


class TestSqliteRuntimeEntityDataAccess(
    SqliteRuntimeDatabaseTestCase, TestRuntimeEntityDataAccess
):
    # Run all tests in TestRuntimeEntityDataAccess
    pass
