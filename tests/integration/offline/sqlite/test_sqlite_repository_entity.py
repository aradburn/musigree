from tests.integration.offline.database.test_repository_entity import (
    TestRepositoryEntity,
)
from tests.integration.offline.sqlite.sqlite_repository_test_case import (
    SqliteRepositoryTestCase,
)


class TestSqliteRepositoryEntity(SqliteRepositoryTestCase, TestRepositoryEntity):
    # Run all tests in TestRepositoryEntity
    pass
