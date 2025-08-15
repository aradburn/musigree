"""Tests for RelationRepository with async/await and pytest fixtures."""
import pytest

from musigree import utils
from musigree.constants import DISCOGS_DATA, ROLES_DATA, INSTRUMENTS_DATA
from musigree.library.fields.entity_id import to_entity_internal_id
from musigree.offline.data_access_layer.role_data_access import RoleDataAccess
from musigree.offline.database.entity_repository import EntityRepository
from musigree.offline.database.offline_transaction import offline_transaction
from musigree.offline.database.relation_repository import RelationRepository
from musigree.offline.domain.relation import (
    Relation,
    RelationInternal,
    RelationUncommitted,
)
from musigree.offline.loader.loader_role import LoaderRole
from musigree.offline.loader.loader_utils import LoaderUtils
from musigree.offline.loader.parser_entity import ParserEntity
from tests.conftest import AbstractDatabaseTest


@pytest.mark.parametrize("is_load_offline_data_required", [False], scope="class")
class TestRepositoryRelation(AbstractDatabaseTest):

    @pytest.mark.asyncio
    async def test_create_relation(self, offline_database_setup, offline_config) -> None:
        """Test creating a relation in the repository.

        Args:
            offline_database_setup: Pytest fixture for database setup.
            offline_config: Pytest fixture for configuration.
        """
        # GIVEN
        await LoaderRole.load_roles_into_database(
            offline_config.DATA_DIR / ROLES_DATA,
            offline_config.DATA_DIR / INSTRUMENTS_DATA,
        )
        await RoleDataAccess.load_all_roles_into_cache()
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

        # WHEN - Create entities first
        async with offline_transaction():
            repository = EntityRepository()
            created_entity_1 = await repository.create(entity_1)
            created_entity_2 = await repository.create(entity_2)

        id_1 = to_entity_internal_id(
            created_entity_1.entity_id, created_entity_1.entity_type
        )
        id_2 = to_entity_internal_id(
            created_entity_2.entity_id, created_entity_2.entity_type
        )
        relation = RelationInternal(
            id=1,
            subject=id_1,
            object=id_2,
            role="Composed By",
        )
        relation_dict = relation.model_dump()
        relation_dicts = [relation_dict]

        # WHEN - Create relation
        async with offline_transaction():
            relation_repository = RelationRepository()
            relations = RelationUncommitted.from_dicts(relation_dicts)

            await relation_repository.create(relations[0])
            async for created_relation_db in relation_repository.all():
                """Retrieve all created relations."""
                assert created_relation_db is not None, "Created relation db should not be None"
            created_relation = created_relation_db.to_domain().to_relation()
            assert created_relation is not None, "Created relation should not be None"
            actual = utils.normalize_dict(created_relation.model_dump())

        # THEN
        expected_relation = Relation(
            id=1,
            entity_one_id=created_entity_1.entity_id,
            entity_one_type=created_entity_1.entity_type,
            entity_two_id=created_entity_2.entity_id,
            entity_two_type=created_entity_2.entity_type,
            role="Composed By",
        )
        expected = utils.normalize_dict(expected_relation.model_dump())
        assert actual == expected
