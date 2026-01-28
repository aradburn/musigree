"""
This module provides data access functionality for relations within the Musigree offline system.

It defines the `OfflineRelationDataAccess` class, which offers methods for extracting
relations from `Release` objects, determining relationships between artists and
labels, handling compilations, and converting between different relation
representations. It is designed to be used during the offline data loading
process.

Key functionalities include:
    - Extracting relations from `Release` objects, considering artists, extra
      artists, companies, and track information.
    - Determining artist-label relationships based on release data, handling
      compilations differently.
    - Identifying and handling compilation releases, where various artists
      are credited on individual tracks.
    - Normalizing role names using `OfflineRoleDataAccess` to ensure consistency.
    - Converting relations between internal and external representations.
    - Finding relations based on a key (subject, role, object).

The `OfflineRelationDataAccess` class interacts with `OfflineRoleDataAccess` for role
normalization and lookup, `EntityRepository` for entity operations, and
`RelationRepository` for relation operations. It uses `Relation`,
`RelationInternal`, and `Release` from `musigree.offline.offline_domain` for
representing relation and release data, and `RoleType` for managing role
types.

The module utilizes logging for debugging and error reporting.
"""

import itertools
import logging
from typing import Any

from musigree.library.fields.role_type import RoleType
from musigree.offline.data_access_layer.offline_role_data_access import OfflineRoleDataAccess
from musigree.offline.data_access_layer.role_data_utils import RoleDataUtils
from musigree.offline.offline_database.relation_repository import RelationRepository
from musigree.offline.offline_domain.relation import Relation, RelationUncommitted
from musigree.offline.offline_domain.release import Release

log = logging.getLogger(__name__)
"""
The logger for the OfflineRelationDataAccess module.
"""


