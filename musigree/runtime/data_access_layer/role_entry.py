"""
This module defines the `RoleEntry` class, which represents a role entry with an optional detail.

The `RoleEntry` class is used to parse and represent role information from various
sources, such as XML elements or text strings, in the Musigree system. It handles
the extraction of the role's name and any associated details (often found within
brackets). It also provides a method to generate a multiselect mapping of roles
by category for UI purposes.

Key functionalities include:
    - **Parsing from XML**: `from_element` extracts role entries from an XML element's text,
      handling the common pattern of comma-separated roles with optional bracketed details.
    - **Parsing from Text**: `from_text` parses a single text string to create a `RoleEntry`,
      separating the role name from any bracketed details.
    - **Multiselect Mapping**: `get_multiselect_mapping` creates an ordered dictionary mapping
      role categories to lists of role names, suitable for populating a UI multiselect component.
    - **Equality Check**: Implements `__eq__` for comparing `RoleEntry` instances based on
      their name and detail.

The `RoleEntry` class interacts with the following components:
    - `RoleCache`: For accessing the mapping between role names, IDs, and categories.
    - `Element` from `xml.etree.ElementTree`: For handling XML element input.
    - `collections.OrderedDict`: For creating ordered dictionaries.

The module utilizes `logging` for logging operations, `typing` for type hinting,
and `collections` for creating the ordered dictionary. It uses `musigree` library for
musigree specific operations.
"""

import collections
from typing import Self, Any
from xml.etree.ElementTree import Element

from musigree.library.cache.role_cache import RoleCache
from musigree.library.fields.role_type import RoleType


class RoleEntry:
    """
    Represents a role entry with an optional detail.

    This class is used to parse and represent role information, handling both the
    role name and any associated details.
    """

    # CLASS VARIABLES

    # INITIALIZER

    def __init__(self, name: str | None = None, detail: str | None = None) -> None:
        """
        Initializes a RoleEntry instance.

        Args:
            name (str, optional): The name of the role. Defaults to None.
            detail (str, optional): Additional details associated with the role. Defaults to None.
        """
        self._name = name
        """The name of the role."""
        self._detail = detail
        """Additional details associated with the role."""

    def __eq__(self, other: Any) -> bool:
        """
        Checks if two RoleEntry instances are equal.

        Args:
            other (RoleEntry): The other RoleEntry instance to compare.

        Returns:
            bool: True if the instances are equal, False otherwise.
        """
        if not isinstance(other, RoleEntry):
            """If the other object is not a RoleEntry, return False."""
            return False
        return self._name == other.name and self._detail == other.detail

    # PUBLIC METHODS

    @classmethod
    def from_element(cls, element: Element) -> list["RoleEntry"]:
        """
        Extracts role entries from an XML element's text.

        This method parses an XML element's text, which may contain a comma-separated
        list of roles, each with optional bracketed details.

        Args:
            element (Element): The XML element containing the role information.

        Returns:
            list[RoleEntry]: A list of RoleEntry instances parsed from the XML text.
        """
        credit_roles: list["RoleEntry"] = []
        """List to store the created RoleEntry objects."""
        if element is None or not element.text:
            return credit_roles
        current_text = ""
        """The current text being parsed."""
        bracket_depth = 0
        """The current bracket depth."""
        for character in element.text:
            """Iterate through the character in the text."""
            if character == "[":
                bracket_depth += 1
                """Increment the bracket depth."""
            elif character == "]":
                bracket_depth -= 1
                """Decrement the bracket depth."""
            elif not bracket_depth and character == ",":
                """If it's a comma at bracket_depth zero, it's a separator."""
                current_text = current_text.strip()
                if current_text:
                    credit_roles.append(cls.from_text(current_text))
                current_text = ""
                continue
            current_text += character
            """Append the character to the current text."""
        current_text = current_text.strip()
        if current_text:
            credit_roles.append(cls.from_text(current_text))
        return credit_roles

    @classmethod
    def from_text(cls, text: str) -> Self:
        """
        Parses a single text string to create a RoleEntry.

        This method extracts the role name and any bracketed detail from a text
        string.

        Args:
            text (str): The text string containing the role information.

        Returns:
            RoleEntry: A RoleEntry instance parsed from the text.
        """
        role_name = ""
        """The role name."""
        current_buffer = ""
        """The current buffer being processed."""
        details = []
        """The list of details."""
        had_detail = False
        """Flag to indicate if any detail were found."""
        bracket_depth = 0
        """The current bracket depth."""
        for character in text:
            """Iterate through the characters in the text."""
            if character == "[":
                bracket_depth += 1
                """Increment the bracket depth."""
                if bracket_depth == 1 and not had_detail:
                    role_name = current_buffer
                    """Assign the current buffer to the role name."""
                    current_buffer = ""
                    had_detail = True
                elif 1 < bracket_depth:
                    current_buffer += character
                    """Append the character to the current buffer."""
            elif character == "]":
                bracket_depth -= 1
                """Decrement the bracket depth."""
                if not bracket_depth:
                    details.append(current_buffer)
                    """Append the current buffer to the details."""
                    current_buffer = ""
                else:
                    current_buffer += character
                    """Append the character to the current buffer."""
            else:
                current_buffer += character
                """Append the character to the current buffer."""
        if current_buffer and not had_detail:
            role_name = current_buffer
            """If there's a buffer and no detail, assign the buffer to the role name."""
        role_name = role_name.strip()
        role_detail = ", ".join(_.strip() for _ in details)
        """Join the details with comma."""
        role_detail_opt = role_detail or None
        """If no detail use None."""
        return cls(name=role_name, detail=role_detail_opt)

    @classmethod
    def get_multiselect_mapping(cls) -> collections.OrderedDict:
        """
        Creates a multiselect mapping of roles by category.

        This method generates an ordered dictionary that maps role categories to
        lists of role names. This is useful for creating UI components that
        allow the user to select multiple roles, grouped by category.

        Returns:
            collections.OrderedDict: An ordered dictionary mapping role categories to
                lists of role names.
        """
        mapping: collections.OrderedDict[RoleType.Category, list[str]] = collections.OrderedDict()
        """Ordered dictionary to store the mapping."""
        for role_name in sorted(RoleCache.role_name_to_role_id_lookup.keys()):
            """Iterate over all role names."""
            role_id = RoleCache.role_name_to_role_id_lookup[role_name]
            """Get the role ID."""
            role_category = RoleCache.role_id_to_role_category_lookup[role_id]
            """Get the role category."""

            if role_category not in mapping:
                """If the category has not been seen yet."""
                mapping[role_category] = []
                """Create a new list for the category."""
            mapping[role_category].append(role_name)
            """Append the role to the category."""
        return mapping

    # PUBLIC PROPERTIES

    @property
    def detail(self) -> str | None:
        """
        Gets the detail associated with the role.

        Returns:
            str | None: The role detail, or None if no detail is present.
        """
        return self._detail

    @property
    def name(self) -> str | None:
        """
        Gets the name of the role.

        Returns:
            str: The role name.
        """
        return self._name
