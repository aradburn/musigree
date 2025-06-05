import logging
import unittest
from typing import Type

from sqlalchemy.exc import DatabaseError

from musigree.config import (
    Configuration,
)
from musigree.constants import ALL_RUNTIME_DATABASE_TABLE_NAMES
from musigree.library.cache.cache_manager import CacheManager
from musigree.logging_config import setup_logging, shutdown_logging
from musigree.runtime.data_access_layer.relation_grapher import RelationGrapher
from musigree.runtime.runtime_database_manager import RuntimeDatabaseManager

log = logging.getLogger(__name__)


class RuntimeRepositoryTestCase(unittest.TestCase):
    runtime_config: Configuration | None = None
    relation_grapher: Type[RelationGrapher] | None = None

    # noinspection PyPep8Naming
    def __init__(self, methodName="runTest"):
        ignore_test_prefixes = "TestRuntimeRepository"
        if self.__class__.__name__.startswith(ignore_test_prefixes):
            # don't run these tests in the abstract base implementation
            methodName = "runTestIgnoreInBaseClass"
            # methodName = "runNoTestsInBaseClass"
        super().__init__(methodName)

    def runTestIgnoreInBaseClass(self):
        pass

    @classmethod
    def setUpClass(cls):
        setup_logging(is_testing=True)
        if cls.runtime_config is not None:
            CacheManager.setup_cache(cls.runtime_config)
            table_names_to_drop = [table_name for table_name in ALL_RUNTIME_DATABASE_TABLE_NAMES if "role" not in table_name]

            try:
                RuntimeDatabaseManager.setup_database(cls.runtime_config)
            except DatabaseError:
                log.error("Error in database setup")
                RuntimeDatabaseManager.runtime_database_helper.drop_tables(table_names_to_drop)
            else:
                RuntimeDatabaseManager.runtime_database_helper.drop_tables(table_names_to_drop)
                RuntimeDatabaseManager.runtime_database_helper.create_tables(
                    ALL_RUNTIME_DATABASE_TABLE_NAMES
                )
                # Note: No data loading, empty repositories

    @classmethod
    def tearDownClass(cls):
        log.info(f"RepositoryTestCase tearDownClass: {cls.__name__}")
        # release resources
        if cls.runtime_config is not None:
            RuntimeDatabaseManager.shutdown_database()
            CacheManager.shutdown_cache()
            shutdown_logging()

    @classmethod
    def resetDB(cls):
        if RuntimeDatabaseManager.runtime_database_helper is not None:
            log.info(f"Reset runtime database tables: {cls.__name__}")
            RuntimeDatabaseManager.runtime_database_helper.drop_tables(
                ALL_RUNTIME_DATABASE_TABLE_NAMES
            )
            RuntimeDatabaseManager.runtime_database_helper.create_tables(
                ALL_RUNTIME_DATABASE_TABLE_NAMES
            )

    def setUp(self):
        log.info("-------------------------------------------------------------------")
        log.info(f"Test {self.id()}")
