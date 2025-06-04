"""
Unit tests for FastAPI dependencies and rate limiting.
"""

from unittest.mock import Mock, patch

import fakeredis
import pytest
from fastapi import Request, Response

from musigree.app.fastapi_dependencies import (
    get_redis_client,
    rate_limiter
)
from musigree.exceptions import RateLimitError


class TestRedisClient:
    """Test cases for Redis client management."""

    def test_get_redis_client_initialization(self):
        """Test that Redis client is properly initialized."""
        # Reset global client
        global _redis_client
        original_client = _redis_client
        _redis_client = None
        
        try:
            client = get_redis_client()
            assert client is not None
            assert isinstance(client, fakeredis.FakeStrictRedis)
            
            # Subsequent calls should return the same client
            client2 = get_redis_client()
            assert client is client2
        finally:
            # Restore original client
            _redis_client = original_client

    def test_redis_client_configuration(self):
        """Test that Redis client is configured with proper settings."""
        # Reset global client
        global _redis_client
        original_client = _redis_client
        _redis_client = None
        
        try:
            client = get_redis_client()
            
            # Test that the client can perform basic operations
            client.set("test_key", "test_value")
            assert client.get("test_key") == "test_value"
            
            # Test TTL functionality
            client.setex("ttl_test", 60, "value")
            ttl = client.ttl("ttl_test")
            assert ttl > 0
        finally:
            # Restore original client
            _redis_client = original_client


