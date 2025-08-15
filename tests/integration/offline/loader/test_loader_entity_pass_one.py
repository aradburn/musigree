import pytest

from musigree.offline.database.entity_repository import EntityRepository
from musigree.offline.database.offline_transaction import offline_transaction
from tests.conftest import AbstractDatabaseTest


@pytest.mark.parametrize("is_load_offline_data_required", [True], scope="class")
class TestLoaderEntityPassOne(AbstractDatabaseTest):
    @pytest.mark.asyncio
    async def test_loader_entity_pass_one(self, offline_database_setup):
        # GIVEN

        # WHEN
        async with offline_transaction():
            actual = await EntityRepository().count()

        # THEN
        expected = 6216
        assert actual == expected
