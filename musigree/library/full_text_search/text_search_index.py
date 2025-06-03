import logging
import math
import pickle
import random
from collections import Counter
from pathlib import Path
from typing import Self, Dict, List

from musigree.library.full_text_search.text_search_utils import (
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
        index (dict[str, set[int]]): The inverted index mapping tokens to sets of document IDs.
        documents (dict[int, str]): A mapping of document IDs to their original text content.
        keys (list[int]): A list of all document IDs in the index, used for random access.
    """

    STOP_WORDS = {
        "the",
        "and",
        "a",
        "of",
        "studio",
        "studios",
        "productions",
        "music",
        "records",
        "recordings",
        "entertainment",
    }
    """
        A set of common words (stop words) to be ignored during indexing and search.
    """

    def __init__(self):
        """
        Initializes an empty TextSearchIndex.
        """
        self.index: Dict[str, List[int]] = {}
        """The inverted index mapping tokens to sets of document IDs."""
        self.documents: Dict[int, str] = {}
        """A mapping of document IDs to their original text content."""
        self.keys: List[int] = []
        """A list of all document IDs in the index."""

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
        self.documents[id_] = text
        self.keys.append(id_)

        normalised_text = normalise_search_content(text)
        for token in normalised_text.split():
            if token in TextSearchIndex.STOP_WORDS:
                continue
            if token not in self.index:
                self.index[token] = list[int]()
            self.index[token].append(id_)
            # log.debug(f"search add: {token}: {self.index[token]}")

        # Handle cases like hyphens in surnames
        if "-" in normalised_text:
            normalised_text = normalised_text.replace("-", " ")
            for token in normalised_text.split():
                if token not in self.index:
                    self.index[token] = list[int]()
                self.index[token].append(id_)
                # log.debug(f"search add: {token}: {self.index[token]}")

    def document_frequency(self, token: str) -> int:
        """
        Calculates the document frequency of a token.

        The document frequency is the number of documents in which the token appears.

        Args:
            token: The token for which to calculate the document frequency.

        Returns:
            int: The document frequency of the token.
        """
        return len(self.index.get(token, list[int]()))

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
        return math.log10(len(self.documents) / self.document_frequency(token))

    def _results(self, analyzed_query: List[str]) -> List[List[int]]:
        """
        Retrieves the sets of document IDs for each token in a query.

        Args:
            analyzed_query: A list of tokens in the query.

        Returns:
            list[set[int]]: A list of sets, where each set contains the document IDs
                for a token in the query.
        """
        return [self.index.get(token, list[int]()) for token in analyzed_query]

    def search(self, query: str) -> List[tuple[int, str]]:
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
        analyzed_query = query.split()
        # log.debug(f"search analyzed_query: {analyzed_query}")

        results = self._results(analyzed_query)
        result_sets = [set[int](result) for result in results]
        # all tokens must be in the document
        documents = [
            (doc_id, self.documents[doc_id])
            for doc_id in set[int].intersection(*result_sets)
        ]
        return self.rank(analyzed_query, documents)

    def rank(
        self, analyzed_query: list[str], documents: list[tuple[int, str]]
    ) -> list[tuple[int, str]]:
        """
        Ranks documents based on their relevance to the query.

        The relevance is calculated using TF-IDF (Term Frequency-Inverse Document
        Frequency) scoring.

        Args:
            analyzed_query: A list of query tokens.
            documents: A list of document ID and text tuples to be ranked.

        Returns:
            list[tuple[int, str]]: A list of document ID and text tuples,
                ordered by their relevance to the query.
        """
        results: list[tuple[tuple[int, str], float]] = []
        if not documents:
            return list[tuple[int, str]]()
        for document in documents:

            normalised_name = normalise_search_content(document[1])
            term_frequencies = Counter(normalised_name.split())

            score = 0.0
            for token in analyzed_query:
                if token in TextSearchIndex.STOP_WORDS:
                    continue
                tf = term_frequencies.get(token, 0)
                # tf = document.term_frequency(token)
                idf = self.inverse_document_frequency(token)
                score += tf * idf
            results.append((document, score))
        ranked = sorted(results, key=lambda doc: doc[1], reverse=True)
        return [ranked_item[0] for ranked_item in ranked]

    def reduce_list_to_set(self):
        for key, words in self.index.items():
            reduced_set = set(words)
            self.index[key] = list(reduced_set)

    def list_stop_words(self) -> list[str]:
        """
        Identifies and lists potential stop words based on their frequency.

        Words that appear in a large number of documents are considered potential
        stop words.

        Returns:
            list[str]: A list of potential stop words.
        """
        results = {}
        for key, words in self.index.items():
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
        size_index = calculate_size(self.index)
        size_documents = calculate_size(self.documents)
        size_keys = calculate_size(self.keys)
        log.debug(f"size of index    : {size_index}")
        log.debug(f"size of documents: {size_documents}")
        log.debug(f"size of keys: {size_keys}")

    def get_random_id(self) -> int:
        """
        Retrieves a random document ID from the index.

        Returns:
            int: A random document ID.
        """
        count = len(self.keys)
        random_index = random.randint(0, count)
        return self.keys[random_index]

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

        return text_search_index
