import logging
from typing import AsyncGenerator

import pytest

from musigree import utils
from musigree.library.fields.entity_type import EntityType
from musigree.runtime.data_access_layer.runtime_entity_data_access import (
    RuntimeEntityDataAccess,
)
from musigree.runtime.runtime_database.runtime_entity_repository import (
    RuntimeEntityRepository,
)
from musigree.runtime.runtime_database.runtime_transaction import runtime_transaction
from tests.conftest import AbstractDatabaseTest

log = logging.getLogger(__name__)


@pytest.mark.parametrize("is_load_offline_data_required", [True], scope="class")
@pytest.mark.parametrize("is_load_runtime_data_required", [True], scope="class")
class TestRuntimeEntityStructuralRolesToRelations(AbstractDatabaseTest):
    @pytest.mark.asyncio
    async def test_01(
        self,
        offline_database_setup: AsyncGenerator[None, None],
        runtime_database_setup: AsyncGenerator[None, None],
    ) -> None:
        """Test structural roles to relations conversion."""
        entity_id = 430141
        entity_type = EntityType.ARTIST
        async with runtime_transaction():
            entity_repository = RuntimeEntityRepository()
            entity = await entity_repository.get_by_entity_id_and_entity_type(
                entity_id, entity_type
            )
            print(f"entity: {entity}")
            roles = ["Alias", "Member Of"]
            relations = RuntimeEntityDataAccess.structural_roles_to_relations(
                entity, roles=roles
            )
            print(f"relations: {relations}")
            actual = utils.normalize_dict(relations)
            print(f"actual: {actual}")

        expected_relations = {
            "artist-430141-member-of-artist-307": {
                "distance": None,
                "entity_one_id": 430141,
                "entity_one_type": EntityType.ARTIST,
                "entity_two_id": 307,
                "entity_two_type": EntityType.ARTIST,
                "id": 0,
                "releases": None,
                "role": "Member Of",
            },
            "artist-430141-member-of-artist-3603": {
                "distance": None,
                "entity_one_id": 430141,
                "entity_one_type": EntityType.ARTIST,
                "entity_two_id": 3603,
                "entity_two_type": EntityType.ARTIST,
                "id": 0,
                "releases": None,
                "role": "Member Of",
            },
        }
        expected = utils.normalize_dict(expected_relations)
        assert actual == expected
