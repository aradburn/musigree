"""Split and prune the roles used while searching."""

from musigree.library.cache.role_cache import RoleCache

STRUCTURAL_ROLE_NAMES: frozenset[str] = frozenset({"Alias", "Member Of", "Sublabel Of"})
ROLES_TO_PRUNE: frozenset[str] = frozenset(
    {
        "Released On",
        "Compiled On",
        "Producer",
        "Remix",
        "DJ Mix",
        "Written-By",
    }
)
# Alias edges past this distance explode dense pseudonym clusters.
ALIAS_CUTOFF_DISTANCE = 3
# Once the graph is this full, drop the noisiest roles.
NODE_PRUNE_DIVISOR = 4


class RolePartition:
    """Roles that come from the entity document, and roles that come from the database."""

    __slots__ = ("relational", "structural")

    def __init__(self, structural: tuple[str, ...], relational: tuple[str, ...]) -> None:
        self.structural = structural
        self.relational = relational

    @property
    def all_roles(self) -> list[str]:
        return list(self.structural) + list(self.relational)


def partition_roles(role_names: list[str]) -> RolePartition:
    """Split role names into structural and relational lists, preserving order."""
    if role_names:
        unknown = [name for name in role_names if name not in RoleCache.role_name_to_role_id_lookup]
        if unknown:
            raise ValueError(f"Unknown roles: {', '.join(unknown)}")
    structural: list[str] = []
    relational: list[str] = []
    for role_name in role_names:
        if role_name in STRUCTURAL_ROLE_NAMES:
            structural.append(role_name)
        else:
            relational.append(role_name)
    return RolePartition(tuple(structural), tuple(relational))


def prune_roles(
    role_names: list[str],
    *,
    distance: int,
    node_count: int,
    max_nodes: int,
    center_is_artist: bool,
) -> list[str]:
    """Drop noisy roles once the graph is past the prune threshold.

    Returns a new list. The caller keeps the result and passes it on the
    next distance, so pruning accumulates.
    """
    if distance <= 0 or node_count <= max_nodes / NODE_PRUNE_DIVISOR:
        return list(role_names)
    pruned = [role_name for role_name in role_names if role_name not in ROLES_TO_PRUNE]
    if center_is_artist:
        pruned = [role_name for role_name in pruned if role_name != "Sublabel Of"]
    return pruned


def structural_roles_for_distance(
    structural_roles: tuple[str, ...] | list[str], distance: int
) -> list[str]:
    """Alias links are only walked near the center."""
    if distance < ALIAS_CUTOFF_DISTANCE:
        return list(structural_roles)
    return [role_name for role_name in structural_roles if role_name != "Alias"]


def roles_for_database(
    active_roles: list[str], structural_roles: tuple[str, ...] | list[str]
) -> list[str]:
    """Roles to load from the database, including structural roles for release years."""
    roles_to_load = list(active_roles)
    for role_name in structural_roles:
        if role_name not in roles_to_load:
            roles_to_load.append(role_name)
    return roles_to_load
