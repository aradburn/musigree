import logging

from musigree.config import PostgresTestConfiguration
from tests.integration.offline.database.offline_database_test_case import (
    OfflineDatabaseTestCase,
)
from tests.integration.runtime.database.runtime_database_test_case import (
    RuntimeDatabaseTestCase,
)

log = logging.getLogger(__name__)


class PostgresRuntimeDatabaseTestCase(RuntimeDatabaseTestCase):
    @classmethod
    def setUpClass(cls):
        print("PostgresRuntimeDatabaseTestCase setUpClass")
        OfflineDatabaseTestCase.offline_config = PostgresTestConfiguration()
        RuntimeDatabaseTestCase.runtime_config = PostgresTestConfiguration()
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
