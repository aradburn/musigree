from sqlalchemy import String, Enum, Integer
from sqlalchemy.orm import Mapped, mapped_column

from musigree import utils
from musigree.offline.offline_database.base_table import OfflineBase
from musigree.library.fields.role_type import RoleType


class RoleTable(OfflineBase):
    """
    Represents the 'role' table in the offline_database.

    This table stores information about the different roles that entities can
    have in the Musigree system, such as 'Producer', 'Remixer', or 'Label Manager'.
    It categorizes roles into main categories and subcategories to provide a
    structured way of classifying relationships between entities.

    Attributes:
        __tablename__ (str): The name of the table in the offline_database.
        id (Mapped[int]): The primary key of the table, an auto-incrementing
            integer representing the unique identifier for the role.
        role_name (Mapped[str]): The name of the role (e.g., 'Producer', 'Remixer').
        role_category (Mapped[RoleType.Category]): The main category to which the
            role belongs (e.g., 'Production', 'Management'). Stored as an Enum.
        role_subcategory (Mapped[RoleType.Subcategory]): The subcategory to which
            the role belongs (e.g., 'Mix', 'Executive'). Stored as an Enum.
        role_category_name (Mapped[str]): The name of the main category to which the role belongs.
        role_subcategory_name (Mapped[str]): The name of the subcategory to which the role belongs.
    """

    __tablename__ = "role"
    """The name of the table in the offline_database."""

    # COLUMNS

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    """
    The primary key of the table, an auto-incrementing integer representing the unique identifier for the role.
    """
    role_name: Mapped[str] = mapped_column(String, index=True, nullable=False, unique=True)
    """
    The name of the role (e.g., 'Producer', 'Remixer'). Indexed for faster lookup.
    """
    role_category: Mapped[RoleType.Category] = mapped_column(Enum(RoleType.Category))
    """
    The main category to which the role belongs (e.g., 'Production', 'Management'). Stored as an Enum.
    """
    role_subcategory: Mapped[RoleType.Subcategory] = mapped_column(Enum(RoleType.Subcategory))
    """
    The subcategory to which the role belongs (e.g., 'Mix', 'Executive'). Stored as an Enum.
    """
    role_category_name: Mapped[str] = mapped_column(String, nullable=False)
    """
    The name of the main category to which the role belongs.
    """
    role_subcategory_name: Mapped[str | None] = mapped_column(String, nullable=True)
    """
     The name of the subcategory to which the role belongs.
    """

    def __repr__(self) -> str:
        """
        Returns a string representation of the RoleTable object.

        The string is a normalized dictionary representation of the object's data,
        skipping no keys.

        Returns:
            str: A normalized dictionary string representation of the object.
        """
        return utils.normalize_dict(utils.table2dict(self), skip_keys=[])
