from tests.integration.offline.database.test_database_entity import TestDatabaseEntity
from tests.integration.offline.sqlite.sqlite_database_test_case import (
    SqliteDatabaseTestCase,
)


class TestSqliteDatabaseEntity(SqliteDatabaseTestCase, TestDatabaseEntity):
    # Run all tests in TestDatabaseEntity
    pass
