"""
This module defines the offline_domain objects for representing roles within the Musigree system.

It provides classes for handling roles, including their representation before
runtime_database persistence (`RoleUncommitted`) and after runtime_database persistence (`Role`).

Key functionalities include:
    - Representing roles with attributes like name, category, and subcategory.
    - Providing a separate class for roles before they are committed to the
      runtime_database (`RoleUncommitted`).
    - Managing roles with an ID after they are stored in the runtime_database (`Role`).
    - Categorizing roles using the `RoleType` enumeration for main categories and
      subcategories.
"""

__all__ = [
    "RoleUncommitted",
    "Role",
]

from pydantic import StrictInt
from musigree.library.domain.base import InternalDomainObject
from musigree.library.fields.role_type import RoleType


class _RoleBase(InternalDomainObject):
    """
    Base class for role entities.

    This class defines the common attributes shared by all role entities
    in the Musigree system. It provides a structure for roles with a name,
    category, and subcategory.

    Attributes:
        role_name (str): The name of the role (e.g., 'Producer', 'Remixer').
        role_category (RoleType.Category): The main category to which the
            role belongs (e.g., 'Production', 'Management'). This is an
            enumeration value from `RoleType.Category`.
        role_subcategory (RoleType.Subcategory): The subcategory to which the
            role belongs (e.g., 'Mix', 'Executive'). This is an enumeration
            value from `RoleType.Subcategory`.
        role_category_name (str): The name of the main category to which the role belongs.
        role_subcategory_name (str): The name of the subcategory to which the role belongs.
    """

    role_name: str
    """The name of the role."""
    role_category: RoleType.Category
    """The main category of the role."""
    role_subcategory: RoleType.Subcategory
    """The subcategory of the role."""
    role_category_name: str
    """The name of the main category of the role."""
    role_subcategory_name: str
    """The name of the subcategory of the role."""


class RoleUncommitted(_RoleBase):
    """
    Represents a role before it is persisted into the runtime_database.

    This class is used to hold the data for a new role before it is
    assigned an ID and stored in the runtime_database. It inherits attributes
    from `_RoleBase`.
    """

    pass


class Role(_RoleBase):
    """
    Represents a role after it has been stored in the runtime_database.

    This class reflects the internal representation of a role in the
    runtime_database, with an ID, name, category and subcategory.

    Attributes:
        id (StrictInt): The unique identifier for the role. This is assigned by
            the runtime_database when the role is stored.
    """

    id: StrictInt
    """The unique identifier for the role."""
