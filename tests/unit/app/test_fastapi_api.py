"""
Unit tests for musigree.app.fastapi_api module.
"""

from unittest.mock import patch, AsyncMock, MagicMock, Mock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.requests import Request
from starlette.responses import JSONResponse

from musigree.app.fastapi_api import router
from musigree.config import SqliteTestConfiguration, Configuration
from musigree.exceptions import BadRequestError, NotFoundError, DatabaseError
from musigree.library.fields.entity_type import EntityType


# Exception handlers for the test FastAPI app
async def bad_request_handler(_request: Request, _exc: Exception) -> JSONResponse:
    """Mock bad request handler for testing."""
    return JSONResponse(status_code=400, content={"error": "Bad Request"})


async def not_found_handler(_request: Request, _exc: Exception) -> JSONResponse:
    """Mock not found handler for testing."""
    return JSONResponse(status_code=404, content={"error": "Not Found"})


async def database_error_handler(_request: Request, _exc: Exception) -> JSONResponse:
    """Mock database error handler for testing."""
    return JSONResponse(status_code=500, content={"error": "Database Error"})


@pytest.fixture
def client() -> TestClient:
    """Create a test client."""
    app = FastAPI()
    app.include_router(router, prefix="/api")

    # Add exception handlers
    app.add_exception_handler(BadRequestError, bad_request_handler)
    app.add_exception_handler(NotFoundError, not_found_handler)
    app.add_exception_handler(DatabaseError, database_error_handler)

    return TestClient(app)


