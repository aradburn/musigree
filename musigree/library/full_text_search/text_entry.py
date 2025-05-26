from dataclasses import dataclass


@dataclass
class TextEntry:
    """
    Represents a text entry associated with a specific ID.

    This class is a simple data container that holds an ID and a text string.
    It's primarily used for storing and retrieving text data that is associated
    with some identifier, such as an entity ID in a full-text search index.

    Attributes:
        id (int): The unique identifier associated with the text entry.
        text (str): The text string associated with the ID.
    """

    id: int
    """The unique identifier for this text entry."""
    text: str
    """The text content associated with the identifier."""
