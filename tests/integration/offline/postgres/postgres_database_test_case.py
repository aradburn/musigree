import logging

from musigree.config import PostgresTestConfiguration
from tests.integration.offline.database.offline_database_test_case import (
    OfflineDatabaseTestCase,
)

log = logging.getLogger(__name__)


class PostgresDatabaseTestCase(OfflineDatabaseTestCase):
    @classmethod
    def setUpClass(cls):
        OfflineDatabaseTestCase.offline_config = PostgresTestConfiguration()
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
