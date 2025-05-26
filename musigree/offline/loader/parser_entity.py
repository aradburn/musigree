"""
This module defines the `ParserEntity` class, which is responsible for parsing
XML data representing entities (artists and labels) in the Musigree offline
system.

It extends the `ParserBase` class to provide entity-specific parsing logic,
including handling aliases, groups, members, parent labels, sublabels,
and other entity metadata.

Key functionalities include:
    - **`element_to_names`**: Extracts a dictionary of names from an XML
      element. Used for aliases and groups.
    - **`element_to_names_and_ids`**: Extracts a dictionary of names and their
      corresponding Discogs IDs from an XML element. Used for members.
    - **`element_to_parent_label`**: Extracts a dictionary containing a parent
      label name from an XML element.
    - **`element_to_sublabels`**: Extracts a dictionary of sublabel names from
      an XML element.
    - **`from_element`**: Creates an `Entity` domain object from an XML element.
    - **`preprocess_data`**: Preprocesses the extracted data, organizing it
      into `entity_metadata` and `entities` dictionaries, normalizing the
      entity name for search, and setting the `entity_type`. It also converts
      the element id into an internal entity id.
    - **Tag-to-Field Mapping**: Defines a mapping (`_tags_to_fields_mapping`)
      that specifies how XML tags should be processed and mapped to the fields
      of an `Entity` object.

The `ParserEntity` class interacts with the following components:
    - `ParserBase`: The base class for XML parsing, providing common parsing
      functionalities.
    - `ParserUtils`: For generic XML parsing utilities, such as converting
      elements to strings or integers.
    - `Entity`: The domain object representing an entity (artist or label).
    - `EntityType`: An enum representing the different types of entities.
    - `to_entity_internal_id`: A function for converting an external entity id
    to an internal one.
    - `normalise_search_content`: A function for normalising content for
      search purposes.
    - `logging`: For logging operations.

The module utilizes `logging` for logging operations, `Element` from
`xml.etree.ElementTree` for XML handling, and `typing` for type hinting. It
also uses `musigree` library for musigree specific operations.
"""

import logging
from xml.etree.ElementTree import Element

from musigree.library.fields.entity_id import to_entity_internal_id
from musigree.library.full_text_search.text_search_utils import (
    normalise_search_content,
)
from musigree.offline.domain.entity import Entity
from musigree.library.fields.entity_type import EntityType
from musigree.offline.loader.parser_base import ParserBase
from musigree.offline.loader.parser_utils import ParserUtils

log = logging.getLogger(__name__)
"""
The logger for the ParserEntity module.
"""


