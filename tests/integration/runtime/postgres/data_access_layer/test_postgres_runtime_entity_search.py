from tests.integration.runtime.data_access_layer.test_runtime_entity_search import (
    TestRuntimeEntitySearch,
)
from tests.integration.runtime.postgres.postgres_runtime_database_test_case import (
    PostgresRuntimeDatabaseTestCase,
)


class TestPostgresRuntimeEntitySearch(
    PostgresRuntimeDatabaseTestCase, TestRuntimeEntitySearch
):
    # Run all tests in TestRuntimeEntitySearch
    pass
