from musigree.library.fields.entity_type import EntityType
from musigree.runtime.data_access_layer.runtime_entity_data_access import (
    RuntimeEntityDataAccess,
)
from musigree.runtime.runtime_database.runtime_entity_repository import (
    RuntimeEntityRepository,
)
from musigree.runtime.runtime_database.runtime_transaction import runtime_transaction
from tests.integration.runtime.database.runtime_database_test_case import (
    RuntimeDatabaseTestCase,
)


class TestRuntimeEntityDataAccess(RuntimeDatabaseTestCase):

    def test_get_id_by_entity_type_and_entity_name(self):
        entity_type = EntityType.ARTIST
        entity_name = "Joker, The (3)"
        with runtime_transaction():
            entity_repository = RuntimeEntityRepository()
            result = RuntimeEntityDataAccess.get_id_by_entity_type_and_entity_name(
                entity_repository, entity_type, entity_name
            )

        # THEN
        expected = 8526
        self.assertEqual(expected, result)
