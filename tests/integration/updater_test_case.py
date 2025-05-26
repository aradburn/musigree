import logging

from musigree.config import PostgresTestConfiguration
from musigree.loader.loader import load_offline_test_tables
from tests.integration.offline.database.offline_database_test_case import (
    OfflineDatabaseTestCase,
)

log = logging.getLogger(__name__)


class UpdaterTestCase(OfflineDatabaseTestCase):
    @classmethod
    def setUpClass(cls):
        OfflineDatabaseTestCase.offline_config = PostgresTestConfiguration()
        super().setUpClass()

        # Run the test update process
        load_offline_test_tables(
            OfflineDatabaseTestCase.offline_config.DATA_DIR,
            "testupdate",
            is_bulk_inserts=False,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def setUp(self):
        log.info("-------------------------------------------------------------------")
        log.info(f"Test {self.id()}")
