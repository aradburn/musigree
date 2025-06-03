"""
This module provides data access functionality for releases within the Musigree offline system.

It defines the `ReleaseDataAccess` class, which offers methods for creating
and managing an `EntityDetailsIndex`. This index stores detailed information
about entities, such as their countries, genres, and styles, derived from
release data. It is designed to be used during the offline data loading
process.

Key functionalities include:
    - Creating an `EntityDetailsIndex` by iterating through all releases.
    - Indexing release-related data (country, genres, styles) for each
      artist and label associated with a release.
    - Logging the progress of indexing and printing index details and sizes.
    - Interacting with `ReleaseRepository` for release data.

The `ReleaseDataAccess` class interacts with `ReleaseRepository` for
database operations and `EntityDetailsIndex` for managing the detailed entity
index. It uses `LoaderBase` to report the progress of bulk operations.

The `Release` class from `musigree.offline.domain` is used to represent releases.
`EntityDetailsIndex` from `musigree.library.full_text_search` is used to manage
the index.
"""

import logging

from musigree.offline.database.release_repository import ReleaseRepository
from musigree.runtime.data_access_layer.entity_details_index import EntityDetailsIndex
from musigree.offline.loader.loader_base import LoaderBase

log = logging.getLogger(__name__)
"""
The logger for the ReleaseDataAccess module.
"""


class ReleaseDataAccess:
    """
    Provides data access functionality for releases within the Musigree offline system.

    This class offers methods for creating and managing an `EntityDetailsIndex`,
    which stores detailed information about entities derived from release data.
    """

    @staticmethod
    def create_entity_details_index(
        release_repository: ReleaseRepository,
    ) -> EntityDetailsIndex:
        """
        Creates an `EntityDetailsIndex` by iterating through all releases.

        This method processes all releases in the database, extracting
        information about the countries, genres, and styles associated with
        each release. It then indexes this information for each artist and
        label involved in the release.

        Args:
            release_repository (ReleaseRepository): The repository for release database operations.

        Returns:
            EntityDetailsIndex: The created and populated `EntityDetailsIndex`.
        """
        log.debug("Create EntityDetailsIndex")
        entity_details_index = EntityDetailsIndex()
        """Create the entity details index instance."""
        count = 0
        for release in release_repository.all():
            """Iterate through all the releases."""
            country = release.country
            """Get the country of the release."""
            if country is not None:
                """Check if the release has a country."""
                for artist in release.artists:
                    """Iterate over artists in the release."""
                    if "id" in artist:
                        entity_details_index.index_country(artist["id"], country)
                        """Index the country for each artist."""
                for label in release.labels:
                    """Iterate over labels in the release."""
                    if "id" in label:
                        entity_details_index.index_country(label["id"], country)
                        """Index the country for each label."""

            if release.genres is not None:
                """Check if the release has genres."""
                for genre in release.genres:
                    """Iterate over genres in the release."""
                    for artist in release.artists:
                        """Iterate over artists in the release."""
                        if "id" in artist:
                            entity_details_index.index_genre(artist["id"], genre)
                            """Index the genre for each artist."""
                    for label in release.labels:
                        """Iterate over labels in the release."""
                        if "id" in label:
                            entity_details_index.index_genre(label["id"], genre)
                            """Index the genre for each label."""

            if release.styles is not None:
                """Check if the release has styles."""
                for style in release.styles:
                    """Iterate over styles in the release."""
                    for artist in release.artists:
                        """Iterate over artists in the release."""
                        if "id" in artist:
                            entity_details_index.index_style(artist["id"], style)
                            """Index the style for each artist."""
                    for label in release.labels:
                        """Iterate over labels in the release."""
                        if "id" in label:
                            entity_details_index.index_style(label["id"], style)
                            """Index the style for each label."""

            count += 1
            if count % (LoaderBase.BULK_REPORTING_SIZE * 100) == 0:
                log.debug(f"Indexed {count} releases")
                """Log the indexing progress."""
        if count % (LoaderBase.BULK_REPORTING_SIZE * 100) != 0:
            log.debug(f"Indexed {count} releases")
            """Log the final number of indexed releases."""
        entity_details_index.print_details()
        """Print the details of the indexed data."""
        entity_details_index.print_sizes()
        """Print the sizes of the different indexed data."""
        return entity_details_index

    # @classmethod
    # def _as_artist_credits(cls, companies):
    #     artists = []
    #     for company in companies:
    #         artist = {
    #             "name": company["name"],
    #             "id": company["id"],
    #             "roles": [{"name": company["entity_type_name"]}],
    #         }
    #         artists.append(artist)
    #     return artists
