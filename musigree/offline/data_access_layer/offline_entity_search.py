import logging
import re
from typing import Any

import rapidfuzz

from musigree.exceptions import DatabaseError
from musigree.library.fields.entity_id import (
    LABEL_ENTITY_ID_OFFSET,
    to_entity_external_id,
)
from musigree.library.full_text_search.text_search_index import TextSearchIndex
from musigree.library.full_text_search.text_search_utils import (
    normalise_search_content,
)
from musigree.offline.offline_database.entity_repository import EntityRepository
from musigree.offline.offline_database.token_repository import TokenRepository
from musigree.offline.offline_database_manager import OfflineDatabaseManager
from musigree.offline.offline_domain.entity import Entity

log = logging.getLogger(__name__)


class OfflineEntitySearch:
    @staticmethod
    async def search_entities(
        entity_repository: EntityRepository,
        token_repository: TokenRepository,
        search_string: str,
    ) -> dict[str, Any]:
        assert OfflineDatabaseManager.offline_database_helper is not None, (
            "OfflineDatabaseManager.offline_database_helper is not set."
        )
        documents = await OfflineEntitySearch.search_text_index(
            entity_repository, token_repository, search_string
        )

        sorted_documents = OfflineEntitySearch.sort_search_results(search_string, documents)

        data: list[dict[str, str]] = []
        for document in sorted_documents:
            entity_id, entity_type = to_entity_external_id(document[0])
            json_entity_key = Entity.to_json_entity_key(entity_id, entity_type)
            datum = dict(
                key=json_entity_key,
                name=document[1],
            )
            data.append(datum)
            # log.debug(f"    {datum}")
        result_data = {"results": tuple(data)}
        return result_data

    @staticmethod
    def sort_search_results(
        search_string: str,
        documents: list[tuple[int, str]],
    ) -> list[tuple[int, str]]:
        scored_documents: list[tuple[float, tuple[int, str]]] = list()
        for document in documents:
            candidate_id = document[0]
            candidate_name = document[1]
            score = rapidfuzz.distance.JaroWinkler.normalized_distance(
                search_string, candidate_name
            )

            matched_digits = re.match(r"(.*) \((\d+)\)", candidate_name)

            # Boost candidates that match and order by the number in brackets
            # eg. Test (1) is better than Test (23)
            if matched_digits:
                digits = matched_digits.group(2)
                if matched_digits.group(1) == search_string:
                    score += 1.0 + (1000.0 - int(digits)) / 1000.0
                else:
                    score += (1000.0 - int(digits)) / 1000.0

            # Boost candidates that start with the given search string
            if candidate_name.lower().startswith(search_string.lower()):
                score += 1.0

            # Boost candidates that are an exact match
            if candidate_name.lower() == search_string.lower():
                score += 100.0

            # Penalise candidates that differ in length (longer or shorter)
            len_diff = abs(len(candidate_name) - len(search_string)) / 100.0
            score -= len_diff

            # Put artists before labels
            if candidate_id >= LABEL_ENTITY_ID_OFFSET:
                score -= 10.0

            scored_documents.append((score, document))
        sorted_documents = sorted(
            scored_documents,
            key=lambda scored_document: scored_document[0],
            reverse=True,
        )
        result_documents = [sorted_document[1] for sorted_document in sorted_documents]
        return result_documents

    @staticmethod
    async def search_text_index(
        entity_repository: EntityRepository,
        token_repository: TokenRepository,
        search_text: str,
    ) -> list[tuple[int, str]]:
        """
        Searches the offline_database for documents matching the query.

        This method returns documents that contain all of the query terms, and
        ranks them based on their relevance to the query.

        Args:
            entity_repository: The offline entity repository.
            token_repository: The token repository.
            search_text: The text to search for.

        Returns:
            list[tuple[int, str]]: A list of tuples, where each tuple contains a
                document ID and the corresponding document text, ordered by relevance.
        """
        from musigree.offline.data_access_layer.offline_entity_data_access import (
            OfflineEntityDataAccess,
        )

        # Normalize the query and filter out stop words
        normalized_query = normalise_search_content(search_text)
        analyzed_query = [
            token for token in normalized_query.split() if token not in TextSearchIndex.STOP_WORDS
        ]

        # Handle empty query after filtering stop words
        if not analyzed_query:
            return []

        result_sets = await OfflineEntitySearch.get_lists_of_ids_from_token_db(
            token_repository, analyzed_query
        )

        # all tokens must be in the document
        search_results: list[tuple[int, str]] = []
        document_results: set[int] = set.intersection(*result_sets)
        for id_ in document_results:
            name = await OfflineEntityDataAccess.get_entity_name_by_id(entity_repository, id_)
            if name is not None:
                document_entry = (id_, name)
                search_results.append(document_entry)
        return search_results

    @staticmethod
    async def get_lists_of_ids_from_token_db(
        token_repository: TokenRepository, analyzed_query: list[str]
    ) -> list[set[int]]:
        """
        Retrieves the sets of document IDs for each token in a query.

        Args:
            token_repository: The token reporitory.
            analyzed_query: A list of tokens in the query.

        Returns:
            list[set[int]]: A list of sets, where each set contains the document IDs
                for a token in the query.
        """
        result_ids_list: list[set[int]] = []
        for token in analyzed_query:
            result_ids = await OfflineEntitySearch.get_ids_from_token_db(token_repository, token)
            result_ids_list.append(result_ids)
        return result_ids_list

    @staticmethod
    async def get_ids_from_token_db(token_repository: TokenRepository, token: str) -> set[int]:
        result_set: set[int] = set[int]()
        try:
            """Attempt to get the entity ids for the token."""
            token_ids = await token_repository.get_by_token(token)
            result_set = set[int](token_ids)

        except DatabaseError:
            """Handle potential offline_database errors."""
            log.error("Error in text_search data access")

        return result_set
