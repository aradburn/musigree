"""Merge database rows into the links collected so far."""

from typing import TYPE_CHECKING

from musigree.library.fields.entity_id import to_entity_internal_id

if TYPE_CHECKING:
    from musigree.runtime.data_access_layer.trellis_node import TrellisNode
    from musigree.runtime.runtime_domain.runtime_relation import RuntimeRelationResult

# Role name, then the two entity ends ordered so direction does not matter.
EndsKey = tuple[str, tuple[str, int], tuple[str, int]]

# Unordered internal ids of the two entities on a link.
EntityPair = tuple[int, int]

# A relation batch this many times max_links is too wide to keep expanding.
RELATION_STOP_MULTIPLIER = 3

MEMBER_OF_ROLE = "Member Of"


def apply_release_years(
    relations: dict[str, RuntimeRelationResult],
    releases_by_ends: dict[EndsKey, dict[str, int | None]],
) -> None:
    """Copy database release years onto links that were built without them."""
    for link_key, relation in list(relations.items()):
        releases = releases_by_ends.get(relation.ends_key)
        if not releases:
            continue
        merged = dict(relation.releases or {})
        merged.update(releases)
        if merged != relation.releases:
            relations[link_key] = relation.model_copy(update={"releases": merged})


def merge_database_relations(
    relations: dict[str, RuntimeRelationResult],
    database_relations: list[RuntimeRelationResult],
    structural_role_names: set[str],
) -> None:
    """Add relational links and copy release years onto structural links.

    Structural roles are already represented by links built from the entity
    document. Database rows for those roles only contribute release years,
    matched by ``ends_key`` so either direction attaches.
    """
    releases_by_ends: dict[EndsKey, dict[str, int | None]] = {}
    for relation in database_relations:
        if relation.releases:
            releases_by_ends.setdefault(relation.ends_key, {}).update(relation.releases)
        if relation.role not in structural_role_names:
            relations[relation.link_key] = relation
    apply_release_years(relations, releases_by_ends)


def commit_relations(
    links: dict[str, RuntimeRelationResult],
    relations: dict[str, RuntimeRelationResult],
    nodes: dict[int, TrellisNode],
) -> list[int]:
    """Store links and return internal ids that are not nodes yet.

    A new link with no release years does not replace one that already
    has them. Self-links are not stored.
    """
    next_ids: set[int] = set()
    for link_key, relation in sorted(relations.items()):
        if not relation.entity_one_id or not relation.entity_two_id:
            continue
        id_one = to_entity_internal_id(relation.entity_one_id, relation.entity_one_type)
        id_two = to_entity_internal_id(relation.entity_two_id, relation.entity_two_type)
        if id_one not in nodes:
            next_ids.add(id_one)
        if id_two not in nodes:
            next_ids.add(id_two)
        if id_one == id_two:
            continue
        previous = links.get(link_key)
        if relation.releases is None and previous is not None and previous.releases:
            relation = previous
        links[link_key] = relation
    return sorted(next_ids)


def _relation_volume(node: TrellisNode | None) -> int:
    """How many relation rows an entity is expected to have.

    This is the cost of scanning that entity's relation index. Structural
    links are not rows, so an entity known only through membership still
    counts as small.
    """
    if node is None or not node.entity.relation_counts:
        return 0
    return sum(count for count in node.entity.relation_counts.values() if isinstance(count, int))


def _entity_pair(relation: RuntimeRelationResult) -> EntityPair | None:
    """Unordered internal ids for a link, or None when the link is a self-loop."""
    id_one = to_entity_internal_id(relation.entity_one_id, relation.entity_one_type)
    id_two = to_entity_internal_id(relation.entity_two_id, relation.entity_two_type)
    if id_one == id_two:
        return None
    if id_one < id_two:
        return id_one, id_two
    return id_two, id_one


