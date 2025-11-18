"""Tests for RelationRepository with async/await and pytest fixtures."""

from typing import AsyncGenerator

import pytest

from musigree import utils
from musigree.config import Configuration
from musigree.constants import DISCOGS_DATA
from musigree.library.fields.entity_id import to_entity_internal_id
from musigree.offline.data_access_layer.release_data_access import ReleaseDataAccess
from musigree.offline.database.offline_transaction import offline_transaction
from musigree.offline.database.release_repository import ReleaseRepository
from musigree.offline.loader.loader_utils import LoaderUtils
from musigree.offline.loader.parser_entity import ParserEntity
from musigree.runtime.runtime_database.runtime_entity_repository import (
    RuntimeEntityRepository,
)
from musigree.runtime.runtime_database.runtime_relation_repository import (
    RuntimeRelationRepository,
)
from musigree.runtime.runtime_database.runtime_transaction import runtime_transaction
from musigree.runtime.runtime_domain.entity import to_runtime_entity_dict, RuntimeEntity
from musigree.runtime.runtime_domain.relation import (
    RuntimeRelationInternal,
    RuntimeRelationUncommitted,
    RuntimeRelation,
)
from musigree.transfer.transfer_manager import TransferManager
from tests.conftest import AbstractDatabaseTest


@pytest.mark.parametrize("is_load_offline_data_required", [True], scope="class")
@pytest.mark.parametrize("is_load_runtime_data_required", [False], scope="class")
class TestRuntimeRepositoryRelation(AbstractDatabaseTest):
    @pytest.mark.asyncio
    async def test_create_relation(
        self,
        offline_database_setup: AsyncGenerator[None, None],
        runtime_database_setup: AsyncGenerator[None, None],
        offline_config: Configuration,
    ) -> None:
        """Test creating a relation in the repository.

        Args:
            runtime_database_setup: Pytest fixture for database setup.
            offline_config: Pytest fixture for configuration.
        """
        # GIVEN
        async with offline_transaction():
            offline_release_repository = ReleaseRepository()
            entity_details_index = await ReleaseDataAccess.create_entity_details_index(
                offline_release_repository
            )
        await TransferManager.transfer_role()

        discogs_data_directory = offline_config.DATA_DIR / DISCOGS_DATA

        iterator = LoaderUtils.get_iterator(
            discogs_data_directory,
            "artist",
            "testinsert",
        )
        entity_element_1 = next(iterator)
        entity_1 = ParserEntity().from_element(entity_element_1)
        entity_element_2 = next(iterator)
        entity_2 = ParserEntity().from_element(entity_element_2)

        runtime_entity_dict_1 = to_runtime_entity_dict(entity_details_index, entity_1)

        runtime_entity_dict_2 = to_runtime_entity_dict(entity_details_index, entity_2)
        runtime_entity_1 = RuntimeEntity.model_validate(runtime_entity_dict_1)
        runtime_entity_2 = RuntimeEntity.model_validate(runtime_entity_dict_2)

        # WHEN - Create entities first
        async with runtime_transaction():
            repository = RuntimeEntityRepository()
            created_entity_1 = await repository.create(runtime_entity_1)
            created_entity_2 = await repository.create(runtime_entity_2)

        id_1 = to_entity_internal_id(created_entity_1.entity_id, created_entity_1.entity_type)
        id_2 = to_entity_internal_id(created_entity_2.entity_id, created_entity_2.entity_type)
        relation = RuntimeRelationInternal(
            id=1,
            subject=id_1,
            object=id_2,
            role="Composed By",
            release_id=12,
            year=1999,
        )
        relation_dict = relation.model_dump()
        relation_dicts = [relation_dict]

        # WHEN - Create relation
        async with runtime_transaction():
            relation_repository = RuntimeRelationRepository()
            uncommitted_relations = RuntimeRelationUncommitted.from_dicts(relation_dicts)

            await relation_repository.create(uncommitted_relations[0])
            created_relations: list[RuntimeRelationInternal] = []
            async for created_relation_db in relation_repository.all():
                """Retrieve all created relations."""
                assert created_relation_db is not None, "Created relation db should not be None"
                created_relations.append(created_relation_db)

            created_relation = RuntimeRelation.from_relation_internals(created_relations)
            assert created_relation is not None, "Created relation should not be None"
            actual = utils.normalize_dict(created_relation.model_dump())

        # THEN
        expected_relation = RuntimeRelation(
            entity_one_id=created_entity_1.entity_id,
            entity_one_type=created_entity_1.entity_type,
            entity_two_id=created_entity_2.entity_id,
            entity_two_type=created_entity_2.entity_type,
            role="Composed By",
            releases={"12": 1999},
        )
        expected = utils.normalize_dict(expected_relation.model_dump())
        assert actual == expected
