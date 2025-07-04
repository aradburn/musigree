from musigree import utils
from musigree.exceptions import NotFoundError
from musigree.library.fields.entity_id import to_entity_internal_id
from musigree.library.fields.entity_type import EntityType
from musigree.offline.database.offline_database_helper import OfflineDatabaseHelper
from musigree.offline.database.entity_repository import EntityRepository
from musigree.offline.database.relation_release_year_repository import (
    RelationReleaseYearRepository,
)
from musigree.offline.database.relation_repository import RelationRepository
from musigree.offline.database.release_repository import ReleaseRepository
from musigree.offline.database.offline_transaction import offline_transaction
from tests.integration.updater_test_case import UpdaterTestCase


class TestUpdater(UpdaterTestCase):
    async def test_artist_record_updated(self):
        # GIVEN
        entity_id = 20702
        entity_type = EntityType.ARTIST

        # WHEN
        async with offline_transaction():
            entity_repository = EntityRepository()
            entity = await entity_repository.get_by_entity_id_and_entity_type(
                entity_id, entity_type
            )
            actual = utils.normalize_dict(entity.model_dump(exclude={"id"}))

        # THEN
        expected_entity = {
            "entities": {},
            "entity_id": 20702,
            "entity_type": "EntityType.ARTIST",
            "entity_metadata": {
                "name_variations": [
                    "L. Johnson",
                    "L. K. Johnson",
                    "L.K. Johnson",
                    "L.K.J.",
                    "LKJ",
                    'Linton "Kwesi" Johnson',
                    "Linton K. Johnson",
                    "Linton Kwesi-Johnson",
                    "Linton Kwisi Johnson",
                    "Linton Quasi Johnson",
                    "LKJ",
                ],
                "profile": "(Test Updated) Linton Kwesi Johnson (aka LKJ) (born 24 August 1952, "
                + "Chapelton, Jamaica) is a British-based author and dub poet. Johnson's "
                + "poetry makes clever use of the unstandardised transcription of Jamaican "
                + 'Patois and, allied to the Jamaican "toasting" tradition, is regarded as a '
                + "precursor of rap. He became the second living poet, and the only black poet, "
                + "to be published in the Penguin Classics series.",
                "urls": [
                    "http://www.lkjrecords.com/",
                    "http://lister.ultrakohl.com/homepage/Lkj/lkj.htm",
                    "http://en.wikipedia.org/wiki/Linton_Kwesi_Johnson",
                ],
            },
            "entity_name": "Linton Kwesi Johnson",
            "relation_counts": {"Compiled By": 1, "Compiled On": 1, "DJ Mix": 1},
            "search_content": "linton kwesi johnson",
        }
        expected = utils.normalize_dict(expected_entity)
        assert actual == expected

    async def test_artist_record_not_updated(self):
        # GIVEN
        entity_id = 2239
        entity_type = EntityType.ARTIST

        # WHEN
        async with offline_transaction():
            entity_repository = EntityRepository()
            entity = await entity_repository.get_by_entity_id_and_entity_type(
                entity_id, entity_type
            )
            actual = utils.normalize_dict(entity.model_dump(exclude={"id"}))

        # THEN
        expected_entity = {
            "entities": {
                "members": {
                    "Daren Seymour": 66803,
                    "Justin Fletcher": 489350,
                    "Mark Clifford": 51674,
                    "Mark Van Hoen": 41103,
                    "Sarah Peacock": 115880,
                }
            },
            "entity_id": 2239,
            "entity_type": "EntityType.ARTIST",
            "entity_metadata": {
                "profile": "British electronic/rock group formed in the early 1990s. "
                + "They are currently signed to Warp Records.",
                "real_name": "Sarah Peacock, Mark Clifford, Darren Seymour & Justin Fletcher",
                "urls": [
                    "http://www.myspace.com/seefeelmyspace",
                    "http://en.wikipedia.org/wiki/Seefeel",
                    "http://www.facebook.com/pages/Seefeel/146206372061290",
                    "http://twitter.com/#!/_Seefeel_",
                    "http://bit.ly/mQ9t3F",
                    "http://www.seefeel.org",
                ],
            },
            "entity_name": "Seefeel",
            "relation_counts": {
                "Compiled On": 15,
                "Copyright": 2,
                "DJ Mix": 7,
                "Design": 1,
                "Designed At": 1,
                "Film Director": 1,
                "Performer": 1,
                "Phonographic Copyright": 2,
                "Producer": 2,
                "Published By": 1,
                "Released On": 1,
                "Remix": 6,
                "Written By": 5,
            },
            "search_content": "seefeel",
        }
        expected = utils.normalize_dict(expected_entity)
        assert actual == expected

    async def test_artist_record_inserted(self):
        # GIVEN
        entity_id = 9999999
        entity_type = EntityType.ARTIST

        # WHEN
        async with offline_transaction():
            entity_repository = EntityRepository()
            entity = await entity_repository.get_by_entity_id_and_entity_type(
                entity_id, entity_type
            )
            actual = utils.normalize_dict(entity.model_dump(exclude={"id"}))

        # THEN
        expected_entity = {
            "entities": {"groups": {"Test Group": None}},
            "entity_id": 9999999,
            "entity_metadata": {
                "name_variations": ["Test Test", "DJ TEST"],
                "profile": "Test Profile",
                "real_name": "Test 9999999",
                "urls": ["http://www.test.com/", "http://www.testtest.com/"],
            },
            "entity_name": "New Test Artist",
            "entity_type": EntityType.ARTIST,
            "relation_counts": {},
            "search_content": "new test artist",
        }
        expected = utils.normalize_dict(expected_entity)
        assert actual == expected

    async def test_artist_record_deleted(self):
        # GIVEN
        entity_id = 12589
        entity_type = EntityType.ARTIST

        # WHEN
        async with offline_transaction():
            entity_repository = EntityRepository()
            try:
                entity = await entity_repository.get_by_entity_id_and_entity_type(
                    entity_id, entity_type
                )
            except NotFoundError:
                entity = None

        # THEN
        assert entity is None

    async def test_label_record_updated(self):
        # GIVEN
        entity_id = 1
        entity_type = EntityType.LABEL

        # WHEN
        async with offline_transaction():
            entity_repository = EntityRepository()
            entity = await entity_repository.get_by_entity_id_and_entity_type(
                entity_id, entity_type
            )
            actual = utils.normalize_dict(entity.model_dump(exclude={"id"}))

        # THEN
        expected_entity = {
            "entities": {},
            "entity_id": 1,
            "entity_type": "EntityType.LABEL",
            "entity_metadata": {
                "profile": "(Test Update) Classic Techno label from Detroit, USA.\r\n"
                + "[b]Label owner:[/b] [a=Carl Craig].\r\n",
                "urls": [
                    "http://www.planet-e.net/",
                    "http://www.myspace.com/planetecom",
                    "http://www.facebook.com/planetedetroit ",
                    "http://twitter.com/planetedetroit",
                    "http://soundcloud.com/planetedetroit",
                ],
            },
            "entity_name": "Planet E (Test Update)",
            "relation_counts": {"Released On": 1},
            "search_content": "planet e test update",
        }
        expected = utils.normalize_dict(expected_entity)
        assert actual == expected

    async def test_label_record_not_updated(self):
        # GIVEN
        entity_id = 264170
        entity_type = EntityType.LABEL

        # WHEN
        async with offline_transaction():
            entity_repository = EntityRepository()
            entity = await entity_repository.get_by_entity_id_and_entity_type(
                entity_id, entity_type
            )
            actual = utils.normalize_dict(entity.model_dump(exclude={"id"}))

        # THEN
        expected_entity = {
            "entities": {},
            "entity_id": 264170,
            "entity_type": "EntityType.LABEL",
            "entity_metadata": {
                "profile": "American mastering studio located in New Windsor, NY. \r\n\r\n"
                + "Formally located at 2 Engle Street, Tenafly, New Jersey, "
                + "operations were moved to New Windsor in 2005. "
                + "Operated by Chief Engineer [a=Alan Douches].\n",
                "urls": ["http://www.westwestsidemusic.com/"],
            },
            "entity_name": "West West Side Music",
            "relation_counts": {"Mastered At": 1},
            "search_content": "west west side music",
        }
        expected = utils.normalize_dict(expected_entity)
        assert actual == expected

    async def test_label_record_inserted(self):
        # GIVEN
        entity_id = 99999999
        entity_type = EntityType.LABEL

        # WHEN
        async with offline_transaction():
            entity_repository = EntityRepository()
            entity = await entity_repository.get_by_entity_id_and_entity_type(
                entity_id, entity_type
            )
            actual = utils.normalize_dict(entity.model_dump(exclude={"id"}))

        # THEN
        expected_entity = {
            "entities": {},
            "entity_id": 99999999,
            "entity_metadata": {
                "profile": "Test Profile",
                "urls": ["http://www.test.net/", "http://www.testtest.com"],
            },
            "entity_name": "New Label Test",
            "entity_type": EntityType.LABEL,
            "relation_counts": {},
            "search_content": "new label test",
        }
        expected = utils.normalize_dict(expected_entity)
        assert actual == expected

    async def test_label_record_deleted(self):
        # GIVEN
        entity_id = 2529
        entity_type = EntityType.LABEL

        # WHEN
        async with offline_transaction():
            entity_repository = EntityRepository()
            try:
                entity = await entity_repository.get_by_entity_id_and_entity_type(
                    entity_id, entity_type
                )
            except NotFoundError:
                entity = None

        # THEN
        assert entity is None

    async def test_release_updated(self):
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
            "labels": [
                {"catalog_number": "WAP54", "id": 1000023528, "name": "Warp Records"}
            ],
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

    async def test_release_not_updated(self):
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
        assert actual == expected

    async def test_release_inserted(self):
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

    async def test_release_deleted(self):
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

    async def test_relation_updated_01(self):
        # GIVEN
        entity_one_id = 42
        entity_one_type = EntityType.ARTIST
        entity_two_id = 49
        entity_two_type = EntityType.ARTIST
        role = "Producer"

        id_1 = to_entity_internal_id(entity_one_id, entity_one_type)
        id_2 = to_entity_internal_id(entity_two_id, entity_two_type)
        key = dict(
            subject=id_1,
            role=role,
            object=id_2,
        )

        # WHEN
        async with offline_transaction():
            relation_repository = RelationRepository()
            relation_release_year_repository = RelationReleaseYearRepository()
            relation = await OfflineDatabaseHelper.get_relation_by_key(
                relation_repository,
                relation_release_year_repository,
                key,
            )
            actual = utils.normalize_dict(relation.model_dump(exclude={"id"}))

        # THEN
        expected_relation = {
            "entity_one_id": 42,
            "entity_one_type": "EntityType.ARTIST",
            "entity_two_id": 49,
            "entity_two_type": "EntityType.ARTIST",
            "releases": {"157": 1994},
            "role": "Producer",
        }

        expected = utils.normalize_dict(expected_relation)
        assert actual == expected

    async def test_relation_updated_02(self):
        # GIVEN
        entity_one_id = 49
        entity_one_type = EntityType.ARTIST
        entity_two_id = 23528
        entity_two_type = EntityType.LABEL
        role = "Released On"

        id_1 = to_entity_internal_id(entity_one_id, entity_one_type)
        id_2 = to_entity_internal_id(entity_two_id, entity_two_type)
        key = dict(
            subject=id_1,
            role=role,
            object=id_2,
        )

        # WHEN
        async with offline_transaction():
            relation_repository = RelationRepository()
            relation_release_year_repository = RelationReleaseYearRepository()
            relation = await OfflineDatabaseHelper.get_relation_by_key(
                relation_repository,
                relation_release_year_repository,
                key,
            )
            actual = utils.normalize_dict(relation.model_dump(exclude={"id"}))

        # THEN
        expected_relation = {
            "entity_one_id": 49,
            "entity_one_type": "EntityType.ARTIST",
            "entity_two_id": 23528,
            "entity_two_type": "EntityType.LABEL",
            "releases": {"157": 1994, "162": 1996, "1829266": 2004},
            "role": "Released On",
        }

        expected = utils.normalize_dict(expected_relation)
        assert actual == expected

    async def test_relation_updated_03(self):
        # GIVEN
        entity_one_id = 300407
        entity_one_type = EntityType.ARTIST
        entity_two_id = 49
        entity_two_type = EntityType.ARTIST
        role = "Producer"

        id_1 = to_entity_internal_id(entity_one_id, entity_one_type)
        id_2 = to_entity_internal_id(entity_two_id, entity_two_type)
        key = dict(
            subject=id_1,
            role=role,
            object=id_2,
        )

        # WHEN
        async with offline_transaction():
            relation_repository = RelationRepository()
            relation_release_year_repository = RelationReleaseYearRepository()
            relation = await OfflineDatabaseHelper.get_relation_by_key(
                relation_repository,
                relation_release_year_repository,
                key,
            )
            actual = utils.normalize_dict(relation.model_dump(exclude={"id"}))

        # THEN
        expected_relation = {
            "entity_one_id": 300407,
            "entity_one_type": "EntityType.ARTIST",
            "entity_two_id": 49,
            "entity_two_type": "EntityType.ARTIST",
            "releases": {"157": 1994},
            "role": "Producer",
        }

        expected = utils.normalize_dict(expected_relation)
        assert actual == expected

    async def test_relation_updated_04(self):
        # GIVEN
        entity_one_id = 445854
        entity_one_type = EntityType.ARTIST
        entity_two_id = 49
        entity_two_type = EntityType.ARTIST
        role = "Design"

        id_1 = to_entity_internal_id(entity_one_id, entity_one_type)
        id_2 = to_entity_internal_id(entity_two_id, entity_two_type)
        key = dict(
            subject=id_1,
            role=role,
            object=id_2,
        )

        # WHEN
        async with offline_transaction():
            relation_repository = RelationRepository()
            relation_release_year_repository = RelationReleaseYearRepository()
            relation = await OfflineDatabaseHelper.get_relation_by_key(
                relation_repository,
                relation_release_year_repository,
                key,
            )
            actual = utils.normalize_dict(relation.model_dump(exclude={"id"}))

        # THEN
        expected_relation = {
            "entity_one_id": 445854,
            "entity_one_type": "EntityType.ARTIST",
            "entity_two_id": 49,
            "entity_two_type": "EntityType.ARTIST",
            "releases": {"157": 1994},
            "role": "Design",
        }

        expected = utils.normalize_dict(expected_relation)
        assert actual == expected

    async def test_relation_not_updated_01(self):
        # GIVEN
        key = dict(
            subject=42,
            object=41,
            role="Producer",
        )

        # WHEN
        async with offline_transaction():
            relation_repository = RelationRepository()
            relation_release_year_repository = RelationReleaseYearRepository()
            relation = await OfflineDatabaseHelper.get_relation_by_key(
                relation_repository,
                relation_release_year_repository,
                key,
            )
            actual = utils.normalize_dict(relation.model_dump(exclude={"id"}))

        # THEN
        expected_relation = {
            "entity_one_id": 42,
            "entity_one_type": "EntityType.ARTIST",
            "entity_two_id": 41,
            "entity_two_type": "EntityType.ARTIST",
            "releases": {
                "1000619": 2003,
                "1054046": None,
                "1099482": 2001,
                "11216": 1998,
                "1141130": None,
                "1169229": 2007,
                "1195788": 2005,
                "1203976": 1997,
                "1203978": 1993,
                "1257383": 2008,
                "1265276": 2008,
                "135858": 2002,
                "1377682": 1997,
                "13939": 1997,
                "1530077": 2002,
                "1530086": 2006,
                "157": 1994,
                "168639": 2003,
                "1741441": None,
                "1774969": 1999,
                "197416": 2003,
                "2009213": 1998,
                "2012450": 2006,
                "21351": 1999,
                "2188879": 2002,
                "2191313": 2010,
                "2276345": 2002,
                "2291695": 1994,
                "2317370": 2009,
                "239832": 1996,
                "2493": 1993,
                "2502": 1994,
                "251157": 2001,
                "25492": 1994,
                "26454": 1994,
                "26455": 1994,
                "2776338": 2001,
                "292020": 2004,
                "29372": 1992,
                "29373": 1992,
                "29900": 1993,
                "30187": 1994,
                "30188": 1994,
                "3066": 2001,
                "315067": 1992,
                "33098": 1995,
                "33099": 1996,
                "3392955": 2005,
                "34629": 2002,
                "3564784": 1992,
                "3674448": 1999,
                "36895": 2002,
                "383794": 1994,
                "398252": 1997,
                "4030071": 2012,
                "426323": 2005,
                "435111": 2005,
                "491787": 1997,
                "51735": 1994,
                "51766": 1994,
                "539874": 1995,
                "549": 1992,
                "571561": 1998,
                "66011": 1997,
                "708572": 1997,
                "752745": 1993,
                "790582": 1994,
                "793894": 1994,
                "81009": 1991,
                "826408": 2006,
                "870851": 2005,
                "8816": 1994,
            },
            "role": "Producer",
        }

        expected = utils.normalize_dict(expected_relation)
        assert actual == expected

    async def test_relation_not_updated_02(self):
        # GIVEN
        key = dict(
            subject=21209,
            object=3771,
            role="Compiled By",
        )

        # WHEN
        async with offline_transaction():
            relation_repository = RelationRepository()
            relation_release_year_repository = RelationReleaseYearRepository()
            relation = await OfflineDatabaseHelper.get_relation_by_key(
                relation_repository,
                relation_release_year_repository,
                key,
            )
            actual = utils.normalize_dict(relation.model_dump(exclude={"id"}))

        # THEN
        expected_relation = {
            "entity_one_id": 21209,
            "entity_one_type": "EntityType.ARTIST",
            "entity_two_id": 3771,
            "entity_two_type": "EntityType.ARTIST",
            "releases": {
                "1112162": 1996,
                "1112454": 1996,
                "17268": 1994,
                "63148": 1994,
            },
            "role": "Compiled By",
        }

        expected = utils.normalize_dict(expected_relation)
        assert actual == expected

    async def test_relation_not_updated_03(self):
        # GIVEN
        key = dict(
            subject=335173,
            object=41,
            role="Mastered By",
        )

        # WHEN
        async with offline_transaction():
            relation_repository = RelationRepository()
            relation_release_year_repository = RelationReleaseYearRepository()
            relation = await OfflineDatabaseHelper.get_relation_by_key(
                relation_repository,
                relation_release_year_repository,
                key,
            )
            actual = utils.normalize_dict(relation.model_dump(exclude={"id"}))

        # THEN
        expected_relation = {
            "entity_one_id": 335173,
            "entity_one_type": "EntityType.ARTIST",
            "entity_two_id": 41,
            "entity_two_type": "EntityType.ARTIST",
            "releases": {
                "1255104": 2008,
                "1257383": 2008,
                "1265276": 2008,
                "1265680": 2008,
                "130115": 2003,
                "130319": 2003,
                "156930": 2003,
                "2191313": 2010,
                "2192053": 2010,
                "2316777": None,
                "2346144": 2010,
                "2348913": 2010,
                "2351842": 2010,
                "2363967": 2010,
                "2513487": 2010,
                "3392955": 2005,
                "397637": 2003,
                "414646": 2005,
                "426323": 2005,
                "435111": 2005,
                "593584": 2003,
                "870851": 2005,
            },
            "role": "Mastered By",
        }

        expected = utils.normalize_dict(expected_relation)
        assert actual == expected
