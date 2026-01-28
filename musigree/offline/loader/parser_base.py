"""
This module defines the base class for XML parsers in the Musigree offline system.

It provides a foundation for loading data from XML files and converting them
into domain objects. It handles common XML parsing tasks, including iterating
through XML elements, extracting data based on a tag-to-field mapping,
preprocessing data, and creating domain object instances.

Key components:
    - `ParserBase`: An abstract base class for XML parsers.
    - Methods for loading data from XML files (`load_from_xml`).
    - Methods for converting XML tags to database fields (`tags_to_fields`).
    - Methods for preprocessing data before creating domain objects
      (`preprocess_data`).
    - A method for creating an instance from an XML element (`from_element`).
    - A class attribute for defining a tag-to-field mapping (`_tags_to_fields_mapping`).

The `ParserBase` class is designed to be subclassed by specific XML parsers,
which implement the abstract or overridable methods to provide
domain-specific logic and define the tag-to-field mapping.

The module utilizes `gzip` for handling compressed XML files, `logging` for
logging operations, `typing` for type hinting, and `musigree.offline.loader.loader_utils`
for loader-specific utilities. `musigree.offline.loader.parser_utils` is used
for generic XML parsing.
"""

import gzip
import logging
from pathlib import Path
from typing import Self, Any, Generator

from musigree.offline.loader.loader_utils import LoaderUtils
from musigree.offline.loader.parser_utils import ParserUtils
from musigree.offline.offline_domain.entity import Entity
from musigree.offline.offline_domain.release import Release

log = logging.getLogger(__name__)
"""
The logger for the ParserBase module.
"""


class ParserBase:
    """
    Abstract base class for XML parsers.

    This class provides a framework for loading data from XML files and
    converting them into domain objects. It defines common methods for
    iterating through XML elements, extracting data, preprocessing, and
    creating instances.

    Attributes:
        _tags_to_fields_mapping (dict): A mapping from XML tags to database
            fields and procedures. This mapping defines how data should be
            extracted from XML elements and processed.
    """

    _tags_to_fields_mapping: dict[str, tuple] | None = None
    """
    A mapping from XML tags to database fields and procedures.

    This attribute should be defined in subclasses to specify how data
    should be extracted from XML elements. The keys are XML tag names,
    and the values are tuples of (field_name, procedure), where field_name
    is the name of the field in the domain object, and procedure is a
    callable that takes an XML element and returns the corresponding
    value.
    """

    @classmethod
    def load_from_xml(
        cls,
        domain_class: type[Entity | Release],
        discogs_data_directory: Path,
        date: str,
        xml_tag: str,
        id_attr: str,
        skip_without: list[str],
    ) -> Generator[Entity | Release, None, None]:
        """
        Loads data from an XML file.

        This method iterates through an XML file, extracts data, and yields
        new domain objects. It uses `ParserUtils.iterparse` for efficient
        XML parsing and the `tags_to_fields` method to extract data based on
        the tag-to-field mapping.

        Args:
            domain_class: The domain class to create instances of.
                This should be a class with a constructor that accepts
                keyword arguments corresponding to the fields in the
                tag-to-field mapping.
            discogs_data_directory (Path): The directory containing the XML files.
            date (str): The date of the XML data dump.
            xml_tag (str): The XML tag representing the records to load.
                For example, "artist", "label", or "release".
            id_attr (str): The attribute name for the ID in the data.
                This is typically "id" for artists and labels, or "release_id"
                for releases.
            skip_without (list[str]): A list of required fields, skip record if any are missing.
              Records missing any of these fields will be ignored.

        Yields:
            Self: A new instance of the domain class.
        """
        xml_path = LoaderUtils.get_xml_path(discogs_data_directory, xml_tag, date)
        """Get the full path to the XML file."""
        log.info(f"Loading data from {xml_path}")
        with gzip.GzipFile(xml_path, "r") as file_pointer:
            """Open the XML file using gzip to read compressed files."""
            iterator = ParserUtils.iterparse(file_pointer, xml_tag)
            """Get an iterator over the XML elements with the specified tag."""
            for _, element in enumerate(iterator):
                """Iterate over each XML element."""
                data = cls.tags_to_fields(element)
                """Extract the data from the element using the tag-to-field mapping."""
                if skip_without:
                    if any(not data.get(_) for _ in skip_without):
                        continue
                if element.get("id"):
                    data[id_attr] = element.get("id")
                """Extract the ID from the element if present."""
                # log.debug(f"data: {data}")

                new_instance = domain_class(**data)
                """Create a new instance of the domain class using the extracted data."""
                # log.debug(f"new_instance: {new_instance}")
                yield new_instance

    @classmethod
    def from_element(cls, element) -> Self:  # type: ignore
        """
        Creates an instance from an XML element.

        This method is a placeholder for future functionality to create an
        instance of the loader from an XML element. Currently, it does not
        perform any action and should be overridden by subclasses if needed.

        Args:
            element: The XML element.
        """
        pass

    @classmethod
    def preprocess_data(cls, data: dict, element: Any) -> dict[str, Any]:
        """
        Preprocesses data before creating a domain object.

        This method can be overridden by subclasses to perform data
        transformations or cleanup on the extracted data before creating
        a domain object. By default, it returns the data as is.

        Args:
            data (dict): The data extracted from the XML element.
            element: The XML element.

        Returns:
            dict[str, Any]: The preprocessed data.
        """
        return data

    @classmethod
    def tags_to_fields(
        cls,
        element: Any,
        ignore_none: bool | None = None,
        mapping: dict[str, tuple] | None = None,
    ) -> dict[str, Any]:
        """
        Converts XML tags to database fields.

        This method extracts data from an XML element and converts it into a
        dictionary of database fields. It uses a mapping to determine which
        tags correspond to which fields and how they should be processed.

        Args:
            element: The XML element.
            ignore_none (bool, optional): Whether to ignore None values.
                If True, fields with None values will be omitted from the
                returned dictionary. Defaults to None.
            mapping (dict, optional): An optional custom mapping.
                If provided, this mapping will be used instead of the
                `_tags_to_fields_mapping` attribute. Defaults to None.

        Returns:
            dict[str, Any]: A dictionary of database fields and their values.
        """
        data = {}
        """Initialize an empty dictionary to store the extracted data."""
        mapping = mapping or cls._tags_to_fields_mapping or {}
        """Use the custom mapping or the class's default mapping."""
        for child_element in element:
            """Iterate over the child elements of the current element."""
            entry = mapping.get(child_element.tag, None)
            """Get the mapping entry for the child element's tag."""
            if entry is None:
                continue
            """Skip the child element if there's no mapping for its tag."""
            field_name, procedure = entry
            """Extract the field name and the processing procedure from the mapping."""
            value = procedure(child_element)
            """Process the child element using the specified procedure."""
            if ignore_none and value is None:
                continue
            """Skip the field if the value is None and ignore_none is True."""
            data[field_name] = value
            """Store the extracted value in the data dictionary."""
        data = cls.preprocess_data(data, element)
        """Preprocess the extracted data."""
        return data
