from tests.integration.offline.loader.test_loader_entity_pass_two import (
    TestLoaderEntityPassTwo,
)
from tests.integration.offline.postgres.postgres_database_test_case import (
    PostgresDatabaseTestCase,
)


class TestPostgresLoaderEntityPassTwo(
    PostgresDatabaseTestCase, TestLoaderEntityPassTwo
):
    # Run all tests in TestLoaderEntityPassTwo
    pass
