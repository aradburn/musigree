from tests.integration.offline.loader.test_loader_entity_details import (
    TestLoaderEntityDetails,
)
from tests.integration.offline.postgres.postgres_database_test_case import (
    PostgresDatabaseTestCase,
)


class TestPostgresLoaderEntityDetails(
    PostgresDatabaseTestCase, TestLoaderEntityDetails
):
    # Run all tests in TestLoaderEntityDetails
    pass
