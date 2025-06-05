"""
This module provides utility functions for parsing XML data in the Musigree offline system.

It defines the `ParserUtils` class, which offers a collection of static
methods for handling common XML parsing tasks, such as:
    - Cleaning up XML elements.
    - Parsing various date formats into `datetime` objects.
    - Converting XML elements to integers, strings, lists of strings, or None.
    - Iterating through XML elements efficiently.
    - Prettifying XML elements for debugging purposes.

Key functionalities include:
    - Cleaning XML elements by removing specific tags (e.g., "images").
    - Parsing release dates from strings with various formats (YYYY-MM-DD, YYYYMMDD, YYYY).
    - Validating and creating `datetime` objects from year, month, and day strings.
    - Converting XML element text to integers, handling missing or invalid data.
    - Converting XML element text to strings, handling missing data.
    - Converting XML elements with multiple children to a list of strings.
    - Providing an `iterparse` method for efficient XML parsing, managing memory usage.
    - Offering a `prettify` method for generating human-readable XML output.

The `ParserUtils` class is designed to be used as a utility class with static
methods, providing helper functions for other XML parsers in the system.

The module uses `datetime` for date and time handling, `logging` for logging
operations, `re` for regular expressions, `Optional` for type hinting,
`minidom` for XML formatting, and `ElementTree` for XML parsing.
"""

import datetime
import logging
import re
from typing import List
from xml.dom import minidom
from xml.etree import ElementTree
from xml.etree.ElementTree import Element

log = logging.getLogger(__name__)
"""
The logger for the ParserUtils module.
"""


