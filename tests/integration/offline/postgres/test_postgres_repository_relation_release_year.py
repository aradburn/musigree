from tests.integration.offline.database.test_repository_relation_release_year import (
    TestRepositoryRelationReleaseYear,
)
from tests.integration.offline.postgres.postgres_repository_test_case import (
    PostgresRepositoryTestCase,
)


class TestPostgresRepositoryRelationReleaseYear(
    PostgresRepositoryTestCase, TestRepositoryRelationReleaseYear
):
    # Run all tests in TestRepositoryRelationReleaseYear
    pass
