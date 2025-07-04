import pytest

from musigree.library.fields.entity_type import EntityType
from musigree.runtime.data_access_layer.runtime_entity_data_access import (
    RuntimeEntityDataAccess,
)
from musigree.runtime.runtime_database.runtime_entity_repository import (
    RuntimeEntityRepository,
)
from musigree.runtime.runtime_database.runtime_transaction import runtime_transaction
from tests.conftest import NotATest


@pytest.mark.parametrize("is_load_offline_data_required", [True], scope="class")
@pytest.mark.parametrize("is_load_runtime_data_required", [True], scope="class")
class TestRuntimeEntityDataAccess(NotATest):

    @pytest.mark.asyncio
    async def test_get_id_by_entity_type_and_entity_name(self, offline_database_setup, runtime_database_setup):
        """Test getting entity ID by type and name."""
        entity_type = EntityType.ARTIST
        entity_name = "Joker, The (3)"
        async with runtime_transaction():
            runtime_entity_repository = RuntimeEntityRepository()
            actual = await RuntimeEntityDataAccess.get_id_by_entity_type_and_entity_name(
                runtime_entity_repository, entity_type, entity_name
            )

        # THEN
        expected = 8526
        assert actual == expected