class TestRateLimiter:
    """Test cases for rate limiting functionality."""

    @pytest.fixture
    def mock_request(self):
        """Create a mock FastAPI request."""
        request = Mock(spec=Request)
        request.client = Mock()
        request.client.host = "127.0.0.1"
        request.url = Mock()
        request.url.path = "/api/test"
        return request

    @pytest.fixture
    def mock_response(self):
        """Create a mock FastAPI response."""
        response = Mock(spec=Response)
        response.headers = {}
        return response

    @pytest.fixture
    def fresh_redis_client(self):
        """Provide a fresh Redis client for each test."""
        client = fakeredis.FakeStrictRedis(decode_responses=True)
        with patch('musigree.app.fastapi_dependencies.get_redis_client', return_value=client):
            yield client

    @pytest.mark.asyncio
    async def test_rate_limiter_allows_within_limit(self, mock_request, mock_response, fresh_redis_client):
        """Test that requests within rate limit are allowed."""
        rate_limit_dep = rate_limiter(max_requests=5, period=60)
        
        # First request should be allowed
        await rate_limit_dep(mock_request, mock_response)
        
        # Verify headers were set
        assert mock_response.headers["X-RateLimit-Limit"] == "5"
        assert mock_response.headers["X-RateLimit-Remaining"] == "4"
        assert "X-RateLimit-Reset" in mock_response.headers

    @pytest.mark.asyncio
    async def test_rate_limiter_blocks_over_limit(self, mock_request, mock_response, fresh_redis_client):
        """Test that requests over rate limit are blocked."""
        rate_limit_dep = rate_limiter(max_requests=2, period=60)
        
        # First two requests should be allowed
        await rate_limit_dep(mock_request, mock_response)
        await rate_limit_dep(mock_request, mock_response)
        
        # Third request should be blocked
        with pytest.raises(RateLimitError):
            await rate_limit_dep(mock_request, mock_response)

    @pytest.mark.asyncio
    async def test_rate_limiter_different_clients(self, mock_response, fresh_redis_client):
        """Test that rate limiting is per client IP."""
        rate_limit_dep = rate_limiter(max_requests=1, period=60)
        
        # Create requests from different IPs
        request1 = Mock(spec=Request)
        request1.client = Mock()
        request1.client.host = "127.0.0.1"
        request1.url = Mock()
        request1.url.path = "/api/test"
        
        request2 = Mock(spec=Request)
        request2.client = Mock()
        request2.client.host = "192.168.1.1"
        request2.url = Mock()
        request2.url.path = "/api/test"
        
        # Both should be allowed (different IPs)
        await rate_limit_dep(request1, mock_response)
        await rate_limit_dep(request2, mock_response)
        
        # Second request from first IP should be blocked
        with pytest.raises(RateLimitError):
            await rate_limit_dep(request1, mock_response)

    @pytest.mark.asyncio
    async def test_rate_limiter_different_endpoints(self, mock_response, fresh_redis_client):
        """Test that rate limiting is per endpoint."""
        rate_limit_dep = rate_limiter(max_requests=1, period=60)
        
        # Create requests to different endpoints
        request1 = Mock(spec=Request)
        request1.client = Mock()
        request1.client.host = "127.0.0.1"
        request1.url = Mock()
        request1.url.path = "/api/endpoint1"
        
        request2 = Mock(spec=Request)
        request2.client = Mock()
        request2.client.host = "127.0.0.1"
        request2.url = Mock()
        request2.url.path = "/api/endpoint2"
        
        # Both should be allowed (different endpoints)
        await rate_limit_dep(request1, mock_response)
        await rate_limit_dep(request2, mock_response)

    @pytest.mark.asyncio
    async def test_rate_limiter_handles_no_client(self, mock_response, fresh_redis_client):
        """Test that rate limiter handles requests with no client info."""
        rate_limit_dep = rate_limiter(max_requests=2, period=60)
        
        # Request with no client
        request = Mock(spec=Request)
        request.client = None
        request.url = Mock()
        request.url.path = "/api/test"
        
        # Should not raise an exception
        await rate_limit_dep(request, mock_response)
        
        # Should use "unknown" as client identifier
        assert "X-RateLimit-Limit" in mock_response.headers

    @pytest.mark.asyncio
    async def test_rate_limiter_headers_countdown(self, mock_request, mock_response, fresh_redis_client):
        """Test that rate limit headers properly count down."""
        rate_limit_dep = rate_limiter(max_requests=3, period=60)
        
        # First request
        mock_response.headers = {}
        await rate_limit_dep(mock_request, mock_response)
        assert mock_response.headers["X-RateLimit-Remaining"] == "2"
        
        # Second request
        mock_response.headers = {}
        await rate_limit_dep(mock_request, mock_response)
        assert mock_response.headers["X-RateLimit-Remaining"] == "1"
        
        # Third request
        mock_response.headers = {}
        await rate_limit_dep(mock_request, mock_response)
        assert mock_response.headers["X-RateLimit-Remaining"] == "0"

    @pytest.mark.asyncio
    async def test_rate_limiter_redis_error_handling(self, mock_request, mock_response):
        """Test that rate limiter handles Redis errors gracefully."""
        # Mock a Redis client that raises exceptions
        mock_redis = Mock()
        mock_redis.get.side_effect = Exception("Redis connection error")
        mock_redis.ttl.side_effect = Exception("Redis TTL error")
        mock_redis.incr.side_effect = Exception("Redis incr error")
        mock_redis.expire.side_effect = Exception("Redis expire error")

        with patch('musigree.app.fastapi_dependencies.get_redis_client', return_value=mock_redis):
            with patch('musigree.app.fastapi_dependencies.log') as mock_log:
                rate_limit_dep = rate_limiter(max_requests=5, period=60)

                # Should not raise an exception, should handle gracefully
                await rate_limit_dep(mock_request, mock_response)

                # Verify that warnings were logged for Redis errors
                mock_log.warning.assert_called()
                warning_calls = [call for call in mock_log.warning.call_args_list]
                assert any("Redis error in rate limiter" in str(call) for call in warning_calls)

                # Verify response headers are still set (with fallback values)
                assert "X-RateLimit-Limit" in mock_response.headers
                assert "X-RateLimit-Remaining" in mock_response.headers
                assert "X-RateLimit-Reset" in mock_response.headers
                assert mock_response.headers["X-RateLimit-Limit"] == "5"

    def test_rate_limiter_factory_different_limits(self):
        """Test that rate limiter factory creates different limiters."""
        limiter1 = rate_limiter(max_requests=10, period=60)
        limiter2 = rate_limiter(max_requests=20, period=120)
        
        # Should be different functions
        assert limiter1 != limiter2
        
        # Both should be callable
        assert callable(limiter1)
        assert callable(limiter2) 