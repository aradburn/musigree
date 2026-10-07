"""Merge database rows into the links collected so far."""

from musigree.library.fields.entity_id import to_entity_internal_id
from musigree.runtime.data_access_layer.trellis_node import TrellisNode
from musigree.runtime.runtime_domain.runtime_relation import RuntimeRelationResult

# Role name, then the two entity ends ordered so direction does not matter.
EndsKey = tuple[str, tuple[str, int], tuple[str, int]]

# A relation batch this many times max_links is too wide to keep expanding.
RELATION_STOP_MULTIPLIER = 3


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


def relation_limit_reached(distance: int, relation_count: int, max_links: int) -> bool:
    """Stop expanding when this pass found nothing, or far too many links."""
    if relation_count == 0:
        return True
    if relation_count >= max_links * RELATION_STOP_MULTIPLIER:
        return True
    return distance > 1 and relation_count >= max_links
