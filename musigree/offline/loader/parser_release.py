"""
This module defines the `ParserRelease` class, which is responsible for parsing
XML data representing releases in the Musigree offline system.

It extends the `ParserBase` class to provide release-specific parsing logic,
including handling artist credits, company credits, tracklists, formats,
identifiers, and label credits. It also includes methods for processing and
normalizing various types of release-related data.

Key functionalities include:
    - **`element_to_artist_credits`**: Extracts artist credit information from
      an XML element, including the artist's ID, name, ANV (Artist Name
      Variation), join information, roles, and tracks.
    - **`element_to_company_credits`**: Extracts company credit information
      from an XML element, including the company's ID, name, catalog number,
      entity type, and entity type name.
    - **`element_to_formats`**: Extracts format information from an XML
      element, including the format name, quantity, text, and descriptions.
    - **`element_to_identifiers`**: Extracts identifier information from an XML
      element, including the description, type, and value.
    - **`element_to_label_credits`**: Extracts label credit information from
      an XML element, including the label's catalog number and name.
    - **`element_to_roles`**: Extracts role information from an XML element,
      handling the complex format of role strings, which may include details
      in brackets.
    - **`element_to_tracks`**: Extracts track information from an XML element,
      including the track's position, title, duration, artists, and extra
      artists.
    - **`from_element`**: Creates a `Release` domain object from an XML
      element, using the extracted data.
    - **`preprocess_data`**: Preprocesses the extracted release data, setting
      the `release_id`, `identifiers`, `master_id`, and `notes`.
    - **Tag-to-Field Mapping**: Defines multiple mappings
      (`_tags_to_fields_mapping`, `_artists_mapping`, `_companies_mapping`,
      `_tracks_mapping`) that specify how XML tags should be processed and
      mapped to the fields of a `Release` object.
    - **Helper Methods**: Includes helper methods for extracting specific
      types of data, such as artist credits, company credits, and track data.

The `ParserRelease` class interacts with the following components:
    - `ParserBase`: The base class for XML parsing, providing common parsing
      functionalities.
    - `ParserUtils`: For generic XML parsing utilities, such as converting
      elements to strings or integers.
    - `Release`: The domain object representing a release.
    - `logging`: For logging operations.
    - `Element` from `xml.etree.ElementTree`: For XML element handling.

The module utilizes `logging` for logging operations, `Element` from
`xml.etree.ElementTree` for XML handling, and `typing` for type hinting.
It uses `musigree` library for musigree specific operations.
"""

import logging

from musigree.offline.domain.release import Release
from musigree.offline.loader.parser_base import ParserBase
from musigree.offline.loader.parser_utils import ParserUtils

log = logging.getLogger(__name__)
"""
The logger for the ParserRelease module.
"""


