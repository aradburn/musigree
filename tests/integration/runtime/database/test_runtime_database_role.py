from typing import AsyncGenerator

import pytest

from musigree import utils
from musigree.runtime.runtime_database.runtime_role_repository import (
    RuntimeRoleRepository,
)
from musigree.runtime.runtime_database.runtime_transaction import runtime_transaction
from tests.conftest import AbstractDatabaseTest


@pytest.mark.parametrize("is_load_offline_data_required", [True], scope="class")
@pytest.mark.parametrize("is_load_runtime_data_required", [True], scope="class")
class TestRuntimeDatabaseRole(AbstractDatabaseTest):
    @pytest.mark.asyncio
    async def test_from_db_01(
        self,
        offline_database_setup: AsyncGenerator[None, None],
        runtime_database_setup: AsyncGenerator[None, None],
    ) -> None:
        name = "Acoustic Bass"
        async with runtime_transaction():
            role_repository = RuntimeRoleRepository()
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
    async def test_from_db_02(
        self,
        offline_database_setup: AsyncGenerator[None, None],
        runtime_database_setup: AsyncGenerator[None, None],
    ) -> None:
        name = "Mezzo-Soprano Vocals"
        async with runtime_transaction():
            role_repository = RuntimeRoleRepository()
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
