"""
This module defines the `RuntimeRoleDataAccess` class, which provides data
access methods for roles in the Musigree runtime system.

It handles the loading of all roles from the runtime database, building a
role tree for UI components, and managing role-related caches for efficient
lookups.

Key functionalities include:
    - **`load_all_roles`**: Loads all roles from the runtime database and
      populates the `RoleCache` with various role-related mappings,
      such as role ID to name, role ID to category, and role name to ID.
    - **`build_role_tree`**: Constructs a hierarchical tree structure of
      roles for UI components, such as a JavaScript tree (jstree). It
      organizes roles by category and subcategory and sets the default
      selection state for specific roles.
    - **Caching**: Utilizes `RoleCache` for efficient storage and retrieval
      of role data.
    - **Role Tree**: Creates the `jstree` for UI by using the
      `RuntimeRoleJSTreeEntry` and `RuntimeRoleJSTreeState`.
    - **Database Interaction**: Interacts with `RuntimeRoleRepository` for
      database operations related to roles.
    - **UI default Roles**: Use `UI_DEFAULT_ROLES` to set the selected state
    of the roles.
    - **Logging**: Includes logging statements for debugging and tracking
      the loading process.

The `RuntimeRoleDataAccess` class interacts with the following components:
    - `RoleCache`: For caching role data.
    - `RoleType`: For managing role categories and subcategories.
    - `RuntimeRoleRepository`: For database operations related to roles.
    - `RuntimeRole`: For representing a role in the runtime system.
    - `RuntimeRoleJSTreeState`: For representing a state in the jstree.
    - `RuntimeRoleJSTreeEntry`: For representing an entry in the jstree.
    - `runtime_transaction`: A decorator for managing database transactions.
    - `logging`: For logging operations.
    - `UI_DEFAULT_ROLES`: For managing the default selected roles.
    - `LOGGING_TRACE`: to check if the trace logging is activated.

The module utilizes `logging` for logging operations, `typing` for type
hinting and interacts with `musigree` library for specific cache and type.
"""

import logging

from musigree.app.fastapi_ui import UI_DEFAULT_ROLES
from musigree.library.cache.role_cache import RoleCache
from musigree.library.fields.role_type import RoleType
from musigree.logging_config import LOGGING_TRACE
from musigree.runtime.runtime_database.runtime_role_repository import (
    RuntimeRoleRepository,
)
from musigree.runtime.runtime_database.runtime_transaction import runtime_transaction
from musigree.runtime.runtime_domain.role import (
    RuntimeRole,
    RuntimeRoleJSTreeState,
    RuntimeRoleJSTreeEntry,
)

log = logging.getLogger(__name__)
"""
The logger for the RuntimeRoleDataAccess module.
"""


