from xml.etree import ElementTree

from musigree import utils
from musigree.config import SqliteTestConfiguration
from musigree.constants import DISCOGS_DATA
from musigree.offline.loader.loader_utils import LoaderUtils
from musigree.offline.loader.parser_master import ParserMaster


# noinspection HttpUrlsUsage
class TestLoaderMaster:
    def test_master_xml_parse(self) -> None:
        # GIVEN
        source = utils.normalize(
            """
            <?xml version="1.0" ?>
            <master id="292">
                <main_release>129407</main_release>
                <artists>
                    <artist>
                        <id>24161</id>
                        <name>Bill Youngman</name>
                    </artist>
                </artists>
                <genres>
                    <genre>Electronic</genre>
                </genres>
                <styles>
                    <style>Breaks</style>
                    <style>Techno</style>
                    <style>Electro</style>
                </styles>
                <year>2003</year>
                <title>Kleingeld E.P.</title>
                <data_quality>Correct</data_quality>
                <videos>
                    <video src="https://www.youtube.com/watch?v=H1g5RgjvXfk" duration="422"
                     embed="true">
                        <title>Bill Youngman - Hammerhead (0.7)</title>
                        <description>A side on Null Records 7 (Bill Youngman - Kleingeld EP), released 2003, Germany, http://www.discogs.com/Bill-Youngman-Kleingeld-EP/release/129407</description>
                    </video>
                </videos>
            </master>
            """
        )
        master_element = ElementTree.fromstring(source)

        # WHEN
        master = ParserMaster().from_element(master_element)
        actual = utils.normalize_dict(master.model_dump())

        # THEN
        expected_master = {
            "artists": [
                {
                    "id": 24161,
                    "name": "Bill Youngman"
                }
            ],
            "data_quality": "Correct",
            "genres": [
                "Electronic"
            ],
            "images": None,
            "main_release": "129407",
            "master_id": 292,
            "styles": [
                "Breaks",
                "Techno",
                "Electro"
            ],
            "title": "Kleingeld E.P.",
            "videos": [
                {
                    "description": "A side on Null Records 7 (Bill Youngman - Kleingeld EP), released 2003, Germany, http://www.discogs.com/Bill-Youngman-Kleingeld-EP/release/129407",
                    "duration": 422,
                    "embed": True,
                    "src": "https://www.youtube.com/watch?v=H1g5RgjvXfk",
                    "title": "Bill Youngman - Hammerhead (0.7)"
                }
            ],
            "year": 2003,
        }
        expected = utils.normalize_dict(expected_master)
        assert actual == expected

    def test_master_from_element_01(self) -> None:
        # GIVEN
        offline_config = SqliteTestConfiguration()
        discogs_data_directory = offline_config.DATA_DIR / DISCOGS_DATA

        iterator = LoaderUtils.get_iterator(discogs_data_directory, "master", "testinsert")
        master_element = next(iterator)

        # WHEN
        master = ParserMaster().from_element(master_element)
        actual = utils.normalize_dict(master.model_dump())

        # THEN
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

    def test_master_from_element_02(self) -> None:
        # GIVEN
        offline_config = SqliteTestConfiguration()
        discogs_data_directory = offline_config.DATA_DIR / DISCOGS_DATA

        iterator = LoaderUtils.get_iterator(discogs_data_directory, "master", "testinsert")
        next(iterator)
        next(iterator)
        next(iterator)
        next(iterator)
        next(iterator)
        next(iterator)
        master_element = next(iterator)

        # WHEN
        master = ParserMaster().from_element(master_element)
        actual = utils.normalize_dict(master.model_dump())

        # THEN
        expected_master = {
            "artists": [
                {
                    "id": 26019,
                    "name": "Rich Lee"
                }
            ],
            "data_quality": "Correct",
            "genres": [
                "Electronic"
            ],
            "images": None,
            "main_release": "32946",
            "master_id": 18041,
            "styles": [
                "Techno"
            ],
            "title": "Rock So Hard",
            "videos": None,
            "year": 1993,
        }
        expected = utils.normalize_dict(expected_master)
        assert actual == expected
