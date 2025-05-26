from tests.integration.offline.loader.test_loader_entity_details import (
    TestLoaderEntityDetails,
)
from tests.integration.offline.sqlite.sqlite_database_test_case import (
    SqliteDatabaseTestCase,
)


class TestSqliteLoaderEntityDetails(SqliteDatabaseTestCase, TestLoaderEntityDetails):
    # Run all tests in TestLoaderEntityDetails
    pass
