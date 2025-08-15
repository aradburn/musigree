from xml.etree import ElementTree

from musigree import utils
from musigree.config import SqliteTestConfiguration
from musigree.constants import DISCOGS_DATA
from musigree.offline.loader.loader_utils import LoaderUtils
from musigree.offline.loader.parser_release import ParserRelease
from tests.conftest import AbstractDatabaseTest


class TestLoaderRelease(AbstractDatabaseTest):
    def test_release_xml_parse(self):
        # GIVEN
        source = utils.normalize(
            """
            <?xml version="1.0" ?>
            <release id="103" status="Accepted">
                <artists>
                    <artist>
                        <id>194</id>
                        <name>Various</name>
                        <anv/>
                        <join/>
                        <role/>
                        <tracks/>
                    </artist>
                </artists>
                <title>The Necessary EP</title>
                <labels>
                    <label catno="NT006" name="Nordic Trax"/>
                </labels>
                <extraartists/>
                <formats>
                    <format name="Vinyl" qty="1" text="">
                        <descriptions>
                            <description>12&quot;</description>
                            <description>EP</description>
                        </descriptions>
                    </format>
                </formats>
                <genres>
                    <genre>Electronic</genre>
                </genres>
                <styles>
                    <style>Deep House</style>
                </styles>
                <country>Canada</country>
                <released>1999-00-00</released>
                <data_quality>Correct</data_quality>
                <tracklist>
                    <track>
                        <position>A1</position>
                        <title>K2morrow</title>
                        <duration/>
                        <artists>
                            <artist>
                                <id>195</id>
                                <name>Peter Hecher</name>
                                <anv/>
                                <join/>
                                <role/>
                                <tracks/>
                            </artist>
                        </artists>
                    </track>
                    <track>
                        <position>A2</position>
                        <title>The Disco Man</title>
                        <duration/>
                        <artists>
                            <artist>
                                <id>195</id>
                                <name>Peter Hecher</name>
                                <anv/>
                                <join/>
                                <role/>
                                <tracks/>
                            </artist>
                        </artists>
                    </track>
                    <track>
                        <position>B1</position>
                        <title>Making Changes (4am Vibez)</title>
                        <duration/>
                        <artists>
                            <artist>
                                <id>196</id>
                                <name>Aaronz</name>
                                <anv/>
                                <join/>
                                <role/>
                                <tracks/>
                            </artist>
                        </artists>
                    </track>
                    <track>
                        <position>B2</position>
                        <title>Up Jumped The Boogie</title>
                        <duration/>
                        <artists>
                            <artist>
                                <id>197</id>
                                <name>Sea To Sky</name>
                                <anv/>
                                <join/>
                                <role/>
                                <tracks/>
                            </artist>
                        </artists>
                    </track>
                </tracklist>
                <videos>
                    <video duration="395" embed="true" src="http://www.youtube.com/watch?v=CmFYUEcD0Xs">
                        <title>K2morrow [Original Mix] - Peter Hecher</title>
                        <description>K2morrow [Original Mix] - Peter Hecher</description>
                    </video>
                </videos>
                <companies/>
            </release>
            """
        )
        release_element = ElementTree.fromstring(source)

        # WHEN
        release = ParserRelease().from_element(release_element)
        actual = utils.normalize_dict(release.model_dump())

        # THEN
        expected_release = {
            "artists": [{"id": 194, "name": "Various"}],
            "companies": [],
            "country": "Canada",
            "extra_artists": [],
            "formats": [
                {"descriptions": ['12"', "EP"], "name": "Vinyl", "quantity": "1"}
            ],
            "genres": ["Electronic"],
            "identifiers": None,
            "labels": [{"catalog_number": "NT006", "name": "Nordic Trax"}],
            "master_id": None,
            "notes": None,
            "release_date": "1999-01-01",
            "release_id": 103,
            "styles": ["Deep House"],
            "title": "The Necessary EP",
            "tracklist": [
                {
                    "artists": [{"id": 195, "name": "Peter Hecher"}],
                    "position": "A1",
                    "title": "K2morrow",
                },
                {
                    "artists": [{"id": 195, "name": "Peter Hecher"}],
                    "position": "A2",
                    "title": "The Disco Man",
                },
                {
                    "artists": [{"id": 196, "name": "Aaronz"}],
                    "position": "B1",
                    "title": "Making Changes (4am Vibez)",
                },
                {
                    "artists": [{"id": 197, "name": "Sea To Sky"}],
                    "position": "B2",
                    "title": "Up Jumped The Boogie",
                },
            ],
        }
        expected = utils.normalize_dict(expected_release)
        assert actual == expected

    def test_release_from_element_01(self):
        # GIVEN
        offline_config = SqliteTestConfiguration()
        discogs_data_directory = offline_config.DATA_DIR / DISCOGS_DATA

        iterator = LoaderUtils.get_iterator(
            discogs_data_directory, "release", "testinsert"
        )
        release_element = next(iterator)

        # WHEN
        release = ParserRelease().from_element(release_element)
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
            "labels": [{"catalog_number": "WAP54", "name": "Warp Records"}],
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

    def test_release_from_element_02(self):
        # GIVEN
        offline_config = SqliteTestConfiguration()
        discogs_data_directory = offline_config.DATA_DIR / DISCOGS_DATA

        iterator = LoaderUtils.get_iterator(
            discogs_data_directory, "release", "testinsert"
        )
        next(iterator)
        next(iterator)
        next(iterator)
        next(iterator)
        next(iterator)
        next(iterator)
        release_element = next(iterator)

        # WHEN
        release = ParserRelease().from_element(release_element)
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
            "labels": [{"catalog_number": "HIACD2", "name": "Beyond"}],
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
