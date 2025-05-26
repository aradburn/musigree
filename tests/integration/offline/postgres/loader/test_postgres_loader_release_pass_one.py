from tests.integration.offline.loader.test_loader_release_pass_one import (
    TestLoaderReleasePassOne,
)
from tests.integration.offline.postgres.postgres_database_test_case import (
    PostgresDatabaseTestCase,
)


class TestPostgresLoaderReleasePassOne(
    PostgresDatabaseTestCase, TestLoaderReleasePassOne
):
    # Run all tests in TestLoaderReleasePassOne
    pass
