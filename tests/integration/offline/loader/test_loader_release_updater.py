from typing import AsyncGenerator

import pytest

from musigree import utils
from musigree.exceptions import NotFoundError
from musigree.offline.database.offline_transaction import offline_transaction
from musigree.offline.database.release_repository import ReleaseRepository
from tests.conftest import AbstractDatabaseTest


@pytest.mark.parametrize("is_load_offline_data_required", [True], scope="class")
class TestLoaderReleaseUpdater(AbstractDatabaseTest):
    @pytest.mark.asyncio
    async def test_release_updated(
        self,
        offline_database_setup: AsyncGenerator[None, None],
        offline_database_update: AsyncGenerator[None, None],
    ) -> None:
        # GIVEN
        release_id = 157

        # WHEN
        async with offline_transaction():
            release_repository = ReleaseRepository()
            release = await release_repository.get_by_id(release_id)
            actual = utils.normalize_dict(release.model_dump(exclude={"id"}))

        # THEN
        expected_release = {
            "artists": [{"id": 41, "name": "Autechre"}, {"id": 49, "name": "Gescom"}],
            "companies": [],
            "country": "UK",
            "extra_artists": [
                {
                    "id": 445854,
                    "name": "Designers Republic, The (Test Update)",
                    "roles": [{"name": "Design"}],
                },
                {
                    "anv": "Brown",
                    "id": 300407,
                    "name": "Rob Brown (3)",
                    "roles": [{"name": "Producer"}],
                },
                {
                    "anv": "Booth",
                    "id": 42,
                    "name": "Sean Booth",
                    "roles": [{"name": "Producer"}],
                },
            ],
            "formats": [
                {
                    "descriptions": ['12"', "EP", "33 \u2153 RPM", "45 RPM"],
                    "name": "Vinyl",
                    "quantity": "1",
                }
            ],
            "genres": ["Electronic", "(Test Update)"],
            "identifiers": [
                {"description": None, "type": "Barcode", "value": "5 021603 054066"},
                {
                    "description": "Etching A",
                    "type": "Matrix / Runout",
                    "value": "WAP-54-A\u2081 MA.",
                },
                {
                    "description": "Etching B",
                    "type": "Matrix / Runout",
                    "value": "WAP-54-B\u2081 MA.",
                },
            ],
            "labels": [{"catalog_number": "WAP54", "id": 1000023528, "name": "Warp Records"}],
            "master_id": 1315,
            "notes": None,
            "release_date": "1994-09-03",
            "release_id": 157,
            "styles": ["Abstract", "IDM", "Experimental", "(Test Update)"],
            "title": "Anti EP",
            "tracklist": [
                {"position": "A1", "title": "Lost"},
                {"position": "A2", "title": "Djarum"},
                {"position": "B", "title": "Flutter"},
            ],
        }

        expected = utils.normalize_dict(expected_release)
        assert actual == expected

    @pytest.mark.asyncio
    async def test_release_not_updated(
        self,
        offline_database_setup: AsyncGenerator[None, None],
        offline_database_update: AsyncGenerator[None, None],
    ) -> None:
        # GIVEN
        release_id = 635

        # WHEN
        async with offline_transaction():
            release_repository = ReleaseRepository()
            release = await release_repository.get_by_id(release_id)
            actual = utils.normalize_dict(release.model_dump(exclude={"id"}))

        # THEN
        expected_release = {
            "artists": [{"id": 939, "name": "Higher Intelligence Agency, The"}],
            "companies": [],
            "country": "UK",
            "extra_artists": [
                {
                    "id": 939,
                    "name": "Higher Intelligence Agency, The",
                    "roles": [{"name": "Written-By"}],
                }
            ],
            "formats": [{"descriptions": ["EP"], "name": "CD", "quantity": "1"}],
            "genres": ["Electronic"],
            "identifiers": [
                {"description": None, "type": "Barcode", "value": "5 018524 066308"},
                {
                    "description": None,
                    "type": "Matrix / Runout",
                    "value": "DISCTRONICS S HIA 2 CD 01",
                },
            ],
            "labels": [{"catalog_number": "HIACD2", "id": 1000000233, "name": "Beyond"}],
            "master_id": 21103,
            "notes": None,
            "release_date": "1994-01-01",
            "release_id": 635,
            "styles": ["Techno", "Ambient"],
            "title": "Colour Reform",
            "tracklist": [
                {
                    "duration": "8:49",
                    "extra_artists": [
                        {
                            "id": 932,
                            "name": "A Positive Life",
                            "roles": [{"name": "Remix"}],
                        }
                    ],
                    "position": "1",
                    "title": "Universal Entity (Ketamine Entity Reformed By A Positive Life)",
                },
                {
                    "duration": "6:24",
                    "extra_artists": [{"id": 41, "name": "Autechre", "roles": [{"name": "Remix"}]}],
                    "position": "2",
                    "title": "Speech3 (Conoid Tone Reformed By Autechre)",
                },
                {
                    "duration": "8:30",
                    "extra_artists": [
                        {
                            "id": 379334,
                            "name": "Adrian Harrow",
                            "roles": [{"name": "Engineer"}],
                        },
                        {
                            "id": 953,
                            "name": "Irresistible Force, The",
                            "roles": [{"name": "Remix"}],
                        },
                    ],
                    "position": "3",
                    "title": "Speedlearn (Reformed By The Irresistible Force)",
                },
                {
                    "duration": "6:20",
                    "extra_artists": [
                        {"id": 954, "name": "Pentatonik", "roles": [{"name": "Remix"}]}
                    ],
                    "position": "4",
                    "title": "Alpha 1999 (Delta Reformed By Pentatonik)",
                },
            ],
        }

        expected = utils.normalize_dict(expected_release)
        assert actual == expected

    @pytest.mark.asyncio
    async def test_release_inserted(
        self,
        offline_database_setup: AsyncGenerator[None, None],
        offline_database_update: AsyncGenerator[None, None],
    ) -> None:
        # GIVEN
        release_id = 99999999

        # WHEN
        async with offline_transaction():
            release_repository = ReleaseRepository()
            release = await release_repository.get_by_id(release_id)
            actual = utils.normalize_dict(release.model_dump(exclude={"id"}))

        # THEN
        expected_release = {
            "artists": [
                {"id": 99999999, "name": "Test Artist"},
                {"id": 99999999, "name": "Test Artist"},
            ],
            "companies": [],
            "country": "UK",
            "extra_artists": [
                {
                    "id": 445854,
                    "name": "Designers Republic, The (Test Update)",
                    "roles": [{"name": "Design"}],
                },
                {
                    "anv": "Brown",
                    "id": 300407,
                    "name": "Rob Brown (3)",
                    "roles": [{"name": "Producer"}],
                },
                {
                    "anv": "Booth",
                    "id": 42,
                    "name": "Sean Booth",
                    "roles": [{"name": "Producer"}],
                },
            ],
            "formats": [
                {
                    "descriptions": ['12"', "EP", "33 \u2153 RPM", "45 RPM"],
                    "name": "Vinyl",
                    "quantity": "1",
                }
            ],
            "genres": ["Electronic", "(Test Update)"],
            "identifiers": [
                {"description": None, "type": "Barcode", "value": "5 021603 054066"},
                {
                    "description": "Etching A",
                    "type": "Matrix / Runout",
                    "value": "WAP-54-A\u2081 MA.",
                },
                {
                    "description": "Etching B",
                    "type": "Matrix / Runout",
                    "value": "WAP-54-B\u2081 MA.",
                },
            ],
            "labels": [
                {
                    "catalog_number": "TEST99999999",
                    "id": -2000000000,
                    "name": "Test Records",
                }
            ],
            "master_id": 99999999,
            "notes": None,
            "release_date": "1994-09-03",
            "release_id": 99999999,
            "styles": ["Abstract", "IDM", "Experimental", "(Test Update)"],
            "title": "Test EP",
            "tracklist": [
                {"position": "A1", "title": "Test"},
                {"position": "A2", "title": "Djarum"},
                {"position": "B", "title": "Flutter"},
            ],
        }

        expected = utils.normalize_dict(expected_release)
        assert actual == expected

    @pytest.mark.asyncio
    async def test_release_deleted(
        self,
        offline_database_setup: AsyncGenerator[None, None],
        offline_database_update: AsyncGenerator[None, None],
    ) -> None:
        # GIVEN
        release_id = 61930

        # WHEN
        async with offline_transaction():
            release_repository = ReleaseRepository()
            try:
                release = await release_repository.get_by_id(release_id)
            except NotFoundError:
                release = None

        # THEN
        assert release is None
