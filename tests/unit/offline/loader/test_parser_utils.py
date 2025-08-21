import datetime
import io
import re
from xml.etree import ElementTree

import pytest

from musigree.offline.loader.parser_utils import ParserUtils


class TestParserUtils:
    def test_clean_elements(self) -> None:
        # GIVEN
        xml_string = """
        <root>
            <element>
                <name>Test Element</name>
                <images>
                    <image>image1.jpg</image>
                </images>
                <images>
                    <image>image2.jpg</image>
                </images>
            </element>
             <element>
                <name>Test Element 2</name>
            </element>
        </root>
        """
        root = ElementTree.fromstring(xml_string)
        elements = iter(root.findall("element"))

        # WHEN
        cleaned_elements = list(ParserUtils.clean_elements(elements))

        # THEN
        assert len(cleaned_elements) == 2
        assert cleaned_elements[0].find("images") is None
        assert cleaned_elements[1].find("images") is None

    @pytest.mark.parametrize(
        "date_string, expected_datetime",
        [
            ("2023-10-27", datetime.datetime(2023, 10, 27, 0, 0)),
            ("20231027", datetime.datetime(2023, 10, 27, 0, 0)),
            ("2023", datetime.datetime(2023, 1, 1, 0, 0)),
            ("", None),
            (None, None),
            ("2023-13-01", datetime.datetime(2023, 1, 13, 0, 0)),  # Invalid month
            (
                "2023-02-30",
                datetime.datetime(2023, 3, 2, 0, 0),
            ),  # Invalid day for month
            ("2023-02-0", None),  # Invalid day
            ("2023-0-2", None),  # Invalid month
            ("????", None),
            ("Unknown", None),
            ("20231132", datetime.datetime(2023, 12, 2, 0, 0)),
            ("2023-12-0", None),
            ("2023-0-12", None),
        ],
    )
    def test_parse_release_date(
        self, date_string: str, expected_datetime: datetime.datetime
    ) -> None:
        # WHEN
        result = ParserUtils.parse_release_date(date_string)

        # THEN
        assert result == expected_datetime

    def test_validate_release_date(self) -> None:
        # WHEN
        date = ParserUtils.validate_release_date("2023", "10", "27")

        # THEN
        assert date == datetime.datetime(2023, 10, 27, 0, 0)

    def test_element_to_datetime(self) -> None:
        # GIVEN
        xml_string = "<element>2023-10-27</element>"
        element = ElementTree.fromstring(xml_string)

        # WHEN
        result = ParserUtils.element_to_datetime(element)

        # THEN
        assert result == datetime.datetime(2023, 10, 27, 0, 0)

    def test_element_to_datetime_none(self) -> None:
        # WHEN
        result = ParserUtils.element_to_datetime(None)

        # THEN
        assert result is None

    def test_element_to_datetime_empty(self) -> None:
        # GIVEN
        xml_string = "<element></element>"
        element = ElementTree.fromstring(xml_string)

        # WHEN
        result = ParserUtils.element_to_datetime(element)

        # THEN
        assert result is None

    def test_element_to_integer(self) -> None:
        # GIVEN
        xml_string = "<element>123</element>"
        element = ElementTree.fromstring(xml_string)

        # WHEN
        result = ParserUtils.element_to_integer(element)

        # THEN
        assert result == 123

    def test_element_to_integer_none(self) -> None:
        # WHEN
        result = ParserUtils.element_to_integer(None)

        # THEN
        assert result is None

    def test_element_to_string(self) -> None:
        # GIVEN
        xml_string = "<element>test string</element>"
        element = ElementTree.fromstring(xml_string)

        # WHEN
        result = ParserUtils.element_to_string(element)

        # THEN
        assert result == "test string"

    def test_element_to_string_none(self) -> None:
        # WHEN
        result = ParserUtils.element_to_string(None)

        # THEN
        assert result is None

    def test_element_to_string_empty(self) -> None:
        # GIVEN
        xml_string = "<element></element>"
        element = ElementTree.fromstring(xml_string)

        # WHEN
        result = ParserUtils.element_to_string(element)

        # THEN
        assert result is None

    def test_element_to_strings(self) -> None:
        # GIVEN
        xml_string = """
        <element>
            <child>string1</child>
            <child>string2</child>
        </element>
        """
        element = ElementTree.fromstring(xml_string)

        # WHEN
        result = ParserUtils.element_to_strings(element)

        # THEN
        assert result == ["string1", "string2"]

    def test_element_to_strings_none(self) -> None:
        # WHEN
        result = ParserUtils.element_to_strings(None)

        # THEN
        assert result is None

    def test_element_to_strings_empty(self) -> None:
        # GIVEN
        xml_string = "<element></element>"
        element = ElementTree.fromstring(xml_string)

        # WHEN
        result = ParserUtils.element_to_strings(element)

        # THEN
        assert result is None

    def test_element_to_none(self) -> None:
        # GIVEN
        xml_string = "<element></element>"
        element = ElementTree.fromstring(xml_string)

        # WHEN
        result = ParserUtils.element_to_none(element)

        # THEN
        assert result is None

    def test_iterparse(self) -> None:
        # GIVEN
        xml_string = """
        <root>
            <record>
                <id>1</id>
                <name>Record 1</name>
            </record>
            <record>
                <id>2</id>
                <name>Record 2</name>
            </record>
        </root>
        """
        xml = io.StringIO(xml_string)

        # WHEN
        records = list(ParserUtils.iterparse(source=xml, tag="record"))

        # THEN
        assert len(records) == 2
        assert records[0].find("id").text == "1"  # type: ignore
        assert records[1].find("id").text == "2"  # type: ignore

    def test_prettify(self) -> None:
        # GIVEN
        xml_string = "<element><child>text</child></element>"
        element = ElementTree.fromstring(xml_string)

        # WHEN
        result = ParserUtils.prettify(element)

        # THEN
        assert result is not None
        assert "<element>" in result
        assert "<child>" in result
        assert "text" in result
        assert re.search(r"<element>\s+<child>", result)
