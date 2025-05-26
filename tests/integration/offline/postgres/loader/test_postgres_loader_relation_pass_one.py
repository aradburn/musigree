from tests.integration.offline.loader.test_loader_relation_pass_one import (
    TestLoaderRelationPassOne,
)
from tests.integration.offline.postgres.postgres_database_test_case import (
    PostgresDatabaseTestCase,
)


class TestPostgresLoaderRelationPassOne(
    PostgresDatabaseTestCase, TestLoaderRelationPassOne
):
    # Run all tests in TestLoaderRelationPassOne
    pass
