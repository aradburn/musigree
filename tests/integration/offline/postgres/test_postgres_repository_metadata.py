from tests.integration.offline.database.test_repository_metadata import (
    TestRepositoryMetadata,
)
from tests.integration.offline.postgres.postgres_repository_test_case import (
    PostgresRepositoryTestCase,
)


class TestPostgresRepositoryMetadata(
    PostgresRepositoryTestCase, TestRepositoryMetadata
):
    # Run all tests in TestRepositoryMetadata
    pass
