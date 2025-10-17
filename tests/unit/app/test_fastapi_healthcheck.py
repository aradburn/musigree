"""
Unit tests for musigree.app.fastapi_healthcheck module.
"""

import logging
from typing import Any, Dict
from unittest.mock import patch

import pytest
from fastapi import APIRouter
from fastapi.testclient import TestClient
from pydantic import ValidationError
from starlette import status

from musigree.app.fastapi_healthcheck import HealthCheck, get_health, router


class TestHealthCheck:
    """Test cases for HealthCheck Pydantic model."""

    def test_healthcheck_default_status(self) -> None:
        """Test that HealthCheck model has correct default status."""
        # Act
        health_check = HealthCheck()
        
        # Assert
        assert health_check.status == "OK"

    def test_healthcheck_custom_status(self) -> None:
        """Test that HealthCheck model accepts custom status."""
        # Act
        health_check = HealthCheck(status="HEALTHY")
        
        # Assert
        assert health_check.status == "HEALTHY"

    def test_healthcheck_model_validation(self) -> None:
        """Test that HealthCheck model validates input correctly."""
        # Act & Assert - Valid status
        health_check = HealthCheck(status="OK")
        assert health_check.status == "OK"
        
        # Act & Assert - Empty string status
        health_check = HealthCheck(status="")
        assert health_check.status == ""
        
        # Act & Assert - Numeric string status
        health_check = HealthCheck(status="200")
        assert health_check.status == "200"

    def test_healthcheck_model_serialization(self) -> None:
        """Test that HealthCheck model serializes correctly."""
        # Arrange
        health_check = HealthCheck(status="OK")
        
        # Act
        serialized = health_check.model_dump()
        
        # Assert
        assert serialized == {"status": "OK"}

    def test_healthcheck_model_json_serialization(self) -> None:
        """Test that HealthCheck model serializes to JSON correctly."""
        # Arrange
        health_check = HealthCheck(status="OK")
        
        # Act
        json_str = health_check.model_dump_json()
        
        # Assert
        assert json_str == '{"status":"OK"}'

    def test_healthcheck_model_from_dict(self) -> None:
        """Test creating HealthCheck from dictionary."""
        # Arrange
        data = {"status": "HEALTHY"}
        
        # Act
        health_check = HealthCheck.model_validate(data)
        
        # Assert
        assert health_check.status == "HEALTHY"

    def test_healthcheck_model_invalid_type(self) -> None:
        """Test that HealthCheck model rejects invalid types."""
        # Act & Assert - Non-string status should raise ValidationError
        with pytest.raises(ValidationError):
            HealthCheck(status=200)  # type: ignore[arg-type]
        
        # Act & Assert - None status should raise ValidationError
        with pytest.raises(ValidationError):
            HealthCheck(status=None)  # type: ignore[arg-type]


class TestGetHealth:
    """Test cases for get_health endpoint function."""

    def test_get_health_returns_healthcheck(self) -> None:
        """Test that get_health returns a HealthCheck instance."""
        # Act
        result = get_health()
        
        # Assert
        assert isinstance(result, HealthCheck)
        assert result.status == "OK"

    def test_get_health_returns_correct_status(self) -> None:
        """Test that get_health returns the correct status."""
        # Act
        result = get_health()
        
        # Assert
        assert result.status == "OK"

    def test_get_health_is_pure_function(self) -> None:
        """Test that get_health is a pure function with no side effects."""
        # Act
        result1 = get_health()
        result2 = get_health()
        
        # Assert
        assert result1.status == result2.status
        assert result1.model_dump() == result2.model_dump()

    def test_get_health_with_logging(self) -> None:
        """Test that get_health function works correctly with logging enabled."""
        # Arrange
        with patch('musigree.app.fastapi_healthcheck.log') as mock_log:
            # Act
            result = get_health()
            
            # Assert
            assert result.status == "OK"
            # Note: The function doesn't actually log anything, but we verify it doesn't break

    def test_get_health_docstring_presence(self) -> None:
        """Test that get_health function has proper documentation."""
        # Act & Assert
        assert get_health.__doc__ is not None
        assert "Perform a Health Check" in get_health.__doc__
        assert "Docker" in get_health.__doc__
        assert "HTTP status code" in get_health.__doc__


