import pytest

from musigree.offline.database.offline_transaction import offline_transaction
from musigree.offline.database.release_repository import ReleaseRepository
from tests.conftest import NotATest


@pytest.mark.parametrize("is_load_offline_data_required", [True], scope="class")
class TestLoaderReleasePassOne(NotATest):
    @pytest.mark.asyncio
    async def test_loader_release_pass_one(self, offline_database_setup):
        # GIVEN

        # WHEN
        async with offline_transaction():
            actual = await ReleaseRepository().count()

        # THEN
        expected = 1700
        assert actual == expected