def release_year_probes(
    links: dict[str, RuntimeRelationResult],
    nodes: dict[int, TrellisNode],
) -> dict[int, set[int]]:
    """Pick the smaller end of each undated link to read release years from.

    Alias, Member Of, and Sublabel Of links come from the entity document, so
    they have no release year of their own. Years live on other roles between
    the same two entities. Scanning the smaller end keeps that lookup on a
    short index range.
    """
    probes: dict[int, set[int]] = {}
    volumes: dict[int, int] = {}
    for relation in links.values():
        if relation.releases is not None:
            continue
        pair = _entity_pair(relation)
        if pair is None:
            continue
        id_one, id_two = pair
        if id_one not in volumes:
            volumes[id_one] = _relation_volume(nodes.get(id_one))
        if id_two not in volumes:
            volumes[id_two] = _relation_volume(nodes.get(id_two))
        # Two entities with no credit rows have no release year to find.
        if volumes[id_one] == 0 and volumes[id_two] == 0:
            continue
        if (volumes[id_one], id_one) <= (volumes[id_two], id_two):
            probe, other = id_one, id_two
        else:
            probe, other = id_two, id_one
        probes.setdefault(probe, set()).add(other)
    return probes


def _year_inside(year: int, min_year: int | None, max_year: int | None) -> bool:
    """True when ``year`` falls inside the inclusive bounds. A missing bound is open."""
    lower_ok = min_year is None or year >= min_year
    upper_ok = max_year is None or year <= max_year
    return lower_ok and upper_ok


def restrict_links_to_year_bounds(
    links: dict[str, RuntimeRelationResult],
    min_year: int | None,
    max_year: int | None,
) -> dict[str, RuntimeRelationResult]:
    """Drop links whose known years all fall outside the bounds.

    A link with no known year stays. A link that has a year inside the bounds
    stays, and years outside the bounds are removed from it. No bounds means
    every link stays as it is.
    """
    if min_year is None and max_year is None:
        return links
    kept: dict[str, RuntimeRelationResult] = {}
    for link_key, relation in links.items():
        known_years = relation._release_years()
        if not known_years:
            kept[link_key] = relation
            continue
        if not any(_year_inside(year, min_year, max_year) for year in known_years):
            continue
        releases = relation.releases or {}
        trimmed = {
            release_id: year
            for release_id, year in releases.items()
            if year is None or _year_inside(year, min_year, max_year)
        }
        if trimmed == releases:
            kept[link_key] = relation
            continue
        kept[link_key] = relation.model_copy(update={"releases": trimmed})
    return kept


def drop_undated_center_member_links(
    links: dict[str, RuntimeRelationResult],
    nodes: dict[int, TrellisNode],
    center_id: int,
    min_year: int | None,
    max_year: int | None,
) -> dict[str, RuntimeRelationResult]:
    """Drop center Member Of links that have no release years.

    A year filter is set, and this membership has no credit years in that
    range. Memberships farther from the center are left in place.
    """
    if min_year is None and max_year is None:
        return links
    center = nodes.get(center_id)
    if center is None:
        return links
    drop = {
        key
        for key in center.links
        if key in links and links[key].role == MEMBER_OF_ROLE and not links[key]._release_years()
    }
    if not drop:
        return links
    return {key: relation for key, relation in links.items() if key not in drop}


def apply_cross_role_release_years(
    links: dict[str, RuntimeRelationResult],
    releases_by_pair: dict[EntityPair, dict[str, int | None]],
) -> int:
    """Copy any-role release years onto links that were stored without them.

    A link that already has its own releases is left alone. Returns how many
    links gained a release map.
    """
    if not releases_by_pair:
        return 0
    filled = 0
    for link_key, relation in list(links.items()):
        if relation.releases is not None:
            continue
        pair = _entity_pair(relation)
        if pair is None:
            continue
        releases = releases_by_pair.get(pair)
        if not releases:
            continue
        links[link_key] = relation.model_copy(update={"releases": dict(releases)})
        filled += 1
    return filled


def relation_limit_reached(distance: int, relation_count: int, max_links: int) -> bool:
    """Stop expanding when this pass found nothing, or far too many links."""
    if relation_count == 0:
        return True
    if relation_count >= max_links * RELATION_STOP_MULTIPLIER:
        return True
    return distance > 1 and relation_count >= max_links
