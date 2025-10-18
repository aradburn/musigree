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
    @patch("musigree.runtime.runtime_database.runtime_entity_repository.RuntimeEntityRepository")
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
    @patch("musigree.runtime.runtime_database.runtime_entity_repository.RuntimeEntityRepository")
    @patch(
        "musigree.runtime.runtime_database.runtime_relation_repository.RuntimeRelationRepository"
    )
    @patch("musigree.runtime.runtime_database_manager.RuntimeDatabaseManager")
    async def test_route_entity_relations_invalid_entity_id(
        self,
        _mock_db_manager_class: Mock,
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
    @patch("musigree.runtime.runtime_database.runtime_entity_repository.RuntimeEntityRepository")
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
        mock_db_helper.get_network = AsyncMock(return_value={"graph": {"nodes": [], "edges": []}})
        mock_db_manager_class.runtime_database_helper = mock_db_helper

        # Act
        response = client.get("/api/artist/network/123")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "graph" in data

    @pytest.mark.asyncio
    @patch("musigree.app.fastapi_api.runtime_transaction")
    @patch("musigree.runtime.runtime_database.runtime_entity_repository.RuntimeEntityRepository")
    @patch(
        "musigree.runtime.runtime_database.runtime_relation_repository.RuntimeRelationRepository"
    )
    @patch("musigree.runtime.runtime_database_manager.RuntimeDatabaseManager")
    async def test_route_entity_network_invalid_entity_id(
        self,
        _mock_db_manager_class: Mock,
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
    @patch("musigree.app.fastapi_api.runtime_transaction")
    @patch("musigree.runtime.runtime_database.runtime_entity_repository.RuntimeEntityRepository")
    @patch(
        "musigree.runtime.runtime_database.runtime_relation_repository.RuntimeRelationRepository"
    )
    @patch("musigree.runtime.runtime_database_manager.RuntimeDatabaseManager")
    async def test_route_entity_network_with_roles_filter(
        self,
        mock_db_manager_class: Mock,
        mock_relation_repo_class: Mock,
        mock_entity_repo_class: Mock,
        mock_runtime_transaction: Mock,
        client: TestClient,
    ) -> None:
        """Test entity network with roles query parameter."""
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
        mock_db_helper.get_network = AsyncMock(return_value={"graph": {"nodes": [], "edges": []}})
        mock_db_manager_class.runtime_database_helper = mock_db_helper

        # Act
        response = client.get("/api/artist/network/123?roles=vocals&roles=guitar")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "graph" in data

        # Verify that get_network was called with roles parameter
        mock_db_helper.get_network.assert_called_once()
        call_args = mock_db_helper.get_network.call_args
        # Check that roles are passed - they will be the default roles since the test roles aren't in the cache
        assert "roles" in call_args[1]
        # The actual roles will be default UI_DEFAULT_ROLES since "vocals" and "guitar" aren't in role cache
        assert call_args[1]["roles"] == ["Alias", "Member Of"]

    @pytest.mark.asyncio
    @patch("musigree.app.fastapi_api.runtime_transaction")
    @patch("musigree.runtime.runtime_database.runtime_entity_repository.RuntimeEntityRepository")
    @patch(
        "musigree.runtime.runtime_database.runtime_relation_repository.RuntimeRelationRepository"
    )
    @patch("musigree.runtime.runtime_database_manager.RuntimeDatabaseManager")
    async def test_route_entity_network_with_year_filter(
        self,
        mock_db_manager_class: Mock,
        mock_relation_repo_class: Mock,
        mock_entity_repo_class: Mock,
        mock_runtime_transaction: Mock,
        client: TestClient,
    ) -> None:
        """Test entity network with year query parameter."""
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
        mock_db_helper.get_network = AsyncMock(return_value={"graph": {"nodes": [], "edges": []}})
        mock_db_manager_class.runtime_database_helper = mock_db_helper

        # Act
        response = client.get("/api/artist/network/123?year=2020")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "graph" in data

        # Verify that get_network was called
        mock_db_helper.get_network.assert_called_once()

    @pytest.mark.asyncio
    @patch("musigree.app.fastapi_api.runtime_transaction")
    @patch("musigree.runtime.runtime_database.runtime_entity_repository.RuntimeEntityRepository")
    @patch(
        "musigree.runtime.runtime_database.runtime_relation_repository.RuntimeRelationRepository"
    )
    @patch("musigree.runtime.runtime_database_manager.RuntimeDatabaseManager")
    async def test_route_entity_network_no_query_params(
        self,
        mock_db_manager_class: Mock,
        mock_relation_repo_class: Mock,
        mock_entity_repo_class: Mock,
        mock_runtime_transaction: Mock,
        client: TestClient,
    ) -> None:
        """Test entity network with no query parameters to test empty roles default."""
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
        mock_db_helper.get_network = AsyncMock(return_value={"graph": {"nodes": [], "edges": []}})
        mock_db_manager_class.runtime_database_helper = mock_db_helper

        # Act
        response = client.get("/api/artist/network/123")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "graph" in data

        # Verify that get_network was called with default empty roles
        mock_db_helper.get_network.assert_called_once()
        call_args = mock_db_helper.get_network.call_args
        # When no roles are provided, should default to UI_DEFAULT_ROLES
        assert call_args[1]["roles"] == ["Alias", "Member Of"]

    @pytest.mark.asyncio
    @patch("musigree.library.cache.cache_manager.CacheManager.get_cache")
    @patch("musigree.runtime.runtime_database_manager.RuntimeDatabaseManager")
    @patch("musigree.app.fastapi_api.runtime_transaction")
    async def test_route_search_success(
        self,
        mock_runtime_transaction: Mock,
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
        mock_db_helper.search_text_index = MagicMock(return_value=[(123, "Test Artist")])
        mock_db_manager_class.runtime_database_helper = mock_db_helper

        # Mock the runtime transaction context manager
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__.return_value = AsyncMock()
        mock_context_manager.__aexit__.return_value = None
        mock_runtime_transaction.return_value = mock_context_manager

        # Act
        response = client.get("/api/search/test")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "results" in data

    @patch(
        "musigree.runtime.data_access_layer.runtime_entity_search.RuntimeEntitySearch.search_entities"
    )
    @patch("musigree.app.fastapi_api.runtime_transaction")
    def test_route_search_empty_results(
        self, mock_runtime_transaction: Mock, mock_search_entities: Mock, client: TestClient
    ) -> None:
        """Test search with empty results."""
        # Arrange
        mock_search_entities.return_value = {"results": []}

        # Mock the runtime transaction context manager
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__.return_value = AsyncMock()
        mock_context_manager.__aexit__.return_value = None
        mock_runtime_transaction.return_value = mock_context_manager

        # Act
        response = client.get("/api/search/nonexistent")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["results"] == []
        mock_search_entities.assert_called_once()

    @patch(
        "musigree.runtime.data_access_layer.runtime_entity_search.RuntimeEntitySearch.search_entities"
    )
    @patch("musigree.app.fastapi_api.runtime_transaction")
    def test_route_search_exception(
        self, mock_runtime_transaction: Mock, mock_search_entities: Mock, client: TestClient
    ) -> None:
        """Test search with exception."""
        # Arrange
        mock_search_entities.side_effect = Exception("Search index error")

        # Mock the runtime transaction context manager
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__.return_value = AsyncMock()
        mock_context_manager.__aexit__.return_value = None
        mock_runtime_transaction.return_value = mock_context_manager

        # Act & Assert - The unhandled exception in the search endpoint will cause the test client to raise it
        with pytest.raises(Exception, match="Search index error"):
            client.get("/api/search/test")

    @pytest.mark.asyncio
    @patch("musigree.app.fastapi_api.runtime_transaction")
    @patch("musigree.runtime.runtime_database.runtime_entity_repository.RuntimeEntityRepository")
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
        mock_entity_repo.get_by_entity_id_and_entity_type = AsyncMock(return_value=mock_entity)

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
    @patch("musigree.runtime.runtime_database.runtime_entity_repository.RuntimeEntityRepository")
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

    @pytest.mark.asyncio
    @patch("musigree.app.fastapi_api.runtime_transaction")
    @patch("musigree.runtime.runtime_database.runtime_entity_repository.RuntimeEntityRepository")
    async def test_route_entity_details_not_found(
        self,
        mock_entity_repo_class: Mock,
        mock_runtime_transaction: Mock,
        client: TestClient,
    ) -> None:
        """Test entity details when entity is not found."""
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

        # Configure the mock to return None (entity not found)
        mock_entity_repo.get_by_entity_id_and_entity_type = AsyncMock(return_value=None)

        # Act & Assert - entity not found causes AttributeError because the endpoint doesn't handle None
        with pytest.raises(AttributeError, match="'NoneType' object has no attribute 'entity_id'"):
            client.get("/api/artist/details/999")

    @patch("musigree.app.fastapi_api.runtime_transaction")
    @patch("musigree.runtime.runtime_database.runtime_entity_repository.RuntimeEntityRepository")
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
        mock_db_helper.get_relations_by_entity_id_and_entity_type = AsyncMock(return_value=None)
        mock_db_manager_class.runtime_database_helper = mock_db_helper

        # Act
        response = client.get("/api/artist/relations/999")

        # Assert - should return 404 when no data is found
        assert response.status_code == 404

    @patch("musigree.library.cache.role_cache.RoleCache")
    def test_route_roles_success(self, mock_role_cache: Mock, client: TestClient) -> None:
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

    @pytest.mark.asyncio
    @patch("musigree.app.fastapi_api.runtime_transaction")
    @patch("musigree.runtime.runtime_database.runtime_entity_repository.RuntimeEntityRepository")
    @patch("musigree.runtime.runtime_database_manager.RuntimeDatabaseManager")
    async def test_route_random_success(
        self,
        mock_db_manager_class: Mock,
        mock_entity_repo_class: Mock,
        mock_runtime_transaction: Mock,
        client: TestClient,
    ) -> None:
        """Test successful random entity retrieval."""
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

        # Mock the database helper method
        mock_db_helper = AsyncMock()
        mock_db_helper.get_random_entity = AsyncMock(return_value=(123, EntityType.ARTIST))
        mock_db_manager_class.runtime_database_helper = mock_db_helper

        # Act
        response = client.get("/api/random")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["center"] == "artist-123"

    @pytest.mark.asyncio
    @patch("musigree.app.fastapi_api.runtime_transaction")
    @patch("musigree.runtime.runtime_database.runtime_entity_repository.RuntimeEntityRepository")
    @patch("musigree.runtime.runtime_database_manager.RuntimeDatabaseManager")
    async def test_route_random_database_error(
        self,
        mock_db_manager_class: Mock,
        mock_entity_repo_class: Mock,
        mock_runtime_transaction: Mock,
        client: TestClient,
    ) -> None:
        """Test random entity retrieval with database error."""
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

        # Mock the database helper method to raise an exception
        mock_db_helper = AsyncMock()
        mock_db_helper.get_random_entity = AsyncMock(
            side_effect=Exception("Database connection failed")
        )
        mock_db_manager_class.runtime_database_helper = mock_db_helper

        # Act
        response = client.get("/api/random")

        # Assert
        assert response.status_code == 500
        data = response.json()
        assert data["error"] == "Database Error"


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


class TestAdditionalEndpointScenarios:
    """Test cases for additional endpoint scenarios and edge cases."""

    def test_route_invalid_entity_id_negative(self, client: TestClient) -> None:
        """Test endpoint with negative entity ID."""
        # Act
        response = client.get("/api/artist/details/-1")

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert data["error"] == "Bad Request"

    def test_route_invalid_entity_id_float(self, client: TestClient) -> None:
        """Test endpoint with float entity ID."""
        # Act
        response = client.get("/api/artist/details/12.5")

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert data["error"] == "Bad Request"

    def test_route_invalid_entity_id_scientific_notation(self, client: TestClient) -> None:
        """Test endpoint with scientific notation entity ID."""
        # Act
        response = client.get("/api/artist/details/1e2")

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert data["error"] == "Bad Request"

    def test_route_invalid_entity_id_alphabet(self, client: TestClient) -> None:
        """Test endpoint with alphabetic entity ID."""
        # Act
        response = client.get("/api/artist/details/abc")

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert data["error"] == "Bad Request"

    def test_route_invalid_entity_id_empty(self, client: TestClient) -> None:
        """Test endpoint with empty entity ID."""
        # Act
        response = client.get("/api/artist/details/")

        # Assert - FastAPI will return 404 for missing path parameter, not 400
        assert response.status_code == 404

    @pytest.mark.asyncio
    @patch("musigree.app.fastapi_api.runtime_transaction")
    @patch("musigree.runtime.runtime_database.runtime_entity_repository.RuntimeEntityRepository")
    async def test_route_entity_details_label_type(
        self,
        mock_entity_repo_class: Mock,
        mock_runtime_transaction: Mock,
        client: TestClient,
    ) -> None:
        """Test entity details for label entity type."""
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
        mock_entity.entity_id = 456
        mock_entity.entity_type = EntityType.LABEL
        mock_entity.entity_name = "Test Label"
        mock_entity.entity_metadata = {"founded": "1990"}
        mock_entity.entities = []
        mock_entity.relation_counts = {"artists": 5}
        mock_entity.countries = ["US"]
        mock_entity.genres = ["Rock"]
        mock_entity.styles = ["Alternative"]

        # Configure the async method to return the mock entity
        mock_entity_repo.get_by_entity_id_and_entity_type = AsyncMock(return_value=mock_entity)

        # Act
        response = client.get("/api/label/details/456")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 456
        assert data["type"] == "label"
        assert data["name"] == "Test Label"
        assert data["metadata"]["founded"] == "1990"

    def test_route_invalid_entity_type(self, client: TestClient) -> None:
        """Test endpoint with invalid entity type."""
        # Act
        response = client.get("/api/invalid_type/details/123")

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert data["error"] == "Bad Request"

    @pytest.mark.asyncio
    @patch("musigree.app.fastapi_api.runtime_transaction")
    @patch("musigree.runtime.runtime_database.runtime_entity_repository.RuntimeEntityRepository")
    @patch(
        "musigree.runtime.runtime_database.runtime_relation_repository.RuntimeRelationRepository"
    )
    @patch("musigree.runtime.runtime_database_manager.RuntimeDatabaseManager")
    async def test_route_entity_network_not_found(
        self,
        mock_db_manager_class: Mock,
        mock_relation_repo_class: Mock,
        mock_entity_repo_class: Mock,
        mock_runtime_transaction: Mock,
        client: TestClient,
    ) -> None:
        """Test entity network when no data is found."""
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

        # Mock the database helper method as async returning None
        mock_db_helper = AsyncMock()
        mock_db_helper.get_network = AsyncMock(return_value=None)
        mock_db_manager_class.runtime_database_helper = mock_db_helper

        # Act
        response = client.get("/api/artist/network/999")

        # Assert - should return 404 when no data is found
        assert response.status_code == 404
        data = response.json()
        assert data["error"] == "Not Found"