class ParserRelease(ParserBase):
    """
    Parses XML data representing releases.

    This class extends `ParserBase` to provide release-specific parsing
    logic, including handling artist credits, company credits, tracklists,
    formats, identifiers, and label credits.
    """

    # CLASS VARIABLES

    _artists_mapping = {}
    """
    Mapping for artist credit XML elements to their corresponding fields.
    """

    _companies_mapping = {}
    """
    Mapping for company credit XML elements to their corresponding fields.
    """

    _tracks_mapping = {}
    """
    Mapping for track XML elements to their corresponding fields.
    """

    # CLASS METHODS

    @classmethod
    def element_to_artist_credits(cls, element):
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
        result = []
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
    def element_to_company_credits(cls, element):
        """
        Extracts company credit information from an XML element.

        This method parses an XML element containing company credit
        information and returns a list of dictionaries, where each
        dictionary represents a company credit.

        Args:
            element: The XML element containing the company credits.

        Returns:
            list: A list of dictionaries, each representing a company credit.
        """
        result = []
        if element is None or not len(element):
            return result
        for subelement in element:
            data = cls.tags_to_fields(
                subelement,
                ignore_none=True,
                mapping=cls._companies_mapping,
            )
            result.append(data)
        return result

    @classmethod
    def element_to_formats(cls, element):
        """
        Extracts format information from an XML element.

        This method parses an XML element containing format information and
        returns a list of dictionaries, where each dictionary represents a
        format.

        Args:
            element: The XML element containing the formats.

        Returns:
            list: A list of dictionaries, each representing a format.
        """
        result = []
        if element is None or not len(element):
            return result
        for sub_element in element:
            document = {
                "name": sub_element.get("name"),
                "quantity": sub_element.get("qty"),
            }
            if sub_element.get("text"):
                document["text"] = sub_element.get("text")
            if len(sub_element):
                sub_element = sub_element[0]
                descriptions = ParserUtils.element_to_strings(sub_element)
                document["descriptions"] = descriptions
            result.append(document)
        return result

    @classmethod
    def element_to_identifiers(cls, element):
        """
        Extracts identifier information from an XML element.

        This method parses an XML element containing identifier information
        and returns a list of dictionaries, where each dictionary represents
        an identifier.

        Args:
            element: The XML element containing the identifiers.

        Returns:
            list: A list of dictionaries, each representing an identifier.
        """
        result = []
        if element is None or not len(element):
            return result
        for sub_element in element:
            data = {
                "description": sub_element.get("description"),
                "type": sub_element.get("type"),
                "value": sub_element.get("value"),
            }
            result.append(data)
        return result

    @classmethod
    def element_to_label_credits(cls, element):
        """
        Extracts label credit information from an XML element.

        This method parses an XML element containing label credit information
        and returns a list of dictionaries, where each dictionary represents
        a label credit.

        Args:
            element: The XML element containing the label credits.

        Returns:
            list: A list of dictionaries, each representing a label credit.
        """
        result = []
        if element is None or not len(element):
            return result
        for sub_element in element:
            data = {
                # id gets filled in later in EntityDataAccess.resolve_references_from_release
                "catalog_number": sub_element.get("catno"),
                "name": sub_element.get("name"),
            }
            result.append(data)
        return result

    @classmethod
    def element_to_roles(cls, element):
        """
        Extracts role information from an XML element.

        This method parses an XML element containing role information,
        handling the complex format where roles and their details can be
        mixed within brackets.

        Args:
            element: The XML element containing the roles.

        Returns:
            list: A list of dictionaries, each representing a role.
        """

        def from_text(text):
            """
            Helper function to parse role text.

            Args:
                text (str): role string.

            Returns:
                dict: dictionary containing name and detail (if present)
            """
            name = ""
            current_buffer = ""
            details = []
            had_detail = False
            _bracket_depth = 0
            for _character in text:
                if _character == "[":
                    _bracket_depth += 1
                    if _bracket_depth == 1 and not had_detail:
                        name = current_buffer
                        current_buffer = ""
                        had_detail = True
                    elif 1 < _bracket_depth:
                        current_buffer += _character
                elif _character == "]":
                    _bracket_depth -= 1
                    if not _bracket_depth:
                        details.append(current_buffer)
                        current_buffer = ""
                    else:
                        current_buffer += _character
                else:
                    current_buffer += _character
            if current_buffer and not had_detail:
                name = current_buffer
            name = name.strip()
            detail = ", ".join(_.strip() for _ in details)
            result = {"name": name}
            if detail:
                result["detail"] = detail
            return result

        credit_roles: list[dict[str, str]] = []
        if element is None or not element.text:
            return credit_roles or None
        current_text = ""
        bracket_depth = 0
        for character in element.text:
            if character == "[":
                bracket_depth += 1
            elif character == "]":
                bracket_depth -= 1
            elif not bracket_depth and character == ",":
                current_text = current_text.strip()
                if current_text:
                    credit_roles.append(from_text(current_text))
                current_text = ""
                continue
            current_text += character
        current_text = current_text.strip()
        if current_text:
            credit_roles.append(from_text(current_text))
        # log.debug(f"credit_roles: {credit_roles}")
        return credit_roles or None

    @classmethod
    def element_to_tracks(cls, element):
        """
        Extracts track information from an XML element.

        This method parses an XML element containing track information and
        returns a list of dictionaries, where each dictionary represents a
        track.

        Args:
            element: The XML element containing the tracks.

        Returns:
            list: A list of dictionaries, each representing a track.
        """
        result = []
        if element is None or not len(element):
            return result
        for sub_element in element:
            data = cls.tags_to_fields(
                sub_element,
                ignore_none=True,
                mapping=cls._tracks_mapping,
            )
            result.append(data)
        return result

    @classmethod
    def from_element(cls, element) -> Release:
        """
        Creates a `Release` domain object from an XML element.

        This method takes an XML element and uses the `tags_to_fields`
        method to extract the relevant data. It then creates and returns a
        `Release` object.

        Args:
            element: The XML element.

        Returns:
            Release: The created `Release` object.
        """
        data = cls.tags_to_fields(element)
        return Release(**data)

    @classmethod
    def preprocess_data(cls, data, element):
        """
        Preprocesses the extracted release data.

        This method performs preprocessing steps on the data extracted from
        an XML element, such as setting the `release_id`, ensuring that
        `identifiers`, `master_id`, and `notes` are present (even if they
        are `None`),

        Args:
            data (dict): The data extracted from the XML element.
            element: The XML element.

        Returns:
            dict: The preprocessed data.
        """
        if element.tag == "release":
            data["release_id"] = int(element.get("id"))
            if "identifiers" not in data:
                data["identifiers"] = None
            if "master_id" not in data:
                data["master_id"] = None
            if "notes" not in data:
                data["notes"] = None
        return data


