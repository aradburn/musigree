"""
This module defines the common base for all Domain Objects.
"""

import json
from typing import Any, TypeVar

from pydantic import BaseModel, ConfigDict

__all__ = [
    "InternalDomainObject",
    "_InternalDomainObject",
    "PublicDomainObject",
    "_PublicDomainObject",
]

from musigree import utils


def to_camelcase(string: str) -> str:
    """
    Converts a string from snake_case to camelCase.

    This function splits the input string by underscores and capitalizes each word
    except the first one, then joins the words together.

    Args:
        string (str): The input string in snake_case.

    Returns:
        str: The converted string in camelCase.
    """
    resp = "".join(
        word.capitalize() if index else word for index, word in enumerate(string.split("_"))
    )
    return resp


# Deprecated json_encoders replaced with field_serializer decorators in subclasses


class InternalDomainObject(BaseModel):
    """
    Base class for internal domain objects.

    These objects are used internally within the application and have specific
    configuration settings for validation and data handling.

    Attributes:
        model_config (ConfigDict): Configuration settings for the Pydantic model.
            - extra: "ignore" to ignore extra fields during validation.
            - use_enum_values: False to use enum values directly.
            - validate_assignment: True to validate field assignments.
            - arbitrary_types_allowed: False to disallow arbitrary types.
            - from_attributes: True to enable creating models from attributes.

    """

    model_config = ConfigDict(
        extra="ignore",
        use_enum_values=False,
        validate_assignment=True,
        arbitrary_types_allowed=False,
        from_attributes=True,
    )

    def __repr__(self) -> str:
        """
        Returns a normalized dictionary representation of the model.

        Returns:
            str: A string representation of the normalized dictionary.
        """
        return utils.normalize_dict(self.model_dump())


_InternalDomainObject = TypeVar("_InternalDomainObject", bound=InternalDomainObject)


class PublicDomainObject(BaseModel):
    """
    Base class for public domain objects.

    These objects are exposed to the outside world and have specific
    configuration settings for alias generation and data handling.

    Attributes:
        model_config (ConfigDict): Configuration settings for the Pydantic model.
            - extra: "ignore" to ignore extra fields during validation.
            - use_enum_values: False to use enum values directly.
            - validate_assignment: True to validate field assignments.
            - arbitrary_types_allowed: True to allow arbitrary types.
            - from_attributes: True to enable creating models from attributes.

            - loc_by_alias: True to locate fields by alias.
            - alias_generator: The function to generate aliases for field names.
    """

    model_config = ConfigDict(
        extra="ignore",
        use_enum_values=False,
        validate_assignment=True,
        arbitrary_types_allowed=True,
        from_attributes=True,
        loc_by_alias=True,
        alias_generator=to_camelcase,
    )

    def flat_dict(self, by_alias: bool = True) -> dict[str, Any]:
        """
        Returns a flattened dictionary representation of the model.

        This method converts the model to a dictionary that contains only primitive
        data types that are allowed by JSON format.

        Args:
            by_alias (bool): Whether to use aliases for field names.

        Returns:
            dict: A flattened dictionary representation of the model.
        """
        return json.loads(self.model_dump_json(by_alias=by_alias))  # type: ignore


_PublicDomainObject = TypeVar("_PublicDomainObject", bound=PublicDomainObject)
