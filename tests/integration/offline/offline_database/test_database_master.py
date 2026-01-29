from typing import AsyncGenerator

import pytest

from musigree import utils
from musigree.offline.offline_database.master_repository import MasterRepository
from musigree.offline.offline_database.offline_transaction import offline_transaction
from tests.conftest import AbstractDatabaseTest


@pytest.mark.parametrize("is_load_offline_data_required", [True], scope="class")
class TestDatabaseMaster(AbstractDatabaseTest):
    @pytest.mark.asyncio
    async def test_from_db_01(self, offline_database_setup: AsyncGenerator[None, None],
                              is_load_offline_data_required: bool) -> None:
        master_id = 37574
        async with offline_transaction():
            master_repository = MasterRepository()
            master = await master_repository.get_by_id(master_id)
            actual = utils.normalize_dict(master.model_dump())

        expected_master = {
            "artists": [
                {
                    "id": 0,
                    "name": "Various"
                }
            ],
            "data_quality": "Correct",
            "genres": [
                "Electronic"
            ],
            "images": None,
            "main_release": "54573",
            "master_id": 37574,
            "styles": [
                "Leftfield",
                "Breaks",
                "Trip Hop"
            ],
            "title": "Free The Funk - Compilation 3",
            "videos": None,
            "year": 1998
        }

        expected = utils.normalize_dict(expected_master)
        assert actual == expected

    @pytest.mark.asyncio
    async def test_from_db_02(self, offline_database_setup: AsyncGenerator[None, None],
                              is_load_offline_data_required: bool) -> None:
        master_id = 19671
        async with offline_transaction():
            master_repository = MasterRepository()
            master = await master_repository.get_by_id(master_id)
            actual = utils.normalize_dict(master.model_dump())

        expected_master = {
            "artists": [
                {
                    "id": 5783,
                    "name": "David Morley"
                }
            ],
            "data_quality": "Correct",
            "genres": [
                "Electronic"
            ],
            "images": None,
            "main_release": "18489",
            "master_id": 19671,
            "styles": [
                "Ambient"
            ],
            "title": "Stardancer EP",
            "videos": None,
            "year": 1996,
        }

        expected = utils.normalize_dict(expected_master)
        assert actual == expected
