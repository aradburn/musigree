"""
Unit tests for musigree.app.fastapi_api module.
"""
from unittest.mock import Mock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.requests import Request
from starlette.responses import JSONResponse

from musigree.app.fastapi_api import router
from musigree.config import SqliteTestConfiguration
from musigree.exceptions import BadRequestError, NotFoundError, DatabaseError
from musigree.library.fields.entity_type import EntityType


# Exception handlers for the test FastAPI app
async def bad_request_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Handle BadRequestError exceptions."""
    return JSONResponse(status_code=400, content={"detail": str(exc)})


async def not_found_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Handle NotFoundError exceptions."""
    return JSONResponse(status_code=404, content={"detail": str(exc)})


async def database_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Handle DatabaseError exceptions."""
    return JSONResponse(status_code=500, content={"detail": str(exc)})


class TestFastAPIRoutes:
    """Test cases for FastAPI route handlers."""

    @pytest.fixture
    def test_config(self):
        """Provide test configuration."""
        return SqliteTestConfiguration()

    @pytest.fixture
    def client(self):
        """Provide FastAPI test client."""
        app = FastAPI()
        app.include_router(router, prefix="/api")
        
        # Add exception handlers
        app.add_exception_handler(BadRequestError, bad_request_handler)
        app.add_exception_handler(NotFoundError, not_found_handler)
        app.add_exception_handler(DatabaseError, database_error_handler)
        
        return TestClient(app)

    @patch('musigree.runtime.runtime_database.runtime_transaction.runtime_transaction')
    @patch('musigree.runtime.runtime_database.runtime_entity_repository.RuntimeEntityRepository')
    @patch('musigree.runtime.runtime_database.runtime_relation_repository.RuntimeRelationRepository')
    @patch('musigree.runtime.runtime_database_manager.RuntimeDatabaseManager')
    def test_route_entity_relations_success(
        self,
        mock_db_manager_class,
        mock_relation_repo_class,
        mock_entity_repo_class,
        mock_transaction,
        client
    ):
        """Test successful entity relations retrieval."""
        # Arrange
        mock_entity_repo = Mock()
        mock_relation_repo = Mock()
        mock_entity_repo_class.return_value = mock_entity_repo
        mock_relation_repo_class.return_value = mock_relation_repo

        # Mock the transaction context manager to yield a mock session
        mock_session = Mock()
        mock_transaction.return_value.__enter__ = Mock(return_value=mock_session)
        mock_transaction.return_value.__exit__ = Mock(return_value=None)

        # Configure get_concurrency_count to return an integer
        mock_db_manager_class.get_concurrency_count.return_value = 1

        expected_data = {"relations": [{"id": 1, "name": "test"}]}
        mock_db_manager_class.runtime_database_helper.get_relations_by_entity_id_and_entity_type.return_value = expected_data

        # Act
        response = client.get("/api/artist/relations/123")
        
        # Assert
        assert response.status_code == 200
        assert response.json() == expected_data
        mock_db_manager_class.runtime_database_helper.get_relations_by_entity_id_and_entity_type.assert_called_once_with(
            mock_entity_repo,
            mock_relation_repo,
            123,
            EntityType.ARTIST
        )

    def test_route_entity_relations_invalid_entity_type(self, client):
        """Test entity relations with invalid entity type."""
        response = client.get("/api/invalid_type/relations/123")
        assert response.status_code == 400

    def test_route_entity_relations_invalid_entity_id(self, client):
        """Test entity relations with invalid entity ID."""
        response = client.get("/api/artist/relations/invalid_id")
        assert response.status_code == 400

    @patch('musigree.runtime.runtime_database.runtime_transaction.runtime_transaction')
    @patch('musigree.runtime.runtime_database.runtime_entity_repository.RuntimeEntityRepository')
    @patch('musigree.runtime.runtime_database.runtime_relation_repository.RuntimeRelationRepository')
    @patch('musigree.runtime.runtime_database_manager.RuntimeDatabaseManager')
    @patch('musigree.utils.parse_request_args')
    def test_route_entity_network_success(
        self,
        mock_parse_args,
        mock_db_manager_class,
        mock_relation_repo_class,
        mock_entity_repo_class,
        mock_transaction,
        client
    ):
        """Test successful entity network retrieval."""
        # Arrange
        mock_entity_repo = Mock()
        mock_relation_repo = Mock()
        mock_entity_repo_class.return_value = mock_entity_repo
        mock_relation_repo_class.return_value = mock_relation_repo

        # Mock the transaction context manager to yield a mock session
        mock_session = Mock()
        mock_transaction.return_value.__enter__ = Mock(return_value=mock_session)
        mock_transaction.return_value.__exit__ = Mock(return_value=None)

        # Configure get_concurrency_count to return an integer
        mock_db_manager_class.get_concurrency_count.return_value = 1

        mock_parse_args.return_value = (["vocals"], 2020)
        expected_data = {"network": {"nodes": [], "edges": []}}
        mock_db_manager_class.runtime_database_helper.get_network.return_value = expected_data

        # Act
        response = client.get("/api/artist/network/123?roles=vocals&year=2020")
        
        # Assert
        assert response.status_code == 200
        assert response.json() == expected_data
        mock_db_manager_class.runtime_database_helper.get_network.assert_called_once_with(
            mock_entity_repo,
            mock_relation_repo,
            123,
            EntityType.ARTIST,
            on_mobile=False,
            roles=["vocals"]
        )

    @patch('musigree.runtime.runtime_database.runtime_transaction.runtime_transaction')
    @patch('musigree.runtime.runtime_database.runtime_entity_repository.RuntimeEntityRepository')
    @patch('musigree.runtime.runtime_database.runtime_relation_repository.RuntimeRelationRepository')
    @patch('musigree.runtime.runtime_database_manager.RuntimeDatabaseManager')
    @patch('musigree.utils.parse_request_args')
    def test_route_entity_network_no_roles(
        self,
        mock_parse_args,
        mock_db_manager_class,
        mock_relation_repo_class,
        mock_entity_repo_class,
        mock_transaction,
        client
    ):
        """Test entity network retrieval with no roles specified."""
        # Arrange
        mock_entity_repo = Mock()
        mock_relation_repo = Mock()
        mock_entity_repo_class.return_value = mock_entity_repo
        mock_relation_repo_class.return_value = mock_relation_repo

        # Mock the transaction context manager to yield a mock session
        mock_session = Mock()
        mock_transaction.return_value.__enter__ = Mock(return_value=mock_session)
        mock_transaction.return_value.__exit__ = Mock(return_value=None)

        # Configure get_concurrency_count to return an integer
        mock_db_manager_class.get_concurrency_count.return_value = 1

        mock_parse_args.return_value = (None, None)
        expected_data = {"network": {"nodes": [], "edges": []}}
        mock_db_manager_class.runtime_database_helper.get_network.return_value = expected_data

        # Act
        response = client.get("/api/artist/network/123")
        
        # Assert
        assert response.status_code == 200
        assert response.json() == expected_data
        mock_db_manager_class.runtime_database_helper.get_network.assert_called_once_with(
            mock_entity_repo,
            mock_relation_repo,
            123,
            EntityType.ARTIST,
            on_mobile=False,
            roles=[]
        )

    def test_route_entity_network_invalid_entity_type(self, client):
        """Test entity network with invalid entity type."""
        response = client.get("/api/invalid_type/network/123")
        assert response.status_code == 400

    def test_route_entity_network_invalid_entity_id(self, client):
        """Test entity network with invalid entity ID."""
        response = client.get("/api/artist/network/invalid_id")
        assert response.status_code == 400

    @patch('musigree.runtime.data_access_layer.runtime_entity_search.RuntimeEntitySearch')
    def test_route_search_success(self, mock_search_class, client):
        """Test successful search."""
        # Arrange
        expected_data = {"results": [{"id": 1, "name": "test artist"}]}
        mock_search_class.search_entities.return_value = expected_data
        
        # Act
        response = client.get("/api/search/test%20query")
        
        # Assert
        assert response.status_code == 200
        assert response.json() == expected_data
        mock_search_class.search_entities.assert_called_once_with("test query")

    @patch('musigree.runtime.runtime_database.runtime_transaction.runtime_transaction')
    @patch('musigree.runtime.runtime_database.runtime_entity_repository.RuntimeEntityRepository')
    @patch('musigree.runtime.runtime_database.runtime_relation_repository.RuntimeRelationRepository')
    @patch('musigree.runtime.runtime_database_manager.RuntimeDatabaseManager')
    def test_route_entity_details_success(
        self,
        mock_db_manager_class,
        mock_relation_repo_class,
        mock_entity_repo_class,
        mock_transaction,
        client
    ):
        """Test successful entity details retrieval."""
        # Arrange
        mock_entity_repo = Mock()
        mock_relation_repo = Mock()
        mock_entity_repo_class.return_value = mock_entity_repo
        mock_relation_repo_class.return_value = mock_relation_repo

        # Mock the transaction context manager to yield a mock session
        mock_session = Mock()
        mock_transaction.return_value.__enter__ = Mock(return_value=mock_session)
        mock_transaction.return_value.__exit__ = Mock(return_value=None)

        # Configure get_concurrency_count to return an integer
        mock_db_manager_class.get_concurrency_count.return_value = 1

        # Mock entity object with required attributes
        mock_entity = Mock()
        mock_entity.entity_id = 123
        mock_entity.entity_type = Mock()
        mock_entity.entity_type.name = "ARTIST"
        mock_entity.entity_name = "Test Artist"
        mock_entity.entity_metadata = {"test": "data"}
        mock_entity.entities = []
        mock_entity.relation_counts = {}
        mock_entity.countries = []
        mock_entity.genres = []
        mock_entity.styles = []

        mock_entity_repo.get_by_entity_id_and_entity_type.return_value = mock_entity

        # Act
        response = client.get("/api/artist/details/123")

        # Assert
        assert response.status_code == 200
        result = response.json()
        assert result["id"] == 123
        assert result["type"] == "artist"
        assert result["name"] == "Test Artist"
        assert result["metadata"] == {"test": "data"}

    def test_route_entity_details_invalid_entity_type(self, client):
        """Test entity details with invalid entity type."""
        response = client.get("/api/invalid_type/details/123")
        assert response.status_code == 400

    def test_route_entity_details_invalid_entity_id(self, client):
        """Test entity details with invalid entity ID."""
        response = client.get("/api/artist/details/invalid_id")
        assert response.status_code == 400

    @patch('musigree.runtime.runtime_database.runtime_transaction.runtime_transaction')
    @patch('musigree.runtime.runtime_database.runtime_entity_repository.RuntimeEntityRepository')
    @patch('musigree.runtime.runtime_database.runtime_relation_repository.RuntimeRelationRepository')
    @patch('musigree.runtime.runtime_database_manager.RuntimeDatabaseManager')
    def test_route_random_success(
        self,
        mock_db_manager_class,
        mock_relation_repo_class,
        mock_entity_repo_class,
        mock_transaction,
        client
    ):
        """Test successful random entity retrieval."""
        # Arrange
        mock_entity_repo = Mock()
        mock_relation_repo = Mock()
        mock_entity_repo_class.return_value = mock_entity_repo
        mock_relation_repo_class.return_value = mock_relation_repo

        # Mock the transaction context manager to yield a mock session
        mock_session = Mock()
        mock_transaction.return_value.__enter__ = Mock(return_value=mock_session)
        mock_transaction.return_value.__exit__ = Mock(return_value=None)

        # Configure get_concurrency_count to return an integer
        mock_db_manager_class.get_concurrency_count.return_value = 1

        # Mock entity type
        mock_entity_type = Mock()
        mock_entity_type.name = "ARTIST"

        # get_random_entity should return a tuple (entity_id, entity_type)
        mock_db_manager_class.runtime_database_helper.get_random_entity.return_value = (456, mock_entity_type)

        # Act
        response = client.get("/api/random")

        # Assert
        assert response.status_code == 200
        result = response.json()
        assert result["center"] == "artist-456"

    @patch('musigree.runtime.runtime_database.runtime_transaction.runtime_transaction')
    @patch('musigree.runtime.runtime_database.runtime_entity_repository.RuntimeEntityRepository')
    @patch('musigree.runtime.runtime_database.runtime_relation_repository.RuntimeRelationRepository')
    @patch('musigree.runtime.runtime_database_manager.RuntimeDatabaseManager')
    def test_route_random_database_error(
        self,
        mock_db_manager_class,
        mock_relation_repo_class,
        mock_entity_repo_class,
        mock_transaction,
        client
    ):
        """Test random entity retrieval with database error."""
        # Arrange
        mock_entity_repo = Mock()
        mock_relation_repo = Mock()
        mock_entity_repo_class.return_value = mock_entity_repo
        mock_relation_repo_class.return_value = mock_relation_repo

        # Mock the transaction context manager to yield a mock session
        mock_session = Mock()
        mock_transaction.return_value.__enter__ = Mock(return_value=mock_session)
        mock_transaction.return_value.__exit__ = Mock(return_value=None)

        # Configure get_concurrency_count to return an integer
        mock_db_manager_class.get_concurrency_count.return_value = 1

        mock_db_manager_class.runtime_database_helper.get_random_entity.side_effect = Exception("Database connection failed")

        # Act
        response = client.get("/api/random")

        # Assert
        assert response.status_code == 500
        assert "API error" in response.json()["detail"]

    @patch('musigree.library.cache.role_cache.RoleCache')
    def test_route_roles_success(self, mock_role_cache, client):
        """Test successful roles retrieval."""
        # Arrange
        expected_data = {"roles": ["vocals", "guitar", "bass"]}
        mock_role_cache.get_all_roles.return_value = expected_data
        
        # Act
        response = client.get("/api/roles")
        
        # Assert
        assert response.status_code == 200
        assert response.json() == expected_data
        mock_role_cache.get_all_roles.assert_called_once()

    @patch('musigree.runtime.runtime_database.runtime_transaction.runtime_transaction')
    @patch('musigree.runtime.runtime_database.runtime_entity_repository.RuntimeEntityRepository')
    @patch('musigree.runtime.runtime_database.runtime_relation_repository.RuntimeRelationRepository')
    @patch('musigree.runtime.runtime_database_manager.RuntimeDatabaseManager')
    def test_route_entity_relations_not_found(
        self,
        mock_db_manager_class,
        mock_relation_repo_class,
        mock_entity_repo_class,
        mock_transaction,
        client
    ):
        """Test entity relations when no data is found."""
        # Arrange
        mock_entity_repo = Mock()
        mock_relation_repo = Mock()
        mock_entity_repo_class.return_value = mock_entity_repo
        mock_relation_repo_class.return_value = mock_relation_repo

        # Mock the transaction context manager to yield a mock session
        mock_session = Mock()
        mock_transaction.return_value.__enter__ = Mock(return_value=mock_session)
        mock_transaction.return_value.__exit__ = Mock(return_value=None)

        # Configure get_concurrency_count to return an integer
        mock_db_manager_class.get_concurrency_count.return_value = 1

        mock_db_manager_class.runtime_database_helper.get_relations_by_entity_id_and_entity_type.return_value = None

        # Act
        response = client.get("/api/artist/relations/123")

        # Assert
        assert response.status_code == 404


class TestEntityTypeValidation:
    """Test cases for entity type validation."""

    def test_valid_entity_types(self):
        """Test that valid entity types are accepted."""
        valid_types = ["artist", "label"]
        for entity_type_str in valid_types:
            try:
                entity_type = EntityType.from_str(entity_type_str.upper())
                assert entity_type is not None
            except NotImplementedError:
                pytest.fail(f"Valid entity type {entity_type_str} should not raise NotImplementedError")

    def test_invalid_entity_types(self):
        """Test that invalid entity types raise NotImplementedError."""
        invalid_types = ["invalid", "unknown", ""]
        for entity_type_str in invalid_types:
            with pytest.raises(NotImplementedError):
                EntityType.from_str(entity_type_str.upper())


class TestRequestValidation:
    """Test cases for request parameter validation."""

    def test_numeric_entity_id_validation(self):
        """Test numeric entity ID validation."""
        valid_ids = ["123", "456", "0"]
        for entity_id in valid_ids:
            assert entity_id.isnumeric()

    def test_invalid_entity_id_validation(self):
        """Test invalid entity ID validation."""
        invalid_ids = ["abc", "12.3", "", "-1", "1e2"]
        for entity_id in invalid_ids:
            assert not entity_id.isnumeric() 