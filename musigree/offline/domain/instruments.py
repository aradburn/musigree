"""
This module defines domain objects related to musical instruments, specifically
the `Instrument` class and the `HornbostelSachs` class for instrument classification.

It provides a structured way to represent and categorize musical instruments
within the Musigree system.

Key functionalities include:
    - Representing individual musical instruments with attributes like label,
      instrument names, and description.
    - Representing the Hornbostel-Sachs classification system as a hierarchy of
      instrument categories.
    - Providing iteration capabilities for the Hornbostel-Sachs classification.
"""

__all__ = [
    "Instrument",
    "HornbostelSachs",
]

import logging

from pydantic import ConfigDict, RootModel

from musigree.library.domain.base import InternalDomainObject

log = logging.getLogger(__name__)


class Instrument(InternalDomainObject):
    """
    Represents a musical instrument.

    This class encapsulates information about a specific musical instrument,
    including its label, a list of associated instrument names, and a
    description.

    Attributes:
        label (str): The label or common name of the instrument.
        instruments (List[str]): A list of instrument names associated with
            this instrument. This can include variations or synonyms.
        description (str): A detailed description of the instrument, including
            its characteristics and usage.
    """

    model_config = ConfigDict(alias_generator=lambda field_name: field_name.title())
    """
        Configuration settings for the Pydantic model.

        - `alias_generator`: A function to generate aliases for field names.
                             In this case, it converts field names to title case.
    """

    label: str
    """The label or common name of the instrument."""
    instruments: list[str]
    """
    A list of instrument names associated with this instrument.
    This can include variations or synonyms.
    """
    description: str
    """
    A detailed description of the instrument, including its characteristics and usage.
    """


class HornbostelSachs(RootModel):
    """
    Represents the Hornbostel-Sachs classification system for musical instruments.

    The Hornbostel-Sachs system is a widely used method for classifying musical
    instruments based on how they produce sound. This class provides a structured
    way to represent the hierarchy of instrument categories defined by this system.

    Attributes:
        root (dict[str, Instrument]): A dictionary mapping instrument categories
            (e.g., 'Aerophones', 'Chordophones') to their corresponding
            `Instrument` objects. Each `Instrument` object contains further
            details about the instruments within that category.
    """

    root: dict[str, Instrument]
    """
    A dictionary mapping instrument categories to their corresponding `Instrument` objects.
    """
