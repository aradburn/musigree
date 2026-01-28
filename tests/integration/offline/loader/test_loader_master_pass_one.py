from typing import AsyncGenerator

import pytest

from musigree.offline.offline_database.master_repository import MasterRepository
from musigree.offline.offline_database.offline_transaction import offline_transaction
from tests.conftest import AbstractDatabaseTest


@pytest.mark.parametrize("is_load_offline_data_required", [True], scope="class")
class TestLoaderMasterPassOne(AbstractDatabaseTest):
    @pytest.mark.asyncio
    async def test_loader_master_pass_one(
        self, offline_database_setup: AsyncGenerator[None, None], is_load_offline_data_required: bool
    ) -> None:
        # GIVEN

        # WHEN
        async with offline_transaction():
            actual = await MasterRepository().count()

        # THEN
        expected = 396
        assert actual == expected
