from sqlalchemy import String, Enum, inspect
from sqlalchemy.orm import Mapped, mapped_column

from musigree import utils
from musigree.library.fields.role_type import RoleType
from musigree.runtime.runtime_database.runtime_base_table import RuntimeBase


class RuntimeRoleTable(RuntimeBase):
    """
    Represents the 'runtime_role' table in the database.

    This table stores information about roles in the Musigree runtime system.
    Each role has a name, a main category, and a subcategory. This table is
    designed for efficient lookup and management of roles during runtime
    operations.

    Attributes:
        __tablename__ (str): The name of the table in the database.
        id (Mapped[int]): The primary key of the table, an auto-incrementing
            integer representing the unique identifier for the runtime role.
        role_name (Mapped[str]): The name of the role (e.g., 'Producer',
            'Remixer'). This column is indexed for faster lookups.
        role_category (Mapped[RoleType.Category]): The main category to which
            the role belongs (e.g., 'Production', 'Management'). Stored as an
            Enum.
        role_subcategory (Mapped[RoleType.Subcategory]): The subcategory to
            which the role belongs (e.g., 'Mix', 'Executive'). Stored as an
            Enum.
        role_category_name (Mapped[str]): The name of the main category to
            which the role belongs.
        role_subcategory_name (Mapped[str]): The name of the subcategory to
            which the role belongs.
    """

    __tablename__ = "runtime_role"
    """The name of the table in the database."""

    # COLUMNS

    id: Mapped[int] = mapped_column(primary_key=True)
    """
    The primary key of the table, an auto-incrementing integer representing
    the unique identifier for the runtime role.
    """
    role_name: Mapped[str] = mapped_column(String, index=True, nullable=False)
    """
    The name of the role (e.g., 'Producer', 'Remixer'). Indexed for faster lookup.
    """
    role_category: Mapped[RoleType.Category] = mapped_column(
        Enum(RoleType.Category, name="runtime_role_category")
    )
    """
    The main category to which the role belongs (e.g., 'Production',
    'Management'). Stored as an Enum.
    """
    role_subcategory: Mapped[RoleType.Subcategory] = mapped_column(
        Enum(RoleType.Subcategory, name="runtime_role_subcategory")
    )
    """
    The subcategory to which the role belongs (e.g., 'Mix', 'Executive').
    Stored as an Enum.
    """
    role_category_name: Mapped[str] = mapped_column(String)
    """The name of the main category to which the role belongs."""
    role_subcategory_name: Mapped[str] = mapped_column(String)
    """The name of the subcategory to which the role belongs."""

    def __init__(self, **entries):
        """
        Initializes a RuntimeRoleTable instance.

        This constructor allows for the initialization of a `RuntimeRoleTable`
        object with keyword arguments that match the table's columns. It
        ensures that only valid column names are used during initialization.

        Args:
            entries (dict): Keyword arguments corresponding to the table's
                columns and their values.
        """
        column_names = set(
            [column.name for column in inspect(RuntimeRoleTable).columns]
        )
        superentries = {
            k: entries[k] for k in column_names.intersection(entries.keys())
        }
        super().__init__(**superentries)

    def __repr__(self):
        """
        Returns a string representation of the RuntimeRoleTable instance.

        The string is a normalized dictionary representation of the object's
        data, skipping no keys.

        Returns:
            str: A normalized dictionary string representation of the object.
        """
        return utils.normalize_dict(utils.row2dict(self), skip_keys={})
