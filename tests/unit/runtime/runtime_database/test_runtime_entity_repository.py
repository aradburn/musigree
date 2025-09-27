from unittest.mock import Mock, patch, AsyncMock

import pytest
from sqlalchemy import Result

from musigree.exceptions import NotFoundError, UnprocessableError
from musigree.library.fields.entity_type import EntityType
from musigree.runtime.runtime_database.runtime_entity_repository import (
    RuntimeEntityRepository,
)
from musigree.runtime.runtime_database.runtime_entity_table import RuntimeEntityTable
from musigree.runtime.runtime_database.runtime_session import CTX_RUNTIME_SESSION
from musigree.runtime.runtime_domain.entity import RuntimeEntityDB


# Import the test utility


class TestRuntimeEntityRepository:
    """Unit tests for RuntimeEntityRepository class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.repository = RuntimeEntityRepository()

    def test_schema_class(self) -> None:
        """Test that schema_class is correctly set."""
        # GIVEN/WHEN/THEN
        assert self.repository.schema_class == RuntimeEntityTable

    @pytest.mark.asyncio
    @patch.object(RuntimeEntityRepository, "execute")
    async def test_get_by_id_not_found(self, mock_execute: Mock) -> None:
        """Test retrieving an entity by ID when not found."""
        # GIVEN
        entity_id = 999

        mock_result = Mock(spec=Result)
        mock_scalars = Mock()
        mock_scalars.one_or_none.return_value = None
        mock_result.scalars.return_value = mock_scalars
        mock_execute.return_value = mock_result

        # WHEN/THEN
        with pytest.raises(NotFoundError):
            await self.repository.get_by_id(entity_id)

    @pytest.mark.asyncio
    @patch.object(RuntimeEntityRepository, "execute")
    async def test_get_by_id_success(self, mock_execute: Mock) -> None:
        """Test successfully retrieving an entity by ID."""
        # GIVEN
        entity_id = 1
        mock_instance = Mock()
        mock_instance.id = entity_id
        mock_instance.entity_id = 12345
        mock_instance.entity_type = EntityType.ARTIST
        mock_instance.entity_name = "Test Entity"
        mock_instance.relation_counts = {}
        mock_instance.entity_metadata = {}
        mock_instance.aliases = None
        mock_instance.groups = None
        mock_instance.members = None
        mock_instance.countries = None
        mock_instance.genres = None
        mock_instance.styles = None

        mock_result = Mock(spec=Result)
        mock_scalars = Mock()
        mock_scalars.one_or_none.return_value = mock_instance
        mock_result.scalars.return_value = mock_scalars
        mock_execute.return_value = mock_result

        # Mock the model validation and domain conversion
        with patch.object(RuntimeEntityDB, "model_validate") as mock_validate:
            mock_entity_db = Mock()
            mock_domain_entity = Mock()
            mock_entity_db.to_domain.return_value = mock_domain_entity
            mock_validate.return_value = mock_entity_db

            # WHEN
            result = await self.repository.get_by_id(entity_id)

            # THEN
            assert result == mock_domain_entity
            mock_validate.assert_called_once_with(mock_instance)
            mock_entity_db.to_domain.assert_called_once()

    @pytest.mark.asyncio
    @patch.object(RuntimeEntityRepository, "execute")
    async def test_count_by_type_success(self, mock_execute: Mock) -> None:
        """Test successfully counting entities by type."""
        # GIVEN
        entity_type = EntityType.ARTIST
        expected_count = 100

        mock_result = Mock(spec=Result)
        mock_result.scalar.return_value = expected_count
        mock_execute.return_value = mock_result

        # WHEN
        result = await self.repository.count_by_type(entity_type)

        # THEN
        assert result == expected_count

    @pytest.mark.asyncio
    @patch.object(RuntimeEntityRepository, "execute")
    async def test_count_by_type_non_integer_error(self, mock_execute: Mock) -> None:
        """Test count_by_type when database returns non-integer."""
        # GIVEN
        entity_type = EntityType.ARTIST

        mock_result = Mock(spec=Result)
        mock_result.scalar.return_value = "not_an_integer"
        mock_execute.return_value = mock_result

        # WHEN/THEN
        with pytest.raises(UnprocessableError):
            await self.repository.count_by_type(entity_type)

    @pytest.mark.asyncio
    async def test_update_success(self) -> None:
        """Test successfully updating an entity."""
        # GIVEN
        entity_id = 1
        payload = {"entity_name": "Updated Name", "genres": "Updated Genre"}

        # Create mock result and instance
        mock_result = Mock()
        mock_instance = Mock()
        mock_instance.id = entity_id
        mock_instance.entity_name = "Updated Name"
        mock_instance.genres = "Updated Genre"
        mock_result.scalar_one_or_none.return_value = mock_instance

        # Mock the session directly with AsyncMock
        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_result
        mock_session.flush.return_value = None

        # Set up context variable
        CTX_RUNTIME_SESSION.set(mock_session)

        try:
            # WHEN
            await self.repository.update(entity_id, payload)

            # THEN
            mock_session.execute.assert_called_once()
            mock_session.flush.assert_called_once()
        finally:
            # Clean up context
            try:
                CTX_RUNTIME_SESSION.get()
            except LookupError:
                pass

    @pytest.mark.asyncio
    async def test_delete_by_id_success(self) -> None:
        """Test successfully deleting an entity by ID."""
        # GIVEN
        entity_id = 1

        # Set up context variable
        mock_session = AsyncMock()
        token = CTX_RUNTIME_SESSION.set(mock_session)

        try:
            # WHEN
            await self.repository.delete_by_id(entity_id)

            # THEN
            mock_session.execute.assert_called_once()
            mock_session.flush.assert_called_once()
        finally:
            CTX_RUNTIME_SESSION.reset(token)

    @pytest.mark.asyncio
    @patch.object(RuntimeEntityRepository, "execute")
    async def test_get_by_entity_id_and_entity_type_not_found(
        self, mock_execute: Mock
    ) -> None:
        """Test get_by_entity_id_and_entity_type when entity not found."""
        # GIVEN
        entity_id = 12345
        entity_type = EntityType.ARTIST

        mock_result = Mock(spec=Result)
        mock_scalars = Mock()
        mock_scalars.one_or_none.return_value = None
        mock_result.scalars.return_value = mock_scalars
        mock_execute.return_value = mock_result

        # WHEN/THEN
        with pytest.raises(NotFoundError):
            await self.repository.get_by_entity_id_and_entity_type(
                entity_id, entity_type
            )

    @pytest.mark.asyncio
    @patch.object(RuntimeEntityRepository, "execute")
    async def test_get_by_entity_id_and_entity_type_success(
        self, mock_execute: Mock
    ) -> None:
        """Test successfully getting entity by entity_id and entity_type."""
        # GIVEN
        entity_id = 12345
        entity_type = EntityType.ARTIST
        mock_instance = Mock()
        mock_instance.id = 1
        mock_instance.entity_id = entity_id
        mock_instance.entity_type = entity_type
        mock_instance.entity_name = "Test Artist"
        mock_instance.relation_counts = {}
        mock_instance.entity_metadata = {}
        mock_instance.aliases = None
        mock_instance.groups = None
        mock_instance.members = None
        mock_instance.countries = None
        mock_instance.genres = None
        mock_instance.styles = None

        mock_result = Mock(spec=Result)
        mock_scalars = Mock()
        mock_scalars.one_or_none.return_value = mock_instance
        mock_result.scalars.return_value = mock_scalars
        mock_execute.return_value = mock_result

        # Mock the model validation and domain conversion
        with patch.object(RuntimeEntityDB, "model_validate") as mock_validate:
            mock_entity_db = Mock()
            mock_domain_entity = Mock()
            mock_entity_db.to_domain.return_value = mock_domain_entity
            mock_validate.return_value = mock_entity_db

            # WHEN
            result = await self.repository.get_by_entity_id_and_entity_type(
                entity_id, entity_type
            )

            # THEN
            assert result == mock_domain_entity
            mock_validate.assert_called_once_with(mock_instance)
            mock_entity_db.to_domain.assert_called_once()

    @pytest.mark.asyncio
    @patch.object(RuntimeEntityRepository, "execute")
    async def test_get_by_type_and_name_not_found(self, mock_execute: Mock) -> None:
        """Test get_by_type_and_name when entity not found."""
        # GIVEN
        entity_type = EntityType.ARTIST
        entity_name = "Nonexistent Artist"

        mock_result = Mock(spec=Result)
        mock_scalars = Mock()
        mock_scalars.one_or_none.return_value = None
        mock_result.scalars.return_value = mock_scalars
        mock_execute.return_value = mock_result

        # WHEN/THEN
        with pytest.raises(NotFoundError):
            await self.repository.get_by_type_and_name(entity_type, entity_name)

    @pytest.mark.asyncio
    @patch.object(RuntimeEntityRepository, "execute")
    async def test_get_by_type_and_name_success(self, mock_execute: Mock) -> None:
        """Test successfully getting entity by type and name."""
        # GIVEN
        entity_type = EntityType.ARTIST
        entity_name = "Test Artist"
        mock_instance = Mock()
        mock_instance.id = 1
        mock_instance.entity_id = 12345
        mock_instance.entity_type = entity_type
        mock_instance.entity_name = entity_name
        mock_instance.relation_counts = {}
        mock_instance.entity_metadata = {}
        mock_instance.aliases = None
        mock_instance.groups = None
        mock_instance.members = None
        mock_instance.countries = None
        mock_instance.genres = None
        mock_instance.styles = None

        mock_result = Mock(spec=Result)
        mock_scalars = Mock()
        mock_scalars.one_or_none.return_value = mock_instance
        mock_result.scalars.return_value = mock_scalars
        mock_execute.return_value = mock_result

        # Mock the model validation and domain conversion
        with patch.object(RuntimeEntityDB, "model_validate") as mock_validate:
            mock_entity_db = Mock()
            mock_domain_entity = Mock()
            mock_entity_db.to_domain.return_value = mock_domain_entity
            mock_validate.return_value = mock_entity_db

            # WHEN
            result = await self.repository.get_by_type_and_name(
                entity_type, entity_name
            )

            # THEN
            assert result == mock_domain_entity
            mock_validate.assert_called_once_with(mock_instance)
            mock_entity_db.to_domain.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_entity_id_by_entity_type_and_entity_name_success(self) -> None:
        """Test successfully retrieving entity ID by type and name."""
        # GIVEN
        entity_type = EntityType.ARTIST
        entity_name = "Test Artist"
        expected_entity_id = 12345

        # Set up context variable
        mock_session = AsyncMock()
        token = CTX_RUNTIME_SESSION.set(mock_session)

        try:
            # Mock the database result to return the expected ID
            mock_result = Mock()
            mock_result.scalar_one_or_none.return_value = expected_entity_id
            mock_session.execute.return_value = mock_result

            # WHEN
            result = await self.repository.get_entity_id_by_entity_type_and_entity_name(
                entity_type, entity_name
            )

            # THEN
            assert result == expected_entity_id
            mock_session.execute.assert_called_once()
        finally:
            CTX_RUNTIME_SESSION.reset(token)

    @pytest.mark.asyncio
    async def test_get_id_by_entity_type_and_entity_name_success(self) -> None:
        """Test successfully retrieving ID by entity type and name."""
        # GIVEN
        entity_type = EntityType.ARTIST
        entity_name = "Test Artist"
        expected_id = 1

        # Set up context variable
        mock_session = AsyncMock()
        token = CTX_RUNTIME_SESSION.set(mock_session)

        try:
            # Mock the database result to return the expected ID
            mock_result = Mock()
            mock_result.scalar_one_or_none.return_value = expected_id
            mock_session.execute.return_value = mock_result

            # WHEN
            result = await self.repository.get_id_by_entity_type_and_entity_name(
                entity_type, entity_name
            )

            # THEN
            assert result == expected_id
            mock_session.execute.assert_called_once()
        finally:
            CTX_RUNTIME_SESSION.reset(token)
