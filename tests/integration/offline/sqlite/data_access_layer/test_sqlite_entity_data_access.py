from tests.integration.offline.data_access_layer.test_entity_data_access import (
    TestEntityDataAccess,
)
from tests.integration.offline.sqlite.sqlite_database_test_case import (
    SqliteDatabaseTestCase,
)


class TestSqliteEntityDataAccess(SqliteDatabaseTestCase, TestEntityDataAccess):
    # Run all tests in TestEntityDataAccess
    pass
