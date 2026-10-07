"""Unit tests for relation-graph role rules."""

import pytest

from musigree.library.cache.role_cache import RoleCache
from musigree.runtime.data_access_layer.relation_graph.roles import (
    partition_roles,
    prune_roles,
    roles_for_database,
    structural_roles_for_distance,
)

ROLE_LOOKUP = {
    "Artist": 1,
    "Alias": 3,
    "Member Of": 4,
    "Sublabel Of": 5,
    "Producer": 6,
    "Released On": 7,
}


@pytest.fixture
def role_lookup(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(RoleCache, "role_name_to_role_id_lookup", ROLE_LOOKUP)


def test_partition_roles_splits_structural_and_relational(role_lookup: None) -> None:
    roles = partition_roles(["Artist", "Alias", "Member Of"])

    assert roles.structural == ("Alias", "Member Of")
    assert roles.relational == ("Artist",)
    assert roles.all_roles == ["Alias", "Member Of", "Artist"]


def test_partition_roles_rejects_unknown_names(role_lookup: None) -> None:
    with pytest.raises(ValueError, match="Unknown roles"):
        partition_roles(["Not A Role"])


def test_partition_roles_allows_an_empty_list(role_lookup: None) -> None:
    roles = partition_roles([])

    assert roles.structural == ()
    assert roles.relational == ()


def test_prune_roles_drops_noisy_roles_once_the_graph_is_large() -> None:
    pruned = prune_roles(
        ["Artist", "Producer", "Released On"],
        distance=1,
        node_count=30,
        max_nodes=100,
        center_is_artist=False,
    )

    assert pruned == ["Artist"]


def test_prune_roles_keeps_roles_near_the_center_and_on_small_graphs() -> None:
    roles = ["Producer", "Released On"]

    assert (
        prune_roles(roles, distance=0, node_count=30, max_nodes=100, center_is_artist=True) == roles
    )
    assert (
        prune_roles(roles, distance=1, node_count=25, max_nodes=100, center_is_artist=True) == roles
    )


def test_prune_roles_drops_sublabel_of_for_an_artist_center() -> None:
    pruned = prune_roles(
        ["Artist", "Sublabel Of"],
        distance=1,
        node_count=30,
        max_nodes=100,
        center_is_artist=True,
    )

    assert pruned == ["Artist"]


def test_structural_roles_for_distance_drops_alias_after_the_cutoff() -> None:
    roles = ["Alias", "Member Of"]

    assert structural_roles_for_distance(roles, distance=2) == roles
    assert structural_roles_for_distance(roles, distance=3) == ["Member Of"]


def test_roles_for_database_appends_structural_roles_once() -> None:
    assert roles_for_database(["Artist", "Alias"], ["Alias", "Member Of"]) == [
        "Artist",
        "Alias",
        "Member Of",
    ]
