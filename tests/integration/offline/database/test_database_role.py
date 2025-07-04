import pytest

from musigree import utils
from musigree.offline.database.role_repository import RoleRepository
from musigree.offline.database.offline_transaction import offline_transaction
from tests.conftest import NotATest


@pytest.mark.parametrize("is_load_offline_data_required", [True], scope="class")
class TestDatabaseRole(NotATest):
    @pytest.mark.asyncio
    async def test_from_db_01(self, offline_database_setup) -> None:
        name = "Acoustic Bass"
        async with offline_transaction():
            role_repository = RoleRepository()
            role = await role_repository.get_by_name(name)
            actual = utils.normalize_dict(role.model_dump(exclude={"id"}))

        expected_role = {
            "role_category": "Category.INSTRUMENTS",
            "role_category_name": "Instruments",
            "role_name": "Acoustic Bass",
            "role_subcategory": "Subcategory.STRINGED_INSTRUMENTS",
            "role_subcategory_name": "String Instruments",
        }
        expected = utils.normalize_dict(expected_role)
        assert actual == expected

    @pytest.mark.asyncio
    async def test_from_db_02(self, offline_database_setup) -> None:
        name = "Mezzo-Soprano Vocals"
        async with offline_transaction():
            role_repository = RoleRepository()
            role = await role_repository.get_by_name(name)
            actual = utils.normalize_dict(role.model_dump(exclude={"id"}))

        expected_role = {
            "role_category": "Category.VOCAL",
            "role_category_name": "Vocal",
            "role_name": "Mezzo-Soprano Vocals",
            "role_subcategory": "Subcategory.NONE",
            "role_subcategory_name": "None",
        }
        expected = utils.normalize_dict(expected_role)
        assert actual == expected
