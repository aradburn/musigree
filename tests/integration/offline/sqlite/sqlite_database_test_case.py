import logging

from musigree.config import SqliteTestConfiguration
from tests.integration.offline.database.offline_database_test_case import (
    OfflineDatabaseTestCase,
)

log = logging.getLogger(__name__)


class SqliteDatabaseTestCase(OfflineDatabaseTestCase):
    @classmethod
    def setUpClass(cls):
        OfflineDatabaseTestCase.offline_config = SqliteTestConfiguration()
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
