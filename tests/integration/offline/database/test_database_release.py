from musigree import utils
from musigree.offline.database.release_repository import ReleaseRepository
from musigree.offline.database.offline_transaction import offline_transaction
from tests.integration.offline.database.offline_database_test_case import (
    OfflineDatabaseTestCase,
)


class TestDatabaseRelease(OfflineDatabaseTestCase):
    def test_from_db_01(self):
        release_id = 157
        with offline_transaction():
            release_repository = ReleaseRepository()
            release = release_repository.get(release_id)
            actual = utils.normalize_dict(release.model_dump())

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
            "labels": [
                {"catalog_number": "WAP54", "id": 1000023528, "name": "Warp Records"}
            ],
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
        self.assertEqual(expected, actual)

    def test_from_db_02(self):
        release_id = 635
        with offline_transaction():
            release_repository = ReleaseRepository()
            release = release_repository.get(release_id)
            actual = utils.normalize_dict(release.model_dump())

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
            "labels": [
                {"catalog_number": "HIACD2", "id": 1000000233, "name": "Beyond"}
            ],
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
                    "extra_artists": [
                        {"id": 41, "name": "Autechre", "roles": [{"name": "Remix"}]}
                    ],
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
        self.assertEqual(expected, actual)
