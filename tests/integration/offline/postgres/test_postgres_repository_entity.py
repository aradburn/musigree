from tests.integration.offline.database.test_repository_entity import (
    TestRepositoryEntity,
)
from tests.integration.offline.postgres.postgres_repository_test_case import (
    PostgresRepositoryTestCase,
)


class TestPostgresRepositoryEntity(PostgresRepositoryTestCase, TestRepositoryEntity):
    # Run all tests in TestRepositoryEntity
    pass
