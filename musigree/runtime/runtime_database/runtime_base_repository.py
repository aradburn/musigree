import logging
from collections.abc import AsyncIterator
from typing import Any, Generic, Type

from sqlalchemy import asc, delete, desc, func, select, update
from sqlalchemy.engine import Result

__all__ = ("RuntimeBaseRepository",)

from sqlalchemy.exc import IntegrityError, InvalidRequestError

from musigree.exceptions import UnprocessableError, DatabaseError, NotFoundError
from musigree.runtime.runtime_database.runtime_base_table import RuntimeConcreteTable
from musigree.runtime.runtime_database.runtime_session import RuntimeSession

log = logging.getLogger(__name__)


class RuntimeBaseRepository(RuntimeSession, Generic[RuntimeConcreteTable]):
    """
    Base class for creating repositories that interact with the runtime database.

    This class provides a generic interface for common async database operations, such as
    creating, retrieving, updating, and deleting data. It simplifies database
    interactions and enforces type safety through the use of generics.

    It inherits from `RuntimeSession` to manage async database sessions and transactions.

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

        This method initializes the async database session through the parent class
        `RuntimeSession` and ensures that the `schema_class` attribute is set.

        Raises:
            UnprocessableError: If the `schema_class` attribute is not set.
        """
        super().__init__()

        if not self.schema_class:
            raise UnprocessableError(
                message="Can not initiate the class without schema_class attribute"
            )

    async def _update(
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
            result: Result = await self.execute(query)
        except (IntegrityError, InvalidRequestError):
            raise DatabaseError

        if not (schema := result.scalar_one_or_none()):
            raise DatabaseError

        return schema

    async def _get(self, key: str, value: Any) -> RuntimeConcreteTable:
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
        result: Result = await self.execute(query)

        if not (_result := result.scalars().one_or_none()):
            raise NotFoundError

        return _result

    async def count(self) -> int:
        """
        Counts the total number of records in the associated database table.

        Returns:
            int: The total count of records.

        Raises:
            UnprocessableError: If the database query returns a non-integer value.
        """
        query = select(func.count()).select_from(self.schema_class)
        result: Result = await self.execute(query)
        value = result.scalar()

        if not isinstance(value, int):
            raise UnprocessableError(
                message=(
                    "For some reason count function returned not an integer."
                    f"Value: {value}"
                ),
            )

        return value

    async def _first(self, by: str = "id") -> RuntimeConcreteTable:
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
        result: Result = await self.execute(
            select(self.schema_class).order_by(asc(by)).limit(1)
        )

        if not (_result := result.scalar_one_or_none()):
            raise NotFoundError

        return _result

    async def _last(self, by: str = "id") -> RuntimeConcreteTable:
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
        result: Result = await self.execute(
            select(self.schema_class).order_by(desc(by)).limit(1)
        )

        if not (_result := result.scalar_one_or_none()):
            raise NotFoundError

        return _result

    async def _save(self, payload: dict[str, Any]) -> RuntimeConcreteTable:
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
            await self._session.flush()
            await self._session.refresh(schema)
            return schema
        except (IntegrityError, InvalidRequestError):
            raise DatabaseError

    async def save_all(self, payloads: list[dict[str, Any]]) -> None:
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
            await self._session.flush()
        except (IntegrityError, InvalidRequestError):
            raise DatabaseError

    async def _all(self) -> AsyncIterator[RuntimeConcreteTable]:
        """
        Retrieves all records from the database table.

        Yields:
            AsyncIterator[RuntimeConcreteTable]: An async iterator that yields each
                database row as an object.
        """
        result: Result = await self.execute(select(self.schema_class))
        schemas = result.scalars().all()

        for schema in schemas:
            yield schema

    async def delete(self, id_: int) -> None:
        """
        Deletes a record from the database table by its ID.

        Args:
            id_ (int): The ID of the record to delete.
        """
        # noinspection PyTypeChecker,Mypy
        await self.execute(delete(self.schema_class).where(self.schema_class.id == id_))  # type: ignore
        await self._session.flush()

    async def commit(self) -> None:
        """
        Commits the current transaction.
        """
        await self._session.commit()

    async def rollback(self) -> None:
        """
        Rolls back the current transaction.
        """
        await self._session.rollback()