class RuntimeRoleDataAccess:
    """
    Provides data access methods for roles in the Musigree runtime system.

    This class handles loading roles from the runtime database, building a role
    tree, and managing role-related caches.
    """

    @classmethod
    async def build_role_tree(cls, roles: list[RuntimeRole]) -> None:
        """
        Builds a hierarchical tree structure of roles for UI components.

        This method organizes roles by category and subcategory, creating a tree
        structure suitable for a JavaScript tree (jstree). It also sets the
        default selection state for specific roles based on `UI_DEFAULT_ROLES`.

        Args:
            roles (list[RuntimeRole]): A list of `RuntimeRole` objects.
        """
        for category_name in sorted(RoleType.category_names.values()):
            """Iterate over each category."""
            state = RuntimeRoleJSTreeState(opened=False, disabled=False, selected=False)
            """Create the `RuntimeRoleJSTreeState` object."""
            tree_entry = RuntimeRoleJSTreeEntry(
                id=category_name,
                parent="#",
                text=category_name,
                icon=None,
                state=state,
                li_attr={},
                a_attr={},
            )
            """Create the `RuntimeRoleJSTreeEntry` object."""
            RoleCache.role_jstree.data.append(tree_entry)
            """Add the entry to the role jstree."""
            RoleCache.role_category_to_role_name_lookup[category_name] = []
            """Add empty array to category lookup."""

        for subcategory_name in sorted(RoleType.subcategory_names.values()):
            """Iterate over each subcategory."""
            if (
                subcategory_name
                is not RoleType.subcategory_names[RoleType.Subcategory.NONE]
            ):
                """Skip the NONE subcategory."""
                state = RuntimeRoleJSTreeState(
                    opened=False, disabled=False, selected=False
                )
                """Create the `RuntimeRoleJSTreeState` object."""
                tree_entry = RuntimeRoleJSTreeEntry(
                    id=subcategory_name,
                    parent="Instruments",
                    text=subcategory_name,
                    icon=None,
                    state=state,
                    li_attr={},
                    a_attr={},
                )
                """Create the `RuntimeRoleJSTreeEntry` object."""
                RoleCache.role_jstree.data.append(tree_entry)
                """Add the entry to the role jstree."""
                RoleCache.role_category_to_role_name_lookup[subcategory_name] = []
                """Add empty array to category lookup."""

        for role in sorted(
            roles,
            key=lambda k: (
                k.model_dump()["role_category_name"],
                k.model_dump()["role_subcategory_name"],
                k.model_dump()["role_name"],
            ),
        ):
            """Iterate over each role."""
            if role.role_subcategory is not RoleType.Subcategory.NONE:
                """Get the parent based on the subcategory."""
                parent = role.role_subcategory_name
            else:
                """Or on the category."""
                parent = role.role_category_name
            if role.role_name in UI_DEFAULT_ROLES:
                """Check if the role is selected by default."""
                state = RuntimeRoleJSTreeState(
                    opened=False, disabled=False, selected=True
                )
            else:
                """Or not."""
                state = RuntimeRoleJSTreeState(
                    opened=False, disabled=False, selected=False
                )
            """Create the `RuntimeRoleJSTreeState` object."""
            tree_entry = RuntimeRoleJSTreeEntry(
                id=str(role.id),
                parent=parent,
                text=role.role_name,
                icon=None,
                state=state,
                li_attr={},
                a_attr={},
            )
            """Create the `RuntimeRoleJSTreeEntry` object."""
            RoleCache.role_jstree.data.append(tree_entry)
            """Add the entry to the role jstree."""
            RoleCache.role_category_to_role_name_lookup[parent].append(role.role_name)
            """Add the role name to the category lookup."""

    @classmethod
    async def load_all_roles_into_cache(cls) -> None:
        """
        Loads all roles from the runtime database and populates the RoleCache.

        This method retrieves all roles from the runtime database, then
        populates the `RoleCache` with various mappings, including:
            - role ID to role name
            - role ID to role category
            - role name to role ID
            - set of role names

        The method populates the following cache structures:
        - role_id_to_role_name_lookup: Maps role IDs to role names
        - role_id_to_role_category_lookup: Maps role IDs to role categories
        - role_name_to_role_id_lookup: Maps role names to role IDs
        - role_name_set: Set of all role names

        After loading the roles, it builds the role tree structure and logs
        the number of roles loaded.
        """

        log.debug("Loading roles from RoleRepository")
        RoleCache.role_id_to_role_name_lookup.clear()
        RoleCache.role_id_to_role_category_lookup.clear()
        RoleCache.role_name_to_role_id_lookup.clear()
        RoleCache.role_name_set.clear()
        """Clear the cache."""

        async with runtime_transaction():
            """Ensure that database operations are performed within a transaction."""
            role_repository = RuntimeRoleRepository()
            """Get the instance of the `RuntimeRoleRepository`."""
            roles = role_repository.all()

            role_list = []
            async for role in roles:
                """Iterate over the roles."""
                RoleCache.role_id_to_role_name_lookup[role.id] = role.role_name
                """Add the mapping from id to name."""
                RoleCache.role_id_to_role_category_lookup[role.id] = role.role_category
                """Add the mapping from id to category."""
                role_list.append(role)
                """Also collect roles for the tree building."""
                if LOGGING_TRACE:
                    """If trace logging is enabled."""
                    log.debug(role.role_name)
                    """Log each role name."""

            await cls.build_role_tree(role_list)
            """Build the role tree."""

        RoleCache.role_name_to_role_id_lookup = {
            v: k for k, v in RoleCache.role_id_to_role_name_lookup.items()
        }
        """Add the mapping from name to id."""
        for role_name in RoleCache.role_id_to_role_name_lookup.values():
            """Iterate over the role names."""
            RoleCache.role_name_set.add(role_name)
            """Add the role name in the set."""
        if LOGGING_TRACE:
            """If the trace logging is enable."""
            sorted_list = sorted(RoleCache.role_name_set)
            """Sort the list."""
            for item in sorted_list:
                """Iterate over the role."""
                log.debug(f"{item}")
                """Log the role name."""
        log.debug(
            f"Loaded {len(RoleCache.role_name_to_role_id_lookup)} roles from RoleRepository"
        )
