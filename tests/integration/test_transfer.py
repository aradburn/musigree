from musigree.config import SqliteTestConfiguration
from musigree.offline.database.entity_repository import EntityRepository
from musigree.offline.database.relation_repository import RelationRepository
from musigree.offline.database.role_repository import RoleRepository
from musigree.runtime.runtime_database.runtime_entity_repository import (
    RuntimeEntityRepository,
)
from musigree.runtime.runtime_database.runtime_relation_repository import (
    RuntimeRelationRepository,
)
from musigree.runtime.runtime_database.runtime_role_repository import (
    RuntimeRoleRepository,
)
from musigree.transfer.transfer_manager import TransferManager
from tests.integration.transfer_test_case import TransferTestCase


class TestTransfer(TransferTestCase):
    def test_transfer_roles(self):
        # GIVEN
        offline_role_repository = RoleRepository()
        runtime_role_repository = RuntimeRoleRepository()

        expected_count = offline_role_repository.count()

        # WHEN
        TransferManager.transfer_role()

        # THEN
        actual_count = runtime_role_repository.count()

        self.assertEqual(expected_count, actual_count)

    def test_transfer_entities(self):
        # GIVEN
        config = SqliteTestConfiguration()
        data_directory = config.DATA_DIR
        offline_entity_repository = EntityRepository()
        runtime_entity_repository = RuntimeEntityRepository()

        expected_count = offline_entity_repository.count()

        # WHEN
        TransferManager.transfer_entity(data_directory)

        # THEN
        actual_count = runtime_entity_repository.count()

        self.assertEqual(expected_count, actual_count)

    def test_transfer_relations(self):
        # GIVEN
        offline_relation_repository = RelationRepository()
        runtime_relation_repository = RuntimeRelationRepository()

        expected_count = offline_relation_repository.count()

        # WHEN
        TransferManager.transfer_relation()

        # THEN
        actual_count = runtime_relation_repository.count()

        self.assertEqual(expected_count, actual_count)
