from typing import AsyncGenerator

import pytest

from musigree import utils
from musigree.exceptions import NotFoundError
from musigree.offline.database.release_repository import ReleaseRepository
from musigree.offline.database.offline_transaction import offline_transaction
from tests.conftest import AbstractDatabaseTest


@pytest.mark.parametrize("is_load_offline_data_required", [True], scope="class")
class TestLoaderReleasePassTwo(AbstractDatabaseTest):
    @pytest.mark.asyncio
    async def test_loader_release_pass_two(
        self, offline_database_setup: AsyncGenerator[None, None], is_load_offline_data_required: bool
    ) -> None:
        # GIVEN

        # WHEN
        async with offline_transaction():
            actual = await ReleaseRepository().count()

        # THEN
        expected = 1700
        assert actual == expected

    @pytest.mark.asyncio
    async def test_release_157(self, offline_database_setup: AsyncGenerator[None, None],
                               is_load_offline_data_required: bool) -> None:
        # GIVEN
        release_id = 157

        # WHEN
        async with offline_transaction():
            release_repository = ReleaseRepository()
            release = await release_repository.get_by_id(release_id)
            actual = utils.normalize_dict(release.model_dump())

        # THEN
        expected_release = {
            "artists": [{"id": 41, "name": "Autechre"}],
            "companies": [],
            "country": "UK",
            "extra_artists": [
                {
                    "id": 445854,
                    "name": "Designers Republic, The",
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
            "genres": ["Electronic"],
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
            "styles": ["Abstract", "IDM", "Experimental"],
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
    async def test_release_635(self, offline_database_setup: AsyncGenerator[None, None],
                               is_load_offline_data_required: bool) -> None:
        # GIVEN
        release_id = 635

        # WHEN
        async with offline_transaction():
            release_repository = ReleaseRepository()
            release = await release_repository.get_by_id(release_id)
            actual = utils.normalize_dict(release.model_dump())

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
    async def test_release_99999999(
        self, offline_database_setup: AsyncGenerator[None, None], is_load_offline_data_required: bool
    ) -> None:
        # GIVEN
        release_id = 99999999

        # WHEN
        async with offline_transaction():
            release_repository = ReleaseRepository()
            try:
                release = await release_repository.get_by_id(release_id)
            except NotFoundError:
                release = None

        # THEN
        assert release is None, f"Release with ID {release_id} should not exist."

    @pytest.mark.asyncio
    async def test_release_61930(self, offline_database_setup: AsyncGenerator[None, None],
                                 is_load_offline_data_required: bool) -> None:
        # GIVEN
        release_id = 61930

        # WHEN
        async with offline_transaction():
            release_repository = ReleaseRepository()
            release = await release_repository.get_by_id(release_id)
            actual = utils.normalize_dict(release.model_dump())

        # THEN
        expected_release = {
            "artists": [
                {
                    "id": 7434,
                    "name": "Space Opera",
                },
            ],
            "companies": [
                {
                    "entity_type": 21,
                    "entity_type_name": "Published By",
                    "id": 1000276116,
                    "name": "Breaking Bones Music",
                },
                {
                    "entity_type": 21,
                    "entity_type_name": "Published By",
                    "id": 1000000245,
                    "name": "R & S Records",
                },
                {
                    "entity_type": 21,
                    "entity_type_name": "Published By",
                    "id": 1000281210,
                    "name": "R&S Music",
                },
                {
                    "entity_type": 29,
                    "entity_type_name": "Mastered At",
                    "id": 1000213793,
                    "name": "Foon",
                },
            ],
            "country": "Belgium",
            "extra_artists": [],
            "formats": [
                {
                    "descriptions": ['12"', "45 RPM"],
                    "name": "Vinyl",
                    "quantity": "1",
                }
            ],
            "genres": [
                "Electronic",
            ],
            "identifiers": [
                {
                    "description": None,
                    "type": "Matrix / Runout",
                    "value": "RS 89014-A1 FOON MASTERING",
                },
                {
                    "description": None,
                    "type": "Matrix / Runout",
                    "value": "RS 89014-B1 FOON MASTERING",
                },
                {
                    "description": None,
                    "type": "Rights Society",
                    "value": "SABAM TM",
                },
            ],
            "labels": [
                {
                    "catalog_number": "RS 890014",
                    "id": 1000000245,
                    "name": "R & S Records",
                }
            ],
            "master_id": None,
            "notes": None,
            "release_date": "1989-01-01",
            "release_id": 61930,
            "styles": [
                "Techno",
                "New Beat",
            ],
            "title": "Call It Techno",
            "tracklist": [
                {
                    "duration": "5:15",
                    "extra_artists": [
                        {
                            "anv": "Per.",
                            "id": 52170,
                            "name": "Per Martinsen",
                            "roles": [
                                {
                                    "name": "Mixed By",
                                }
                            ],
                        },
                        {
                            "anv": "Renaat",
                            "id": 51032,
                            "name": "Renaat Vandepapeliere",
                            "roles": [
                                {
                                    "name": "Mixed By",
                                }
                            ],
                        },
                        {
                            "id": 5783,
                            "name": "David Morley",
                            "roles": [
                                {
                                    "name": "Producer",
                                }
                            ],
                        },
                        {
                            "anv": "Renaat VDP",
                            "id": 51032,
                            "name": "Renaat Vandepapeliere",
                            "roles": [
                                {
                                    "name": "Producer",
                                }
                            ],
                        },
                        {
                            "id": 2742,
                            "name": "Frankie Bones",
                            "roles": [
                                {
                                    "name": "Written-By",
                                }
                            ],
                        },
                    ],
                    "position": "A1",
                    "title": "Call It Techno (Straight Mix)",
                },
                {
                    "duration": "6:30",
                    "extra_artists": [
                        {
                            "anv": "Per.",
                            "id": 52170,
                            "name": "Per Martinsen",
                            "roles": [
                                {
                                    "name": "Mixed By",
                                }
                            ],
                        },
                        {
                            "anv": "Renaat",
                            "id": 51032,
                            "name": "Renaat Vandepapeliere",
                            "roles": [
                                {
                                    "name": "Mixed By",
                                }
                            ],
                        },
                        {
                            "id": 5783,
                            "name": "David Morley",
                            "roles": [
                                {
                                    "name": "Producer",
                                }
                            ],
                        },
                        {
                            "anv": "Renaat VDP",
                            "id": 51032,
                            "name": "Renaat Vandepapeliere",
                            "roles": [
                                {
                                    "name": "Producer",
                                }
                            ],
                        },
                        {
                            "id": 2742,
                            "name": "Frankie Bones",
                            "roles": [
                                {
                                    "name": "Written-By",
                                }
                            ],
                        },
                    ],
                    "position": "A2",
                    "title": "Call It Techno (Extended Version)",
                },
                {
                    "duration": "6:00",
                    "extra_artists": [
                        {
                            "id": 5783,
                            "name": "David Morley",
                            "roles": [
                                {
                                    "name": "Mixed By",
                                }
                            ],
                        },
                        {
                            "anv": "Renaat",
                            "id": 51032,
                            "name": "Renaat Vandepapeliere",
                            "roles": [
                                {
                                    "name": "Mixed By",
                                }
                            ],
                        },
                        {
                            "id": 5783,
                            "name": "David Morley",
                            "roles": [
                                {
                                    "name": "Producer",
                                }
                            ],
                        },
                        {
                            "anv": "Renaat VDP",
                            "id": 51032,
                            "name": "Renaat Vandepapeliere",
                            "roles": [
                                {
                                    "name": "Producer",
                                }
                            ],
                        },
                        {
                            "id": 2742,
                            "name": "Frankie Bones",
                            "roles": [
                                {
                                    "name": "Written-By",
                                }
                            ],
                        },
                    ],
                    "position": "B1",
                    "title": "Call It Techno (Underground Mix)",
                },
                {
                    "duration": "5:08",
                    "extra_artists": [
                        {
                            "anv": "Patrick",
                            "id": 71540,
                            "name": "Patrick Degraeve",
                            "roles": [
                                {
                                    "name": "Mixed By",
                                }
                            ],
                        },
                        {
                            "anv": "Renaat",
                            "id": 51032,
                            "name": "Renaat Vandepapeliere",
                            "roles": [
                                {
                                    "name": "Producer",
                                }
                            ],
                        },
                        {
                            "id": 7434,
                            "name": "Space Opera",
                            "roles": [
                                {
                                    "name": "Producer",
                                }
                            ],
                        },
                        {
                            "anv": "D. Holdenberg",
                            "id": 827850,
                            "name": "Dani\u00ebl Holderberg",
                            "roles": [
                                {
                                    "name": "Written-By",
                                }
                            ],
                        },
                        {
                            "anv": "D. Biot",
                            "id": 827851,
                            "name": "Didier Biot",
                            "roles": [
                                {
                                    "name": "Written-By",
                                }
                            ],
                        },
                        {
                            "anv": "P. Degraeve",
                            "id": 71540,
                            "name": "Patrick Degraeve",
                            "roles": [
                                {
                                    "name": "Written-By",
                                }
                            ],
                        },
                    ],
                    "position": "B2",
                    "title": "Space Opera Theme",
                },
            ],
        }

        expected = utils.normalize_dict(expected_release)
        self.maxDiff = None
        assert actual == expected
