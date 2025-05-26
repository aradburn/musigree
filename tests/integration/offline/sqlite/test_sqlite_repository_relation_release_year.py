from tests.integration.offline.database.test_repository_relation_release_year import (
    TestRepositoryRelationReleaseYear,
)
from tests.integration.offline.sqlite.sqlite_repository_test_case import (
    SqliteRepositoryTestCase,
)


class TestSqliteRepositoryRelationReleaseYear(
    SqliteRepositoryTestCase, TestRepositoryRelationReleaseYear
):
    # Run all tests in TestRepositoryRelationReleaseYear
    pass
