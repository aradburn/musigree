from musigree.library.full_text_search.text_search_utils import normalise_search_content


class TestTextSearchUtils:
    """Test cases for text search utility functions."""

    def test_normalise_search_content_basic(self) -> None:
        """Test basic text normalization."""
        result = normalise_search_content("Hello World")
        assert result == "hello world"

    def test_normalise_search_content_strips_numeric_catalog_number(self) -> None:
        """Test that purely numeric parenthesised catalog numbers are removed."""
        result = normalise_search_content("Hello, World (5)")
        assert result == "hello, world"

    def test_normalise_search_content_preserves_punctuation(self) -> None:
        """Test that general punctuation is preserved."""
        result = normalise_search_content("Hello, World!")
        assert result == "hello, world!"

    def test_normalise_search_content_preserves_special_characters(self) -> None:
        """Test that special characters outside strip patterns are preserved."""
        input_text = (
            "abcdefghijklmnopqrstuvwxyz ABCDEFGHIJKLMNOPQRSTUVWXYZ "
            "1234567890!@#$%^&*()_+-=[]{}|;':\",.<>?/"
        )
        result = normalise_search_content(input_text)
        assert result == input_text.lower()

    def test_normalise_search_content_strips_not_on_label(self) -> None:
        """Test that 'not on label' text is removed while other punctuation remains."""
        result = normalise_search_content("Hello, World (not on label)")
        assert result == "hello, world ()"

    def test_normalise_search_content_strips_self_released(self) -> None:
        """Test that 'self-released' and spaced variants are removed."""
        assert normalise_search_content("Hello, World self-released") == "hello, world"
        assert normalise_search_content("Hello, World self released") == "hello, world"

    def test_normalise_search_content_with_leading_trailing_spaces(self) -> None:
        """Test normalization with leading and trailing spaces."""
        result = normalise_search_content("   Hello World   ")
        assert result == "hello world"

    def test_normalise_search_content_empty_string(self) -> None:
        """Test normalization of empty string."""
        result = normalise_search_content("")
        assert result == ""

    def test_normalise_search_content_only_spaces(self) -> None:
        """Test normalization of string with only spaces."""
        result = normalise_search_content("   ")
        assert result == ""

    def test_normalise_search_content_mixed_case(self) -> None:
        """Test normalization of mixed case text."""
        result = normalise_search_content("HeLLo WoRLd")
        assert result == "hello world"

    def test_normalise_search_content_numbers(self) -> None:
        """Test normalization with numbers."""
        result = normalise_search_content("Hello 123 World")
        assert result == "hello 123 world"

    def test_normalise_search_content_special_characters(self) -> None:
        """Test normalization with various special characters."""
        result = normalise_search_content("Hello@#$%^&*()World")
        assert result == "hello@#$%^&*()world"

    def test_normalise_search_content_unicode_characters(self) -> None:
        """Test normalization with unicode characters."""
        result = normalise_search_content("Café naïve résumé")
        assert result == "café naïve résumé"

    def test_normalise_search_content_multiple_spaces(self) -> None:
        """Test normalization with multiple consecutive spaces."""
        result = normalise_search_content("Hello    World")
        # Check that it's normalized but may keep internal spaces
        assert "hello" in result
        assert "world" in result

    def test_normalise_search_content_newlines_and_tabs(self) -> None:
        """Test normalization with newlines and tabs."""
        result = normalise_search_content("Hello\nWorld\tTest")
        assert "hello" in result
        assert "world" in result
        assert "test" in result

    def test_normalise_search_content_single_character(self) -> None:
        """Test normalization of single character."""
        result = normalise_search_content("A")
        assert result == "a"

    def test_normalise_search_content_hyphenated_words(self) -> None:
        """Test normalization with hyphenated words."""
        result = normalise_search_content("Self-contained")
        assert result == "self-contained"

    def test_normalise_search_content_apostrophes(self) -> None:
        """Test normalization with apostrophes."""
        result = normalise_search_content("Don't can't won't")
        assert result == "don't can't won't"

    def test_normalise_search_content_preserves_alphanumeric_catalog_number(self) -> None:
        """Test that non-numeric parenthesised catalog numbers are preserved."""
        result = normalise_search_content("Hello, World (CAT123)")
        assert result == "hello, world (cat123)"

    def test_normalise_search_content_music_terms(self) -> None:
        """Test normalization with music-related terms."""
        result = normalise_search_content("The Beatles & The Rolling Stones")
        assert "beatles" in result
        assert "rolling" in result
        assert "stones" in result
