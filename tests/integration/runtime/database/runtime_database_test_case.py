import logging

from sqlalchemy.exc import DatabaseError

from musigree.config import (
    Configuration,
)
from musigree.loader.loader import load_runtime_test_tables
from musigree.runtime.runtime_database_manager import RuntimeDatabaseManager
from tests.integration.offline.database.offline_database_test_case import (
    OfflineDatabaseTestCase,
)

log = logging.getLogger(__name__)


class RuntimeDatabaseTestCase(OfflineDatabaseTestCase):
    runtime_config: Configuration | None = None

    # noinspection PyPep8Naming
    def __init__(self, methodName="runTest"):
        ignore_test_prefixes = (
            "TestRuntimeDatabase",
            "TestRuntimeEntity",
            "TestRuntimeRelation",
            "TestRuntimeRole",
        )
        if self.__class__.__name__.startswith(ignore_test_prefixes):
            # don't run these tests in the abstract base implementation
            methodName = "runTestIgnoreInBaseClass"
            # methodName = "runNoTestsInBaseClass"
        super().__init__(methodName)

    def runTestIgnoreInBaseClass(self):
        pass

    @classmethod
    def setUpClass(cls):
        print("RuntimeDatabaseTestCase setUpClass")
        super().setUpClass()

        log.debug("RuntimeDatabaseTestCase setUpClass")

        if RuntimeDatabaseTestCase.runtime_config is None:
            return

        try:
            RuntimeDatabaseManager.setup_database(cls.runtime_config)
        except DatabaseError:
            log.error("Error in runtime database setup")
            # noinspection PyTypeChecker
            cls.fail(cls, "Error in runtime database test setup")

        data_directory = RuntimeDatabaseTestCase.runtime_config.DATA_DIR
        load_runtime_test_tables(data_directory)

        # TODO - was Load the tables
        # TransferManager.transfer_all()
        # RuntimeDatabaseManager.runtime_database_helper.load_tables()

        print("Done RuntimeDatabaseTestCase setUpClass")

    @classmethod
    def tearDownClass(cls):
        log.info(f"RuntimeDatabaseTestCase tearDownClass: {cls.__name__}")
        # release resources
        if RuntimeDatabaseTestCase.runtime_config is not None:
            RuntimeDatabaseManager.shutdown_database()
        super().tearDownClass()

    # def setUp(self):
    #     log.info("-------------------------------------------------------------------")
    #     log.info(f"Test {self.id()}")