class TestFastAPIRoutes:
    """Test cases for FastAPI routes."""

    @pytest.fixture
    def test_config(self) -> Configuration:
        """Provide test configuration."""
        return SqliteTestConfiguration()

    @pytest.mark.asyncio
    @patch("musigree.app.fastapi_api.runtime_transaction")
    @patch(
        "musigree.runtime.runtime_database.runtime_entity_repository.RuntimeEntityRepository"
    )
    @patch(
        "musigree.runtime.runtime_database.runtime_relation_repository.RuntimeRelationRepository"
    )
    @patch("musigree.runtime.runtime_database_manager.RuntimeDatabaseManager")
    async def test_route_entity_relations_success(
        self,
        mock_db_manager_class: Mock,
        mock_relation_repo_class: Mock,
        mock_entity_repo_class: Mock,
        mock_runtime_transaction: Mock,
        client: TestClient,
    ) -> None:
        """Test successful entity relations retrieval."""
        # Arrange
        mock_entity_repo = AsyncMock()
        mock_relation_repo = AsyncMock()
        mock_entity_repo_class.return_value = mock_entity_repo
        mock_relation_repo_class.return_value = mock_relation_repo

        # Mock the async session
        mock_session = AsyncMock()

        # Mock the transaction context manager
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__.return_value = mock_session
        mock_context_manager.__aexit__.return_value = None
        mock_runtime_transaction.return_value = mock_context_manager

        # Mock the database helper method as async
        mock_db_helper = AsyncMock()
        mock_db_helper.get_relations_by_entity_id_and_entity_type = AsyncMock(
            return_value={"relations": [{"id": "1", "type": "artist"}]}
        )
        mock_db_manager_class.runtime_database_helper = mock_db_helper

        # Act
        response = client.get("/api/artist/relations/123")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "relations" in data

    @pytest.mark.asyncio
    @patch("musigree.app.fastapi_api.runtime_transaction")
    @patch(
        "musigree.runtime.runtime_database.runtime_entity_repository.RuntimeEntityRepository"
    )
    @patch(
        "musigree.runtime.runtime_database.runtime_relation_repository.RuntimeRelationRepository"
    )
    @patch("musigree.runtime.runtime_database_manager.RuntimeDatabaseManager")
    async def test_route_entity_relations_invalid_entity_id(
        self,
        mock_db_manager_class: Mock,
        mock_relation_repo_class: Mock,
        mock_entity_repo_class: Mock,
        mock_runtime_transaction: Mock,
        client: TestClient,
    ) -> None:
        """Test entity relations with invalid entity ID."""
        # Arrange
        mock_entity_repo = AsyncMock()
        mock_relation_repo = AsyncMock()
        mock_entity_repo_class.return_value = mock_entity_repo
        mock_relation_repo_class.return_value = mock_relation_repo

        # Mock the async session
        mock_session = AsyncMock()

        # Mock the transaction context manager
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__.return_value = mock_session
        mock_context_manager.__aexit__.return_value = None
        mock_runtime_transaction.return_value = mock_context_manager

        # Configure the mock
        mock_entity_repo.exists.return_value = False

        # Act
        response = client.get("/api/artist/relations/invalid_id")

        # Assert - invalid entity ID format returns 400, not 404
        assert response.status_code == 400

    @pytest.mark.asyncio
    @patch("musigree.app.fastapi_api.runtime_transaction")
    @patch(
        "musigree.runtime.runtime_database.runtime_entity_repository.RuntimeEntityRepository"
    )
    @patch(
        "musigree.runtime.runtime_database.runtime_relation_repository.RuntimeRelationRepository"
    )
    @patch("musigree.runtime.runtime_database_manager.RuntimeDatabaseManager")
    async def test_route_entity_network_success(
        self,
        mock_db_manager_class: Mock,
        mock_relation_repo_class: Mock,
        mock_entity_repo_class: Mock,
        mock_runtime_transaction: Mock,
        client: TestClient,
    ) -> None:
        """Test successful entity network retrieval."""
        # Arrange
        mock_entity_repo = AsyncMock()
        mock_relation_repo = AsyncMock()
        mock_entity_repo_class.return_value = mock_entity_repo
        mock_relation_repo_class.return_value = mock_relation_repo

        # Mock the async session
        mock_session = AsyncMock()

        # Mock the transaction context manager
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__.return_value = mock_session
        mock_context_manager.__aexit__.return_value = None
        mock_runtime_transaction.return_value = mock_context_manager

        # Mock the database helper method as async
        mock_db_helper = AsyncMock()
        mock_db_helper.get_network = AsyncMock(
            return_value={"graph": {"nodes": [], "edges": []}}
        )
        mock_db_manager_class.runtime_database_helper = mock_db_helper

        # Act
        response = client.get("/api/artist/network/123")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "graph" in data

    @pytest.mark.asyncio
    @patch("musigree.app.fastapi_api.runtime_transaction")
    @patch(
        "musigree.runtime.runtime_database.runtime_entity_repository.RuntimeEntityRepository"
    )
    @patch(
        "musigree.runtime.runtime_database.runtime_relation_repository.RuntimeRelationRepository"
    )
    @patch("musigree.runtime.runtime_database_manager.RuntimeDatabaseManager")
    async def test_route_entity_network_invalid_entity_id(
        self,
        mock_db_manager_class: Mock,
        mock_relation_repo_class: Mock,
        mock_entity_repo_class: Mock,
        mock_runtime_transaction: Mock,
        client: TestClient,
    ) -> None:
        """Test entity network with invalid entity ID."""
        # Arrange
        mock_entity_repo = AsyncMock()
        mock_relation_repo = AsyncMock()
        mock_entity_repo_class.return_value = mock_entity_repo
        mock_relation_repo_class.return_value = mock_relation_repo

        # Mock the async session
        mock_session = AsyncMock()

        # Mock the transaction context manager
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__.return_value = mock_session
        mock_context_manager.__aexit__.return_value = None
        mock_runtime_transaction.return_value = mock_context_manager

        # Configure the mock
        mock_entity_repo.exists.return_value = False

        # Act
        response = client.get("/api/artist/network/invalid_id")

        # Assert - invalid entity ID format returns 400, not 404
        assert response.status_code == 400

    @pytest.mark.asyncio
    @patch("musigree.library.cache.cache_manager.CacheManager.get_cache")
    @patch("musigree.runtime.runtime_database_manager.RuntimeDatabaseManager")
    async def test_route_search_success(
        self,
        mock_db_manager_class: Mock,
        mock_cache_manager: Mock,
        client: TestClient,
    ) -> None:
        """Test successful search."""
        # Arrange
        # Mock cache
        mock_cache = MagicMock()
        mock_cache.get.return_value = None  # Force a cache miss
        mock_cache_manager.return_value = mock_cache

        # Mock the database helper method for search
        mock_db_helper = MagicMock()
        mock_db_helper.search_text_index = MagicMock(
            return_value=[(123, "Test Artist")]
        )
        mock_db_manager_class.runtime_database_helper = mock_db_helper

        # Act
        response = client.get("/api/search/test")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "results" in data

    @pytest.mark.asyncio
    @patch("musigree.app.fastapi_api.runtime_transaction")
    @patch(
        "musigree.runtime.runtime_database.runtime_entity_repository.RuntimeEntityRepository"
    )
    async def test_route_entity_details_success(
        self,
        mock_entity_repo_class: Mock,
        mock_runtime_transaction: Mock,
        client: TestClient,
    ) -> None:
        """Test successful entity details retrieval."""
        # Arrange
        mock_entity_repo = AsyncMock()
        mock_entity_repo_class.return_value = mock_entity_repo

        # Mock the async session
        mock_session = AsyncMock()

        # Mock the transaction context manager
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__.return_value = mock_session
        mock_context_manager.__aexit__.return_value = None
        mock_runtime_transaction.return_value = mock_context_manager

        # Create a mock entity with proper attributes
        mock_entity = MagicMock()
        mock_entity.entity_id = 123
        mock_entity.entity_type = EntityType.ARTIST
        mock_entity.entity_name = "Test Artist"
        mock_entity.entity_metadata = {}
        mock_entity.entities = []
        mock_entity.relation_counts = {}
        mock_entity.countries = []
        mock_entity.genres = []
        mock_entity.styles = []

        # Configure the async method to return the mock entity
        mock_entity_repo.get_by_entity_id_and_entity_type = AsyncMock(
            return_value=mock_entity
        )

        # Act
        response = client.get("/api/artist/details/123")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 123
        assert data["type"] == "artist"
        assert data["name"] == "Test Artist"

    @pytest.mark.asyncio
    @patch("musigree.app.fastapi_api.runtime_transaction")
    @patch(
        "musigree.runtime.runtime_database.runtime_entity_repository.RuntimeEntityRepository"
    )
    async def test_route_entity_details_invalid_entity_id(
        self,
        mock_entity_repo_class: Mock,
        mock_runtime_transaction: Mock,
        client: TestClient,
    ) -> None:
        """Test entity details with invalid entity ID."""
        # Arrange
        mock_entity_repo = AsyncMock()
        mock_entity_repo_class.return_value = mock_entity_repo

        # Mock the async session
        mock_session = AsyncMock()

        # Mock the transaction context manager
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__.return_value = mock_session
        mock_context_manager.__aexit__.return_value = None
        mock_runtime_transaction.return_value = mock_context_manager

        # Configure the mock
        mock_entity_repo.exists.return_value = False

        # Act
        response = client.get("/api/artist/details/invalid_id")

        # Assert - invalid entity ID format returns 400, not 404
        assert response.status_code == 400

    @patch("musigree.app.fastapi_api.runtime_transaction")
    @patch(
        "musigree.runtime.runtime_database.runtime_entity_repository.RuntimeEntityRepository"
    )
    @patch(
        "musigree.runtime.runtime_database.runtime_relation_repository.RuntimeRelationRepository"
    )
    @patch("musigree.runtime.runtime_database_manager.RuntimeDatabaseManager")
    def test_route_entity_relations_not_found(
        self,
        mock_db_manager_class: Mock,
        mock_relation_repo_class: Mock,
        mock_entity_repo_class: Mock,
        mock_runtime_transaction: Mock,
        client: TestClient,
    ) -> None:
        """Test entity relations when no data is found."""
        # Arrange
        mock_entity_repo = AsyncMock()
        mock_relation_repo = AsyncMock()
        mock_entity_repo_class.return_value = mock_entity_repo
        mock_relation_repo_class.return_value = mock_relation_repo

        # Mock the async session
        mock_session = AsyncMock()

        # Mock the transaction context manager
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__.return_value = mock_session
        mock_context_manager.__aexit__.return_value = None
        mock_runtime_transaction.return_value = mock_context_manager

        # Configure get_concurrency_count to return an integer
        mock_db_manager_class.get_concurrency_count.return_value = 1

        # Mock the database helper method as async returning None
        mock_db_helper = AsyncMock()
        mock_db_helper.get_relations_by_entity_id_and_entity_type = AsyncMock(
            return_value=None
        )
        mock_db_manager_class.runtime_database_helper = mock_db_helper

        # Act
        response = client.get("/api/artist/relations/999")

        # Assert - should return 404 when no data is found
        assert response.status_code == 404

    @patch("musigree.library.cache.role_cache.RoleCache")
    def test_route_roles_success(
        self, mock_role_cache: Mock, client: TestClient
    ) -> None:
        """Test successful roles retrieval."""
        # Arrange
        expected_data = {"roles": ["vocals", "guitar", "drums"]}
        mock_role_cache.get_all_roles.return_value = expected_data

        # Act
        response = client.get("/api/roles")

        # Assert
        assert response.status_code == 200
        assert response.json() == expected_data
        mock_role_cache.get_all_roles.assert_called_once()


