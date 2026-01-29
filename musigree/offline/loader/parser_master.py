"""
This module defines the `ParserMaster` class, which is responsible for parsing
XML data representing master data records in the Musigree offline system.

It extends the `ParserBase` class to provide master-specific parsing logic,
including handling artist credits, genres, styles, videos, and images.

Key functionalities include:
    - **`element_to_artist_credits`**: Extracts artist credit information from
      an XML element, including the artist's ID, name, ANV (Artist Name
      Variation), and join information.
    - **`element_to_videos`**: Extracts video information from an XML element,
      including the video's src, duration, embed flag, title, and description.
    - **`element_to_images`**: Extracts image information from an XML element,
      including the image's type, width, and height.
    - **`from_element`**: Creates a `Master` offline_domain object from an XML
      element, using the extracted data.
    - **`preprocess_data`**: Preprocesses the extracted master data, setting
      the `master_id` from the element's id attribute.
    - **Tag-to-Field Mapping**: Defines mappings
      (`_tags_to_fields_mapping`, `_artists_mapping`) that specify how XML tags
      should be processed and mapped to the fields of a `Master` object.
    - **Helper Methods**: Includes helper methods for extracting specific
      types of data, such as artist credits, videos, and images.

The `ParserMaster` class interacts with the following components:
    - `ParserBase`: The base class for XML parsing, providing common parsing
      functionalities.
    - `ParserUtils`: For generic XML parsing utilities, such as converting
      elements to strings or integers.
    - `Master`: The offline_domain object representing a master record.
    - `logging`: For logging operations.
    - `Element` from `xml.etree.ElementTree`: For XML element handling.

The module utilizes `logging` for logging operations, `Element` from
`xml.etree.ElementTree` for XML handling, and `typing` for type hinting.
It uses `musigree` library for musigree specific operations.
"""

import logging
from typing import Any
from xml.etree.ElementTree import Element

from musigree.offline.offline_domain.master import Master
from musigree.offline.loader.parser_base import ParserBase
from musigree.offline.loader.parser_utils import ParserUtils

log = logging.getLogger(__name__)
"""
The logger for the ParserMaster module.
"""


class ParserMaster(ParserBase):
    """
    Parses XML data representing master data records.

    This class extends `ParserBase` to provide master-specific parsing
    logic, including handling artist credits, genres, styles, videos, and images.
    """

    # CLASS VARIABLES

    _artists_mapping: dict[str, Any] = {}
    """
    Mapping for artist credit XML elements to their corresponding fields.
    """

    # CLASS METHODS

    @classmethod
    def element_to_artist_credits(cls, element: Element) -> list[dict[str, Any]]:
        """
        Extracts artist credit information from an XML element.

        This method parses an XML element containing artist credit information
        and returns a list of dictionaries, where each dictionary represents
        an artist credit.

        Args:
            element: The XML element containing the artist credits.

        Returns:
            list: A list of dictionaries, each representing an artist credit.
        """
        result: list[dict[str, Any]] = []
        if element is None or not len(element):
            return result
        for subelement in element:
            data = cls.tags_to_fields(
                subelement,
                ignore_none=True,
                mapping=cls._artists_mapping,
            )
            result.append(data)
        return result

    @classmethod
    def element_to_videos(cls, element: Element) -> list[dict[str, Any]]:
        """
        Extracts video information from an XML element.

        This method parses an XML element containing video information and
        returns a list of dictionaries, where each dictionary represents a video.

        Args:
            element: The XML element containing the videos.

        Returns:
            list: A list of dictionaries, each representing a video.
        """
        result: list[dict[str, Any]] = []
        if element is None or not len(element):
            return result
        for sub_element in element:
            video_data: dict[str, Any] = {
                "src": sub_element.get("src"),
                "embed": sub_element.get("embed", "false").lower() == "true",
            }
            # Parse duration - handle both presence and value
            duration_attr = sub_element.get("duration")
            if duration_attr is not None:
                try:
                    video_data["duration"] = int(duration_attr)
                except (ValueError, TypeError):
                    video_data["duration"] = None
            else:
                video_data["duration"] = None
            # Extract title and description from child elements
            title_elem = sub_element.find("title")
            if title_elem is not None and title_elem.text:
                video_data["title"] = title_elem.text
            description_elem = sub_element.find("description")
            if description_elem is not None and description_elem.text:
                video_data["description"] = description_elem.text
            result.append(video_data)
        return result

    @classmethod
    def element_to_images(cls, element: Element) -> list[dict[str, Any]]:
        """
        Extracts image information from an XML element.

        This method parses an XML element containing image information and
        returns a list of dictionaries, where each dictionary represents an image.

        Args:
            element: The XML element containing the images.

        Returns:
            list: A list of dictionaries, each representing an image.
        """
        result: list[dict[str, Any]] = []
        if element is None or not len(element):
            return result
        for sub_element in element:
            image_data: dict[str, Any] = {
                "type": sub_element.get("type"),
            }
            # Parse width and height - handle both presence and value
            width_attr = sub_element.get("width")
            if width_attr is not None:
                try:
                    image_data["width"] = int(width_attr)
                except (ValueError, TypeError):
                    image_data["width"] = None
            else:
                image_data["width"] = None
            height_attr = sub_element.get("height")
            if height_attr is not None:
                try:
                    image_data["height"] = int(height_attr)
                except (ValueError, TypeError):
                    image_data["height"] = None
            else:
                image_data["height"] = None
            result.append(image_data)
        return result

    @classmethod
    def from_element(cls, element: Element) -> Master:  # type: ignore
        """
        Creates a `Master` offline_domain object from an XML element.

        This method takes an XML element and uses the `tags_to_fields`
        method to extract the relevant data. It then creates and returns a
        `Master` object.

        Args:
            element: The XML element.

        Returns:
            Master: The created `Master` object.
        """
        data = cls.tags_to_fields(element)
        return Master(**data)

    @classmethod
    def preprocess_data(cls, data: dict[str, Any], element: Element) -> dict[str, Any]:
        """
        Preprocesses the extracted master data.

        This method performs preprocessing steps on the data extracted from
        an XML element, such as setting the `master_id` from the element's
        id attribute.

        Args:
            data (dict): The data extracted from the XML element.
            element: The XML element.

        Returns:
            dict: The preprocessed data.
        """
        if element.tag == "master":
            data["master_id"] = int(element.get("id"))  # type: ignore
        return data


ParserMaster._tags_to_fields_mapping = {
    "artists": ("artists", ParserMaster.element_to_artist_credits),
    "genres": ("genres", ParserUtils.element_to_strings),
    "styles": ("styles", ParserUtils.element_to_strings),
    "title": ("title", ParserUtils.element_to_string),
    "year": ("year", ParserUtils.element_to_integer),
    "main_release": ("main_release", ParserUtils.element_to_string),
    "data_quality": ("data_quality", ParserUtils.element_to_string),
    "videos": ("videos", ParserMaster.element_to_videos),
    "images": ("images", ParserMaster.element_to_images),
}
"""
Mapping of XML tags to fields for master elements.
"""

ParserMaster._artists_mapping = {
    "id": ("id", ParserUtils.element_to_integer),
    "name": ("name", ParserUtils.element_to_string),
    "anv": ("anv", ParserUtils.element_to_string),
    "join": ("join", ParserUtils.element_to_string),
}
"""
Mapping of XML tags to fields for artist credit elements.
"""
