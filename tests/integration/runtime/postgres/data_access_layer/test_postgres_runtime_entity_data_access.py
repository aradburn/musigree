from tests.integration.runtime.data_access_layer.test_runtime_entity_data_access import (
    TestRuntimeEntityDataAccess,
)
from tests.integration.runtime.postgres.postgres_runtime_database_test_case import (
    PostgresRuntimeDatabaseTestCase,
)


class TestPostgresRuntimeEntityDataAccess(
    PostgresRuntimeDatabaseTestCase, TestRuntimeEntityDataAccess
):
    # Run all tests in TestRuntimeEntityDataAccess
    pass
