import logging
import math
import pickle
import random
from collections import Counter
from pathlib import Path
from typing import Self

from musigree.library.full_text_search.text_search_utils import (
    SEARCH_STOP_WORDS,
    normalise_search_content,
)
from musigree.utils import calculate_size

log = logging.getLogger(__name__)


class TextSearchIndex:
    """
    Provides an inverted index for full-text search capabilities.

    This class builds and manages an inverted index, which maps tokens (words)
    to the IDs of documents (text entries) that contain those tokens. It supports
    indexing, searching, ranking, and persistence via pickling.

    Attributes:
        STOP_WORDS (set[str]): A set of common words to ignore during indexing and searching.
        token_index (dict[str, set[int]]): The inverted index mapping tokens to sets of document IDs.
        documents (dict[int, str]): A mapping of document IDs to their original text content.
        keys (list[int]): A list of all document IDs in the index, used for random access.
    """

    STOP_WORDS = SEARCH_STOP_WORDS
    """Common tokens ignored during indexing and search."""

    def __init__(self) -> None:
        """
        Initializes an empty TextSearchIndex.
        """
        self.token_index: dict[str, list[int]] = {}
        """The inverted index mapping tokens to sets of document IDs."""
        self.documents: dict[int, str] = {}
        """A mapping of document IDs to their original text content."""
        self.keys: list[int] = []
        """A list of all document IDs in the index."""
        self.number_of_documents = 0

    def index_entry(self, id_: int, text: str) -> None:
        """
        Indexes a text entry by adding it to the inverted index.

        The text is normalized, split into tokens, and each token (excluding stop
        words) is added to the index along with the document ID. Hyphenated words
        are also handled by indexing both the hyphenated form and the split words.

        Args:
            id_: The ID of the document being indexed.
            text: The text content of the document.
        """
        # Save the original document to return when searched for
        # log.debug(f"Text indexing: {id_}: {text}")
        self.save_document_text(id_, text)
        self.keys.append(id_)

        normalised_text = normalise_search_content(text)
        self.add_tokens(normalised_text, id_)

        # Handle cases like hyphens in surnames
        if "-" in normalised_text:
            normalised_text_no_hyphens = normalised_text.replace("-", " ")
            self.add_tokens(normalised_text_no_hyphens, id_)

        self.number_of_documents += 1

    def add_tokens(self, tokens: str, id_: int) -> None:
        for token in tokens.split():
            if token in TextSearchIndex.STOP_WORDS:
                continue
            self.add_token(token, id_)

    def add_token(self, token: str, id_: int) -> None:
        if token not in self.token_index:
            self.token_index[token] = list[int]()
        self.token_index[token].append(id_)

    def document_frequency(self, token: str) -> int:
        """
        Calculates the document frequency of a token.

        The document frequency is the number of documents in which the token appears.

        Args:
            token: The token for which to calculate the document frequency.

        Returns:
            int: The document frequency of the token.
        """
        token_occurrences = self.token_index.get(token, list[int]())
        return len(set(token_occurrences))

    def inverse_document_frequency(self, token: str) -> float:
        """
        Calculates the inverse document frequency (IDF) of a token.

        IDF is a measure of how much information the token provides, i.e., whether
        the term is common or rare across all documents. It is calculated using
        log10.

        Args:
            token: The token for which to calculate the IDF.

        Returns:
            float: The IDF of the token.
        """
        # Manning, Hinrich and Schütze use log10, so we do too, even though it
        # doesn't really matter which log we use anyway
        # https://nlp.stanford.edu/IR-book/html/htmledition/inverse-document-frequency-1.html
        return math.log10(self.number_of_documents / self.document_frequency(token))

    def get_ids_from_token_index(self, analyzed_query: list[str]) -> list[list[int]]:
        """
        Retrieves the sets of document IDs for each token in a query.

        Args:
            analyzed_query: A list of tokens in the query.

        Returns:
            list[list[int]]: A list of sets, where each set contains the document IDs
                for a token in the query.
        """
        result_ids_list: list[list[int]] = []
        for token in analyzed_query:
            # result_ids = get_token_ids_from_db(token)
            result_ids = self.token_index.get(token, list[int]())
            result_ids_list.append(result_ids)
        return result_ids_list

    def search(self, query: str) -> list[tuple[int, str]]:
        """
        Searches the index for documents matching the query.

        This method returns documents that contain all of the query terms, and
        ranks them based on their relevance to the query.

        Args:
            query: The query string.

        Returns:
            list[tuple[int, str]]: A list of tuples, where each tuple contains a
                document ID and the corresponding document text, ordered by relevance.
        """
        # Normalize the query and filter out stop words
        normalized_query = normalise_search_content(query)
        analyzed_query = [
            token for token in normalized_query.split() if token not in TextSearchIndex.STOP_WORDS
        ]

        # Handle empty query after filtering stop words
        if not analyzed_query:
            return []

        # log.debug(f"search analyzed_query: {analyzed_query}")

        results = self.get_ids_from_token_index(analyzed_query)
        result_sets = [set[int](result) for result in results]
        # all tokens must be in the document
        search_results: list[tuple[int, str]] = []
        document_results: set[int] = set.intersection(*result_sets)
        for doc_id in document_results:
            document_entry = (doc_id, self.get_document_text(doc_id))
            search_results.append(document_entry)
        return self.rank(analyzed_query, search_results)

    def get_document_text(self, doc_id: int) -> str:
        return self.documents[doc_id]

    def save_document_text(self, id_: int, text: str) -> None:
        self.documents[id_] = text

    def rank(
        self, analyzed_query: list[str], search_results: list[tuple[int, str]]
    ) -> list[tuple[int, str]]:
        """
        Ranks documents based on their relevance to the query.

        The relevance is calculated using TF-IDF (Term Frequency-Inverse Document
        Frequency) scoring.

        Args:
            analyzed_query: A list of query tokens.
            search_results: A list of document ID and text tuples to be ranked.

        Returns:
            list[tuple[int, str]]: A list of document ID and text tuples,
                ordered by their relevance to the query.
        """
        unranked_results: list[tuple[tuple[int, str], float]] = []
        if not search_results:
            return list[tuple[int, str]]()
        for search_result in search_results:
            normalised_name = normalise_search_content(search_result[1])
            term_frequencies = Counter(normalised_name.split())

            score = 0.0
            for token in analyzed_query:
                if token in TextSearchIndex.STOP_WORDS:
                    continue
                tf = term_frequencies.get(token, 0)
                # tf = document.term_frequency(token)
                idf = self.inverse_document_frequency(token)
                score += tf * idf
            unranked_results.append((search_result, score))

        ranked_results = sorted(unranked_results, key=lambda doc: doc[1], reverse=True)
        return [ranked_item[0] for ranked_item in ranked_results]

    def reduce_list_to_set(self) -> None:
        for key, words in self.token_index.items():
            reduced_set = set(words)
            self.token_index[key] = list(reduced_set)

    def generate_list_of_stop_words(self) -> list[str]:
        """
        Identifies and lists potential stop words based on their frequency.

        Words that appear in a large number of documents are considered potential
        stop words.

        Returns:
            list[str]: A list of potential stop words.
        """
        results = {}
        for key, words in self.token_index.items():
            if len(words) > 10000:
                # print(f"{key}: {len(words)}")
                results[key] = len(words)
        log.debug(f"found {len(results)} stop words")
        sorted_results = sorted(results.items(), key=lambda item: int(item[1]))
        for entry in sorted_results:
            print(f"{entry[0]}: {entry[1]}")
        return list(results.keys())

    def print_sizes(self) -> None:
        """
        Calculates and logs the memory size of the index, documents, and keys.
        """
        size_index = calculate_size(self.token_index)
        size_documents = calculate_size(self.documents)
        size_keys = calculate_size(self.keys)
        log.debug(f"number in index  : {self.number_of_documents}")
        log.debug(f"size of index    : {size_index}")
        log.debug(f"size of documents: {size_documents}")
        log.debug(f"size of keys     : {size_keys}")

    def get_random_id(self) -> int:
        """
        Retrieves a random document ID from the index.

        Returns:
            int: A random document ID.
        """
        count = len(self.keys)
        random_index = random.randint(0, count - 1)
        return self.keys[random_index]

    def save_text_search_index_to_file(self, filename: Path) -> None:
        log.debug(f"save text search index to file: {filename}")

        # open a file to store the data
        with open(filename, "wb") as file:
            # dump information to that file
            # noinspection PyTypeChecker
            pickle.dump(self, file)

    @classmethod
    def load_text_search_index_from_file(cls, filename: Path) -> Self:
        """
        Loads a TextSearchIndex from a pickled file.

        Args:
            filename: The path to the pickled file.

        Returns:
            Self: The loaded TextSearchIndex.
        """
        log.debug(f"load text search index from file: {filename}")

        # open a file, where you stored the pickled data
        with open(filename, "rb") as file:
            # read pickle dump information from that file
            text_search_index: TextSearchIndex = pickle.load(file)

        text_search_index.print_sizes()

        # text_search_index.number_of_documents = len(text_search_index.documents)

        # noinspection Mypy
        return text_search_index  # type: ignore
