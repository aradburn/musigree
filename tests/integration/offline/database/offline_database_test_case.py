import logging
import unittest

from sqlalchemy.exc import DatabaseError

from musigree.config import (
    Configuration,
)
from musigree.constants import ALL_OFFLINE_DATABASE_TABLE_NAMES
from musigree.library.cache.cache_manager import CacheManager
from musigree.loader.loader import load_offline_test_tables
from musigree.logging_config import setup_logging
from musigree.offline.offline_database_manager import OfflineDatabaseManager

log = logging.getLogger(__name__)


class OfflineDatabaseTestCase(unittest.TestCase):
    offline_config: Configuration = None

    # noinspection PyPep8Naming
    def __init__(self, methodName="runTest"):
        ignore_test_prefixes = (
            "TestDatabase",
            "TestEntity",
            "TestRelease",
            "TestRelation",
            "TestRole",
            "TestRepository",
            "TestLoader",
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
        print("DatabaseTestCase setUpClass")
        setup_logging(is_testing=True)
        log.info(f"DatabaseTestCase setUpClass: {cls.__name__}")

        if OfflineDatabaseTestCase.offline_config is None:
            return

        CacheManager.setup_cache(OfflineDatabaseTestCase.offline_config)
        try:
            OfflineDatabaseManager.setup_database(
                OfflineDatabaseTestCase.offline_config
            )
        except DatabaseError:
            log.error("Error in offline database test setup")
            # noinspection PyTypeChecker
            cls.fail(cls, "Error in offline database test setup")

        table_names_to_drop = [table_name for table_name in ALL_OFFLINE_DATABASE_TABLE_NAMES if "role" not in table_name]
        OfflineDatabaseManager.offline_database_helper.drop_tables(table_names_to_drop)
        OfflineDatabaseManager.offline_database_helper.create_tables(ALL_OFFLINE_DATABASE_TABLE_NAMES)

        load_offline_test_tables(
            OfflineDatabaseTestCase.offline_config.DATA_DIR,
            "testinsert",
            is_bulk_inserts=True,
        )

        # TODO - was Load the tables
        # LoaderRole.load_roles_into_database()
        # OfflineDatabaseManager.offline_database_helper.load_tables(
        #     TEST_DATA_DIR, "testinsert", is_bulk_inserts=True
        # )
        # OfflineDatabaseManager.offline_database_helper.text_search_index = (
        #     TextSearchIndex.load_text_search_index_from_file(TEXT_SEARCH_PATH)
        # )

        print("Done OfflineDatabaseTestCase setUpClass")

    @classmethod
    def tearDownClass(cls):
        log.info(f"DatabaseTestCase tearDownClass: {cls.__name__}")
        # release resources
        if OfflineDatabaseTestCase.offline_config is not None:
            OfflineDatabaseManager.shutdown_database()
        CacheManager.shutdown_cache()
        # shutdown_logging()

    def setUp(self):
        log.info("-------------------------------------------------------------------")
        log.info(f"Test {self.id()}")
