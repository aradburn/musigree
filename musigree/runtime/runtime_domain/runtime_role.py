"""
This module defines the offline_domain objects and data structures for representing roles
and their hierarchical organization within the Musigree runtime system,
specifically for use with JSTree.

It provides classes for representing a role (`RuntimeRole`), the state of a
JSTree node (`RuntimeRoleJSTreeState`), an entry in a JSTree
(`RuntimeRoleJSTreeEntry`), a complete JSTree structure (`RuntimeRoleJSTree`),
and a wrapper for JSTree configurations (`RuntimeRoleJSTreeWrapper`).

Key functionalities include:
    - Representing a role with its ID, name, category, and subcategory
      (`RuntimeRole`).
    - Defining the state of a JSTree node with attributes for opened,
      disabled, and selected status (`RuntimeRoleJSTreeState`).
    - Representing a JSTree entry with attributes for its ID, parent, text,
      icon, state, and HTML attributes (`RuntimeRoleJSTreeEntry`).
    - Encapsulating a complete JSTree structure as a list of entries
      (`RuntimeRoleJSTree`).
    - Providing a wrapper for configuring a JSTree with its core structure,
      checkbox settings, and plugins (`RuntimeRoleJSTreeWrapper`).
"""

__all__ = [
    "RuntimeRole",
    "RuntimeRoleJSTree",
    "RuntimeRoleJSTreeEntry",
    "RuntimeRoleJSTreeState",
    "RuntimeRoleJSTreeWrapper",
]

from dataclasses import field

from musigree.library.domain.base import InternalDomainObject
from musigree.library.fields.role_type import RoleType


class RuntimeRole(InternalDomainObject):
    """
    Represents a runtime role.

    This class encapsulates the properties of a role within the Musigree
    system, including its unique identifier, name, category, and subcategory.

    Attributes:
        id (int): The unique identifier for the role.
        role_name (str): The name of the role.
        role_category (RoleType.Category): The category of the role. This is an
            enumeration value from `RoleType.Category`.
        role_subcategory (RoleType.Subcategory): The subcategory of the role.
            This is an enumeration value from `RoleType.Subcategory`.
        role_category_name (str): The name of the role category.
        role_subcategory_name (str): The name of the role subcategory.
    """

    id: int
    """The unique identifier for the role."""
    role_name: str
    """The name of the role."""
    role_category: RoleType.Category
    """The category of the role."""
    role_subcategory: RoleType.Subcategory
    """The subcategory of the role."""
    role_category_name: str
    """The name of the role category."""
    role_subcategory_name: str
    """The name of the role subcategory."""


class RuntimeRoleJSTreeState(InternalDomainObject):
    """
    Represents the state of a node in a JSTree.

    This class defines the visual and interactive state of a node in a JSTree,
    including whether it is opened, disabled, or selected.

    Attributes:
        opened (bool): Indicates if the node is open.
        disabled (bool): Indicates if the node is disabled.
        selected (bool): Indicates if the node is selected.
    """

    opened: bool
    """Indicates if the node is open."""
    disabled: bool
    """Indicates if the node is disabled."""
    selected: bool
    """Indicates if the node is selected."""


class RuntimeRoleJSTreeEntry(InternalDomainObject):
    """
    Represents an entry in a JSTree.

    This class defines the structure of a single entry (node) in a JSTree,
    including its unique identifier, parent node, display text, optional icon,
    state, and HTML attributes.

    Attributes:
        id (str): The unique identifier for the entry.
        parent (str): The parent node identifier.
        text (str): The text of the node.
        icon (str | None): The custom icon for the node.
        state (RuntimeRoleJSTreeState): The state of the node.
        li_attr (dict): The attributes for the generated LI node.
        a_attr (dict): The attributes for the generated A node.
    """

    id: str
    """The unique identifier for the entry."""
    parent: str
    """The parent node identifier."""
    text: str
    """The text of the node."""
    icon: str | None = None
    """The custom icon for the node."""
    state: RuntimeRoleJSTreeState
    """The state of the node."""
    li_attr: dict
    """The attributes for the generated LI node."""
    a_attr: dict
    """The attributes for the generated A node."""


class RuntimeRoleJSTree(InternalDomainObject):
    """
    Represents a JSTree structure.

    This class encapsulates the entire structure of a JSTree, which is
    represented as a list of `RuntimeRoleJSTreeEntry` objects.

    Attributes:
        data (list[RuntimeRoleJSTreeEntry]): A list of JSTree entries.
    """

    data: list[RuntimeRoleJSTreeEntry] = field(default_factory=list)
    """A list of JSTree entries."""


class RuntimeRoleJSTreeWrapper(InternalDomainObject):
    """
    Wrapper for JSTree configuration.

    This class provides a wrapper for configuring a JSTree, including its core
    structure, checkbox settings, and plugins.

    Attributes:
        core (RuntimeRoleJSTree): The core JSTree structure.
        checkbox (dict): The configuration for checkboxes.
        plugins (list[str]): A list of plugins for the JSTree.
    """

    core: RuntimeRoleJSTree
    """The core JSTree structure."""
    checkbox: dict
    """The configuration for checkboxes."""
    plugins: list[str]
    """A list of plugins for the JSTree."""
