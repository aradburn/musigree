import logging
from typing import Any, Generic, Type, AsyncGenerator

from sqlalchemy import delete, func, select, update
from sqlalchemy.engine import Result

__all__ = ("BaseRepository",)

from sqlalchemy.exc import IntegrityError, InvalidRequestError

from musigree.exceptions import UnprocessableError, DatabaseError, NotFoundError
from musigree.offline.database.base_table import ConcreteTable
from musigree.offline.database.offline_session import OfflineSession

log = logging.getLogger(__name__)


class BaseRepository(OfflineSession, Generic[ConcreteTable]):
    """
    This class implements the base interface for working with a database and provides
    a set of common async database operations. It's designed to be subclassed by more specific
    repository classes, allowing for type-safe interactions with the database.

    The Session class implements the async database interaction layer.

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

    async def _update(
        self, key: str, value: Any, payload: dict[str, Any]
    ) -> ConcreteTable:
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
            result: Result = await self.execute(query)
        except (IntegrityError, InvalidRequestError) as err:
            raise DatabaseError from err

        if not (schema := result.scalar_one_or_none()):
            raise DatabaseError

        return schema  # type: ignore

    async def _get(self, key: str, value: Any) -> ConcreteTable:
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
        result: Result = await self.execute(query)

        if not (_result := result.scalars().one_or_none()):
            raise NotFoundError

        return _result  # type: ignore

    async def count(self) -> int:
        """
        Counts the total number of records in the table.

        Returns:
            int: The number of records in the table.

        Raises:
            UnprocessableError: If the count function returns a non-integer value.
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

    async def _save(self, payload: dict[str, Any]) -> ConcreteTable:
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
            await self._session.flush()
            await self._session.refresh(schema)
            return schema
        except (IntegrityError, InvalidRequestError) as err:
            raise DatabaseError from err

    async def save_all(self, payloads: list[dict[str, Any]]) -> None:
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
            await self._session.flush()
        except (IntegrityError, InvalidRequestError) as err:
            raise DatabaseError from err

    async def _all(self) -> AsyncGenerator[ConcreteTable, None]:
        """
        Retrieves all records from the table.

        Yields:
            AsyncGenerator[ConcreteTable]: An async iterator that yields each
                database row as an object.
        """
        result: Result = await self.execute(select(self.schema_class))
        schemas = result.scalars().all()

        for schema in schemas:
            yield schema

    async def delete(self, id_: int) -> None:
        """
        Deletes a record from the table by its ID.

        Args:
            id_: The ID of the record to delete.
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
