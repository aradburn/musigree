"""Search bounds for one relation graph."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GraphLimits:
    """How far a search may grow.

    ``max_links`` is the per-entity cap used when deciding whether a
    neighborhood is small enough to fetch and cache.
    """

    degree: int
    max_nodes: int
    link_ratio: int

    def __post_init__(self) -> None:
        if self.degree <= 0:
            raise ValueError("degree must be positive")
        if self.max_nodes <= 0:
            raise ValueError("max_nodes must be positive")
        if self.link_ratio <= 0:
            raise ValueError("link_ratio must be positive")

    @property
    def max_links(self) -> int:
        return self.max_nodes * self.link_ratio


def resolve_limits(degree: int, max_nodes: int | None, link_ratio: int | None) -> GraphLimits:
    """Fill missing bounds from the runtime database helper.

    The helper import stays inside this function because the helper module
    imports ``RelationGrapher`` at module level.
    """
    resolved_nodes = max_nodes
    resolved_ratio = link_ratio
    if resolved_nodes is None or resolved_ratio is None:
        from musigree.runtime.runtime_database.runtime_database_helper import (
            RuntimeDatabaseHelper,
        )

        if resolved_nodes is None:
            resolved_nodes = RuntimeDatabaseHelper.MAX_NODES
        if resolved_ratio is None:
            resolved_ratio = RuntimeDatabaseHelper.LINK_RATIO
    return GraphLimits(
        degree=int(degree),
        max_nodes=int(resolved_nodes),
        link_ratio=int(resolved_ratio),
    )
