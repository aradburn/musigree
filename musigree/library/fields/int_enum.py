from sqlalchemy import TypeDecorator, Integer


class IntEnum(TypeDecorator):
    """
    Enables using Python enums with integer values directly in a SQLAlchemy database.

    This custom type decorator allows you to pass a Python enum (e.g., an `enum.Enum`)
    and store the enum's *integer value* in the database. By default, SQLAlchemy would
    store the enum's *name* (i.e., the string representation) instead.

    This class ensures that:
        - When binding a parameter to a SQL query, the integer value of the enum is used.
        - When fetching a result from the database, the integer value is converted back
          to the corresponding enum member.

    Usage:
        - When defining a database model, use `IntEnum` as the type of a column where
          you want to store an enum's value.
        - Pass the enum class you're using as the first argument to `IntEnum`.

    Example:
        ```python
        import enum
        from sqlalchemy import Column, Integer
        from sqlalchemy.ext.declarative import declarative_base
        from musigree.library.fields.int_enum import IntEnum

        Base = declarative_base()

        class MyEnum(enum.Enum):
            VALUE_A = 1
            VALUE_B = 2

        class MyTable(Base):
            __tablename__ = "my_table"
            id = Column(Integer, primary_key=True)
            my_enum_value = Column(IntEnum(MyEnum))
        ```

    """

    impl = Integer
    cache_ok = True

    def __init__(self, enumtype, *args, **kwargs):
        """
        Initializes the IntEnum type decorator.

        Args:
            enumtype: The Python enum class (e.g., MyEnum) that this column will represent.
            *args: Additional positional arguments to pass to the parent class's constructor.
            **kwargs: Additional keyword arguments to pass to the parent class's constructor.
        """
        super(IntEnum, self).__init__(*args, **kwargs)
        self._enumtype = enumtype

    def process_bind_param(self, value, dialect):
        """
        Converts a Python value to a bind parameter for a SQL query.

        If the value is already an integer, it's returned directly.
        Otherwise, it's assumed to be an enum member, and its integer value is returned.

        Args:
            value: The Python value to convert (either an integer or an enum member).
            dialect: The database dialect (not used in this implementation).

        Returns:
            int: The integer value to bind to the SQL query.
        """
        if value is None:
            return None
        if isinstance(value, int):
            return value

        # noinspection PyUnresolvedReferences
        return value.value

    def process_result_value(self, value, dialect):
        """
        Converts a result value from the database to a Python value.

        This method receives an integer from the database and converts it back to
        the corresponding enum member.

        Args:
            value: The integer value from the database.
            dialect: The database dialect (not used in this implementation).

        Returns:
            The corresponding enum member.
        """
        if value is None:
            return None
        return self._enumtype(value)