class ParserEntity(ParserBase):
    """
    Parses XML data representing entities (artists and labels).

    This class extends `ParserBase` to provide entity-specific parsing
    logic, including handling aliases, groups, members, parent labels,
    sublabels, and other entity metadata.
    """

    # CLASS METHODS

    @classmethod
    def element_to_names(cls, names):
        """
        Extracts a dictionary of names from an XML element.

        This method is used to extract names from XML elements that
        represent lists of names, such as aliases or groups.

        Args:
            names: The XML element containing the names.

        Returns:
            dict: A dictionary where keys are the names and values are None.
        """
        result = {}
        if names is None or not len(names):
            return result
        for name in names:
            name = name.text
            if not name:
                continue
            result[name] = None
        return result

    @classmethod
    def element_to_names_and_ids(cls, names_and_ids: Element):
        """
        Extracts a dictionary of names and their corresponding Discogs IDs.

        This method is used to extract names and their IDs from XML elements
        that represent lists of members.

        Args:
            names_and_ids (Element): The XML element containing the names and IDs.

        Returns:
            dict: A dictionary where keys are names and values are their Discogs IDs.
        """
        # print(f"names_and_ids1: {[(item.tag, item.text) for item in names_and_ids]}")
        result = {}
        if names_and_ids is None or not len(names_and_ids):
            return result
        current_discogs_id = 0
        for item in names_and_ids:
            if item.tag == "id":
                current_discogs_id = int(item.text)
            elif item.tag == "name":
                result[item.text] = current_discogs_id
                current_discogs_id = 0
        return result

    @classmethod
    def element_to_parent_label(cls, parent_label):
        """
        Extracts a dictionary containing a parent label name.

        This method is used to extract the name of a parent label from an
        XML element.

        Args:
            parent_label: The XML element containing the parent label.

        Returns:
            dict: A dictionary where the key is the parent label name and the value is None.
        """
        result = {}
        if parent_label is None or parent_label.text is None:
            return result
        name = parent_label.text.strip()
        if not name:
            return result
        result[name] = None
        return result

    @classmethod
    def element_to_sublabels(cls, sublabels):
        """
        Extracts a dictionary of sublabel names from an XML element.

        This method is used to extract a list of sublabel names from an
        XML element.

        Args:
            sublabels: The XML element containing the sublabels.

        Returns:
            dict: A dictionary where keys are sublabel names and values are None.
        """
        result = {}
        if sublabels is None or not len(sublabels):
            return result
        for sublabel in sublabels:
            name = sublabel.text
            if name is None:
                continue
            name = name.strip()
            if not name:
                continue
            result[name] = None
        return result

    @classmethod
    def from_element(cls, element) -> Entity:
        """
        Creates an `Entity` domain object from an XML element.

        This method uses the `tags_to_fields` method to extract data from the
        XML element and then creates a new `Entity` object.

        Args:
            element: The XML element.

        Returns:
            Entity: The created `Entity` object.
        """
        data = cls.tags_to_fields(element)
        return Entity(**data)

    @classmethod
    def preprocess_data(cls, data, element):
        """
        Preprocesses the extracted entity data.

        This method organizes the extracted data into `entity_metadata` and
        `entities` dictionaries, normalizes the entity name for search, and
        sets the `entity_type`.

        Args:
            data (dict): The data extracted from the XML element.
            element: The XML element.

        Returns:
            dict: The preprocessed data.
        """
        if element.tag == "artist" or element.tag == "label":
            data["entity_metadata"] = {}
            data["entities"] = {}
            data["relation_counts"] = {}
            for key in (
                "aliases",
                "groups",
                "members",
                "parent_label",
                "sublabels",
            ):
                if key in data:
                    key_entry = data.pop(key)
                    if key_entry is not None and len(key_entry) > 0:
                        data["entities"][key] = key_entry
            for key in (
                "contact_info",
                "name_variations",
                "profile",
                "real_name",
                "urls",
            ):
                if key in data:
                    data["entity_metadata"][key] = data.pop(key)
            if "entity_name" in data and data.get("entity_name"):
                name = data.get("entity_name")
                data["search_content"] = normalise_search_content(name)
            if element.tag == "artist":
                data["entity_type"] = EntityType.ARTIST
            elif element.tag == "label":
                data["entity_type"] = EntityType.LABEL
            # data["element_id"] = int(element.get("id"))
            data["entity_id"] = data["id"]
            data["id"] = to_entity_internal_id(data["entity_id"], data["entity_type"])
        return data


ParserEntity._tags_to_fields_mapping = {
    "aliases": ("aliases", ParserEntity.element_to_names),
    "contact_info": ("contact_info", ParserUtils.element_to_string),
    "groups": ("groups", ParserEntity.element_to_names),
    "id": ("id", ParserUtils.element_to_integer),
    "members": ("members", ParserEntity.element_to_names_and_ids),
    "name": ("entity_name", ParserUtils.element_to_string),
    "namevariations": ("name_variations", ParserUtils.element_to_strings),
    "parentLabel": ("parent_label", ParserEntity.element_to_parent_label),
    "profile": ("profile", ParserUtils.element_to_string),
    "realname": ("real_name", ParserUtils.element_to_string),
    "sublabels": ("sublabels", ParserEntity.element_to_sublabels),
    "urls": ("urls", ParserUtils.element_to_strings),
}
