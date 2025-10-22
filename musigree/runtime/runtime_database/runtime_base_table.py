"""
This module defines the base class for declarative base and a type variable for runtime database tables.

It provides a foundation for creating tables in the runtime database using SQLAlchemy's
Declarative Base system.

Key components:
    - `RuntimeBase`: A subclass of `sqlalchemy.orm.DeclarativeBase` that serves as the base class
      for all declarative table definitions in the runtime database.
    - `RuntimeConcreteTable`: A type variable (`TypeVar`) that is bound to `RuntimeBase`,
      ensuring type safety and consistency when defining tables and working with them
      generically.
"""

from typing import TypeVar

from sqlalchemy.orm import DeclarativeBase


class RuntimeBase(DeclarativeBase):
    """
    Base class for declarative table definitions in the runtime database.

    This class extends SQLAlchemy's `DeclarativeBase` and should be used as the
    base class for all table definitions within the runtime database. It provides
    a common foundation for creating tables with consistent behavior and metadata.

    Example:
        ```python
        from sqlalchemy.orm import Mapped, mapped_column
        from sqlalchemy import Integer, String
        from musigree.runtime.runtime_database.runtime_base_table import RuntimeBase

        class MyTable(RuntimeBase):
            __tablename__ = "my_table"
            id: Mapped[int] = mapped_column(Integer, primary_key=True)
            name: Mapped[str] = mapped_column(String)
        ```
    """

    pass


RuntimeConcreteTable = TypeVar("RuntimeConcreteTable", bound=RuntimeBase)
"""
Type variable for concrete table classes in the runtime database.

This `TypeVar` is bound to `RuntimeBase` and should be used to annotate
variables and function parameters that represent concrete table classes
within the runtime database. It enforces type safety and ensures that only
subclasses of `RuntimeBase` are used where a table class is expected.

Example:
    ```python
    from typing import Type
    from musigree.runtime.runtime_database.runtime_base_table import RuntimeConcreteTable

    def create_table(table_class: Type[RuntimeConcreteTable]):
        # use table_class to interact with the database
        pass
    ```
"""
