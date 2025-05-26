import logging

from sqlalchemy.exc import DatabaseError

from musigree.constants import ALL_OFFLINE_DATABASE_TABLE_NAMES
from musigree.offline.offline_database_manager import OfflineDatabaseManager
from tests.integration.offline.database.offline_database_test_case import (
    OfflineDatabaseTestCase,
)

log = logging.getLogger(__name__)


class OfflineRepositoryTestCase(OfflineDatabaseTestCase):

    @classmethod
    def setUpClass(cls):
        log.info(f"RepositoryTestCase setUpClass: {cls.__name__}")
        super().setUpClass()
        cls.resetDB()

    @classmethod
    def tearDownClass(cls):
        log.info(f"RepositoryTestCase tearDownClass: {cls.__name__}")
        # release resources
        super().tearDownClass()

    @classmethod
    def resetDB(cls):
        if OfflineDatabaseManager.offline_database_helper is not None:
            log.info(f"Reset offline database tables: {cls.__name__}")
            try:
                OfflineDatabaseManager.offline_database_helper.drop_tables(
                    ALL_OFFLINE_DATABASE_TABLE_NAMES
                )
                OfflineDatabaseManager.offline_database_helper.create_tables(
                    ALL_OFFLINE_DATABASE_TABLE_NAMES
                )
            except DatabaseError:
                log.error("Error in RepositoryTestCase database reset")
