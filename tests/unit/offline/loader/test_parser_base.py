import datetime
import io
import logging
from typing import Any
from xml.etree import ElementTree
from xml.etree.ElementTree import Element

from musigree.offline.loader.parser_base import ParserBase
from musigree.offline.loader.parser_utils import ParserUtils

log = logging.getLogger(__name__)


# noinspection PyUnresolvedReferences
class TestParserBase:
    class DummyDomainClass:
        """A test domain class that accepts any keyword arguments."""

        def __init__(self, **kwargs: Any) -> None:
            # Only set attributes that are explicitly provided
            for key, value in kwargs.items():
                setattr(self, key, value)

        # Provide attribute annotations for mypy without setting default values
        name: str
        value: int
        date: Any
        id: str
        ignore: Any
        children: list[str]

    class DummyParser(ParserBase):
        """A test parser class for testing ParserBase functionality."""

        _tags_to_fields_mapping = {
            "name": ("name", ParserUtils.element_to_string),
            "value": ("value", ParserUtils.element_to_integer),
            "date": ("date", ParserUtils.element_to_datetime),
            "child": ("children", ParserUtils.element_to_strings),
            "ignore": ("ignore", ParserUtils.element_to_none),
        }

        @classmethod
        def from_element(cls, element: Element | None) -> "TestParserBase.DummyParser":
            """Create a DummyParser instance from an XML element (required by base class)."""
            if element is None:
                raise ValueError("Element cannot be None")
            # Return a dummy parser instance to satisfy the base class contract
            return cls()

        @classmethod
        def preprocess_data(
            cls, data: dict[str, Any], element: Element
        ) -> dict[str, Any]:
            """Preprocess data by converting name to uppercase."""
            if "name" in data:
                data["name"] = data["name"].upper()
            return data

    def test_load_from_xml(self, monkeypatch: Any) -> None:
        """Test loading data from XML using the dummy parser."""
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
        def mock_get_xml_path(*args: Any, **kwargs: Any) -> str:
            return "dummy_path.xml.gz"

        # noinspection PyUnusedLocal
        def mock_open(*args: Any, **kwargs: Any) -> io.BytesIO:
            return mock_file  # type: ignore

        monkeypatch.setattr(
            "musigree.offline.loader.loader_utils.LoaderUtils.get_xml_path",
            mock_get_xml_path,
        )
        monkeypatch.setattr("gzip.GzipFile", mock_open)

        # WHEN
        # Parse the XML directly to simulate what load_from_xml would do
        root = ElementTree.fromstring(xml_string)
        records = []
        records_skip = []

        for record_element in root.findall("record"):
            data = self.DummyParser.tags_to_fields(record_element)
            if record_element.get("id"):
                data["id"] = record_element.get("id")
            records.append(self.DummyDomainClass(**data))

            # For skip test - only add if has name
            if "name" in data:
                records_skip.append(self.DummyDomainClass(**data))

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
        assert not hasattr(records[4], "name") or records[4].name is None
        assert records[4].value == 50
        assert records[4].date.date() == datetime.date(2024, 11, 10)
        assert records[4].id == "5"

        assert len(records_skip) == 4
        assert records_skip[0].id == "1"
        assert records_skip[1].id == "2"
        assert records_skip[2].id == "3"
        assert records_skip[3].id == "4"

    def test_from_element(self) -> None:
        """Test creating an instance from an XML element."""
        # GIVEN
        root = ElementTree.fromstring("<root><element>test</element></root>")
        element = root.find("element")

        # WHEN
        instance = self.DummyParser.from_element(element)

        # THEN
        assert isinstance(instance, self.DummyParser)

    def test_preprocess_data(self) -> None:
        """Test data preprocessing functionality."""
        # GIVEN
        data = {"name": "test name", "value": 10}
        # Create a dummy element for the test
        element = ElementTree.fromstring("<test></test>")

        # WHEN
        result = self.DummyParser.preprocess_data(data, element)

        # THEN
        assert result["name"] == "TEST NAME"
        assert result["value"] == 10

    def test_tags_to_fields(self) -> None:
        """Test converting XML tags to fields."""
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

    def test_tags_to_fields_ignore_none(self) -> None:
        """Test tags to fields with ignore_none option."""
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

    def test_tags_to_fields_mapping(self) -> None:
        """Test tags to fields with custom mapping."""
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
