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
from musigree.exceptions import BadRequestError, NotFoundError, DatabaseError, UnprocessableContentError
from musigree.library.fields.entity_type import EntityType


def _async_cache_mock() -> MagicMock:
    """Cache mock with async get/ttl/incr/expire so rate_limiter can await them without warnings."""
    cache = MagicMock()
    cache.get = AsyncMock(return_value=None)
    cache.ttl = AsyncMock(return_value=60)
    cache.incr = AsyncMock()
    cache.expire = AsyncMock()
    cache.hgetall = AsyncMock(return_value=None)
    cache.hset = AsyncMock()
    return cache


# Exception handlers for the test FastAPI app
async def bad_request_handler(_request: Request, _exc: Exception) -> JSONResponse:
    """Mock bad request handler for testing."""
    return JSONResponse(status_code=400, content={"error": "Bad Request"})


async def not_found_handler(_request: Request, _exc: Exception) -> JSONResponse:
    """Mock not found handler for testing."""
    return JSONResponse(status_code=404, content={"error": "Not Found"})


async def unprocessable_content_handler(_request: Request, _exc: Exception) -> JSONResponse:
    """Mock not found handler for testing."""
    return JSONResponse(status_code=422, content={"error": "Unprocessable Content"})


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
    app.add_exception_handler(UnprocessableContentError, unprocessable_content_handler)
    app.add_exception_handler(DatabaseError, database_error_handler)

    return TestClient(app)


