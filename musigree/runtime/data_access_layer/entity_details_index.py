import logging
import re

from musigree.utils import calculate_size

log = logging.getLogger(__name__)


class EntityDetailsIndex:
    """
    Provides an index for efficiently storing and retrieving detailed information
    about entities, including their countries, genres, and styles.

    This class maintains separate indexes for countries, genres, and styles,
    allowing quick lookups of this information for a given entity ID. It
    also provides methods for calculating and logging the size of the indexes.

    Attributes:
        entity_countries (dict[int, list[int]]): A dictionary mapping entity IDs to
            lists of country indexes.
        countries_list (list[str]): A list of unique country names, serving as a
            lookup table for country indexes.
        entity_genres (dict[int, list[int]]): A dictionary mapping entity IDs to
            lists of genre indexes.
        genres_list (list[str]): A list of unique genre names, serving as a
            lookup table for genre indexes.
        entity_styles (dict[int, list[int]]): A dictionary mapping entity IDs to
            lists of style indexes.
        styles_list (list[str]): A list of unique style names, serving as a
            lookup table for style indexes.
    """

    def __init__(self) -> None:
        """
        Initializes an empty EntityDetailsIndex.
        """
        self.entity_countries: dict[int, list[int]] = {}
        self.countries_list: list[str] = []
        self.entity_genres: dict[int, list[int]] = {}
        self.genres_list: list[str] = []
        self.entity_styles: dict[int, list[int]] = {}
        self.styles_list: list[str] = []

    @staticmethod
    def split_country(country: str) -> list[str]:
        # Match regex pattern for country names that should not be split
        if match := re.search(r"(.*),(\s*)(Democratic Republic of the|Republic of the|Republic of|Isle of|The)$",
                              country):
            country = match.group(3).strip() + " " + match.group(1).strip()
        return re.split(r"[&,/]", country)

    def index_country(self, id_: int, country: str) -> None:
        """
        Indexes a country for a given entity ID.

        The country name is split into tokens based on delimiters (&, /, ,), normalized
        by stripping whitespace, and then added to the index if not already present.

        Args:
            id_: The ID of the entity.
            country: The name of the country.
        """

        for token in self.split_country(country):
            normalized_token = token.strip()
            if normalized_token == "":
                continue
            if id_ not in self.entity_countries:
                self.entity_countries[id_] = []
            if normalized_token not in self.countries_list:
                self.countries_list.append(normalized_token)
            country_index = self.countries_list.index(normalized_token)
            if country_index not in self.entity_countries[id_]:
                self.entity_countries[id_].append(country_index)
            # print(f"country add: {id_}: {self.entity_countries[id_]}")

    def index_genre(self, id_: int, genre: str) -> None:
        """
        Indexes a genre for a given entity ID.

        The genre name is split into tokens based on delimiters (&, /, ,), normalized
        by stripping whitespace, and then added to the index if not already present.

        Args:
            id_: The ID of the entity.
            genre: The name of the genre.
        """
        for token in re.split(r"[&,/]", genre):
            normalized_token = token.strip()
            if normalized_token == "":
                continue
            if id_ not in self.entity_genres:
                self.entity_genres[id_] = []
            if normalized_token not in self.genres_list:
                self.genres_list.append(normalized_token)
            genres_index = self.genres_list.index(normalized_token)
            if genres_index not in self.entity_genres[id_]:
                self.entity_genres[id_].append(genres_index)
            # print(f"details add: {id_}: {self.entity_genres[id_]}")

    def index_style(self, id_: int, style: str) -> None:
        """
        Indexes a style for a given entity ID.

        The style name is split into tokens based on delimiters (&, /, ,), normalized
        by stripping whitespace, and then added to the index if not already present.

        Args:
            id_: The ID of the entity.
            style: The name of the style.
        """
        for token in re.split(r"[&,/]", style):
            normalized_token = token.strip()
            if normalized_token == "":
                continue
            if id_ not in self.entity_styles:
                self.entity_styles[id_] = []
            if normalized_token not in self.styles_list:
                self.styles_list.append(normalized_token)
            styles_index = self.styles_list.index(normalized_token)
            if styles_index not in self.entity_styles[id_]:
                self.entity_styles[id_].append(styles_index)
            # print(f"details add: {id_}: {self.entity_styles[id_]}")

    def get_countries_for_id(self, id_: int) -> str | None:
        """
        Gets a comma-separated string of country names for a given entity ID.

        Args:
            id_: The ID of the entity.

        Returns:
            str | None: A comma-separated string of country names, or None if no
                countries are found for the entity.
        """
        entity_countries = self.entity_countries.get(id_)
        if entity_countries is None:
            return None
        entity_countries_strs = [
            self.countries_list[country_index] for country_index in entity_countries
        ]
        sorted_entity_countries_strs = sorted(entity_countries_strs)
        return ",".join(sorted_entity_countries_strs)

    def get_genres_for_id(self, id_: int) -> str | None:
        """
        Gets a comma-separated string of genre names for a given entity ID.

        Args:
            id_: The ID of the entity.

        Returns:
            str | None: A comma-separated string of genre names, or None if no
                genres are found for the entity.
        """
        entity_genres = self.entity_genres.get(id_)
        if entity_genres is None:
            return None
        entity_genres_strs = [
            self.genres_list[genre_index] for genre_index in entity_genres
        ]
        sorted_entity_genres_strs = sorted(entity_genres_strs)
        return ",".join(sorted_entity_genres_strs)

    def get_styles_for_id(self, id_: int) -> str | None:
        """
        Gets a comma-separated string of style names for a given entity ID.

        Args:
            id_: The ID of the entity.

        Returns:
            str | None: A comma-separated string of style names, or None if no
                styles are found for the entity.
        """
        entity_styles = self.entity_styles.get(id_)
        if entity_styles is None:
            return None
        entity_styles_strs = [
            self.styles_list[style_index] for style_index in entity_styles
        ]
        sorted_entity_styles_strs = sorted(entity_styles_strs)
        return ",".join(sorted_entity_styles_strs)

    def print_sizes(self) -> None:
        """
        Calculates and logs the size of the various indexes in the class.
        """
        log.debug(f"number of entity_countries : {len(self.entity_countries)}")
        size_entity_countries = calculate_size(self.entity_countries)
        log.debug(f"size of entity_countries   : {size_entity_countries}")
        log.debug(f"number of countries        : {len(self.countries_list)}")

        log.debug(f"number of entity_genres    : {len(self.entity_genres)}")
        size_entity_genres = calculate_size(self.entity_genres)
        log.debug(f"size of entity_genres      : {size_entity_genres}")
        log.debug(f"number of genres           : {len(self.genres_list)}")

        log.debug(f"number of entity_styles    : {len(self.entity_styles)}")
        size_entity_styles = calculate_size(self.entity_styles)
        log.debug(f"size of entity_styles      : {size_entity_styles}")
        log.debug(f"number of styles           : {len(self.styles_list)}")

    def print_details(self) -> None:
        """
        Prints the contents of the various indexes in the class.
        """
        log.debug("")
        log.debug("Countries")
        log.debug("=========")
        for country in self.countries_list:
            log.debug(country)
        # for entry in self.entity_countries.items():
        #     print(entry)
        log.debug("")
        log.debug("Genres")
        log.debug("=========")
        for genre in self.genres_list:
            log.debug(genre)
        # for entry in self.entity_genres.items():
        #     print(entry)
        log.debug("")
        log.debug("Styles")
        log.debug("=========")
        for style in self.styles_list:
            log.debug(style)
        log.debug("\n")
        # for entry in self.entity_styles.items():
        #     print(entry)
