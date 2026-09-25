from typing import Any, TypeVar

from sqlalchemy.orm import DeclarativeBase


class OfflineBase(DeclarativeBase):
    """
    Base class for declarative base in SQLAlchemy.

    This class serves as the base for defining SQLAlchemy declarative models.
    By inheriting from this class, model classes gain the necessary functionality
    for mapping to runtime_database tables.

    Usage:
        Create your model classes by inheriting from this `Base` class.

        Example:

        ```python
        from sqlalchemy import Column, Integer, String

        class MyModel(Base):
            __tablename__ = "my_table"
            id = Column(Integer, primary_key=True)
            name = Column(String)
        ```
    """


def mapped_entity(cls: Any) -> Any:
    """Return a mapped class as ``Any`` for use as a SQLAlchemy entity value.

    Mapped classes use ``DeclarativeAttributeIntercept``. PyCharm treats that
    metaclass object as an instance (``Self@object``) rather than ``type[Model]``,
    so passing the class to ``select()`` or assigning it to ``schema_class``
    fails type checking. This identity helper keeps runtime behavior unchanged.
    """
    return cls


ConcreteTable = TypeVar("ConcreteTable", bound=OfflineBase)
"""
Type variable for concrete table classes.

This `TypeVar` is used to represent any concrete table class that inherits
from the `Base` class. It's used for type hinting in generic functions and
classes where the specific table class is not known beforehand.
"""