class ParserUtils:
    """
    Provides utility functions for parsing XML data.

    This class offers a collection of static methods for handling common XML
    parsing tasks, such as date parsing, type conversion, and XML cleanup.

    Attributes:
        DATE_REGEX (re.Pattern): Regular expression for matching date strings in YYYY-MM-DD format.
        DATE_NO_DASHES_REGEX (re.Pattern): Regular expression for matching date strings in YYYYMMDD format.
        YEAR_REGEX (re.Pattern): Regular expression for matching year strings in YYYY format.
    """

    DATE_REGEX = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")
    """
    Regular expression for matching date strings in YYYY-MM-DD format.

    This regex is used to extract year, month, and day from date strings
    like "2023-10-27".
    """
    DATE_NO_DASHES_REGEX = re.compile(r"^(\d{4})(\d{2})(\d{2})$")
    """
    Regular expression for matching date strings in YYYYMMDD format.

    This regex is used to extract year, month, and day from date strings
    like "20231027".
    """
    YEAR_REGEX = re.compile(r"^\d\d\d\d$")
    """
    Regular expression for matching year strings in YYYY format.

    This regex is used to validate year strings like "2023".
    """

    # PUBLIC STATIC METHODS

    @staticmethod
    def clean_elements(elements: List[Element]):
        """
        Cleans a list of XML elements by removing unwanted tags.

        Currently, this method removes all "images" tags from the given elements.

        Args:
            elements (list): A list of XML elements to clean.

        Yields:
            Element: The cleaned XML element.
        """
        for element in elements:
            image_tags = element.findall("images")
            if image_tags:
                for image_tag in image_tags:
                    element.remove(image_tag)
            # url_tags = element.findall('urls')
            # if url_tags:
            #    element.remove(*url_tags)
            yield element

    @staticmethod
    def parse_release_date(date_string: str | None) -> datetime.datetime | None:
        """
        Parses a release date string into a datetime object.

        This method handles various date formats, including YYYY-MM-DD, YYYYMMDD,
        and YYYY. It also handles empty or invalid date strings.

        Args:
            date_string (str, optional): The date string to parse.

        Returns:
            datetime.datetime, optional: The parsed datetime object, or None if
                the date string is invalid.
        """
        # empty string
        if not date_string:
            return None
        # yyyy-mm-dd
        match = ParserUtils.DATE_REGEX.match(date_string)
        if match:
            year, month, day = match.groups()
            return ParserUtils.validate_release_date(year, month, day)
        # yyyymmdd
        match = ParserUtils.DATE_NO_DASHES_REGEX.match(date_string)
        if match:
            year, month, day = match.groups()
            return ParserUtils.validate_release_date(year, month, day)
        # yyyy
        match = ParserUtils.YEAR_REGEX.match(date_string)
        if match:
            year, month, day = match.group(), "1", "1"
            return ParserUtils.validate_release_date(year, month, day)
        # other: "?", "????", "None", "Unknown"
        return None

    @staticmethod
    def validate_release_date(
        year_str: str, month_str: str, day_str: str
    ) -> datetime.datetime | None:
        """
        Validates and creates a datetime object from year, month, and day strings.

        This method takes year, month, and day strings and attempts to create a
        valid `datetime` object. It handles cases where month or day is invalid
        (e.g., 0 or out of range) by setting them to a default value (1) or
        swapping them if the day is larger than 12.

        Args:
            year_str (str): The year string.
            month_str (str): The month string.
            day_str (str): The day string.

        Returns:
            datetime.datetime: The validated datetime object.
        """

        try:
            year = int(year_str)
            month = int(month_str)
            day = int(day_str)
            if month < 1:
                month = 1
            if day < 1:
                day = 1
            if month > 12 >= day:
                day, month = month, day

            date = datetime.datetime(year, month, 1, 0, 0)
            day_offset = day - 1
            date = date + datetime.timedelta(days=day_offset)
        except ValueError:
            log.error(f"BAD DATE: {year_str},{month_str},{day_str}")
            date = None
        # log.debug(f"date: {date}")
        return date

    @staticmethod
    def element_to_datetime(element: Element | None) -> datetime.datetime | None:
        """
        Converts an XML element's text to a datetime object.

        This method extracts the text from an XML element, parses it as a
        release date, and returns a `datetime` object.

        Args:
            element (Element): The XML element.

        Returns:
            datetime.datetime, optional: The parsed datetime object, or None if
                the element is None, the text is None or the date is invalid.
        """
        if element is None or element.text is None:
            return None
        date_string = element.text.strip()
        return ParserUtils.parse_release_date(date_string)

    @staticmethod
    def element_to_integer(element: Element | None) -> int | None:
        """
        Converts an XML element's text to an integer.

        This method extracts the text from an XML element and converts it to
        an integer.

        Args:
            element (Element): The XML element.

        Returns:
            int, optional: The integer value, or None if the element or its
                text is None.
        """
        if element is not None and element.text is not None:
            return int(element.text)
        return None

    @staticmethod
    def element_to_string(element: Element | None) -> str | None:
        """
        Converts an XML element's text to a string.

        This method extracts the text from an XML element.

        Args:
            element (Element): The XML element.

        Returns:
            str, optional: The string value, or None if the element is None or has no text.
        """
        if element is not None:
            return element.text or None
        return None

    @staticmethod
    def element_to_strings(element: Element | None) -> list[str] | None:
        """
        Converts an XML element with multiple child elements to a list of strings.

        This method extracts the text from each child element and returns them
        as a list of strings.

        Args:
            element (Element): The XML element.

        Returns:
            list[str], optional: A list of strings, or None if the element is None or has no children.
        """
        if element is not None and len(element):
            return [_.text for _ in element if _.text is not None]
        return None

    # noinspection PyUnusedLocal
    @staticmethod
    def element_to_none(element: Element | None) -> str | None:
        """
        Returns None.

        This method is used as a placeholder when a mapping to an element is required,
        but the element should be ignored.

        Args:
            element: The XML element.

        Returns:
            None
        """
        return None

    @staticmethod
    def iterparse(source, tag: str):
        """
        Provides an iterator for parsing XML, yielding elements with a specific tag.

        This method is similar to `ElementTree.iterparse`, but it's optimized
        for memory usage by clearing the root element after each element with
        the specified tag is processed.

        Args:
            source (file-like object): The source to parse, typically a file-like object.
            tag (str): The tag to look for in the XML.

        Yields:
            Element: An XML element with the specified tag.
        """
        context = ElementTree.iterparse(source, events=("start", "end"))
        context_iter = iter(context)
        _, root = next(context_iter)  # Get the root element and advance the iterator
        depth = 0
        for event, element in context:
            if element.tag == tag:
                if event == "start":
                    depth += 1
                else:
                    depth -= 1
                    if depth == 0:
                        yield element
                        root.clear()

    @staticmethod
    def prettify(element: Element) -> str:
        """
        Generates a human-readable string representation of an XML element.

        This method takes an XML element and returns a nicely formatted
        string representation of it, suitable for debugging or logging.

        Args:
            element (Element): The XML element to prettify.

        Returns:
            str: The formatted XML string.
        """
        string = ElementTree.tostring(element, "utf-8")
        reparsed = minidom.parseString(string)
        return reparsed.toprettyxml(indent="    ")
