from tests.integration.offline.database.test_database_entity import (
    TestDatabaseEntity,
)
from tests.integration.offline.postgres.postgres_database_test_case import (
    PostgresDatabaseTestCase,
)


class TestPostgresDatabaseEntity(PostgresDatabaseTestCase, TestDatabaseEntity):
    # Run all tests in TestDatabaseEntity
    pass
