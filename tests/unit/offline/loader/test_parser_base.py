import datetime
import io
import logging
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

from musigree.offline.loader.parser_base import ParserBase
from musigree.offline.loader.parser_utils import ParserUtils

log = logging.getLogger(__name__)


# noinspection PyUnresolvedReferences
class TestParserBase:
    class DummyDomainClass:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

    class DummyParser(ParserBase):
        _tags_to_fields_mapping = {
            "name": ("name", ParserUtils.element_to_string),
            "value": ("value", ParserUtils.element_to_integer),
            "date": ("date", ParserUtils.element_to_datetime),
            "child": ("children", ParserUtils.element_to_strings),
            "ignore": ("ignore", ParserUtils.element_to_none),
        }

        @classmethod
        def from_element(cls, element):
            data = cls.tags_to_fields(element)
            return TestParserBase.DummyDomainClass(**data)

        @classmethod
        def preprocess_data(cls, data: dict, element) -> dict[str, Any]:
            if "name" in data:
                data["name"] = data["name"].upper()
            return data

    def test_load_from_xml(self, monkeypatch):
        # GIVEN
        xml_string = """
        <root>
            <record id="1">
                <name>record one</name>
                <value>10</value>
                <date>2023-10-27</date>
                <ignore>ignore</ignore>
                <child>child1</child>
                <child>child2</child>
            </record>
            <record id="2">
                <name>record two</name>
                <value>20</value>
                <date>2023-11-27</date>
            </record>
             <record id="3">
                <name>record three</name>
                <value>30</value>
                <date>BAD DATE</date>
            </record>
            <record id="4">
                <name>record four</name>
                <value>40</value>
                <date>2024-11-10</date>
            </record>
            <record id="5">
                <value>50</value>
                <date>2024-11-10</date>
            </record>
        </root>
        """
        mock_file = io.BytesIO(xml_string.encode())

        # noinspection PyUnusedLocal
        def mock_get_xml_path(*args, **kwargs):
            return "dummy_path.xml.gz"

        # noinspection PyUnusedLocal
        def mock_open(*args, **kwargs):
            return mock_file

        monkeypatch.setattr(
            "musigree.offline.loader.loader_utils.LoaderUtils.get_xml_path",
            mock_get_xml_path,
        )
        monkeypatch.setattr("gzip.GzipFile", mock_open)

        # WHEN
        records = list(
            self.DummyParser.load_from_xml(
                self.DummyDomainClass,
                Path("dummy_dir"),
                "dummy_date",
                "record",
                "id",
                [],
            )
        )

        mock_file = io.BytesIO(xml_string.encode())
        records_skip = list(
            self.DummyParser.load_from_xml(
                self.DummyDomainClass,
                Path("dummy_dir"),
                "dummy_date",
                "record",
                "id",
                ["name"],
            )
        )

        # THEN
        assert len(records) == 5
        assert records[0].name == "RECORD ONE"
        assert records[0].value == 10
        assert records[0].date.date() == datetime.date(2023, 10, 27)
        assert records[0].id == "1"
        assert records[0].ignore is None
        assert records[1].name == "RECORD TWO"
        assert records[1].value == 20
        assert records[1].date.date() == datetime.date(2023, 11, 27)
        assert records[1].id == "2"
        assert records[2].name == "RECORD THREE"
        assert records[2].value == 30
        assert records[2].date is None
        assert records[2].id == "3"
        assert records[3].name == "RECORD FOUR"
        assert records[3].value == 40
        assert records[3].date.date() == datetime.date(2024, 11, 10)
        assert records[3].id == "4"
        assert "name" not in records[4].__dict__
        assert records[4].value == 50
        assert records[4].date.date() == datetime.date(2024, 11, 10)
        assert records[4].id == "5"

        assert len(records_skip) == 4
        assert records_skip[0].id == "1"
        assert records_skip[1].id == "2"
        assert records_skip[2].id == "3"
        assert records_skip[3].id == "4"

    def test_from_element(self):
        # GIVEN
        root = ElementTree.fromstring("<root><element>test</element></root>")
        element = root.find("element")

        # WHEN
        instance = self.DummyParser.from_element(element)

        # THEN
        assert isinstance(instance, self.DummyDomainClass)

    def test_preprocess_data(self):
        # GIVEN
        data = {"name": "test name", "value": 10}
        element = None

        # WHEN
        result = self.DummyParser.preprocess_data(data, element)

        # THEN
        assert result["name"] == "TEST NAME"
        assert result["value"] == 10

    def test_tags_to_fields(self):
        # GIVEN
        xml_string = """
        <root>
            <name>record one</name>
            <value>10</value>
            <date>2023-10-27</date>
        </root>
        """
        root = ElementTree.fromstring(xml_string)

        # WHEN
        result = self.DummyParser.tags_to_fields(root)

        # THEN
        assert result["name"] == "RECORD ONE"
        assert result["value"] == 10
        assert result["date"].date() == datetime.date(2023, 10, 27)

    def test_tags_to_fields_ignore_none(self):
        # GIVEN
        xml_string = """
        <root>
            <name>record one</name>
            <value></value>
            <date></date>
        </root>
        """
        root = ElementTree.fromstring(xml_string)

        # WHEN
        result = self.DummyParser.tags_to_fields(root, ignore_none=True)

        # THEN
        assert result["name"] == "RECORD ONE"
        assert "value" not in result
        assert "date" not in result

    def test_tags_to_fields_mapping(self):
        # GIVEN
        xml_string = """
        <root>
            <myname>record one</myname>
        </root>
        """
        root = ElementTree.fromstring(xml_string)
        custom_mapping = {"myname": ("name", ParserUtils.element_to_string)}

        # WHEN
        result = self.DummyParser.tags_to_fields(root, mapping=custom_mapping)

        # THEN
        assert result["name"] == "RECORD ONE"
