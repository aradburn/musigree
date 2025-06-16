import logging
from collections.abc import AsyncIterator
from typing import List

from sqlalchemy import Result, select, Select

from musigree.exceptions import DatabaseError
from musigree.offline.database.base_repository import BaseRepository
from musigree.offline.database.relation_release_year_table import (
    RelationReleaseYearTable,
)
from musigree.offline.domain.relation_release_year import (
    RelationReleaseYearDB,
    RelationReleaseYear,
    RelationReleaseYearUncommitted,
)

log = logging.getLogger(__name__)


class RelationReleaseYearRepository(BaseRepository[RelationReleaseYearTable]):
    """
    Repository for managing RelationReleaseYear objects in the database.

    This class provides async methods for interacting with the RelationReleaseYearTable
    in the database, including creating, retrieving, and bulk creating relation-release-year pairs.

    Inherits from:
        BaseRepository[RelationReleaseYearTable]: Provides the basic async database interaction
            functionality.

    Attributes:
        schema_class (Type[RelationReleaseYearTable]): The SQLAlchemy table class
            for relation-release-year pairs.
    """

    schema_class = RelationReleaseYearTable
    """
        The SQLAlchemy table class for relation-release-year pairs.
    """

    async def _get_all_by_query(
        self, query: Select[tuple[RelationReleaseYearTable]]
    ) -> list[RelationReleaseYear]:
        """
        Executes a query that should return multiple RelationReleaseYear objects.

        Args:
            query: The SQLAlchemy query to execute.

        Returns:
            List[RelationReleaseYear]: A list of retrieved relation-release-year objects.
        """
        result: Result = await self.execute(query)

        instances = result.scalars().all()
        relation_release_year_dbs = [
            RelationReleaseYearDB.model_validate(instance) for instance in instances
        ]
        relation_release_years = [
            relation_release_year_db.to_domain()
            for relation_release_year_db in relation_release_year_dbs
        ]
        return relation_release_years

    async def all(self) -> AsyncIterator[RelationReleaseYear]:
        """
        Retrieves all relation-release-year pairs from the database.

        Yields:
            AsyncIterator[RelationReleaseYear]: An async iterator yielding each
                relation-release-year pair.
        """
        async for instance in self._all():
            yield RelationReleaseYear.model_validate(instance)

    async def get(self, relation_id: int) -> list[RelationReleaseYear]:
        """
        Retrieves all relation-release-year pairs associated with a given relation ID.

        Args:
            relation_id: The ID of the relation.

        Returns:
            List[RelationReleaseYear]: A list of relation-release-year pairs associated
                with the specified relation ID.
        """
        query = (
            select(RelationReleaseYearTable)
            .where(RelationReleaseYearTable.relation_id == relation_id)
        )

        return await self._get_all_by_query(query)

    async def create(
        self,
        relation_release_year: RelationReleaseYearUncommitted,
        on_conflict_do_nothing=False,
    ) -> RelationReleaseYear:
        """
        Creates a new relation-release-year pair in the database.

        Args:
            relation_release_year: The RelationReleaseYearUncommitted object to create.
            on_conflict_do_nothing: If True, prevents the operation from failing if
                a unique constraint is violated.

        Returns:
            RelationReleaseYear: The created relation-release-year object.

        Raises:
            DatabaseError: If there is an error during the database operation.
        """
        from musigree.offline.offline_database_manager import OfflineDatabaseManager

        assert OfflineDatabaseManager.offline_database_helper is not None, (
            "OfflineDatabaseManager.offline_database_helper must be initialized before calling create()"
        )

        relation_release_year_dict = relation_release_year.model_dump()
        query = OfflineDatabaseManager.offline_database_helper.generate_insert_query(
            self.schema_class, relation_release_year_dict, on_conflict_do_nothing
        )
        result: Result = await self.execute(query)
        await self._session.flush()

        if not (instance := result.scalar_one_or_none()):
            raise DatabaseError

        relation_release_year_db = RelationReleaseYearDB.model_validate(instance)
        return relation_release_year_db.to_domain()

    async def create_bulk(
        self,
        relation_release_years: List[RelationReleaseYearUncommitted],
        on_conflict_do_nothing=False,
    ) -> None:
        """
        Creates multiple new relation-release-year pairs in the database.

        Args:
            relation_release_years: A list of RelationReleaseYearUncommitted objects
                to create.
            on_conflict_do_nothing: If True, prevents the operation from failing if
                a unique constraint is violated.
        """
        from musigree.offline.offline_database_manager import OfflineDatabaseManager

        assert OfflineDatabaseManager.offline_database_helper is not None, (
            "OfflineDatabaseManager.offline_database_helper must be initialized before calling create_bulk()"
        )

        relation_release_year_dicts = []
        for relation_release_year in relation_release_years:
            relation_release_year_dict = relation_release_year.model_dump()
            relation_release_year_dicts.append(relation_release_year_dict)
        query = (
            OfflineDatabaseManager.offline_database_helper.generate_insert_bulk_query(
                self.schema_class, relation_release_year_dicts, on_conflict_do_nothing
            )
        )
        await self.execute(query)
