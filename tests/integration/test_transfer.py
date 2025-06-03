from musigree.offline.data_access_layer.release_data_access import ReleaseDataAccess
from musigree.offline.database.entity_repository import EntityRepository
from musigree.offline.database.relation_repository import RelationRepository
from musigree.offline.database.release_repository import ReleaseRepository
from musigree.offline.database.role_repository import RoleRepository
from musigree.runtime.runtime_database.country_repository import CountryRepository
from musigree.runtime.runtime_database.genre_repository import GenreRepository
from musigree.runtime.runtime_database.runtime_entity_repository import (
    RuntimeEntityRepository,
)
from musigree.runtime.runtime_database.runtime_relation_repository import (
    RuntimeRelationRepository,
)
from musigree.runtime.runtime_database.runtime_role_repository import (
    RuntimeRoleRepository,
)
from musigree.runtime.runtime_database.runtime_transaction import runtime_transaction
from musigree.runtime.runtime_database.style_repository import StyleRepository
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
        offline_entity_repository = EntityRepository()
        runtime_entity_repository = RuntimeEntityRepository()

        expected_count = offline_entity_repository.count()

        offline_release_repository = ReleaseRepository()
        entity_details_index = ReleaseDataAccess.create_entity_details_index(offline_release_repository)

        # WHEN
        TransferManager.transfer_entity(entity_details_index)

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

    def test_transfer_entity_details(self):
        # GIVEN
        runtime_country_repository = CountryRepository()
        runtime_genre_repository = GenreRepository()
        runtime_style_repository = StyleRepository()
        with runtime_transaction():
            actual_country_count = runtime_country_repository.count()
            actual_genre_count = runtime_genre_repository.count()
            actual_style_count = runtime_style_repository.count()
            self.assertEqual(0, actual_country_count)
            self.assertEqual(0, actual_genre_count)
            self.assertEqual(0, actual_style_count)

        offline_release_repository = ReleaseRepository()
        entity_details_index = ReleaseDataAccess.create_entity_details_index(offline_release_repository)

        # WHEN
        TransferManager.transfer_entity_details(entity_details_index)

        # THEN
        with runtime_transaction():
            actual_country_count = runtime_country_repository.count()
            actual_genre_count = runtime_genre_repository.count()
            actual_style_count = runtime_style_repository.count()

        expected_country_count = 30
        expected_genre_count = 15
        expected_style_count = 122

        self.assertEqual(expected_country_count, actual_country_count)
        self.assertEqual(expected_genre_count, actual_genre_count)
        self.assertEqual(expected_style_count, actual_style_count)