class TestEntityTypeValidation:
    """Test cases for entity type validation."""

    def test_valid_entity_types(self) -> None:
        """Test that valid entity types are accepted."""
        valid_types = ["artist", "label"]
        for entity_type_str in valid_types:
            try:
                entity_type = EntityType.from_str(entity_type_str.upper())
                assert entity_type is not None
            except NotImplementedError:
                pytest.fail(
                    f"Valid entity type {entity_type_str} should not raise NotImplementedError"
                )

    def test_invalid_entity_types(self) -> None:
        """Test that invalid entity types raise NotImplementedError."""
        invalid_types = ["invalid", "unknown", ""]
        for entity_type_str in invalid_types:
            with pytest.raises(NotImplementedError):
                EntityType.from_str(entity_type_str.upper())


class TestRequestValidation:
    """Test cases for request parameter validation."""

    def test_numeric_entity_id_validation(self) -> None:
        """Test numeric entity ID validation."""
        valid_ids = ["123", "456", "0"]
        for entity_id in valid_ids:
            assert entity_id.isnumeric()

    def test_invalid_entity_id_validation(self) -> None:
        """Test invalid entity ID validation."""
        invalid_ids = ["abc", "12.3", "", "-1", "1e2"]
        for entity_id in invalid_ids:
            assert not entity_id.isnumeric()
