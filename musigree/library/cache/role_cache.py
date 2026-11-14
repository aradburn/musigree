import logging
from typing import TYPE_CHECKING, Any

from musigree.runtime.runtime_domain.runtime_role import (
    RuntimeRoleJSTree,
    RuntimeRoleJSTreeEntry,
    RuntimeRoleJSTreeWrapper,
)

if TYPE_CHECKING:
    from musigree.library.fields.role_type import RoleType

log = logging.getLogger(__name__)


class RoleCache:
    """
    A cache for roles, providing lookups and data structures for role-related information.

    This class manages various mappings and data structures to efficiently access
    and retrieve role information, such as role IDs, names, categories, and a
    JSON tree representation for the UI.

    Attributes:
        role_name_to_role_id_lookup (dict[str, int]): A dictionary mapping role names to role IDs.
        role_name_set (Set[str]): A set containing all role names.
        role_id_to_role_category_lookup (dict[int, RoleType.Category]): A dictionary mapping role IDs to role categories.
        role_id_to_role_name_lookup (dict[int, str]): A dictionary mapping role IDs to role names.
        role_jstree (RuntimeRoleJSTree): A tree structure representing roles for the UI.
        role_category_to_role_name_lookup (dict[str, list[str]]): A dictionary mapping role categories to lists of role names.
    """

    # CLASS VARIABLES
    role_name_to_role_id_lookup: dict[str, int] = {}  # noqa: RUF012
    role_name_set: set[str] = set()  # noqa: RUF012
    role_id_to_role_category_lookup: dict[int, RoleType.Category] = {}  # noqa: RUF012
    role_id_to_role_name_lookup: dict[int, str] = {}  # noqa: RUF012
    role_jstree: RuntimeRoleJSTree = RuntimeRoleJSTree()
    role_category_to_role_name_lookup: dict[str, list[str]] = {}  # noqa: RUF012

    # role_categories: Set[str] = set()

    @staticmethod
    def get_all_roles() -> dict[str, Any]:
        """
        Retrieves all roles with their IDs, names, and categories.

        Returns:
            dict: A dictionary containing a list of roles, where each role is a dictionary
                  with 'id', 'role_name', and 'role_category' keys.
        """
        roles = []
        for role_id, role_name in RoleCache.role_id_to_role_name_lookup.items():
            role_category = RoleCache.role_id_to_role_category_lookup[role_id]
            role = {
                "id": role_id,
                "role_name": role_name,
                "role_category": role_category.name,
            }
            roles.append(role)
        data = {"roles": roles}
        return data

    @staticmethod
    def get_roles_json(selected_roles: set[str] | None = None) -> str:
        """
        Retrieves a JSON representation of the roles in a tree structure.

        The cached tree stays unselected. Pass ``selected_roles`` to mark those
        role names in the JSON for this response without changing the cache.

        Args:
            selected_roles: Role names to mark selected. ``None`` keeps the
                cached selection flags.

        Returns:
            str: A JSON string representing the roles in a tree structure, suitable for UI
            rendering.
        """
        tree = RoleCache.role_jstree
        if selected_roles is not None:
            tree = _tree_with_selected_roles(tree, selected_roles)
        roles_data = RuntimeRoleJSTreeWrapper(
            core=tree,
            checkbox={"keep_selected_style": False},
            plugins=["checkbox"],
        )
        roles_json = roles_data.model_dump_json()
        return roles_json


def _tree_with_selected_roles(
    tree: RuntimeRoleJSTree,
    selected_roles: set[str],
) -> RuntimeRoleJSTree:
    """Return a copy of ``tree`` with role nodes selected by name.

    Only role nodes, whose ids are numeric, are matched against
    ``selected_roles``. Category and subcategory nodes stay unselected.
    """
    data: list[RuntimeRoleJSTreeEntry] = []
    for entry in tree.data:
        is_selected = entry.id.isdecimal() and entry.text in selected_roles
        if entry.state.selected == is_selected:
            data.append(entry)
            continue
        data.append(
            entry.model_copy(
                update={
                    "state": entry.state.model_copy(update={"selected": is_selected}),
                }
            )
        )
    return tree.model_copy(update={"data": data})
