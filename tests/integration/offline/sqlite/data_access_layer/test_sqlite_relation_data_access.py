from tests.integration.offline.data_access_layer.test_relation_data_access import (
    TestRelationDataAccess,
)
from tests.integration.offline.sqlite.sqlite_database_test_case import (
    SqliteDatabaseTestCase,
)


class TestSqliteRelationDataAccess(SqliteDatabaseTestCase, TestRelationDataAccess):
    # Run all tests in TestRelationDataAccess
    pass