ParserRelease._tags_to_fields_mapping = {
    "id": ("id", ParserUtils.element_to_integer),
    "artists": ("artists", ParserRelease.element_to_artist_credits),
    "companies": ("companies", ParserRelease.element_to_company_credits),
    "country": ("country", ParserUtils.element_to_string),
    "extraartists": ("extra_artists", ParserRelease.element_to_artist_credits),
    "formats": ("formats", ParserRelease.element_to_formats),
    "genres": ("genres", ParserUtils.element_to_strings),
    "identifiers": ("identifiers", ParserRelease.element_to_identifiers),
    "labels": ("labels", ParserRelease.element_to_label_credits),
    "master_id": ("master_id", ParserUtils.element_to_integer),
    "notes": ("notes", ParserUtils.element_to_none),
    "released": ("release_date", ParserUtils.element_to_datetime),
    "styles": ("styles", ParserUtils.element_to_strings),
    "title": ("title", ParserUtils.element_to_string),
    "tracklist": ("tracklist", ParserRelease.element_to_tracks),
}
"""
Mapping of XML tags to fields for release elements.
"""

ParserRelease._artists_mapping = {
    "id": ("id", ParserUtils.element_to_integer),
    "name": ("name", ParserUtils.element_to_string),
    "anv": ("anv", ParserUtils.element_to_string),
    "join": ("join", ParserUtils.element_to_string),
    "role": ("roles", ParserRelease.element_to_roles),
    "tracks": ("tracks", ParserUtils.element_to_string),
}
"""
Mapping of XML tags to fields for artist credit elements.
"""

ParserRelease._companies_mapping = {
    "id": ("id", ParserUtils.element_to_integer),
    "name": ("name", ParserUtils.element_to_string),
    "catno": ("catalog_number", ParserUtils.element_to_string),
    "entity_type": ("entity_type", ParserUtils.element_to_integer),
    "entity_type_name": ("entity_type_name", ParserUtils.element_to_string),
}
"""
Mapping of XML tags to fields for company credit elements.
"""

ParserRelease._tracks_mapping = {
    "position": ("position", ParserUtils.element_to_string),
    "title": ("title", ParserUtils.element_to_string),
    "duration": ("duration", ParserUtils.element_to_string),
    "artists": ("artists", ParserRelease.element_to_artist_credits),
    "extraartists": ("extra_artists", ParserRelease.element_to_artist_credits),
}
"""
Mapping of XML tags to fields for track elements.
"""
