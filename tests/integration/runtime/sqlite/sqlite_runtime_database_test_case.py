import logging

from musigree.config import SqliteTestConfiguration
from tests.integration.offline.database.offline_database_test_case import (
    OfflineDatabaseTestCase,
)
from tests.integration.runtime.database.runtime_database_test_case import (
    RuntimeDatabaseTestCase,
)

log = logging.getLogger(__name__)


class SqliteRuntimeDatabaseTestCase(RuntimeDatabaseTestCase):
    @classmethod
    def setUpClass(cls):
        OfflineDatabaseTestCase.offline_config = SqliteTestConfiguration()
        RuntimeDatabaseTestCase.runtime_config = SqliteTestConfiguration()
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
