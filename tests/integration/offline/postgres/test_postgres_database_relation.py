from tests.integration.offline.database.test_database_relation import (
    TestDatabaseRelation,
)
from tests.integration.offline.postgres.postgres_database_test_case import (
    PostgresDatabaseTestCase,
)


class TestPostgresDatabaseRelation(PostgresDatabaseTestCase, TestDatabaseRelation):
    # Run all tests in TestDatabaseRelation
    pass
