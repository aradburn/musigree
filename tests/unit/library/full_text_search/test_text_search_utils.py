from musigree.library.full_text_search.text_search_utils import normalise_search_content


class TestTextSearchUtils:
    """Test cases for text search utility functions."""

    def test_normalise_search_content_basic(self):
        """Test basic text normalization."""
        result = normalise_search_content("Hello World")
        assert result == "hello world"

    def test_normalise_search_content_with_punctuation_1(self):
        """Test normalization with punctuation that should be removed."""
        result = normalise_search_content("Hello, World (5)")
        assert result == "hello world"

    def test_normalise_search_content_with_punctuation_2(self):
        """Test normalization with punctuation that should be removed."""
        result = normalise_search_content("Hello, World!")
        assert result == "hello world"

    def test_normalise_search_content_with_punctuation_3(self):
        """Test normalization with punctuation that should be removed."""
        result = normalise_search_content("abcdefghijklmnopqrstuvwxyz ABCDEFGHIJKLMNOPQRSTUVWXYZ 1234567890!@#$%^&*()_+-=[]{}|;':\",.<>?/")
        assert result == "abcdefghijklmnopqrstuvwxyz abcdefghijklmnopqrstuvwxyz 1234567890-"

    def test_normalise_search_content_with_punctuation_4(self):
        """Test normalization with punctuation that should be removed."""
        result = normalise_search_content("Hello, World (not on label)")
        assert result == "hello world"

    def test_normalise_search_content_with_punctuation_5(self):
        """Test normalization with punctuation that should be removed."""
        result = normalise_search_content("Hello, World self-released")
        assert result == "hello world"

    def test_normalise_search_content_with_leading_trailing_spaces(self):
        """Test normalization with leading and trailing spaces."""
        result = normalise_search_content("   Hello World   ")
        assert result == "hello world"

    def test_normalise_search_content_empty_string(self):
        """Test normalization of empty string."""
        result = normalise_search_content("")
        assert result == ""

    def test_normalise_search_content_only_spaces(self):
        """Test normalization of string with only spaces."""
        result = normalise_search_content("   ")
        assert result == ""

    def test_normalise_search_content_mixed_case(self):
        """Test normalization of mixed case text."""
        result = normalise_search_content("HeLLo WoRLd")
        assert result == "hello world"

    def test_normalise_search_content_numbers(self):
        """Test normalization with numbers."""
        result = normalise_search_content("Hello 123 World")
        assert result == "hello 123 world"

    def test_normalise_search_content_special_characters(self):
        """Test normalization with various special characters."""
        result = normalise_search_content("Hello@#$%^&*()World")
        # The exact result depends on STRIP_PATTERN in utils
        assert result.lower() == result  # Should be lowercase
        assert "hello" in result
        assert "world" in result

    def test_normalise_search_content_unicode_characters(self):
        """Test normalization with unicode characters."""
        result = normalise_search_content("Café naïve résumé")
        assert result == "café naïve résumé"

    def test_normalise_search_content_multiple_spaces(self):
        """Test normalization with multiple consecutive spaces."""
        result = normalise_search_content("Hello    World")
        # Check that it's normalized but may keep internal spaces
        assert "hello" in result
        assert "world" in result

    def test_normalise_search_content_newlines_and_tabs(self):
        """Test normalization with newlines and tabs."""
        result = normalise_search_content("Hello\nWorld\tTest")
        assert "hello" in result
        assert "world" in result
        assert "test" in result

    def test_normalise_search_content_single_character(self):
        """Test normalization of single character."""
        result = normalise_search_content("A")
        assert result == "a"

    def test_normalise_search_content_hyphenated_words(self):
        """Test normalization with hyphenated words."""
        result = normalise_search_content("Self-contained")
        assert "self" in result
        assert "contained" in result

    def test_normalise_search_content_apostrophes(self):
        """Test normalization with apostrophes."""
        result = normalise_search_content("Don't can't won't")
        # The exact behavior depends on STRIP_PATTERN
        assert "don" in result or "dont" in result
        assert "can" in result or "cant" in result
        assert "won" in result or "wont" in result

    def test_normalise_search_content_music_terms(self):
        """Test normalization with music-related terms."""
        result = normalise_search_content("The Beatles & The Rolling Stones")
        assert "beatles" in result
        assert "rolling" in result
        assert "stones" in result 