class TestRouter:
    """Test cases for the APIRouter configuration."""

    def test_router_is_apirouter_instance(self) -> None:
        """Test that router is an instance of APIRouter."""
        # Assert
        assert isinstance(router, APIRouter)

    def test_router_has_health_endpoint(self) -> None:
        """Test that router has the health endpoint configured."""
        # Arrange
        client = TestClient(router)
        
        # Act
        response = client.get("/health")
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"status": "OK"}

    def test_router_health_endpoint_metadata(self) -> None:
        """Test that the health endpoint has correct metadata."""
        # Arrange
        client = TestClient(router)
        
        # Act
        response = client.get("/health")
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == "application/json"

    def test_router_health_endpoint_response_model(self) -> None:
        """Test that the health endpoint returns the correct response model."""
        # Arrange
        client = TestClient(router)
        
        # Act
        response = client.get("/health")
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert "status" in response_data
        assert response_data["status"] == "OK"

    def test_router_health_endpoint_method(self) -> None:
        """Test that the health endpoint only accepts GET requests."""
        # Arrange
        client = TestClient(router)
        
        # Act & Assert - GET should work
        response = client.get("/health")
        assert response.status_code == status.HTTP_200_OK
        
        # Act & Assert - POST should not be allowed
        response = client.post("/health")
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        
        # Act & Assert - PUT should not be allowed
        response = client.put("/health")
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        
        # Act & Assert - DELETE should not be allowed
        response = client.delete("/health")
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_router_health_endpoint_tags(self) -> None:
        """Test that the health endpoint has correct tags for OpenAPI documentation."""
        # Arrange
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        openapi_schema = app.openapi()
        
        # Act & Assert
        assert "paths" in openapi_schema
        assert "/health" in openapi_schema["paths"]
        
        health_endpoint = openapi_schema["paths"]["/health"]["get"]
        assert "tags" in health_endpoint
        assert "healthcheck" in health_endpoint["tags"]

    def test_router_health_endpoint_summary(self) -> None:
        """Test that the health endpoint has correct summary for OpenAPI documentation."""
        # Arrange
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        openapi_schema = app.openapi()
        
        # Act & Assert
        health_endpoint = openapi_schema["paths"]["/health"]["get"]
        assert "summary" in health_endpoint
        assert health_endpoint["summary"] == "Perform a Health Check"

    def test_router_health_endpoint_response_description(self) -> None:
        """Test that the health endpoint has correct response description."""
        # Arrange
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        openapi_schema = app.openapi()
        
        # Act & Assert
        health_endpoint = openapi_schema["paths"]["/health"]["get"]
        assert "responses" in health_endpoint
        assert "200" in health_endpoint["responses"]
        
        response_200 = health_endpoint["responses"]["200"]
        assert "description" in response_200
        assert response_200["description"] == "Return HTTP Status Code 200 (OK)"


class TestIntegration:
    """Integration tests for the healthcheck module."""

    def test_full_healthcheck_flow(self) -> None:
        """Test the complete healthcheck flow from request to response."""
        # Arrange
        client = TestClient(router)
        
        # Act
        response = client.get("/health")
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        
        # Verify response structure
        assert isinstance(response_data, dict)
        assert "status" in response_data
        assert response_data["status"] == "OK"
        
        # Verify response can be parsed back to HealthCheck model
        health_check = HealthCheck.model_validate(response_data)
        assert health_check.status == "OK"

    def test_healthcheck_with_different_clients(self) -> None:
        """Test that healthcheck works with different client configurations."""
        # Arrange
        client1 = TestClient(router)
        client2 = TestClient(router)
        
        # Act
        response1 = client1.get("/health")
        response2 = client2.get("/health")
        
        # Assert
        assert response1.status_code == response2.status_code
        assert response1.json() == response2.json()

    def test_healthcheck_performance(self) -> None:
        """Test that healthcheck endpoint responds quickly."""
        import time
        
        # Arrange
        client = TestClient(router)
        
        # Act
        start_time = time.time()
        response = client.get("/health")
        end_time = time.time()
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert (end_time - start_time) < 0.1  # Should respond in less than 100ms

    def test_healthcheck_concurrent_requests(self) -> None:
        """Test that healthcheck can handle concurrent requests."""
        import threading
        import time
        
        # Arrange
        client = TestClient(router)
        results = []
        
        def make_request() -> None:
            """Make a healthcheck request and store the result."""
            response = client.get("/health")
            results.append(response.status_code)
        
        # Act
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Assert
        assert len(results) == 5
        assert all(response_status == status.HTTP_200_OK for response_status in results)


class TestErrorHandling:
    """Test error handling scenarios."""

    def test_healthcheck_with_invalid_path(self) -> None:
        """Test that invalid paths return 404."""
        # Arrange
        client = TestClient(router)
        
        # Act
        response = client.get("/invalid")
        
        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_healthcheck_with_query_parameters(self) -> None:
        """Test that healthcheck ignores query parameters."""
        # Arrange
        client = TestClient(router)
        
        # Act
        response = client.get("/health?param=value")
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"status": "OK"}

    def test_healthcheck_with_headers(self) -> None:
        """Test that healthcheck works with various headers."""
        # Arrange
        client = TestClient(router)
        headers = {
            "User-Agent": "TestAgent/1.0",
            "Accept": "application/json",
            "X-Custom-Header": "test-value"
        }
        
        # Act
        response = client.get("/health", headers=headers)
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"status": "OK"}