class TestFastAPIRoutes:
    """Test cases for FastAPI routes."""

    @pytest.fixture
    def test_config(self) -> Configuration:
        """Provide test configuration."""
        return SqliteTestConfiguration()

    @pytest.mark.asyncio
    @patch("musigree.library.cache.cache_manager.CacheManager.get_cache")
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
        mock_cache_manager: Mock,
        client: TestClient,
    ) -> None:
        """Test successful entity relations retrieval."""
        # Arrange
        # Mock cache - return None for cache miss
        mock_cache = _async_cache_mock()
        mock_cache.hgetall = AsyncMock(return_value=None)  # Force a cache miss
        mock_cache.hset = AsyncMock()
        mock_cache_manager.return_value = mock_cache

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

        # Verify cache was checked
        mock_cache.hgetall.assert_called_once()
        # Verify result was cached
        mock_cache.hset.assert_called_once()

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
    @patch("musigree.library.cache.cache_manager.CacheManager.get_cache")
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
        mock_cache_manager: Mock,
        client: TestClient,
    ) -> None:
        """Test successful entity network retrieval."""
        # Arrange
        # Mock cache - return None for cache miss
        mock_cache = _async_cache_mock()
        mock_cache.hgetall = AsyncMock(return_value=None)  # Force a cache miss
        mock_cache.hset = AsyncMock()
        mock_cache_manager.return_value = mock_cache

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

        # Verify cache was checked
        mock_cache.hgetall.assert_called_once()
        # Verify result was cached
        mock_cache.hset.assert_called_once()

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
    @patch("musigree.library.cache.cache_manager.CacheManager.get_cache")
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
        mock_cache_manager: Mock,
        client: TestClient,
    ) -> None:
        """Test entity network with roles query parameter."""
        # Arrange
        # Mock cache - return None for cache miss
        mock_cache = _async_cache_mock()
        mock_cache.hgetall = AsyncMock(return_value=None)  # Force a cache miss
        mock_cache.hset = AsyncMock()
        mock_cache_manager.return_value = mock_cache

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

        # Verify cache was checked
        mock_cache.hgetall.assert_called_once()
        # Verify result was cached
        mock_cache.hset.assert_called_once()

    @pytest.mark.asyncio
    @patch("musigree.library.cache.cache_manager.CacheManager.get_cache")
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
        mock_cache_manager: Mock,
        client: TestClient,
    ) -> None:
        """Test entity network with year query parameter."""
        # Arrange
        # Mock cache - return None for cache miss
        mock_cache = _async_cache_mock()
        mock_cache.hgetall = AsyncMock(return_value=None)  # Force a cache miss
        mock_cache.hset = AsyncMock()
        mock_cache_manager.return_value = mock_cache

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

        # Verify cache was checked
        mock_cache.hgetall.assert_called_once()
        # Verify result was cached
        mock_cache.hset.assert_called_once()

    @pytest.mark.asyncio
    @patch("musigree.library.cache.cache_manager.CacheManager.get_cache")
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
        mock_cache_manager: Mock,
        client: TestClient,
    ) -> None:
        """Test entity network with no query parameters to test empty roles default."""
        # Arrange
        # Mock cache - return None for cache miss
        mock_cache = _async_cache_mock()
        mock_cache.hgetall = AsyncMock(return_value=None)  # Force a cache miss
        mock_cache.hset = AsyncMock()
        mock_cache_manager.return_value = mock_cache

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

        # Verify cache was checked
        mock_cache.hgetall.assert_called_once()
        # Verify result was cached
        mock_cache.hset.assert_called_once()

    @pytest.mark.asyncio
    @patch("musigree.library.cache.cache_manager.CacheManager.get_cache")
    @patch("musigree.runtime.data_access_layer.runtime_entity_search.RuntimeEntitySearch.search_entities")
    @patch("musigree.app.fastapi_api.runtime_transaction")
    async def test_route_search_success(
        self,
        mock_runtime_transaction: Mock,
        mock_search_entities: Mock,
        mock_cache_manager: Mock,
        client: TestClient,
    ) -> None:
        """Test successful search with cache miss."""
        # Arrange
        # Mock cache - return None for cache miss
        mock_cache = _async_cache_mock()
        mock_cache.hgetall = AsyncMock(return_value=None)  # Force a cache miss
        mock_cache.hset = AsyncMock()
        mock_cache_manager.return_value = mock_cache

        # Mock search results
        expected_results = {"results": ({"key": "artist-123", "name": "Test Artist"},)}
        mock_search_entities.return_value = expected_results

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
        assert len(data["results"]) == 1
        assert data["results"][0]["key"] == "artist-123"
        assert data["results"][0]["name"] == "Test Artist"

        # Verify cache was checked
        mock_cache.hgetall.assert_called_once()
        # Verify search was performed
        mock_search_entities.assert_called_once()
        # Verify result was cached
        mock_cache.hset.assert_called_once()

    @pytest.mark.asyncio
    @patch("musigree.library.cache.cache_manager.CacheManager.get_cache")
    @patch(
        "musigree.runtime.data_access_layer.runtime_entity_search.RuntimeEntitySearch.search_entities"
    )
    @patch("musigree.app.fastapi_api.runtime_transaction")
    async def test_route_search_empty_results(
        self,
        mock_runtime_transaction: Mock,
        mock_search_entities: Mock,
        mock_cache_manager: Mock,
        client: TestClient,
    ) -> None:
        """Test search with empty results."""
        # Arrange
        # Mock cache - return None for cache miss
        mock_cache = _async_cache_mock()
        mock_cache.hgetall = AsyncMock(return_value=None)  # Force a cache miss
        mock_cache.hset = AsyncMock()
        mock_cache_manager.return_value = mock_cache

        mock_search_entities.return_value = {"results": ()}

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
        # Verify result was cached even for empty results
        mock_cache.hset.assert_called_once()

    @pytest.mark.asyncio
    @patch("musigree.library.cache.cache_manager.CacheManager.get_cache")
    @patch(
        "musigree.runtime.data_access_layer.runtime_entity_search.RuntimeEntitySearch.search_entities"
    )
    @patch("musigree.app.fastapi_api.runtime_transaction")
    async def test_route_search_exception(
        self,
        mock_runtime_transaction: Mock,
        mock_search_entities: Mock,
        mock_cache_manager: Mock,
        client: TestClient,
    ) -> None:
        """Test search with exception."""
        # Arrange
        # Mock cache - return None for cache miss
        mock_cache = _async_cache_mock()
        mock_cache.hgetall = AsyncMock(return_value=None)  # Force a cache miss
        mock_cache.hset = AsyncMock()
        mock_cache_manager.return_value = mock_cache

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
    @patch("musigree.library.cache.cache_manager.CacheManager.get_cache")
    @patch(
        "musigree.runtime.data_access_layer.runtime_entity_search.RuntimeEntitySearch.search_entities"
    )
    @patch("musigree.app.fastapi_api.runtime_transaction")
    async def test_route_search_cache_hit(
        self,
        mock_runtime_transaction: Mock,
        mock_search_entities: Mock,
        mock_cache_manager: Mock,
        client: TestClient,
    ) -> None:
        """Test search with cache hit - should return cached result without calling search."""
        # Arrange
        # Mock cache - return cached data for cache hit
        mock_cache = _async_cache_mock()
        cached_data = {"results": ({"key": "artist-123", "name": "Cached Artist"},)}
        mock_cache.hgetall = AsyncMock(return_value=cached_data)
        mock_cache.hset = AsyncMock()
        mock_cache_manager.return_value = mock_cache

        # Mock the runtime transaction context manager (should not be used on cache hit)
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__.return_value = AsyncMock()
        mock_context_manager.__aexit__.return_value = None
        mock_runtime_transaction.return_value = mock_context_manager

        # Act
        response = client.get("/api/search/cached")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert len(data["results"]) == 1
        assert data["results"][0]["key"] == "artist-123"
        assert data["results"][0]["name"] == "Cached Artist"

        # Verify cache was checked
        mock_cache.hgetall.assert_called_once()
        # Verify search was NOT called (cache hit)
        mock_search_entities.assert_not_called()
        # Verify cache was NOT set (already cached)
        mock_cache.hset.assert_not_called()
        # Verify transaction was NOT used (cache hit)
        mock_runtime_transaction.assert_not_called()

    @pytest.mark.asyncio
    @patch("musigree.library.cache.cache_manager.CacheManager.get_cache")
    @patch(
        "musigree.runtime.data_access_layer.runtime_entity_search.RuntimeEntitySearch.search_entities"
    )
    @patch("musigree.app.fastapi_api.runtime_transaction")
    async def test_route_search_cache_miss_and_set(
        self,
        mock_runtime_transaction: Mock,
        mock_search_entities: Mock,
        mock_cache_manager: Mock,
        client: TestClient,
    ) -> None:
        """Test search with cache miss - should perform search and cache the result."""
        # Arrange
        # Mock cache - return None for cache miss
        mock_cache = _async_cache_mock()
        mock_cache.hgetall = AsyncMock(return_value=None)  # Force a cache miss
        mock_cache.hset = AsyncMock()
        mock_cache_manager.return_value = mock_cache

        # Mock search results
        expected_results = {"results": ({"key": "artist-456", "name": "New Artist"},)}
        mock_search_entities.return_value = expected_results

        # Mock the runtime transaction context manager
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__.return_value = AsyncMock()
        mock_context_manager.__aexit__.return_value = None
        mock_runtime_transaction.return_value = mock_context_manager

        # Act
        response = client.get("/api/search/newquery")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert len(data["results"]) == 1
        assert data["results"][0]["key"] == "artist-456"
        assert data["results"][0]["name"] == "New Artist"

        # Verify cache was checked
        mock_cache.hgetall.assert_called_once()
        # Verify search was performed
        mock_search_entities.assert_called_once()
        # Verify result was cached with correct data
        mock_cache.hset.assert_called_once()
        call_args = mock_cache.hset.call_args
        assert call_args[0][1] == expected_results  # Verify the cached data matches

    @pytest.mark.asyncio
    @patch("musigree.library.cache.cache_manager.CacheManager.get_cache")
    @patch("musigree.app.fastapi_api.runtime_transaction")
    @patch("musigree.runtime.runtime_database.runtime_entity_repository.RuntimeEntityRepository")
    async def test_route_entity_details_success(
        self,
        mock_entity_repo_class: Mock,
        mock_runtime_transaction: Mock,
        mock_cache_manager: Mock,
        client: TestClient,
    ) -> None:
        """Test successful entity details retrieval."""
        # Arrange
        # Mock cache - return None for cache miss
        mock_cache = _async_cache_mock()
        mock_cache.hgetall = AsyncMock(return_value=None)  # Force a cache miss
        mock_cache.hset = AsyncMock()
        mock_cache_manager.return_value = mock_cache

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

        # Verify cache was checked
        mock_cache.hgetall.assert_called_once()
        # Verify entity was fetched
        mock_entity_repo.get_by_entity_id_and_entity_type.assert_called_once()
        # Verify result was cached
        mock_cache.hset.assert_called_once()

    @pytest.mark.asyncio
    @patch("musigree.library.cache.cache_manager.CacheManager.get_cache")
    @patch("musigree.app.fastapi_api.runtime_transaction")
    @patch("musigree.runtime.runtime_database.runtime_entity_repository.RuntimeEntityRepository")
    async def test_route_entity_details_cache_hit(
        self,
        mock_entity_repo_class: Mock,
        mock_runtime_transaction: Mock,
        mock_cache_manager: Mock,
        client: TestClient,
    ) -> None:
        """Test entity details with cache hit - should return cached result without calling repository."""
        # Arrange
        # Mock cache - return cached data for cache hit
        mock_cache = _async_cache_mock()
        cached_data = {
            "id": 123,
            "type": "artist",
            "name": "Cached Artist",
            "metadata": {},
            "entities": [],
            "relation_counts": {},
            "countries": [],
            "genres": [],
            "styles": [],
        }
        mock_cache.hgetall = AsyncMock(return_value=cached_data)
        mock_cache.hset = AsyncMock()
        mock_cache_manager.return_value = mock_cache

        # Mock the runtime transaction context manager (should not be used on cache hit)
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__.return_value = AsyncMock()
        mock_context_manager.__aexit__.return_value = None
        mock_runtime_transaction.return_value = mock_context_manager

        # Act
        response = client.get("/api/artist/details/123")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 123
        assert data["type"] == "artist"
        assert data["name"] == "Cached Artist"

        # Verify cache was checked
        mock_cache.hgetall.assert_called_once()
        # Verify repository was NOT called (cache hit)
        mock_entity_repo_class.assert_not_called()
        # Verify cache was NOT set (already cached)
        mock_cache.hset.assert_not_called()
        # Verify transaction was NOT used (cache hit)
        mock_runtime_transaction.assert_not_called()

    @pytest.mark.asyncio
    @patch("musigree.library.cache.cache_manager.CacheManager.get_cache")
    @patch("musigree.app.fastapi_api.runtime_transaction")
    @patch("musigree.runtime.runtime_database.runtime_entity_repository.RuntimeEntityRepository")
    async def test_route_entity_details_cache_miss_and_set(
        self,
        mock_entity_repo_class: Mock,
        mock_runtime_transaction: Mock,
        mock_cache_manager: Mock,
        client: TestClient,
    ) -> None:
        """Test entity details with cache miss - should fetch from repository and cache the result."""
        # Arrange
        # Mock cache - return None for cache miss
        mock_cache = _async_cache_mock()
        mock_cache.hgetall = AsyncMock(return_value=None)  # Force a cache miss
        mock_cache.hset = AsyncMock()
        mock_cache_manager.return_value = mock_cache

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
        mock_entity.entity_type = EntityType.ARTIST
        mock_entity.entity_name = "New Artist"
        mock_entity.entity_metadata = {"formed": "2020"}
        mock_entity.entities = []
        mock_entity.relation_counts = {"albums": 3}
        mock_entity.countries = ["US"]
        mock_entity.genres = ["Rock"]
        mock_entity.styles = ["Alternative"]

        # Configure the async method to return the mock entity
        mock_entity_repo.get_by_entity_id_and_entity_type = AsyncMock(return_value=mock_entity)

        # Act
        response = client.get("/api/artist/details/456")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 456
        assert data["type"] == "artist"
        assert data["name"] == "New Artist"
        assert data["metadata"]["formed"] == "2020"

        # Verify cache was checked
        mock_cache.hgetall.assert_called_once()
        # Verify entity was fetched
        mock_entity_repo.get_by_entity_id_and_entity_type.assert_called_once()
        # Verify result was cached with correct data
        mock_cache.hset.assert_called_once()
        call_args = mock_cache.hset.call_args
        cached_entity_data = call_args[0][1]
        assert cached_entity_data["id"] == 456
        assert cached_entity_data["name"] == "New Artist"

    @pytest.mark.asyncio
    @patch("musigree.library.cache.cache_manager.CacheManager.get_cache")
    @patch("musigree.app.fastapi_api.runtime_transaction")
    @patch("musigree.runtime.runtime_database.runtime_entity_repository.RuntimeEntityRepository")
    async def test_route_entity_details_invalid_entity_id(
        self,
        mock_entity_repo_class: Mock,
        mock_runtime_transaction: Mock,
        mock_cache_manager: Mock,
        client: TestClient,
    ) -> None:
        """Test entity details with invalid entity ID."""
        # Arrange
        # Mock cache
        mock_cache = _async_cache_mock()
        mock_cache_manager.return_value = mock_cache

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
    @patch("musigree.library.cache.cache_manager.CacheManager.get_cache")
    @patch("musigree.app.fastapi_api.runtime_transaction")
    @patch("musigree.runtime.runtime_database.runtime_entity_repository.RuntimeEntityRepository")
    async def test_route_entity_details_not_found(
        self,
        mock_entity_repo_class: Mock,
        mock_runtime_transaction: Mock,
        mock_cache_manager: Mock,
        client: TestClient,
    ) -> None:
        """Test entity details when entity is not found."""
        # Arrange
        # Mock cache - return None for cache miss
        mock_cache = _async_cache_mock()
        mock_cache.hgetall = AsyncMock(return_value=None)  # Force a cache miss
        mock_cache.hset = AsyncMock()
        mock_cache_manager.return_value = mock_cache

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

    @patch("musigree.library.cache.cache_manager.CacheManager.get_cache")
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
        mock_cache_manager: Mock,
        client: TestClient,
    ) -> None:
        """Test entity relations when no data is found."""
        # Arrange
        # Mock cache - return None for cache miss
        mock_cache = _async_cache_mock()
        mock_cache.hgetall = AsyncMock(return_value=None)  # Force a cache miss
        mock_cache.hset = AsyncMock()
        mock_cache_manager.return_value = mock_cache

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

        # Verify cache was checked
        mock_cache.hgetall.assert_called_once()

    @pytest.mark.asyncio
    @patch("musigree.library.cache.cache_manager.CacheManager.get_cache")
    @patch("musigree.app.fastapi_api.runtime_transaction")
    @patch("musigree.runtime.runtime_database.runtime_entity_repository.RuntimeEntityRepository")
    @patch(
        "musigree.runtime.runtime_database.runtime_relation_repository.RuntimeRelationRepository"
    )
    @patch("musigree.runtime.runtime_database_manager.RuntimeDatabaseManager")
    async def test_route_entity_relations_cache_hit(
        self,
        mock_db_manager_class: Mock,
        _mock_relation_repo_class: Mock,
        _mock_entity_repo_class: Mock,
        mock_runtime_transaction: Mock,
        mock_cache_manager: Mock,
        client: TestClient,
    ) -> None:
        """Test entity relations with cache hit - should return cached result without calling database."""
        # Arrange
        # Mock cache - return cached data for cache hit
        mock_cache = _async_cache_mock()
        cached_data = {"relations": [{"id": "1", "type": "artist"}]}
        mock_cache.hgetall = AsyncMock(return_value=cached_data)
        mock_cache.hset = AsyncMock()
        mock_cache_manager.return_value = mock_cache

        # Act
        response = client.get("/api/artist/relations/123")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "relations" in data
        assert len(data["relations"]) == 1
        assert data["relations"][0]["id"] == "1"

        # Verify cache was checked
        mock_cache.hgetall.assert_called_once()
        # Verify database was NOT called (cache hit)
        mock_db_manager_class.assert_not_called()
        # Verify cache was NOT set (already cached)
        mock_cache.hset.assert_not_called()
        # Verify transaction was NOT used (cache hit)
        mock_runtime_transaction.assert_not_called()

    @pytest.mark.asyncio
    @patch("musigree.library.cache.cache_manager.CacheManager.get_cache")
    @patch("musigree.app.fastapi_api.runtime_transaction")
    @patch("musigree.runtime.runtime_database.runtime_entity_repository.RuntimeEntityRepository")
    @patch(
        "musigree.runtime.runtime_database.runtime_relation_repository.RuntimeRelationRepository"
    )
    @patch("musigree.runtime.runtime_database_manager.RuntimeDatabaseManager")
    async def test_route_entity_relations_cache_miss_and_set(
        self,
        mock_db_manager_class: Mock,
        mock_relation_repo_class: Mock,
        mock_entity_repo_class: Mock,
        mock_runtime_transaction: Mock,
        mock_cache_manager: Mock,
        client: TestClient,
    ) -> None:
        """Test entity relations with cache miss - should fetch from database and cache the result."""
        # Arrange
        # Mock cache - return None for cache miss
        mock_cache = _async_cache_mock()
        mock_cache.hgetall = AsyncMock(return_value=None)  # Force a cache miss
        mock_cache.hset = AsyncMock()
        mock_cache_manager.return_value = mock_cache

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
        expected_data = {"relations": [{"id": "2", "type": "label"}]}
        mock_db_helper = AsyncMock()
        mock_db_helper.get_relations_by_entity_id_and_entity_type = AsyncMock(
            return_value=expected_data
        )
        mock_db_manager_class.runtime_database_helper = mock_db_helper

        # Act
        response = client.get("/api/artist/relations/456")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "relations" in data
        assert len(data["relations"]) == 1
        assert data["relations"][0]["id"] == "2"

        # Verify cache was checked
        mock_cache.hgetall.assert_called_once()
        # Verify database was called
        mock_db_helper.get_relations_by_entity_id_and_entity_type.assert_called_once()
        # Verify result was cached with correct data
        mock_cache.hset.assert_called_once()
        call_args = mock_cache.hset.call_args
        assert call_args[0][1] == expected_data  # Verify the cached data matches

    @pytest.mark.asyncio
    @patch("musigree.library.cache.cache_manager.CacheManager.get_cache")
    @patch("musigree.app.fastapi_api.runtime_transaction")
    @patch("musigree.runtime.runtime_database.runtime_entity_repository.RuntimeEntityRepository")
    @patch(
        "musigree.runtime.runtime_database.runtime_relation_repository.RuntimeRelationRepository"
    )
    @patch("musigree.runtime.runtime_database_manager.RuntimeDatabaseManager")
    async def test_route_entity_network_cache_hit(
        self,
        mock_db_manager_class: Mock,
        _mock_relation_repo_class: Mock,
        _mock_entity_repo_class: Mock,
        mock_runtime_transaction: Mock,
        mock_cache_manager: Mock,
        client: TestClient,
    ) -> None:
        """Test entity network with cache hit - should return cached result without calling database."""
        # Arrange
        # Mock cache - return cached data for cache hit
        mock_cache = _async_cache_mock()
        cached_data = {"graph": {"nodes": [{"id": "1"}], "edges": [{"from": "1", "to": "2"}]}}
        mock_cache.hgetall = AsyncMock(return_value=cached_data)
        mock_cache.hset = AsyncMock()
        mock_cache_manager.return_value = mock_cache

        # Act
        response = client.get("/api/artist/network/123")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "graph" in data
        assert "nodes" in data["graph"]
        assert len(data["graph"]["nodes"]) == 1

        # Verify cache was checked
        mock_cache.hgetall.assert_called_once()
        # Verify database was NOT called (cache hit)
        mock_db_manager_class.assert_not_called()
        # Verify cache was NOT set (already cached)
        mock_cache.hset.assert_not_called()
        # Verify transaction was NOT used (cache hit)
        mock_runtime_transaction.assert_not_called()

    @pytest.mark.asyncio
    @patch("musigree.library.cache.cache_manager.CacheManager.get_cache")
    @patch("musigree.app.fastapi_api.runtime_transaction")
    @patch("musigree.runtime.runtime_database.runtime_entity_repository.RuntimeEntityRepository")
    @patch(
        "musigree.runtime.runtime_database.runtime_relation_repository.RuntimeRelationRepository"
    )
    @patch("musigree.runtime.runtime_database_manager.RuntimeDatabaseManager")
    async def test_route_entity_network_cache_miss_and_set(
        self,
        mock_db_manager_class: Mock,
        mock_relation_repo_class: Mock,
        mock_entity_repo_class: Mock,
        mock_runtime_transaction: Mock,
        mock_cache_manager: Mock,
        client: TestClient,
    ) -> None:
        """Test entity network with cache miss - should fetch from database and cache the result."""
        # Arrange
        # Mock cache - return None for cache miss
        mock_cache = _async_cache_mock()
        mock_cache.hgetall = AsyncMock(return_value=None)  # Force a cache miss
        mock_cache.hset = AsyncMock()
        mock_cache_manager.return_value = mock_cache

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
        expected_data = {"graph": {"nodes": [{"id": "2"}], "edges": [{"from": "2", "to": "3"}]}}
        mock_db_helper = AsyncMock()
        mock_db_helper.get_network = AsyncMock(return_value=expected_data)
        mock_db_manager_class.runtime_database_helper = mock_db_helper

        # Act
        response = client.get("/api/artist/network/456")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "graph" in data
        assert "nodes" in data["graph"]
        assert len(data["graph"]["nodes"]) == 1

        # Verify cache was checked
        mock_cache.hgetall.assert_called_once()
        # Verify database was called
        mock_db_helper.get_network.assert_called_once()
        # Verify result was cached with correct data
        mock_cache.hset.assert_called_once()
        call_args = mock_cache.hset.call_args
        assert call_args[0][1] == expected_data  # Verify the cached data matches

    @patch("musigree.library.cache.cache_manager.CacheManager.get_cache")
    @patch("musigree.library.cache.role_cache.RoleCache")
    def test_route_roles_success(
        self, mock_role_cache: Mock, mock_cache_manager: Mock, client: TestClient
    ) -> None:
        """Test successful roles retrieval."""
        # Arrange
        # Mock cache for rate limiter
        mock_cache = _async_cache_mock()
        mock_cache.get = AsyncMock(return_value=None)  # No rate limit hit
        mock_cache.ttl = AsyncMock(return_value=60)
        mock_cache.incr = AsyncMock()
        mock_cache.expire = AsyncMock()
        mock_cache_manager.return_value = mock_cache

        expected_data = {"roles": ["vocals", "guitar", "drums"]}
        mock_role_cache.get_all_roles.return_value = expected_data

        # Act
        response = client.get("/api/roles")

        # Assert
        assert response.status_code == 200
        assert response.json() == expected_data
        mock_role_cache.get_all_roles.assert_called_once()

    @pytest.mark.asyncio
    @patch("musigree.library.cache.cache_manager.CacheManager.get_cache")
    @patch("musigree.app.fastapi_api.runtime_transaction")
    @patch("musigree.runtime.runtime_database.runtime_entity_repository.RuntimeEntityRepository")
    @patch("musigree.runtime.runtime_database_manager.RuntimeDatabaseManager")
    async def test_route_random_success(
        self,
        mock_db_manager_class: Mock,
        mock_entity_repo_class: Mock,
        mock_runtime_transaction: Mock,
        mock_cache_manager: Mock,
        client: TestClient,
    ) -> None:
        """Test successful random entity retrieval."""
        # Arrange
        # Mock cache for rate limiter
        mock_cache = _async_cache_mock()
        mock_cache.get = AsyncMock(return_value=None)  # No rate limit hit
        mock_cache.ttl = AsyncMock(return_value=60)
        mock_cache.incr = AsyncMock()
        mock_cache.expire = AsyncMock()
        mock_cache_manager.return_value = mock_cache

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
    @patch("musigree.library.cache.cache_manager.CacheManager.get_cache")
    @patch("musigree.app.fastapi_api.runtime_transaction")
    @patch("musigree.runtime.runtime_database.runtime_entity_repository.RuntimeEntityRepository")
    @patch("musigree.runtime.runtime_database_manager.RuntimeDatabaseManager")
    async def test_route_random_database_error(
        self,
        mock_db_manager_class: Mock,
        mock_entity_repo_class: Mock,
        mock_runtime_transaction: Mock,
        mock_cache_manager: Mock,
        client: TestClient,
    ) -> None:
        """Test random entity retrieval with database error."""
        # Arrange
        # Mock cache for rate limiter
        mock_cache = _async_cache_mock()
        mock_cache.get = AsyncMock(return_value=None)  # No rate limit hit
        mock_cache.ttl = AsyncMock(return_value=60)
        mock_cache.incr = AsyncMock()
        mock_cache.expire = AsyncMock()
        mock_cache_manager.return_value = mock_cache

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
    @patch("musigree.library.cache.cache_manager.CacheManager.get_cache")
    @patch("musigree.app.fastapi_api.runtime_transaction")
    @patch("musigree.runtime.runtime_database.runtime_entity_repository.RuntimeEntityRepository")
    async def test_route_entity_details_label_type(
        self,
        mock_entity_repo_class: Mock,
        mock_runtime_transaction: Mock,
        mock_cache_manager: Mock,
        client: TestClient,
    ) -> None:
        """Test entity details for label entity type."""
        # Arrange
        # Mock cache - return None for cache miss
        mock_cache = _async_cache_mock()
        mock_cache.hgetall = AsyncMock(return_value=None)  # Force a cache miss
        mock_cache.hset = AsyncMock()
        mock_cache_manager.return_value = mock_cache

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

        # Verify cache was checked
        mock_cache.hgetall.assert_called_once()
        # Verify entity was fetched
        mock_entity_repo.get_by_entity_id_and_entity_type.assert_called_once()
        # Verify result was cached
        mock_cache.hset.assert_called_once()

    def test_route_invalid_entity_type(self, client: TestClient) -> None:
        """Test endpoint with invalid entity type."""
        # Act
        response = client.get("/api/invalid_type/details/123")

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert data["error"] == "Bad Request"

    @pytest.mark.asyncio
    @patch("musigree.library.cache.cache_manager.CacheManager.get_cache")
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
        mock_cache_manager: Mock,
        client: TestClient,
    ) -> None:
        """Test entity network when no data is found."""
        # Arrange
        # Mock cache - return None for cache miss
        mock_cache = _async_cache_mock()
        mock_cache.hgetall = AsyncMock(return_value=None)  # Force a cache miss
        mock_cache.hset = AsyncMock()
        mock_cache_manager.return_value = mock_cache

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

        # Verify cache was checked
        mock_cache.hgetall.assert_called_once()

    @pytest.mark.asyncio
    @patch("musigree.library.cache.cache_manager.CacheManager.get_cache")
    @patch("musigree.app.fastapi_api.runtime_transaction")
    @patch("musigree.runtime.runtime_database.runtime_entity_repository.RuntimeEntityRepository")
    async def test_route_entity_details_cache_empty_dict(
        self,
        mock_entity_repo_class: Mock,
        mock_runtime_transaction: Mock,
        mock_cache_manager: Mock,
        client: TestClient,
    ) -> None:
        """Test entity details with cache returning empty dict - should be treated as cache hit."""
        # Arrange
        # Mock cache - return empty dict (edge case - should be treated as cache hit)
        mock_cache = _async_cache_mock()
        mock_cache.hgetall = AsyncMock(return_value={})  # Empty dict, not None
        mock_cache.hset = AsyncMock()
        mock_cache_manager.return_value = mock_cache

        # Act
        response = client.get("/api/artist/details/123")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data == {}  # Empty dict from cache

        # Verify cache was checked
        mock_cache.hgetall.assert_called_once()
        # Verify repository was NOT called (empty dict is treated as cache hit)
        mock_entity_repo_class.assert_not_called()
        # Verify cache was NOT set (already cached, even if empty)
        mock_cache.hset.assert_not_called()
        # Verify transaction was NOT used (cache hit)
        mock_runtime_transaction.assert_not_called()

    @pytest.mark.asyncio
    @patch("musigree.library.cache.cache_manager.CacheManager.get_cache")
    @patch("musigree.app.fastapi_api.runtime_transaction")
    @patch("musigree.runtime.runtime_database.runtime_entity_repository.RuntimeEntityRepository")
    @patch(
        "musigree.runtime.runtime_database.runtime_relation_repository.RuntimeRelationRepository"
    )
    @patch("musigree.runtime.runtime_database_manager.RuntimeDatabaseManager")
    async def test_route_entity_relations_cache_key_format(
        self,
        mock_db_manager_class: Mock,
        mock_relation_repo_class: Mock,
        mock_entity_repo_class: Mock,
        mock_runtime_transaction: Mock,
        mock_cache_manager: Mock,
        client: TestClient,
    ) -> None:
        """Test that cache key is constructed correctly for entity relations."""
        # Arrange
        # Mock cache - return None for cache miss
        mock_cache = _async_cache_mock()
        mock_cache.hgetall = AsyncMock(return_value=None)  # Force a cache miss
        mock_cache.hset = AsyncMock()
        mock_cache_manager.return_value = mock_cache

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
        response = client.get("/api/artist/relations/789")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "relations" in data

        # Verify cache was checked with correct key format
        mock_cache.hgetall.assert_called_once()
        cache_key = mock_cache.hgetall.call_args[0][0]
        assert "api" in cache_key
        assert "artist" in cache_key
        assert "relations" in cache_key
        assert "789" in cache_key

        # Verify result was cached
        mock_cache.hset.assert_called_once()
        # Verify cache key used for setting matches the one used for getting
        set_cache_key = mock_cache.hset.call_args[0][0]
        assert set_cache_key == cache_key

    @pytest.mark.asyncio
    @patch("musigree.library.cache.cache_manager.CacheManager.get_cache")
    @patch("musigree.app.fastapi_api.runtime_transaction")
    @patch("musigree.runtime.runtime_database.runtime_entity_repository.RuntimeEntityRepository")
    @patch(
        "musigree.runtime.runtime_database.runtime_relation_repository.RuntimeRelationRepository"
    )
    @patch("musigree.runtime.runtime_database_manager.RuntimeDatabaseManager")
    async def test_route_entity_network_cache_key_includes_entity_type_and_id(
        self,
        mock_db_manager_class: Mock,
        mock_relation_repo_class: Mock,
        mock_entity_repo_class: Mock,
        mock_runtime_transaction: Mock,
        mock_cache_manager: Mock,
        client: TestClient,
    ) -> None:
        """Test that cache key includes entity type and ID for network endpoint."""
        # Arrange
        # Mock cache - return None for cache miss
        mock_cache = _async_cache_mock()
        mock_cache.hgetall = AsyncMock(return_value=None)  # Force a cache miss
        mock_cache.hset = AsyncMock()
        mock_cache_manager.return_value = mock_cache

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
        response = client.get("/api/label/network/999")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "graph" in data

        # Verify cache was checked with correct key format including entity type
        mock_cache.hgetall.assert_called_once()
        cache_key = mock_cache.hgetall.call_args[0][0]
        assert "api" in cache_key
        assert "label" in cache_key  # Entity type should be in key
        assert "network" in cache_key
        assert "999" in cache_key  # Entity ID should be in key
