from tests.integration.runtime.database.test_runtime_repository_entity import (
    TestRuntimeRepositoryEntity,
)
from tests.integration.runtime.postgres.postgres_runtime_repository_test_case import (
    PostgresRuntimeRepositoryTestCase,
)


class TestPostgresRuntimeRepositoryEntity(
    PostgresRuntimeRepositoryTestCase, TestRuntimeRepositoryEntity
):
    # Run all tests in TestRuntimeRepositoryEntity
    pass
