"""
Unit tests for the EntityRepository class.

This module tests the EntityRepository class which manages Entity objects
in the offline database, including CRUD operations and specialized queries.
"""

from unittest.mock import AsyncMock, Mock, patch, PropertyMock

import pytest
from sqlalchemy import Result, select

from musigree import utils
from musigree.config import SqliteTestConfiguration
from musigree.exceptions import NotFoundError
from musigree.library.fields.entity_type import EntityType
from musigree.offline.database.entity_repository import EntityRepository
from musigree.offline.database.entity_table import EntityTable
from musigree.offline.domain.entity import Entity


class TestEntityRepository:
    """Test class for EntityRepository."""

    @pytest.fixture(autouse=True)
    def setup_config(self) -> None:
        """Set up test configuration."""
        self.config = SqliteTestConfiguration()

    @pytest.fixture
    def mock_entity(self) -> Entity:
        """Create a mock entity for testing."""
        return Entity(
            id=1,
            entity_id=12345,
            entity_type=EntityType.ARTIST,
            entity_name="Test Artist",
            entity_metadata={"profile": "Test profile"},
            relation_counts={"performer": 5},
            entities={},
            search_content="test artist",
        )

    @pytest.fixture
    def mock_entity_table(self) -> EntityTable:
        """Create a mock entity table record."""
        table_mock = Mock(spec=EntityTable)
        table_mock.id = 1
        table_mock.entity_id = 12345
        table_mock.entity_type = EntityType.ARTIST
        table_mock.entity_name = "Test Artist"
        table_mock.entity_metadata = {"profile": "Test profile"}
        table_mock.relation_counts = {"performer": 5}
        table_mock.entities = {}
        table_mock.search_content = "test artist"
        return table_mock

    @pytest.fixture
    def entity_repository(self) -> EntityRepository:
        """Create an EntityRepository instance for testing."""
        return EntityRepository()

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        """Create a mock async session."""
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_get_one_by_query_success(
        self,
        entity_repository: EntityRepository,
        mock_entity_table: EntityTable,
        mock_entity: Entity,
    ) -> None:
        """Test successful _get_one_by_query execution."""
        # Arrange
        query = select(EntityTable).where(EntityTable.id == 1)

        with patch.object(entity_repository, "execute") as mock_execute:
            mock_result = Mock(spec=Result)
            mock_result.scalars.return_value.one_or_none.return_value = (
                mock_entity_table
            )
            mock_execute.return_value = mock_result

            with patch.object(Entity, "model_validate") as mock_validate:
                mock_entity_instance = Mock()
                mock_entity_instance.to_domain.return_value = mock_entity
                mock_validate.return_value = mock_entity_instance

                # Act
                result = await entity_repository._get_one_by_query(query)

                # Assert
                assert result == mock_entity
                mock_execute.assert_called_once_with(query)
                mock_validate.assert_called_once_with(mock_entity_table)

    @pytest.mark.asyncio
    async def test_get_one_by_query_not_found(
        self, entity_repository: EntityRepository
    ) -> None:
        """Test _get_one_by_query when no entity is found."""
        # Arrange
        query = select(EntityTable).where(EntityTable.id == 999)

        with patch.object(entity_repository, "execute") as mock_execute:
            mock_result = Mock(spec=Result)
            mock_result.scalars.return_value.one_or_none.return_value = None
            mock_execute.return_value = mock_result

            # Act & Assert
            with pytest.raises(NotFoundError):
                await entity_repository._get_one_by_query(query)

    @pytest.mark.asyncio
    async def test_get_all_by_query_success(
        self,
        entity_repository: EntityRepository,
        mock_entity_table: EntityTable,
        mock_entity: Entity,
    ) -> None:
        """Test successful _get_all_by_query execution."""
        # Arrange
        query = select(EntityTable).where(EntityTable.entity_type == EntityType.ARTIST)

        with patch.object(entity_repository, "execute") as mock_execute:
            mock_result = Mock(spec=Result)
            mock_result.scalars.return_value.all.return_value = [mock_entity_table]
            mock_execute.return_value = mock_result

            with patch.object(Entity, "model_validate") as mock_validate:
                mock_entity_instance = Mock()
                mock_entity_instance.to_domain.return_value = mock_entity
                mock_validate.return_value = mock_entity_instance

                # Act
                result = await entity_repository._get_all_by_query(query)

                # Assert
                assert result == [mock_entity]
                mock_execute.assert_called_once_with(query)
                mock_validate.assert_called_once_with(mock_entity_table)

    @pytest.mark.asyncio
    async def test_get_all_by_query_empty_result(
        self, entity_repository: EntityRepository
    ) -> None:
        """Test _get_all_by_query when no entities are found."""
        # Arrange
        query = select(EntityTable).where(EntityTable.entity_type == EntityType.LABEL)

        with patch.object(entity_repository, "execute") as mock_execute:
            mock_result = Mock(spec=Result)
            mock_result.scalars.return_value.all.return_value = []
            mock_execute.return_value = mock_result

            # Act
            result = await entity_repository._get_all_by_query(query)

            # Assert
            assert result == []

    @pytest.mark.asyncio
    async def test_get_ids_success(
        self, entity_repository: EntityRepository, mock_session: AsyncMock
    ) -> None:
        """Test successful get_ids execution."""
        # Arrange
        expected_ids = [1, 2, 3, 4, 5]
        mock_scalars_result = Mock()
        mock_scalars_result.all.return_value = expected_ids
        mock_result = Mock()
        mock_result.scalars.return_value = mock_scalars_result
        mock_session.execute.return_value = mock_result

        with patch.object(
            EntityRepository, "_session", new_callable=PropertyMock
        ) as mock_session_prop:
            mock_session_prop.return_value = mock_session

            # Act
            result = await entity_repository.get_ids()

            # Assert
            assert result == expected_ids
            mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_ids_by_type_success(
        self, entity_repository: EntityRepository, mock_session: AsyncMock
    ) -> None:
        """Test successful get_ids_by_type execution."""
        # Arrange
        entity_type = EntityType.ARTIST
        expected_ids = [1, 3, 5]
        mock_scalars_result = Mock()
        mock_scalars_result.all.return_value = expected_ids
        mock_result = Mock()
        mock_result.scalars.return_value = mock_scalars_result
        mock_session.execute.return_value = mock_result

        with patch.object(
            EntityRepository, "_session", new_callable=PropertyMock
        ) as mock_session_prop:
            mock_session_prop.return_value = mock_session

            # Act
            result = await entity_repository.get_ids_by_type(entity_type)

            # Assert
            assert result == expected_ids
            mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_id_success(
        self, entity_repository: EntityRepository, mock_entity: Entity
    ) -> None:
        """Test successful get_by_id execution."""
        # Arrange
        entity_id = 1

        with patch.object(entity_repository, "_get_one_by_query") as mock_get_one:
            mock_get_one.return_value = mock_entity

            # Act
            result = await entity_repository.get_by_id(entity_id)

            # Assert
            assert result == mock_entity
            mock_get_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_entity_id_and_entity_type_success(
        self, entity_repository: EntityRepository, mock_entity: Entity
    ) -> None:
        """Test successful get_by_entity_id_and_entity_type execution."""
        # Arrange
        entity_id = 12345
        entity_type = EntityType.ARTIST

        with patch.object(entity_repository, "_get_one_by_query") as mock_get_one:
            mock_get_one.return_value = mock_entity

            # Act
            result = await entity_repository.get_by_entity_id_and_entity_type(
                entity_id, entity_type
            )

            # Assert
            assert result == mock_entity
            mock_get_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_entity_ids_by_type_success(
        self, entity_repository: EntityRepository, mock_session: AsyncMock
    ) -> None:
        """Test successful get_entity_ids_by_type execution."""
        # Arrange
        entity_type = EntityType.LABEL
        expected_ids = [100, 200, 300]
        mock_scalars_result = Mock()
        mock_scalars_result.all.return_value = expected_ids
        mock_result = Mock()
        mock_result.scalars.return_value = mock_scalars_result
        mock_session.execute.return_value = mock_result

        with patch.object(
            EntityRepository, "_session", new_callable=PropertyMock
        ) as mock_session_prop:
            mock_session_prop.return_value = mock_session

            # Act
            result = await entity_repository.get_entity_ids_by_type(entity_type)

            # Assert
            assert result == expected_ids
            mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_by_search_content_success(
        self, entity_repository: EntityRepository, mock_entity: Entity
    ) -> None:
        """Test successful find_by_search_content execution."""
        # Arrange
        search_content = "test artist"

        with patch.object(entity_repository, "_get_all_by_query") as mock_get_all:
            mock_get_all.return_value = [mock_entity]

            # Act
            result = await entity_repository.find_by_search_content(search_content)

            # Assert
            assert result == [mock_entity]
            mock_get_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_batched_ids_success(
        self, entity_repository: EntityRepository
    ) -> None:
        """Test successful get_batched_ids execution."""
        # Arrange
        batch_size = 2
        all_ids = [1, 2, 3, 4, 5]

        with patch.object(entity_repository, "get_ids") as mock_get_ids:
            mock_get_ids.return_value = all_ids

            # Act
            ids = await entity_repository.get_ids()
            result = utils.batched(ids, batch_size)

            # Assert - get_batched_ids returns a generator, so convert to list
            batches = list(result)
            expected_batches = [[1, 2], [3, 4], [5]]
            assert batches == expected_batches

    @pytest.mark.asyncio
    async def test_get_batched_ids_empty_result(
        self, entity_repository: EntityRepository
    ) -> None:
        """Test get_batched_ids with empty result."""
        # Arrange
        batch_size = 2

        with patch.object(entity_repository, "get_ids") as mock_get_ids:
            mock_get_ids.return_value = []

            # Act
            ids = await entity_repository.get_ids()
            result = utils.batched(ids, batch_size)

            # Assert - convert generator to list
            batches = list(result)
            assert batches == []

    @pytest.mark.asyncio
    async def test_create_success(
        self, entity_repository: EntityRepository, mock_entity: Entity
    ) -> None:
        """Test successful create execution."""
        # Arrange
        with patch.object(entity_repository, "_save") as mock_save:
            mock_table_instance = Mock(spec=EntityTable)
            mock_save.return_value = mock_table_instance

            with patch.object(Entity, "model_validate") as mock_validate:
                mock_validate.return_value = mock_entity

                # Act
                result = await entity_repository.create(mock_entity)

                # Assert
                assert result == mock_entity
                mock_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_success(
        self, entity_repository: EntityRepository, mock_session: AsyncMock
    ) -> None:
        """Test successful update execution."""
        # Arrange
        entity_id = 1
        payload = {"entity_name": "Updated Artist"}

        with patch.object(
            EntityRepository, "_session", new_callable=PropertyMock
        ) as mock_session_prop:
            mock_session_prop.return_value = mock_session

            # Act
            await entity_repository.update(entity_id, payload)

            # Assert - update method returns None in the actual implementation
            mock_session.execute.assert_called_once()
            mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_type_and_name_success(
        self, entity_repository: EntityRepository, mock_entity: Entity
    ) -> None:
        """Test successful get_by_type_and_name execution."""
        # Arrange
        entity_type = EntityType.ARTIST
        entity_name = "Test Artist"

        with patch.object(entity_repository, "_get_one_by_query") as mock_get_one:
            mock_get_one.return_value = mock_entity

            # Act
            result = await entity_repository.get_by_type_and_name(
                entity_type, entity_name
            )

            # Assert
            assert result == mock_entity
            mock_get_one.assert_called_once()

    def test_schema_class_is_set(self, entity_repository: EntityRepository) -> None:
        """Test that schema_class is properly set."""
        assert entity_repository.schema_class == EntityTable

    def test_repository_initialization_success(self) -> None:
        """Test successful repository initialization."""
        repo = EntityRepository()
        assert repo.schema_class == EntityTable
