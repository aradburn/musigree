import logging

from fastapi import FastAPI
from starlette.testclient import TestClient

from musigree.app.fastapi_app import create_app
from musigree.config import (
    PostgresTestConfiguration,
    SqliteTestConfiguration,
)
from musigree.constants import ALL_RUNTIME_DATABASE_TABLE_NAMES
from musigree.loader.loader import load_runtime_test_tables
from musigree.offline.offline_database_manager import OfflineDatabaseManager
from musigree.runtime.runtime_database_manager import RuntimeDatabaseManager
from tests.integration.offline.database.offline_database_test_case import (
    OfflineDatabaseTestCase,
)

log = logging.getLogger(__name__)


class AppTestCase(OfflineDatabaseTestCase):
    test_app: FastAPI = None
    client: TestClient = None

    @classmethod
    def setUpClass(cls):
        log.debug("AppTestCase setUpClass")

        OfflineDatabaseTestCase.offline_config = PostgresTestConfiguration()
        super().setUpClass()

        runtime_config = SqliteTestConfiguration()
        AppTestCase.test_app = create_app(runtime_config)

        # For testing, drop and recreate all tables
        RuntimeDatabaseManager.runtime_database_helper.drop_tables(
            ALL_RUNTIME_DATABASE_TABLE_NAMES
        )
        RuntimeDatabaseManager.runtime_database_helper.create_tables(
            ALL_RUNTIME_DATABASE_TABLE_NAMES
        )

        data_directory = OfflineDatabaseTestCase.offline_config.DATA_DIR
        load_runtime_test_tables(data_directory)

        # TODO - was Load the tables
        # TransferManager.transfer_all()
        # RuntimeDatabaseManager.runtime_database_helper.load_tables()

        # Use the FastAPI TestClient for testing
        AppTestCase.client = TestClient(AppTestCase.test_app)
        log.debug("AppTestCase setUpClass done")

    @classmethod
    def tearDownClass(cls):
        if OfflineDatabaseTestCase.offline_config is not None:
            OfflineDatabaseManager.shutdown_database()
        # shutdown_application()
