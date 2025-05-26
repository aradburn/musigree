from tests.integration.offline.database.test_repository_metadata import (
    TestRepositoryMetadata,
)
from tests.integration.offline.sqlite.sqlite_repository_test_case import (
    SqliteRepositoryTestCase,
)


class TestSqliteRepositoryMetadata(SqliteRepositoryTestCase, TestRepositoryMetadata):
    # Run all tests in TestRepositoryMetadata
    pass
