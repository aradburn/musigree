import logging
from collections.abc import Iterator
from typing import Any, Generic, Type

from sqlalchemy import asc, delete, desc, func, select, update, text
from sqlalchemy.engine import Result

__all__ = ("RuntimeBaseRepository",)

from musigree.exceptions import UnprocessableError, DatabaseError, NotFoundError
from musigree.runtime.runtime_database.runtime_base_table import RuntimeConcreteTable
from musigree.runtime.runtime_database.runtime_session import RuntimeSession

log = logging.getLogger(__name__)


class RuntimeBaseRepository(RuntimeSession, Generic[RuntimeConcreteTable]):
    """
    Base class for creating repositories that interact with the runtime database.

    This class provides a generic interface for common database operations, such as
    creating, retrieving, updating, and deleting data. It simplifies database
    interactions and enforces type safety through the use of generics.

    It inherits from `RuntimeSession` to manage database sessions and transactions.

    Attributes:
        schema_class (Type[RuntimeConcreteTable]): The SQLAlchemy schema class
            representing the database table that this repository interacts with.
            This attribute must be set in subclasses.

    Type parameters:
        RuntimeConcreteTable: A type variable representing a concrete subclass of
            `RuntimeBaseTable`, which is used to define the schema class for this
            repository.
    """

    schema_class: Type[RuntimeConcreteTable]
    """
    The SQLAlchemy schema class for the repository. This attribute must be
    set in subclasses to specify the table that the repository will interact with.
    """

    def __init__(self) -> None:
        """
        Initializes the RuntimeBaseRepository instance.

        This method initializes the database session through the parent class
        `RuntimeSession` and ensures that the `schema_class` attribute is set.

        Raises:
            UnprocessableError: If the `schema_class` attribute is not set.
        """
        super().__init__()

        if not self.schema_class:
            raise UnprocessableError(
                message="Can not initiate the class without schema_class attribute"
            )

    def _update(
        self, key: str, value: Any, payload: dict[str, Any]
    ) -> RuntimeConcreteTable:
        """
        Updates an existing instance of the model in the related table.

        This method updates a single record in the database based on the
        provided key-value pair and updates the record with data from the
        payload.

        Args:
            key (str): The name of the column to filter the update.
            value (Any): The value to filter the update with.
            payload (dict[str, Any]): A dictionary containing the data to
                update in the record.

        Returns:
            RuntimeConcreteTable: The updated schema instance.

        Raises:
            DatabaseError: If there is any error during the update operation.
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

    def _get(self, key: str, value: Any) -> RuntimeConcreteTable:
        """
        Retrieves a single record from the database based on the provided filter.

        Args:
            key (str): The name of the column to filter the query.
            value (Any): The value to filter the query with.

        Returns:
            RuntimeConcreteTable: The retrieved schema instance.

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
        Counts the total number of records in the associated database table.

        Returns:
            int: The total count of records.

        Raises:
            UnprocessableError: If the database query returns a non-integer value.
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

    def _first(self, by: str = "id") -> RuntimeConcreteTable:
        """
        Retrieves the first record from the database table based on a sorting criteria.

        Args:
            by (str): The name of the column to order the results by.
                Defaults to "id".

        Returns:
            RuntimeConcreteTable: The first record as a schema instance.

        Raises:
            NotFoundError: If no records are found in the table.
        """
        result: Result = self.execute(
            select(self.schema_class).order_by(asc(by)).limit(1)
        )

        if not (_result := result.scalar_one_or_none()):
            raise NotFoundError

        return _result

    def _last(self, by: str = "id") -> RuntimeConcreteTable:
        """
        Retrieves the last record from the database table based on a sorting criteria.

        Args:
            by (str): The name of the column to order the results by.
                Defaults to "id".

        Returns:
            RuntimeConcreteTable: The last record as a schema instance.

        Raises:
            NotFoundError: If no records are found in the table.
        """
        result: Result = self.execute(
            select(self.schema_class).order_by(desc(by)).limit(1)
        )

        if not (_result := result.scalar_one_or_none()):
            raise NotFoundError

        return _result

    def _save(self, payload: dict[str, Any]) -> RuntimeConcreteTable:
        """
        Saves a new record to the database.

        Args:
            payload (dict[str, Any]): A dictionary containing the data to save.

        Returns:
            RuntimeConcreteTable: The saved schema instance.

        Raises:
            DatabaseError: If there is any error during the save operation.
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
        Saves multiple new records to the database in a single operation.

        Args:
            payloads (list[dict[str, Any]]): A list of dictionaries, where
                each dictionary contains the data for a single record.

        Raises:
            DatabaseError: If there is any error during the save operation.
        """
        try:
            instances = [self.schema_class(**payload) for payload in payloads]
            self._session.add_all(instances)
            self._session.flush()
        except self._ERRORS:
            raise DatabaseError

    def _all(self) -> Iterator[RuntimeConcreteTable]:
        """
        Retrieves all records from the database table.

        Yields:
            Iterator[RuntimeConcreteTable]: An iterator yielding
                each record as a schema instance.
        """
        result: Result = self.execute(select(self.schema_class))
        schemas = result.scalars().all()

        for schema in schemas:
            yield schema

    def delete(self, id_: int) -> None:
        """
        Deletes a record from the database based on its ID.

        Args:
            id_ (int): The ID of the record to delete.
        """
        # noinspection PyTypeChecker
        self.execute(delete(self.schema_class).where(self.schema_class.id == id_))
        self._session.flush()

    def commit(self) -> None:
        """
        Commits the current database transaction.

        This method should be called to persist any changes made to the
        database.
        """
        self._session.commit()

    def rollback(self) -> None:
        """
        Rolls back the current database transaction.

        This method should be called to undo any changes made to the
        database within the current transaction.
        """
        self._session.rollback()

    def vacuum(self, has_tablename=False, is_full=False, is_analyze=False) -> None:
        """
        Performs a VACUUM operation on the database.

        This method optimizes the database by reclaiming storage space and
        optionally analyzing tables.

        Args:
            has_tablename (bool): If True, the table name will be included in
                the VACUUM query.
            is_full (bool): If True, a "FULL" vacuum operation will be performed,
                which reclaims more storage space but can take longer.
            is_analyze (bool): If True, the database will be analyzed after the
                vacuum operation to update the query planner's statistics.
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
            self._session.execute(text("COMMIT"))
        self._session.execute(text(query))