class OfflineRelationDataAccess:
    """
    Provides data access functionality for relations within the Musigree offline system.

    This class offers methods for extracting relations from `Release` objects,
    determining relationships between artists and labels, handling compilations,
    and converting between different relation representations.
    """

    @classmethod
    def from_release(cls, release: Release) -> list[RelationUncommitted]:
        """
        Extracts relations from a `Release` object.

        This method analyzes a `Release` object and extracts all the relations
        present within it, considering artists, extra artists, companies, and
        track information. It handles various types of relationships, including
        artist-label relations, artist-artist relations, and artist-company
        relations.

        Args:
            release (Release): The release object to extract relations from.

        Returns:
            list[RelationUncommitted]: A list of uncommitted relations.
        """
        # log.debug(f"      release: {release}")
        triples: set[tuple[int, str, int]] = set()
        """Set to store unique triples of (subject_id, role, object_id)."""
        artist_ids, label_ids, is_compilation = cls.get_release_setup(release)
        """Get the artist IDs, label IDs, and compilation status from the release."""

        triples.update(
            cls.get_artist_label_relations(
                artist_ids,
                label_ids,
                is_compilation,
            )
        )
        """Update the triples with artist-label relations."""
        aggregate_roles: dict[str, Any] = {}
        """Dictionary to store aggregate roles and their associated artist IDs."""

        if is_compilation:
            iterator = itertools.product(label_ids, release.extra_artists or [])
        else:
            iterator = itertools.product(artist_ids, release.extra_artists or [])
        """Determine the iterator based on whether the release is a compilation."""
        for object_id, credit in iterator:
            if object_id is not None and credit is not None and "roles" in credit:
                for roles in credit["roles"]:
                    if "name" in roles:
                        input_role_str: str = roles["name"]
                        role_str_list = RoleDataUtils.normalise_role_names(input_role_str)
                        """Normalize the role names."""
                        for role_str in role_str_list:
                            role_name = OfflineRoleDataAccess.find_role(role_str)
                            """Find the normalized role name."""
                            if role_name is not None:
                                if role_name in RoleType.aggregate_roles:
                                    if role_name not in aggregate_roles:
                                        aggregate_roles[role_name] = []
                                    if "id" in credit:
                                        aggregate_credit_id = credit["id"]
                                        aggregate_roles[role_name].append(aggregate_credit_id)
                                else:
                                    if "id" in credit:
                                        triples.add((credit["id"], role_name, object_id))

        if is_compilation:
            iterator = itertools.product(label_ids, release.companies or [])
        else:
            iterator = itertools.product(artist_ids, release.companies or [])
        """Determine the iterator based on whether the release is a compilation."""
        for subject_id, company in iterator:
            if subject_id is not None and company is not None and "entity_type_name" in company:
                company_role_str = company["entity_type_name"]
                company_role_strs_list = RoleDataUtils.normalise_role_names(company_role_str)
                """Normalize the role names."""
                for role_str in company_role_strs_list:
                    role_name = OfflineRoleDataAccess.find_role(role_str)
                    """Find the normalized role name."""
                    if role_name is not None:
                        if "id" in company:
                            triples.add((subject_id, role_name, company["id"]))

        all_track_artist_ids: set[int] = set()
        """Set to store all unique artist IDs from tracks."""
        for track in release.tracklist or []:
            track_artist_ids: set[int] = set(
                artist["id"] for artist in track.get("artists", ()) if "id" in artist
            )
            all_track_artist_ids.update(track_artist_ids)
            if not track.get("extra_artists"):
                continue
            track_artist_ids = track_artist_ids or artist_ids or label_ids
            iterator = itertools.product(track_artist_ids, track["extra_artists"] or [])
            for object_id, credit in iterator:
                for roles in credit.get("roles", ()):
                    track_role_str: str = roles["name"]
                    track_role_strs_list = RoleDataUtils.normalise_role_names(track_role_str)
                    """Normalize the role names."""
                    for role_str in track_role_strs_list:
                        role_name = OfflineRoleDataAccess.find_role(role_str)
                        """Find the normalized role name."""
                        if role_name is not None:
                            if "id" in credit:
                                subject_id = credit["id"]
                                triples.add((subject_id, role_name, object_id))

        for role_name, aggregate_artists in aggregate_roles.items():
            iterator = itertools.product(all_track_artist_ids, aggregate_artists)
            for track_artist_id, aggregate_artist_id in iterator:
                subject_id = aggregate_artist_id
                object_id = track_artist_id
                triples.add((subject_id, role_name, object_id))
        # log.debug(f"triples3: {triples}")
        triples_list = list(triples)
        """Sort the triples for consistency."""
        # log.debug(f"      triples: {triples}")
        relation_dicts = cls.from_triples(triples_list, release=release)
        """Convert the triples to a list of relations."""
        # log.debug(f"      relations: {relations}")
        relations = RelationUncommitted.from_dicts(relation_dicts)

        return relations

    @classmethod
    def get_artist_label_relations(
        cls,
        artist_ids: set[int],
        label_ids: set[int],
        is_compilation: bool,
    ) -> set[tuple[int, str, int]]:
        """
        Determines artist-label relations for a release.

        This method determines the relationships between artists and labels
        based on whether the release is a compilation or not.

        Args:
            artist_ids (set[int]): A set of artist IDs.
            label_ids (set[int]): A set of label IDs.
            is_compilation (bool): Whether the release is a compilation.

        Returns:
            set[tuple[int, str, int]]: A set of unique triples representing
                (artist_id, role, label_id).
        """
        triples = set()
        """Set to store unique triples of (artist_id, role, label_id)."""
        iterator = itertools.product(artist_ids, label_ids)
        """Create an iterator for all combinations of artists and labels."""
        if is_compilation:
            role = "Compiled On"
        else:
            role = "Released On"
        """Determine the role based on compilation status."""
        for artist_id, label_id in iterator:
            triples.add((artist_id, role, label_id))
        return triples

    @classmethod
    def get_release_setup(cls, release: Release) -> tuple[set[int], set[int], bool]:
        """
        Extracts the setup information from a release.

        This method extracts the artist IDs, label IDs, and determines if the
        release is a compilation.

        Args:
            release: The release object.

        Returns:
            tuple[set[int], set[int], bool]: A tuple containing the artist IDs,
                label IDs, and the compilation status.
        """
        is_compilation = False
        """Boolean to indicate if a release is a compilation."""
        # log.debug(f"get_release_setup release: {release}")
        artist_ids: set[int] = set(
            artist["id"] for artist in (release.artists or []) if "id" in artist
        )
        """Set to store unique artist IDs."""
        # log.debug(f"get_release_setup artists: {artist_ids}")
        label_ids: set[int] = set(label["id"] for label in (release.labels or []) if "id" in label)
        """Set to store unique label IDs."""
        # log.debug(f"get_release_setup labels: {label_ids}")

        # noinspection PyTypeHints
        if (
            len(artist_ids) == 1
            and release.artists
            and release.artists[0]["name"] in ["Various", "Various Artists"]
        ):
            is_compilation = True
            artist_ids.clear()
            for track in release.tracklist or []:
                artist_ids.update(
                    artist["id"] for artist in track.get("artists", ()) if "id" in artist
                )
            # log.debug(f"get_release_setup various artists: {artist_ids}")
        return artist_ids, label_ids, is_compilation

    @classmethod
    def from_triples(
        cls, triples: list[tuple[int, str, int]], release: Release | None = None
    ) -> list[dict[str, Any]]:
        """
        Converts a list of triples to a list of relations.

        This method takes a list of triples (subject_id, role, object_id) and
        converts them into a list of relation dictionaries.

        Args:
            triples: A set of triples.
            release: The release object (optional).

        Returns:
            list[dict[str, Any]]: A list of relation dictionaries.
        """
        triples_set = set(triples)
        sorted_triples = sorted(list(triples_set))
        relations = []
        for subject_id, role, object_id in sorted_triples:
            relation: dict[str, Any] = dict(
                subject=subject_id,
                role=role,
                object=object_id,
            )
            if release is not None:
                relation["release_id"] = release.release_id
                if release.release_date is not None:
                    relation["year"] = release.release_date.year
                else:
                    relation["year"] = None
            relations.append(relation)
        return relations

    @classmethod
    async def get_relation_by_key(
        cls,
        relation_repository: RelationRepository,
        key: dict[str, Any],
    ) -> Relation | None:
        """
        Retrieves a relation by its key.

        Args:
            relation_repository: The relation repository.
            key: The key to search for.

        Returns:
            Relation: The found relation.
        """
        relation_internals = await relation_repository.find_by_key(key)
        relation = Relation.from_relation_internals(relation_internals)
        return relation
