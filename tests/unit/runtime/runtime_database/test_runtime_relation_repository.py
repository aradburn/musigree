from typing import AsyncGenerator
from unittest.mock import Mock, patch, AsyncMock

import pytest
from sqlalchemy import Result

from musigree.exceptions import NotFoundError
from musigree.runtime.runtime_database.runtime_relation_repository import (
    RuntimeRelationRepository,
)
from musigree.runtime.runtime_database.runtime_relation_table import (
    RuntimeRelationTable,
)
from musigree.runtime.runtime_database.runtime_session import CTX_RUNTIME_SESSION
from musigree.runtime.runtime_domain.relation import (
    RuntimeRelationDB,
    RuntimeRelationUncommitted,
)

# Import the test utility
from .test_utils import RoleCacheMockHelper


class TestRuntimeRelationRepository:
    """Unit tests for RuntimeRelationRepository class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.repository = RuntimeRelationRepository()

    def test_schema_class(self) -> None:
        """Test that schema_class is correctly set."""
        # GIVEN/WHEN/THEN
        assert self.repository.schema_class == RuntimeRelationTable

    @pytest.mark.asyncio
    async def test_get_success(self) -> None:
        """Test successfully retrieving a relation by ID."""
        # GIVEN
        relation_id = 1
        mock_instance = Mock()
        mock_instance.id = relation_id
        mock_instance.subject = 12345
        mock_instance.predicate = 3
        mock_instance.object = 67890

        # Set up context variable
        mock_session = AsyncMock()
        token = CTX_RUNTIME_SESSION.set(mock_session)

        try:
            # Mock the session.execute to return a proper Result mock
            mock_result = Mock(spec=Result)
            mock_scalars = Mock()
            mock_scalars.one_or_none.return_value = mock_instance
            mock_result.scalars.return_value = mock_scalars
            mock_session.execute.return_value = mock_result

            with patch.object(RuntimeRelationDB, "model_validate") as mock_validate:
                expected_relation = RuntimeRelationDB(
                    id=relation_id,
                    subject=12345,
                    predicate=3,
                    object=67890,
                    release_id=12,
                    year=1999,
                )
                mock_validate.return_value = expected_relation

                # WHEN
                result = await self.repository.get(relation_id)

                # THEN
                assert result == expected_relation
                mock_validate.assert_called_once_with(mock_instance)
                mock_session.execute.assert_called_once()
        finally:
            CTX_RUNTIME_SESSION.reset(token)

    @pytest.mark.asyncio
    async def test_get_not_found(self) -> None:
        """Test retrieving a relation by ID when not found."""
        # GIVEN
        relation_id = 999

        # Set up context variable
        mock_session = AsyncMock()
        token = CTX_RUNTIME_SESSION.set(mock_session)

        try:
            # Mock the session.execute to return a proper Result mock
            mock_result = Mock(spec=Result)
            mock_scalars = Mock()
            mock_scalars.one_or_none.return_value = None
            mock_result.scalars.return_value = mock_scalars
            mock_session.execute.return_value = mock_result

            # WHEN/THEN
            with pytest.raises(NotFoundError):
                await self.repository.get(relation_id)
        finally:
            CTX_RUNTIME_SESSION.reset(token)

    @pytest.mark.asyncio
    async def test_get_id_by_key_success(self) -> None:
        """Test successfully retrieving relation ID by key."""
        # GIVEN
        key = {"subject": 12345, "role_id": 3, "object": 67890}
        expected_id = 1

        # Set up context variable
        mock_session = AsyncMock()
        token = CTX_RUNTIME_SESSION.set(mock_session)

        try:
            # Mock the session.execute to return a proper Result mock
            mock_result = Mock(spec=Result)
            mock_result.scalar.return_value = expected_id
            mock_session.execute.return_value = mock_result

            # WHEN
            result = await self.repository.get_id_by_key(key)

            # THEN
            assert result == expected_id
            mock_session.execute.assert_called_once()
        finally:
            CTX_RUNTIME_SESSION.reset(token)

    @pytest.mark.asyncio
    async def test_get_id_by_key_not_found(self) -> None:
        """Test get_id_by_key when relation not found."""
        # GIVEN
        key = {"subject": 12345, "role_id": 3, "object": 67890}

        # Set up context variable
        mock_session = AsyncMock()
        token = CTX_RUNTIME_SESSION.set(mock_session)

        try:
            # Mock the session.execute to return a proper Result mock
            mock_result = Mock(spec=Result)
            mock_result.scalar.return_value = None
            mock_session.execute.return_value = mock_result

            # WHEN/THEN
            with pytest.raises(NotFoundError):
                await self.repository.get_id_by_key(key)
        finally:
            CTX_RUNTIME_SESSION.reset(token)

    @pytest.mark.asyncio
    @patch.object(RuntimeRelationRepository, "execute")
    async def test_find_by_id_success(self, mock_execute: Mock) -> None:
        """Test successfully finding relation by ID with lock."""
        # GIVEN
        relation_id = 1
        mock_instance = Mock()
        mock_instance.id = relation_id
        mock_instance.subject = 12345
        mock_instance.predicate = 3
        mock_instance.object = 67890

        mock_result = Mock(spec=Result)
        mock_scalars = Mock()
        mock_scalars.one_or_none.return_value = mock_instance
        mock_result.scalars.return_value = mock_scalars
        mock_execute.return_value = mock_result

        with patch.object(RuntimeRelationRepository, "_get_one_by_query") as mock_get_one:
            mock_relation = Mock()
            mock_get_one.return_value = mock_relation

            # WHEN
            result = await self.repository.find_by_id(relation_id)

            # THEN
            assert result == mock_relation

    @pytest.mark.asyncio
    @patch.object(RuntimeRelationRepository, "execute")
    async def test_find_by_key_with_role_name(self, mock_execute: Mock) -> None:
        """Test finding relation by key when role_name is provided."""
        # GIVEN
        key = {"subject": 12345, "role_name": "Producer", "object": 67890}
        role_id = 3

        # Use the RoleCacheMockHelper for proper module-specific mocking
        with RoleCacheMockHelper.mock_role_cache_in_module(
            "musigree.runtime.runtime_database.runtime_relation_repository",
            {"Producer": role_id},
        ):
            mock_instance = Mock()
            mock_instance.id = 1
            mock_instance.subject = 12345
            mock_instance.predicate = role_id
            mock_instance.object = 67890

            mock_result = Mock(spec=Result)
            mock_scalars = Mock()
            mock_scalars.all.return_value = mock_instance
            mock_result.scalars.return_value = mock_scalars
            mock_execute.return_value = mock_result

            with patch.object(RuntimeRelationRepository, "_get_all_by_query") as mock_get_all:
                mock_relation = Mock()
                mock_get_all.return_value = mock_relation

                # WHEN
                result = await self.repository.find_by_key(key)

                # THEN
                assert result == mock_relation

    @pytest.mark.asyncio
    @patch.object(RuntimeRelationRepository, "execute")
    async def test_find_by_entity_success(self, mock_execute: Mock) -> None:
        """Test successfully finding relations by entity ID."""
        # GIVEN
        entity_id = 12345

        mock_instance1 = Mock()
        mock_instance1.id = 1
        mock_instance1.subject = entity_id
        mock_instance1.predicate = 3
        mock_instance1.object = 67890

        mock_instance2 = Mock()
        mock_instance2.id = 2
        mock_instance2.subject = 11111
        mock_instance2.predicate = 4
        mock_instance2.object = entity_id

        mock_result = Mock(spec=Result)
        mock_scalars = Mock()
        mock_scalars.all.return_value = [mock_instance1, mock_instance2]
        mock_result.scalars.return_value = mock_scalars
        mock_execute.return_value = mock_result

        with patch.object(RuntimeRelationRepository, "_get_all_by_query") as mock_get_one:
            mock_relations = [Mock(), Mock()]
            mock_get_one.return_value = mock_relations

            # WHEN
            result = await self.repository.find_by_entity(entity_id)

            # THEN
            assert result == mock_relations
            assert len(result) == 2

    @pytest.mark.asyncio
    @patch.object(RuntimeRelationRepository, "execute")
    async def test_find_by_entity_and_roles_success(self, mock_execute: Mock) -> None:
        """Test successfully finding relations by entity ID and roles."""
        # GIVEN
        entity_id = 12345
        role_ids = [3, 4]

        mock_instance1 = Mock()
        mock_instance1.id = 1
        mock_instance1.subject = entity_id
        mock_instance1.predicate = 3
        mock_instance1.object = 67890

        mock_result = Mock(spec=Result)
        mock_scalars = Mock()
        mock_scalars.all.return_value = [mock_instance1]
        mock_result.scalars.return_value = mock_scalars
        mock_execute.return_value = mock_result

        with patch.object(RuntimeRelationRepository, "_get_all_by_query") as mock_get_all:
            mock_relations = [Mock()]
            mock_get_all.return_value = mock_relations

            # WHEN
            result = await self.repository.find_by_entity_and_roles(entity_id, role_ids)

            # THEN
            assert result == mock_relations
            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_create_success(self) -> None:
        """Test successfully creating a new relation."""
        # GIVEN
        from musigree.runtime.runtime_database_manager import RuntimeDatabaseManager

        relation_data = RuntimeRelationUncommitted(
            subject=12345,
            role_name="Producer",
            object=67890,
            release_id=12,
            year=1999,
        )

        # Set up context variable
        mock_session = AsyncMock()
        token = CTX_RUNTIME_SESSION.set(mock_session)

        # Mock the database helper
        mock_helper = Mock()
        mock_query = Mock()
        mock_helper.generate_insert_query.return_value = mock_query
        RuntimeDatabaseManager.runtime_database_helper = mock_helper

        try:
            # Use the RoleCacheMockHelper for proper module-specific mocking
            with RoleCacheMockHelper.mock_role_cache_in_module(
                "musigree.runtime.runtime_database.runtime_relation_repository",
                {"Producer": 3},
            ):
                # Mock the session execute and flush
                mock_result = Mock(spec=Result)
                mock_instance = Mock()
                mock_instance.id = 1
                mock_instance.subject = 12345
                mock_instance.predicate = 3
                mock_instance.object = 67890
                mock_result.scalar_one_or_none.return_value = mock_instance
                mock_session.execute.return_value = mock_result

                with patch.object(RuntimeRelationDB, "model_validate") as mock_validate:
                    mock_relation_db = Mock()
                    mock_relation_internal = Mock()
                    mock_relation_db.to_domain.return_value = mock_relation_internal
                    mock_validate.return_value = mock_relation_db

                    # WHEN
                    result = await self.repository.create(relation_data)

                    # THEN
                    assert result == mock_relation_internal
                    mock_session.execute.assert_called_once_with(mock_query)
                    mock_session.flush.assert_called_once()
                    mock_validate.assert_called_once_with(mock_instance)
        finally:
            CTX_RUNTIME_SESSION.reset(token)
            RuntimeDatabaseManager.runtime_database_helper = None  # type: ignore

    @pytest.mark.asyncio
    async def test_delete_by_entitys_success(self) -> None:
        """Test successfully deleting relations by entity ID."""
        # GIVEN
        entity_id = 12345

        # Set up context variable
        mock_session = AsyncMock()
        token = CTX_RUNTIME_SESSION.set(mock_session)

        try:
            # WHEN
            await self.repository.delete_by_entitys(entity_id)

            # THEN
            mock_session.execute.assert_called_once()
            mock_session.flush.assert_called_once()
        finally:
            CTX_RUNTIME_SESSION.reset(token)

    @pytest.mark.asyncio
    async def test_all_iterator(self) -> None:
        """Test the all() iterator method."""
        # GIVEN
        mock_instance1 = Mock()
        mock_instance1.id = 1
        mock_instance1.subject = 12345
        mock_instance1.predicate = 3
        mock_instance1.object = 67890

        mock_instance2 = Mock()
        mock_instance2.id = 2
        mock_instance2.subject = 11111
        mock_instance2.predicate = 4
        mock_instance2.object = 22222

        # Mock async generator
        async def async_generator() -> AsyncGenerator[Mock, None]:
            yield mock_instance1
            yield mock_instance2

        with patch.object(RuntimeRelationRepository, "_all") as mock_all:
            mock_all.return_value = async_generator()

            with patch.object(RuntimeRelationDB, "model_validate") as mock_validate:
                with patch.object(RuntimeRelationDB, "to_domain") as _mock_to_domain:
                    relation1 = Mock()
                    relation2 = Mock()

                    # Create mock RuntimeRelationDB instances
                    mock_relation_db1 = Mock()
                    mock_relation_db1.to_domain.return_value = relation1
                    mock_relation_db2 = Mock()
                    mock_relation_db2.to_domain.return_value = relation2

                    mock_validate.side_effect = [mock_relation_db1, mock_relation_db2]

                    # WHEN
                    result = []
                    async for relation in self.repository.all():
                        result.append(relation)

                    # THEN
                    assert len(result) == 2
                    assert result[0] == relation1
                    assert result[1] == relation2
