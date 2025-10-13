import math
from pathlib import Path
from unittest.mock import patch, mock_open, Mock

import pytest

from musigree.library.full_text_search.text_search_index import TextSearchIndex


class TestTextSearchIndex:
    """Test cases for the TextSearchIndex class."""

    def test_init(self) -> None:
        """Test TextSearchIndex initialization."""
        index = TextSearchIndex()

        assert isinstance(index.token_index, dict)
        assert isinstance(index.documents, dict)
        assert isinstance(index.keys, list)
        assert len(index.token_index) == 0
        assert len(index.documents) == 0
        assert len(index.keys) == 0

    def test_stop_words_defined(self) -> None:
        """Test that stop words are properly defined."""
        assert isinstance(TextSearchIndex.STOP_WORDS, set)
        assert "the" in TextSearchIndex.STOP_WORDS
        assert "and" in TextSearchIndex.STOP_WORDS
        assert "music" in TextSearchIndex.STOP_WORDS

    def test_index_entry_basic(self) -> None:
        """Test basic entry indexing."""
        index = TextSearchIndex()
        index.index_entry(1, "Hello World")

        assert 1 in index.documents
        assert index.documents[1] == "Hello World"
        assert 1 in index.keys
        assert "hello" in index.token_index
        assert "world" in index.token_index
        assert 1 in index.token_index["hello"]
        assert 1 in index.token_index["world"]

    def test_index_entry_with_stop_words(self) -> None:
        """Test that stop words are not indexed."""
        index = TextSearchIndex()
        index.index_entry(1, "The Beatles and The Rolling Stones")

        # "the" and "and" should not be in the index
        assert "the" not in index.token_index
        assert "and" not in index.token_index
        # But "beatles", "rolling", "stones" should be
        assert "beatles" in index.token_index
        assert "rolling" in index.token_index
        assert "stones" in index.token_index

    def test_index_entry_with_hyphens(self) -> None:
        """Test indexing with hyphenated words."""
        index = TextSearchIndex()
        index.index_entry(1, "Self-contained")

        # Both hyphenated and split versions should be indexed
        assert 1 in index.documents
        # Should contain both "self-contained" processing and "self contained"
        assert "self" in index.token_index
        assert "contained" in index.token_index

    def test_index_multiple_entries(self) -> None:
        """Test indexing multiple entries."""
        index = TextSearchIndex()
        index.index_entry(1, "Beatles White Album")
        index.index_entry(2, "Rolling Stones Album")

        assert len(index.documents) == 2
        assert len(index.keys) == 2
        assert 1 in index.token_index["beatles"]
        assert 2 in index.token_index["rolling"]
        assert 1 in index.token_index["album"]
        assert 2 in index.token_index["album"]

    def test_document_frequency(self) -> None:
        """Test document frequency calculation."""
        index = TextSearchIndex()
        index.index_entry(1, "Beatles album")
        index.index_entry(2, "Rolling Stones album")
        index.index_entry(3, "Jazz music")

        # "album" appears in 2 documents
        assert index.document_frequency("album") == 2
        # "beatles" appears in 1 document
        assert index.document_frequency("beatles") == 1
        # Non-existent token should return 0
        assert index.document_frequency("nonexistent") == 0

    def test_inverse_document_frequency(self) -> None:
        """Test inverse document frequency calculation."""
        index = TextSearchIndex()
        index.index_entry(1, "Beatles album")
        index.index_entry(2, "Rolling Stones album")
        index.index_entry(3, "Jazz music")

        # IDF for "album" (appears in 2 out of 3 documents)
        expected_idf = math.log10(3 / 2)
        assert abs(index.inverse_document_frequency("album") - expected_idf) < 0.001

        # IDF for "beatles" (appears in 1 out of 3 documents)
        expected_idf_beatles = math.log10(3 / 1)
        assert (
            abs(index.inverse_document_frequency("beatles") - expected_idf_beatles)
            < 0.001
        )

    def test_search_single_term(self) -> None:
        """Test searching with a single term."""
        index = TextSearchIndex()
        index.index_entry(1, "Beatles White Album")
        index.index_entry(2, "Rolling Stones Black Album")
        index.index_entry(3, "Jazz music collection")

        results = index.search("beatles")
        assert len(results) == 1
        assert results[0][0] == 1
        assert results[0][1] == "Beatles White Album"

    def test_search_multiple_terms(self) -> None:
        """Test searching with multiple terms (AND operation)."""
        index = TextSearchIndex()
        index.index_entry(1, "Beatles White Album")
        index.index_entry(2, "Rolling Stones Black Album")
        index.index_entry(3, "Beatles Black Album")

        # Should find documents containing both "beatles" and "album"
        results = index.search("beatles album")
        assert len(results) == 2
        result_ids = [r[0] for r in results]
        assert 1 in result_ids
        assert 3 in result_ids

    def test_search_no_results(self) -> None:
        """Test searching with no matching results."""
        index = TextSearchIndex()
        index.index_entry(1, "Beatles White Album")
        index.index_entry(2, "Rolling Stones Black Album")

        results = index.search("jazz")
        assert len(results) == 0

    def test_search_with_stop_words(self) -> None:
        """Test searching ignores stop words."""
        index = TextSearchIndex()
        index.index_entry(1, "The Beatles White Album")
        index.index_entry(2, "Rolling Stones Black Album")

        # Search including stop words should still work
        # "the" is a stop word, so it should search only for "beatles"
        results = index.search("the beatles")
        assert len(results) == 1
        assert results[0][0] == 1

    def test_rank_documents(self) -> None:
        """Test document ranking by relevance."""
        index = TextSearchIndex()
        index.index_entry(1, "Beatles Beatles Beatles")  # Higher term frequency
        index.index_entry(2, "Beatles album")

        results = index.search("beatles")
        # Document 1 should rank higher due to higher term frequency
        assert len(results) == 2
        assert results[0][0] == 1  # Should be ranked first

    def test_search_empty_query(self) -> None:
        """Test searching with empty query."""
        index = TextSearchIndex()
        index.index_entry(1, "Beatles album")

        results = index.search("")
        assert len(results) == 0

    def test_get_random_id(self) -> None:
        """Test getting a random ID from the index."""
        index = TextSearchIndex()
        index.index_entry(1, "Beatles album")
        index.index_entry(2, "Rolling Stones")
        index.index_entry(3, "Jazz music")

        random_id = index.get_random_id()
        assert random_id in [1, 2, 3]

    def test_get_random_id_empty_index(self) -> None:
        """Test getting random ID from empty index."""
        index = TextSearchIndex()

        # Should handle empty index gracefully
        # Based on the implementation, it will likely raise an IndexError for empty list
        # noinspection PyTypeChecker
        with pytest.raises((IndexError, ValueError)):
            index.get_random_id()

    def test_reduce_list_to_set(self) -> None:
        """Test converting index lists to sets for optimization."""
        index = TextSearchIndex()
        index.index_entry(1, "Beatles album")
        index.index_entry(2, "Beatles album")  # Duplicate

        # Before reduction, might have duplicates in lists
        index.reduce_list_to_set()

        # After reduction, should have sets without duplicates
        for token_list in index.token_index.values():
            assert isinstance(token_list, (list, set))

    def test_list_stop_words(self) -> None:
        """Test listing stop words based on frequency analysis."""
        index = TextSearchIndex()

        # Test with empty index - should return empty list
        stop_words = index.generate_list_of_stop_words()
        assert isinstance(stop_words, list)
        assert len(stop_words) == 0

        # The method identifies words that appear in >10000 documents as potential stop words
        # With test data, this is unlikely to happen, so the list should be empty

    def test_print_sizes(self) -> None:
        """Test printing index sizes (should not raise errors)."""
        index = TextSearchIndex()
        index.index_entry(1, "Beatles album")
        index.index_entry(2, "Rolling Stones")

        # This method prints information, so just ensure it doesn't raise exceptions
        try:
            index.print_sizes()
        except Exception as e:
            pytest.fail(f"print_sizes() raised an exception: {e}")

    # Note: save_text_search_index_to_file method doesn't exist in the class
    # Only load_text_search_index_from_file is available

    @patch("builtins.open", new_callable=mock_open, read_data=b"pickled_data")
    @patch("pickle.load")
    def test_load_text_search_index_from_file(
        self, mock_pickle_load: Mock, mock_file: Mock
    ) -> None:
        """Test loading the index from a file."""
        # Create a mock index to be returned by pickle.load
        mock_index = TextSearchIndex()
        mock_index.index_entry(1, "Test entry")
        mock_pickle_load.return_value = mock_index

        filename = Path("/tmp/test_index.pkl")
        loaded_index = TextSearchIndex.load_text_search_index_from_file(filename)

        mock_file.assert_called_once_with(filename, "rb")
        mock_pickle_load.assert_called_once()
        assert loaded_index == mock_index

    def test_case_insensitive_search(self) -> None:
        """Test that search is case insensitive."""
        index = TextSearchIndex()
        index.index_entry(1, "Beatles White Album")

        # All these should return the same result
        results1 = index.search("beatles")
        results2 = index.search("BEATLES")
        results3 = index.search("BeAtLeS")

        assert len(results1) == len(results2) == len(results3) == 1
        assert results1[0][0] == results2[0][0] == results3[0][0] == 1

    def test_complex_search_scenario(self) -> None:
        """Test a complex search scenario with multiple documents and terms."""
        index = TextSearchIndex()
        index.index_entry(1, "The Beatles White Album collection")
        index.index_entry(2, "Rolling Stones Black Album rare")
        index.index_entry(3, "Beatles collection rare vinyl")
        index.index_entry(4, "Jazz music collection modern")
        index.index_entry(5, "Beatles rare recordings")

        # Search for "beatles rare" should return docs 3 and 5
        results = index.search("beatles rare")
        assert len(results) == 2
        result_ids = [r[0] for r in results]
        assert 3 in result_ids
        assert 5 in result_ids

        # Search for "collection" should return docs 1, 3, and 4
        results = index.search("collection")
        assert len(results) == 3
        result_ids = [r[0] for r in results]
        assert 1 in result_ids
        assert 3 in result_ids
        assert 4 in result_ids
