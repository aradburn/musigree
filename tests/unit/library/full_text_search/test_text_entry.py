from musigree.library.full_text_search.text_entry import TextEntry


class TestTextEntry:
    """Test cases for the TextEntry class."""

    def test_text_entry_creation(self) -> None:
        """Test that a TextEntry can be created with id and text."""
        entry = TextEntry(id=123, text="Test text content")

        assert entry.id == 123
        assert entry.text == "Test text content"

    def test_text_entry_with_empty_text(self) -> None:
        """Test TextEntry creation with empty text."""
        entry = TextEntry(id=456, text="")

        assert entry.id == 456
        assert entry.text == ""

    def test_text_entry_with_long_text(self) -> None:
        """Test TextEntry creation with long text content."""
        long_text = "This is a very long text content " * 100
        entry = TextEntry(id=789, text=long_text)

        assert entry.id == 789
        assert entry.text == long_text

    def test_text_entry_with_zero_id(self) -> None:
        """Test TextEntry creation with zero ID."""
        entry = TextEntry(id=0, text="Zero ID text")

        assert entry.id == 0
        assert entry.text == "Zero ID text"

    def test_text_entry_with_negative_id(self) -> None:
        """Test TextEntry creation with negative ID."""
        entry = TextEntry(id=-1, text="Negative ID text")

        assert entry.id == -1
        assert entry.text == "Negative ID text"

    def test_text_entry_equality(self) -> None:
        """Test that two TextEntry objects with same values are equal."""
        entry1 = TextEntry(id=100, text="Same content")
        entry2 = TextEntry(id=100, text="Same content")

        assert entry1 == entry2

    def test_text_entry_inequality(self) -> None:
        """Test that two TextEntry objects with different values are not equal."""
        entry1 = TextEntry(id=100, text="Content 1")
        entry2 = TextEntry(id=100, text="Content 2")
        entry3 = TextEntry(id=200, text="Content 1")

        assert entry1 != entry2
        assert entry1 != entry3

    def test_text_entry_str_representation(self) -> None:
        """Test the string representation of TextEntry."""
        entry = TextEntry(id=42, text="Test content")
        str_repr = str(entry)

        assert "42" in str_repr
        assert "Test content" in str_repr

    def test_text_entry_with_special_characters(self) -> None:
        """Test TextEntry with special characters in text."""
        special_text = "Text with special chars: !@#$%^&*()[]{}|;:,.<>?"
        entry = TextEntry(id=999, text=special_text)

        assert entry.id == 999
        assert entry.text == special_text

    def test_text_entry_with_unicode_characters(self) -> None:
        """Test TextEntry with unicode characters."""
        unicode_text = "Unicode text: café, naïve, résumé, 中文, русский"
        entry = TextEntry(id=1000, text=unicode_text)

        assert entry.id == 1000
        assert entry.text == unicode_text

    def test_text_entry_with_multiline_text(self) -> None:
        """Test TextEntry with multiline text content."""
        multiline_text = """Line 1
Line 2
Line 3"""
        entry = TextEntry(id=2000, text=multiline_text)

        assert entry.id == 2000
        assert entry.text == multiline_text
        assert "\n" in entry.text
