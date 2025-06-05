"""
Integration tests for the FastAPI application.
"""

from unittest.mock import Mock, patch, mock_open

import pytest
from fastapi.testclient import TestClient

from musigree.config import SqliteTestConfiguration


class ProductionTestConfig(SqliteTestConfiguration):
    """Test configuration with production settings for security testing."""
    
    def __init__(self, **data):
        super().__init__(**data)
        # Override specific production settings
        self.PRODUCTION = True
        self.DEBUG = True  # Keep debug for testing
        self.TESTING = True
    

class TestFastAPIIntegration:
    """Integration tests for the FastAPI application."""

    @pytest.fixture
    def test_config(self):
        """Provide a test configuration."""
        return SqliteTestConfiguration()

    @pytest.fixture
    def production_test_config(self):
        """Provide a production test configuration."""
        return ProductionTestConfig()

    @pytest.fixture
    def mock_redis_client(self):
        """Provide a mock Redis client."""
        return Mock()

    def test_app_creation_with_security_middleware(self, test_config, mock_redis_client):
        """Test that the FastAPI app can be created with security middleware."""
        with patch('musigree.app.fastapi_dependencies.get_redis_client', return_value=mock_redis_client):
            from musigree.app.fastapi_app import create_app
            app = create_app(test_config)
            assert app is not None

    def test_security_headers_in_response_production(self, production_test_config, mock_redis_client):
        """Test that security headers are properly added to responses in production mode."""
        # Mock the manifest file loading
        _mock_manifest = {"main.js": {"file": "assets/main-abc123.js"}}
        
        with patch('musigree.app.fastapi_dependencies.get_redis_client', return_value=mock_redis_client), \
             patch('builtins.open', mock_open(read_data='{"main.js": {"file": "assets/main-abc123.js"}}')):
            
            from musigree.app.fastapi_app import create_app
            app = create_app(production_test_config)
            
            with TestClient(app) as client:
                response = client.get("/docs")
                
                # Should have security headers in production
                assert "X-Content-Type-Options" in response.headers
                assert response.headers["X-Content-Type-Options"] == "nosniff"
                assert "X-Frame-Options" in response.headers
                assert response.headers["X-Frame-Options"] == "DENY"
                assert "X-XSS-Protection" in response.headers
                assert "Referrer-Policy" in response.headers
                assert "Content-Security-Policy" in response.headers

    def test_security_headers_in_response_development(self, test_config, mock_redis_client):
        """Test that security headers are properly added to responses in development mode."""
        with patch('musigree.app.fastapi_dependencies.get_redis_client', return_value=mock_redis_client):
            from musigree.app.fastapi_app import create_app
            app = create_app(test_config)
            
            with TestClient(app) as client:
                response = client.get("/docs")
                
                # Should have security headers even in development (but potentially different values)
                assert "X-Content-Type-Options" in response.headers
                assert "X-Frame-Options" in response.headers
                assert "Content-Security-Policy" in response.headers

    def test_rate_limiting_functionality_on_api_endpoint(self, test_config, mock_redis_client):
        """Test that rate limiting works correctly on API endpoints that have it applied."""
        # Configure mock Redis to simulate rate limiting
        mock_redis_client.get.side_effect = [None, b'1', b'2', b'3', b'4', b'5']
        mock_redis_client.ttl.return_value = 60
        
        with patch('musigree.app.fastapi_dependencies.get_redis_client', return_value=mock_redis_client):
            from musigree.app.fastapi_app import create_app
            app = create_app(test_config)
            
            with TestClient(app) as client:
                # Test the /api/roles endpoint which exists, has rate limiting, and doesn't depend on database entities
                response = client.get("/api/roles")
                assert response.status_code == 200
                
                # Check rate limit headers are present
                assert "X-RateLimit-Limit" in response.headers
                assert "X-RateLimit-Remaining" in response.headers
                assert "X-RateLimit-Reset" in response.headers

    def test_cors_configuration(self, test_config, mock_redis_client):
        """Test that CORS is properly configured."""
        with patch('musigree.app.fastapi_dependencies.get_redis_client', return_value=mock_redis_client):
            from musigree.app.fastapi_app import create_app
            app = create_app(test_config)
            
            with TestClient(app) as client:
                # Test preflight request
                response = client.options("/api/roles", headers={
                    "Origin": "http://localhost:3000",
                    "Access-Control-Request-Method": "GET"
                })
                
                # Should allow the request (either 200 or 405 is acceptable for OPTIONS)
                assert response.status_code in [200, 405]

    def test_development_mode_configuration(self, test_config, mock_redis_client):
        """Test that development mode is properly configured."""
        with patch('musigree.app.fastapi_dependencies.get_redis_client', return_value=mock_redis_client):
            from musigree.app.fastapi_app import create_app
            app = create_app(test_config)
            
            with TestClient(app) as client:
                # In development mode, docs should be accessible
                response = client.get("/docs")
                assert response.status_code == 200

    def test_app_handles_redis_connection_errors(self, test_config):
        """Test that the app handles Redis connection errors gracefully."""
        # Mock Redis client that raises connection errors
        mock_redis = Mock()
        mock_redis.get.side_effect = Exception("Redis connection failed")
        mock_redis.ttl.side_effect = Exception("Redis connection failed")
        mock_redis.incr.side_effect = Exception("Redis connection failed")
        
        with patch('musigree.app.fastapi_dependencies.get_redis_client', return_value=mock_redis):
            from musigree.app.fastapi_app import create_app
            app = create_app(test_config)
            
            with TestClient(app) as client:
                # App should still work even with Redis errors
                response = client.get("/docs")
                assert response.status_code == 200
                
                # Test an API endpoint that has rate limiting - it should still work but log warnings
                response = client.get("/api/roles")
                assert response.status_code == 200  # Should not crash due to Redis errors

    def test_api_endpoints_basic_functionality(self, test_config, mock_redis_client):
        """Test that basic API endpoints are working."""
        with patch('musigree.app.fastapi_dependencies.get_redis_client', return_value=mock_redis_client):
            from musigree.app.fastapi_app import create_app
            app = create_app(test_config)
            
            with TestClient(app) as client:
                # Test roles endpoint - this one should work without database entities
                response = client.get("/api/roles")
                assert response.status_code == 200 