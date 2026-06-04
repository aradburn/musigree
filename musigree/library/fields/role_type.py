import enum
import re


class RoleType:
    """
    Provides a structured way to categorize and classify roles within the Musigree system.

    This class defines enums for role categories and subcategories, and offers utility
    methods for mapping and representing these roles. It also includes a regular
    expression pattern for parsing bracketed text, and lists of aggregate roles.

    Attributes:
        RoleType.Category (enum.Enum): An enumeration of the high-level categories that roles can fall into.
        RoleType.Subcategory (enum.Enum): An enumeration of subcategories for more granular role classification.
        category_names (dict): A mapping from Category enum members to their human-readable names.
        subcategory_names (dict): A mapping from Subcategory enum members to their human-readable names.
        aggregate_roles (tuple): A collection of role names that are considered "aggregate" roles.
    """

    class Category(enum.Enum):
        """
        Enumerates the high-level categories that roles can fall into.

        Attributes:
            ACTING_LITERARY_AND_SPOKEN: Roles related to acting, literature, or spoken word.
            COMPANIES: Roles related to companies involved in the industry.
            CONDUCTING_AND_LEADING: Roles related to conducting or leading a performance.
            DJ_MIX: Roles related to DJ mixing.
            FEATURING_AND_PRESENTING: Roles related to featuring or presenting.
            INSTRUMENTS: Roles related to playing musical instruments.
            MANAGEMENT: Roles related to management in the industry.
            PRODUCTION: Roles related to production.
            RELATION: Roles representing structural relationships.
            REMIX: Roles related to remixing.
            TECHNICAL: Roles related to technical aspects.
            VISUAL: Roles related to visual aspects.
            VOCAL: Roles related to vocals.
            WRITING_AND_ARRANGEMENT: Roles related to writing or arranging music.
        """

        ACTING_LITERARY_AND_SPOKEN = 1
        COMPANIES = 2
        CONDUCTING_AND_LEADING = 3
        DJ_MIX = 4
        FEATURING_AND_PRESENTING = 5
        INSTRUMENTS = 6
        MANAGEMENT = 7
        PRODUCTION = 8
        RELATION = 9
        REMIX = 10
        TECHNICAL = 11
        VISUAL = 12
        VOCAL = 13
        WRITING_AND_ARRANGEMENT = 14

    class Subcategory(enum.Enum):
        """
        Enumerates the subcategories for more granular role classification.

        Attributes:
            NONE: No subcategory specified.
            DRUMS_AND_PERCUSSION: Subcategory for drums and percussion instruments.
            KEYBOARDS: Subcategory for keyboard instruments.
            OTHER_MUSICAL: Subcategory for other musical roles.
            STRINGED_INSTRUMENTS: Subcategory for stringed instruments.
            TECHNICAL_MUSICAL: Subcategory for musical technical roles.
            TUNED_PERCUSSION: Subcategory for tuned percussion instruments.
            WIND_INSTRUMENTS: Subcategory for wind instruments.
        """

        NONE = 0
        DRUMS_AND_PERCUSSION = 1
        KEYBOARDS = 2
        OTHER_MUSICAL = 3
        STRINGED_INSTRUMENTS = 4
        TECHNICAL_MUSICAL = 5
        TUNED_PERCUSSION = 6
        WIND_INSTRUMENTS = 7

    _bracket_pattern = re.compile(r"\[(.+?)]")
    """
     A regular expression pattern used for matching bracketed text.
     Useful for extracting additional details from role descriptions.
    """

    category_names: dict[Category, str] = {
        Category.ACTING_LITERARY_AND_SPOKEN: "Acting, Literary & Spoken",
        Category.COMPANIES: "Companies",
        Category.CONDUCTING_AND_LEADING: "Conducting & Leading",
        Category.DJ_MIX: "DJ Mix",
        Category.FEATURING_AND_PRESENTING: "Featuring & Presenting",
        Category.INSTRUMENTS: "Instruments",
        Category.MANAGEMENT: "Management",
        Category.PRODUCTION: "Production",
        Category.RELATION: "Structural Relationships",
        Category.REMIX: "Remix",
        Category.TECHNICAL: "Technical",
        Category.VISUAL: "Visual",
        Category.VOCAL: "Vocal",
        Category.WRITING_AND_ARRANGEMENT: "Writing & Arrangement",
    }
    """
    A mapping from each `Category` enum member to its human-readable name.
    """

    subcategory_names: dict[Subcategory, str] = {
        Subcategory.NONE: "None",
        Subcategory.DRUMS_AND_PERCUSSION: "Drums & Percussion",
        Subcategory.KEYBOARDS: "Keyboards",
        Subcategory.OTHER_MUSICAL: "Other Musical",
        Subcategory.STRINGED_INSTRUMENTS: "String Instruments",
        Subcategory.TECHNICAL_MUSICAL: "Technical Musical",
        Subcategory.TUNED_PERCUSSION: "Tuned Percussion",
        Subcategory.WIND_INSTRUMENTS: "Wind Instruments",
    }
    """
    A mapping from each `Subcategory` enum member to its human-readable name.
    """

    aggregate_roles = (
        "Compiled By",
        "Curated By",
        "DJ Mix",
        "Hosted By",
        "Presenter",
    )
    """
    A collection of role names that are considered "aggregate" roles.
    These are roles that typically represent a collection or curation of content.
    """

    @staticmethod
    def hornbostel_sachs_to_subcategory(
        hornbostel_sachs_classification: str,
    ) -> Subcategory:
        """
        Maps a Hornbostel-Sachs instrument classification to a Subcategory.

        Args:
            hornbostel_sachs_classification: The Hornbostel-Sachs classification string.

        Returns:
            Subcategory: The corresponding Subcategory.
                         Defaults to `OTHER_MUSICAL` if no match is found.

        """
        match hornbostel_sachs_classification.lower():
            case "idiophones":
                return RoleType.Subcategory.DRUMS_AND_PERCUSSION
            case "membranophones":
                return RoleType.Subcategory.DRUMS_AND_PERCUSSION
            case "chordophones":
                return RoleType.Subcategory.STRINGED_INSTRUMENTS
            case "aerophones":
                return RoleType.Subcategory.WIND_INSTRUMENTS
            case "electrophones":
                return RoleType.Subcategory.TECHNICAL_MUSICAL
            case _:
                return RoleType.Subcategory.OTHER_MUSICAL
