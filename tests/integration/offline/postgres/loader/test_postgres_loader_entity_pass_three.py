from tests.integration.offline.loader.test_loader_entity_pass_three import (
    TestLoaderEntityPassThree,
)
from tests.integration.offline.postgres.postgres_database_test_case import (
    PostgresDatabaseTestCase,
)


class TestPostgresLoaderEntityPassThree(
    PostgresDatabaseTestCase, TestLoaderEntityPassThree
):
    # Run all tests in TestLoaderEntityPassThree
    pass
