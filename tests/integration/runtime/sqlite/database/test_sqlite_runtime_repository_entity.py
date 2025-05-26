from tests.integration.runtime.database.test_runtime_repository_entity import (
    TestRuntimeRepositoryEntity,
)
from tests.integration.runtime.sqlite.sqlite_runtime_repository_test_case import (
    SqliteRuntimeRepositoryTestCase,
)


class TestSqliteRuntimeRepositoryEntity(
    SqliteRuntimeRepositoryTestCase, TestRuntimeRepositoryEntity
):
    # Run all tests in TestRuntimeRepositoryEntity
    pass
