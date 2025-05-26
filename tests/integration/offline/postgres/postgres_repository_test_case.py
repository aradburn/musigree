import logging

from musigree.config import PostgresTestConfiguration
from tests.integration.offline.database.offline_database_test_case import (
    OfflineDatabaseTestCase,
)
from tests.integration.offline.database.offline_repository_test_case import (
    OfflineRepositoryTestCase,
)

log = logging.getLogger(__name__)


class PostgresRepositoryTestCase(OfflineRepositoryTestCase):
    @classmethod
    def setUpClass(cls):
        OfflineDatabaseTestCase.offline_config = PostgresTestConfiguration()
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
