import logging
from collections.abc import Iterator
from typing import Any, Generic, Type

from sqlalchemy import asc, delete, desc, func, select, update, text
from sqlalchemy.engine import Result

__all__ = ("BaseRepository",)

from musigree.exceptions import UnprocessableError, DatabaseError, NotFoundError
from musigree.offline.database.base_table import ConcreteTable
from musigree.offline.database.offline_session import OfflineSession

log = logging.getLogger(__name__)


class BaseRepository(OfflineSession, Generic[ConcreteTable]):
    """
    This class implements the base interface for working with a database and provides
    a set of common database operations. It's designed to be subclassed by more specific
    repository classes, allowing for type-safe interactions with the database.

    The Session class implements the database interaction layer.

    Attributes:
        schema_class (Type[ConcreteTable]): The SQLAlchemy table class that this
            repository manages. This must be set in subclasses.
    """

    schema_class: Type[ConcreteTable]
    """
     The SQLAlchemy table class that this repository manages. This must be set in subclasses.
    """

    def __init__(self) -> None:
        """
        Initializes the BaseRepository and checks that a schema_class has been defined.
        """
        super().__init__()

        if not self.schema_class:
            raise UnprocessableError(
                message="Can not initiate the class without schema_class attribute"
            )

    def _update(self, key: str, value: Any, payload: dict[str, Any]) -> ConcreteTable:
        """
        Updates an existing instance of the model in the related table.

        If some data is not present in the payload, then the corresponding
        values in the database will be updated to NULL.

        Args:
            key: The name of the column to filter by.
            value: The value to filter by.
            payload: A dictionary of column names and their new values.

        Returns:
            ConcreteTable: The updated database row as an object.

        Raises:
            DatabaseError: If there is an error during the database operation.
        """

        try:
            # noinspection PyTypeChecker
            query = (
                update(self.schema_class)
                .where(getattr(self.schema_class, key) == value)
                .values(payload)
                .returning(self.schema_class)
            )
            result: Result = self.execute(query)
        except self._ERRORS:
            raise DatabaseError

        if not (schema := result.scalar_one_or_none()):
            raise DatabaseError

        return schema

    def _get(self, key: str, value: Any) -> ConcreteTable:
        """
        Retrieves a single record from the database that matches the given criteria.

        Args:
            key: The name of the column to filter by.
            value: The value to filter by.

        Returns:
            ConcreteTable: The matching database row as an object.

        Raises:
            NotFoundError: If no matching record is found.
        """

        # noinspection PyTypeChecker
        query = select(self.schema_class).where(
            getattr(self.schema_class, key) == value
        )
        result: Result = self.execute(query)

        if not (_result := result.scalars().one_or_none()):
            raise NotFoundError

        return _result

    def count(self) -> int:
        """
        Counts the total number of records in the table.

        Returns:
            int: The number of records in the table.

        Raises:
            UnprocessableError: If the count function returns a non-integer value.
        """
        query = select(func.count()).select_from(self.schema_class)
        result: Result = self.execute(query)
        value = result.scalar()

        if not isinstance(value, int):
            raise UnprocessableError(
                message=(
                    "For some reason count function returned not an integer."
                    f"Value: {value}"
                ),
            )

        return value

    def _first(self, by: str = "id") -> ConcreteTable:
        """
        Retrieves the first record from the table, ordered by the specified column.

        Args:
            by: The name of the column to order by (defaults to "id").

        Returns:
            ConcreteTable: The first database row as an object.

        Raises:
            NotFoundError: If no records are found.
        """
        result: Result = self.execute(
            select(self.schema_class).order_by(asc(by)).limit(1)
        )

        if not (_result := result.scalar_one_or_none()):
            raise NotFoundError

        return _result

    def _last(self, by: str = "id") -> ConcreteTable:
        """
        Retrieves the last record from the table, ordered by the specified column.

        Args:
            by: The name of the column to order by (defaults to "id").

        Returns:
            ConcreteTable: The last database row as an object.

        Raises:
            NotFoundError: If no records are found.
        """
        result: Result = self.execute(
            select(self.schema_class).order_by(desc(by)).limit(1)
        )

        if not (_result := result.scalar_one_or_none()):
            raise NotFoundError

        return _result

    def _save(self, payload: dict[str, Any]) -> ConcreteTable:
        """
        Saves a new record to the database.

        Args:
            payload: A dictionary of column names and their values.

        Returns:
            ConcreteTable: The newly created database row as an object.

        Raises:
            DatabaseError: If there is an error during the database operation.
        """
        try:
            schema = self.schema_class(**payload)
            self._session.add(schema)
            self._session.flush()
            self._session.refresh(schema)
            return schema
        except self._ERRORS:
            raise DatabaseError

    def save_all(self, payloads: list[dict[str, Any]]) -> None:
        """
        Saves multiple new records to the database in a single transaction.

        Args:
            payloads: A list of dictionaries, each containing column names and
                their values for a single record.

        Raises:
            DatabaseError: If there is an error during the database operation.
        """
        try:
            instances = [self.schema_class(**payload) for payload in payloads]
            self._session.add_all(instances)
            self._session.flush()
        except self._ERRORS:
            raise DatabaseError

    def _all(self) -> Iterator[ConcreteTable]:
        """
        Retrieves all records from the table.

        Yields:
            Iterator[ConcreteTable]: A iterator that yields each
                database row as an object.
        """
        result: Result = self.execute(select(self.schema_class))
        schemas = result.scalars().all()

        for schema in schemas:
            yield schema

    def delete(self, id_: int) -> None:
        """
        Deletes a record from the table by its ID.

        Args:
            id_: The ID of the record to delete.
        """
        # noinspection PyTypeChecker
        self.execute(delete(self.schema_class).where(self.schema_class.id == id_))
        self._session.flush()

    def commit(self) -> None:
        """
        Commits the current transaction.
        """
        self._session.commit()

    def rollback(self) -> None:
        """
        Rolls back the current transaction.
        """
        self._session.rollback()

    def vacuum(self, has_tablename=False, is_full=False, is_analyze=False) -> None:
        """
        Performs a VACUUM operation on the database or a specific table.

        Args:
            has_tablename: If True, perform VACUUM on the table in `schema_class`.
            is_full: If True, performs a `VACUUM FULL` operation.
            is_analyze: If True, performs a `VACUUM ANALYZE` operation.
        """
        query = "VACUUM"
        if is_full:
            query += " FULL"
        if is_analyze:
            query += " ANALYZE"
        if has_tablename:
            query += " " + self.schema_class.__tablename__
        query += ";"
        if has_tablename:
            # log.debug("vacuum close transaction")
            self._session.execute(text("COMMIT"))
        self._session.execute(text(query))
