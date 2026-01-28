from typing import AsyncGenerator

import pytest

from musigree.offline.offline_database.offline_transaction import offline_transaction
from musigree.offline.offline_database.release_repository import ReleaseRepository
from tests.conftest import AbstractDatabaseTest


@pytest.mark.parametrize("is_load_offline_data_required", [True], scope="class")
class TestLoaderReleasePassOne(AbstractDatabaseTest):
    @pytest.mark.asyncio
    async def test_loader_release_pass_one(
        self, offline_database_setup: AsyncGenerator[None, None], is_load_offline_data_required: bool
    ) -> None:
        # GIVEN

        # WHEN
        async with offline_transaction():
            actual = await ReleaseRepository().count()

        # THEN
        expected = 1700
        assert actual == expected
