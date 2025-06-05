import logging

from musigree.config import (
    SqliteTestConfiguration,
    Configuration,
)
from musigree.constants import ALL_RUNTIME_DATABASE_TABLE_NAMES
from musigree.exceptions import DatabaseError
from musigree.runtime.runtime_database_manager import RuntimeDatabaseManager
from tests.integration.offline.database.offline_database_test_case import (
    OfflineDatabaseTestCase,
)

log = logging.getLogger(__name__)


class TransferTestCase(OfflineDatabaseTestCase):
    runtime_config: Configuration | None = None

    @classmethod
    def setUpClass(cls):
        log.debug("TransferTestCase setUpClass")

        OfflineDatabaseTestCase.offline_config = SqliteTestConfiguration()
        super().setUpClass()

        TransferTestCase.runtime_config = SqliteTestConfiguration()

        if TransferTestCase.runtime_config is not None:
            try:
                RuntimeDatabaseManager.setup_database(TransferTestCase.runtime_config)
            except DatabaseError:
                log.error("Error in runtime database setup")

        # For testing, drop and recreate all tables
        RuntimeDatabaseManager.runtime_database_helper.drop_tables(
            ALL_RUNTIME_DATABASE_TABLE_NAMES
        )
        RuntimeDatabaseManager.runtime_database_helper.create_tables(
            ALL_RUNTIME_DATABASE_TABLE_NAMES
        )

    @classmethod
    def tearDownClass(cls):
        if TransferTestCase.runtime_config is not None:
            RuntimeDatabaseManager.shutdown_database()
        super().tearDownClass()
