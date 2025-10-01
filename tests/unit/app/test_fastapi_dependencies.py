"""
Unit tests for the musigree.app.fastapi_dependencies module.

This module contains comprehensive tests for the utility functions and dependencies
defined in fastapi_dependencies.py, including entity type parsing, entity ID validation,
year range parsing, role filtering, Redis client management, and rate limiting functionality.
"""

import time
import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi import Request, Response

from musigree.app.fastapi_dependencies import (
    get_entity_type,
    get_entity_id,
    get_year,
    get_roles,
    get_redis_client,
    rate_limiter,
    UI_DEFAULT_ROLES,
)
from musigree.exceptions import BadRequestError, RateLimitError
from musigree.library.fields.entity_type import EntityType


class TestGetEntityType:
    """Test cases for the get_entity_type function."""

    def test_get_entity_type_valid_artist(self) -> None:
        """Test that valid entity type string returns correct EntityType."""
        result = get_entity_type("artist")
        assert result == EntityType.ARTIST

    def test_get_entity_type_valid_label(self) -> None:
        """Test that valid entity type string returns correct EntityType."""
        result = get_entity_type("label")
        assert result == EntityType.LABEL

    def test_get_entity_type_case_insensitive(self) -> None:
        """Test that entity type parsing is case insensitive."""
        result = get_entity_type("ArTiSt")
        assert result == EntityType.ARTIST

    def test_get_entity_type_invalid_raises_bad_request(self) -> None:
        """Test that invalid entity type raises BadRequestError."""
        with pytest.raises(BadRequestError) as exc_info:
            get_entity_type("invalid_type")
        assert exc_info.value.message == "Bad Entity Type"


class TestGetEntityId:
    """Test cases for the get_entity_id function."""

    def test_get_entity_id_valid_numeric_string(self) -> None:
        """Test that valid numeric string returns correct integer."""
        result = get_entity_id("12345")
        assert result == 12345

    def test_get_entity_id_zero(self) -> None:
        """Test that zero string returns zero integer."""
        result = get_entity_id("0")
        assert result == 0

    def test_get_entity_id_non_numeric_raises_bad_request(self) -> None:
        """Test that non-numeric string raises BadRequestError."""
        with pytest.raises(BadRequestError) as exc_info:
            get_entity_id("abc123")
        assert exc_info.value.message == "Bad Entity Id"

    def test_get_entity_id_empty_string_raises_bad_request(self) -> None:
        """Test that empty string raises BadRequestError."""
        with pytest.raises(BadRequestError) as exc_info:
            get_entity_id("")
        assert exc_info.value.message == "Bad Entity Id"

    def test_get_entity_id_negative_string_raises_bad_request(self) -> None:
        """Test that negative number string raises BadRequestError."""
        with pytest.raises(BadRequestError) as exc_info:
            get_entity_id("-123")
        assert exc_info.value.message == "Bad Entity Id"


class TestGetYear:
    """Test cases for the get_year function."""

    def test_get_year_none_returns_none(self) -> None:
        """Test that None input returns None."""
        result = get_year(None)
        assert result is None

    def test_get_year_single_year(self) -> None:
        """Test that single year string returns integer."""
        result = get_year("2023")
        assert result == 2023

    def test_get_year_range_ascending(self) -> None:
        """Test that year range returns tuple with start <= stop."""
        result = get_year("2020-2023")
        assert result == (2020, 2023)

    def test_get_year_range_descending_swapped(self) -> None:
        """Test that descending year range gets swapped to ascending order."""
        result = get_year("2023-2020")
        assert result == (2020, 2023)

    def test_get_year_same_year_range(self) -> None:
        """Test that same year range returns tuple."""
        result = get_year("2022-2022")
        assert result == (2022, 2022)

    def test_get_year_invalid_format_raises_bad_request(self) -> None:
        """Test that invalid year format raises BadRequestError."""
        with pytest.raises(BadRequestError) as exc_info:
            get_year("invalid")
        assert exc_info.value.message == "Invalid year input"

    def test_get_year_invalid_range_format_raises_bad_request(self) -> None:
        """Test that invalid year range format raises BadRequestError."""
        with pytest.raises(BadRequestError) as exc_info:
            get_year("2020-invalid")
        assert exc_info.value.message == "Invalid year input"

    def test_get_year_multiple_dashes_raises_bad_request(self) -> None:
        """Test that multiple dashes raises BadRequestError due to invalid second part."""
        with pytest.raises(BadRequestError) as exc_info:
            get_year("2020-2021-2022")
        assert exc_info.value.message == "Invalid year input"


class TestGetRoles:
    """Test cases for the get_roles function."""

    @patch('musigree.library.cache.role_cache.RoleCache')
    def test_get_roles_none_returns_default(self, mock_role_cache: Mock) -> None:
        """Test that None input returns default roles."""
        mock_role_cache.role_category_to_role_name_lookup = {}
        mock_role_cache.role_name_to_role_id_lookup = {}
        
        result = get_roles(None)
        assert result == sorted(UI_DEFAULT_ROLES)

    @patch('musigree.library.cache.role_cache.RoleCache')
    def test_get_roles_empty_string_returns_default(self, mock_role_cache: Mock) -> None:
        """Test that empty string returns default roles."""
        mock_role_cache.role_category_to_role_name_lookup = {}
        mock_role_cache.role_name_to_role_id_lookup = {}
        
        result = get_roles("")
        assert result == sorted(UI_DEFAULT_ROLES)

    @patch('musigree.library.cache.role_cache.RoleCache')
    def test_get_roles_direct_role_name_lookup(self, mock_role_cache: Mock) -> None:
        """Test that direct role name is found in lookup."""
        mock_role_cache.role_category_to_role_name_lookup = {}
        mock_role_cache.role_name_to_role_id_lookup = {"Producer": 1}
        
        result = get_roles("Producer")
        assert result == ["Producer"]

    @patch('musigree.library.cache.role_cache.RoleCache')
    def test_get_roles_category_lookup_with_valid_entries(self, mock_role_cache: Mock) -> None:
        """Test that role category lookup works with valid role entries."""
        mock_role_cache.role_category_to_role_name_lookup = {
            "Production": ["Producer", "Co-Producer"]
        }
        mock_role_cache.role_name_to_role_id_lookup = {
            "Producer": 1,
            "Co-Producer": 2
        }
        
        result = get_roles("Production")
        assert sorted(result) == ["Co-Producer", "Producer"]

    @patch('musigree.library.cache.role_cache.RoleCache')
    def test_get_roles_category_lookup_with_invalid_entries(self, mock_role_cache: Mock) -> None:
        """Test that role category lookup skips invalid role entries."""
        mock_role_cache.role_category_to_role_name_lookup = {
            "Production": ["Producer", "InvalidRole"]
        }
        mock_role_cache.role_name_to_role_id_lookup = {
            "Producer": 1
            # InvalidRole is not in role_name_to_role_id_lookup
        }
        
        result = get_roles("Production")
        assert result == ["Producer"]

    @patch('musigree.library.cache.role_cache.RoleCache')
    def test_get_roles_comma_separated_roles(self, mock_role_cache: Mock) -> None:
        """Test that comma-separated roles are properly parsed."""
        mock_role_cache.role_category_to_role_name_lookup = {}
        mock_role_cache.role_name_to_role_id_lookup = {
            "Producer": 1,
            "Director": 2
        }
        
        result = get_roles("Producer,Director")
        assert sorted(result) == ["Director", "Producer"]

    @patch('musigree.library.cache.role_cache.RoleCache')
    def test_get_roles_escaped_commas(self, mock_role_cache: Mock) -> None:
        """Test that escaped commas in role names are handled correctly."""
        mock_role_cache.role_category_to_role_name_lookup = {}
        mock_role_cache.role_name_to_role_id_lookup = {
            "A&R, Producer": 1,
            "Director": 2
        }
        
        result = get_roles("A&R\\, Producer,Director")
        assert sorted(result) == ["A&R, Producer", "Director"]

    @patch('musigree.library.cache.role_cache.RoleCache')
    def test_get_roles_not_found_returns_default(self, mock_role_cache: Mock) -> None:
        """Test that roles not found in lookup return default roles."""
        mock_role_cache.role_category_to_role_name_lookup = {}
        mock_role_cache.role_name_to_role_id_lookup = {}
        
        result = get_roles("NonExistentRole")
        assert result == sorted(UI_DEFAULT_ROLES)


class TestGetRedisClient:
    """Test cases for the get_redis_client function."""

    @patch('musigree.app.fastapi_dependencies._redis_client', None)
    def test_get_redis_client_initializes_fake_redis(self) -> None:
        """Test that get_redis_client initializes FakeRedis client."""
        with patch('musigree.app.fastapi_dependencies.fakeredis.FakeStrictRedis') as mock_redis:
            mock_instance = MagicMock()
            mock_redis.return_value = mock_instance
            
            result = get_redis_client()
            
            mock_redis.assert_called_once_with(
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
            )
            assert result == mock_instance

    @patch('musigree.app.fastapi_dependencies._redis_client', None)
    def test_get_redis_client_reuses_existing_client(self) -> None:
        """Test that get_redis_client reuses existing client."""
        with patch('musigree.app.fastapi_dependencies.fakeredis.FakeStrictRedis') as mock_redis:
            mock_instance = MagicMock()
            mock_redis.return_value = mock_instance
            
            # First call initializes
            client1 = get_redis_client()
            # Second call should reuse
            client2 = get_redis_client()
            
            assert client1 == client2
            assert mock_redis.call_count == 1


class TestRateLimiter:
    """Test cases for the rate_limiter function."""

    @pytest.fixture
    def mock_request(self) -> Mock:
        """Create a mock FastAPI Request object."""
        request = Mock(spec=Request)
        request.url.path = "/test/endpoint"
        request.client = Mock()
        request.client.host = "127.0.0.1"
        return request

    @pytest.fixture
    def mock_response(self) -> Mock:
        """Create a mock FastAPI Response object."""
        response = Mock(spec=Response)
        response.headers = {}
        return response

    @patch('musigree.app.fastapi_dependencies.get_redis_client')
    @pytest.mark.asyncio
    async def test_rate_limiter_allows_request_within_limit(
        self, 
        mock_get_redis: Mock,
        mock_request: Mock,
        mock_response: Mock
    ) -> None:
        """Test that rate limiter allows request within limit."""
        mock_redis = MagicMock()
        mock_redis.get.return_value = "5"  # Current requests
        mock_redis.ttl.return_value = 30
        mock_get_redis.return_value = mock_redis

        limiter = rate_limiter(max_requests=10, period=60)
        
        # Should not raise an exception
        await limiter(mock_request, mock_response)
        
        # Verify Redis operations
        mock_redis.get.assert_called_once()
        mock_redis.incr.assert_called_once()
        mock_redis.expire.assert_not_called()  # Not called since current_requests > 0
        
        # Verify response headers
        assert mock_response.headers["X-RateLimit-Limit"] == "10"
        assert mock_response.headers["X-RateLimit-Remaining"] == "4"  # 10 - 5 - 1
        assert "X-RateLimit-Reset" in mock_response.headers

    @patch('musigree.app.fastapi_dependencies.get_redis_client')
    @pytest.mark.asyncio
    async def test_rate_limiter_raises_error_when_limit_exceeded(
        self, 
        mock_get_redis: Mock,
        mock_request: Mock,
        mock_response: Mock
    ) -> None:
        """Test that rate limiter raises RateLimitError when limit exceeded."""
        mock_redis = MagicMock()
        mock_redis.get.return_value = "10"  # Current requests equal to limit
        mock_redis.ttl.return_value = 30
        mock_get_redis.return_value = mock_redis

        limiter = rate_limiter(max_requests=10, period=60)
        
        with pytest.raises(RateLimitError):
            await limiter(mock_request, mock_response)
        
        # Should not increment when limit exceeded
        mock_redis.incr.assert_not_called()

    @patch('musigree.app.fastapi_dependencies.get_redis_client')
    @pytest.mark.asyncio
    async def test_rate_limiter_handles_none_redis_value(
        self, 
        mock_get_redis: Mock,
        mock_request: Mock,
        mock_response: Mock
    ) -> None:
        """Test that rate limiter handles None value from Redis."""
        mock_redis = MagicMock()
        mock_redis.get.return_value = None
        mock_redis.ttl.return_value = 60
        mock_get_redis.return_value = mock_redis

        limiter = rate_limiter(max_requests=10, period=60)
        
        await limiter(mock_request, mock_response)
        
        # Should set expiration for new key
        mock_redis.expire.assert_called_once_with(
            "ratelimit:/test/endpoint:127.0.0.1", 60
        )
        assert mock_response.headers["X-RateLimit-Remaining"] == "9"  # 10 - 0 - 1

    @patch('musigree.app.fastapi_dependencies.get_redis_client')
    @pytest.mark.asyncio
    async def test_rate_limiter_handles_bytes_redis_value(
        self, 
        mock_get_redis: Mock,
        mock_request: Mock,
        mock_response: Mock
    ) -> None:
        """Test that rate limiter handles bytes value from Redis."""
        mock_redis = MagicMock()
        mock_redis.get.return_value = b"3"  # Bytes value
        mock_redis.ttl.return_value = 45
        mock_get_redis.return_value = mock_redis

        limiter = rate_limiter(max_requests=10, period=60)
        
        await limiter(mock_request, mock_response)
        
        assert mock_response.headers["X-RateLimit-Remaining"] == "6"  # 10 - 3 - 1

    @patch('musigree.app.fastapi_dependencies.get_redis_client')
    @pytest.mark.asyncio
    async def test_rate_limiter_handles_invalid_redis_value_types(
        self, 
        mock_get_redis: Mock,
        mock_request: Mock,
        mock_response: Mock
    ) -> None:
        """Test that rate limiter handles invalid Redis value types gracefully."""
        mock_redis = MagicMock()
        # Simulate a value that can't be converted to int
        mock_redis.get.return_value = "invalid_number"
        mock_redis.ttl.return_value = 60
        mock_get_redis.return_value = mock_redis

        limiter = rate_limiter(max_requests=10, period=60)
        
        await limiter(mock_request, mock_response)
        
        # Should default to 0 current requests
        assert mock_response.headers["X-RateLimit-Remaining"] == "9"  # 10 - 0 - 1

    @patch('musigree.app.fastapi_dependencies.get_redis_client')
    @pytest.mark.asyncio
    async def test_rate_limiter_handles_redis_get_exception(
        self, 
        mock_get_redis: Mock,
        mock_request: Mock,
        mock_response: Mock
    ) -> None:
        """Test that rate limiter handles Redis get exception gracefully."""
        mock_redis = MagicMock()
        mock_redis.get.side_effect = Exception("Redis connection error")
        mock_redis.ttl.return_value = 60
        mock_get_redis.return_value = mock_redis

        limiter = rate_limiter(max_requests=10, period=60)
        
        # Should not raise exception, fallback to allowing request
        await limiter(mock_request, mock_response)
        
        assert mock_response.headers["X-RateLimit-Remaining"] == "9"  # Fallback values

    @patch('musigree.app.fastapi_dependencies.get_redis_client')
    @pytest.mark.asyncio
    async def test_rate_limiter_handles_redis_ttl_exception(
        self, 
        mock_get_redis: Mock,
        mock_request: Mock,
        mock_response: Mock
    ) -> None:
        """Test that rate limiter handles Redis TTL exception gracefully."""
        mock_redis = MagicMock()
        mock_redis.get.return_value = "1"
        mock_redis.ttl.side_effect = Exception("Redis TTL error")
        mock_get_redis.return_value = mock_redis

        limiter = rate_limiter(max_requests=10, period=60)
        
        await limiter(mock_request, mock_response)
        
        # Should use period as fallback TTL
        reset_time = int(mock_response.headers["X-RateLimit-Reset"])
        expected_reset = int(time.time()) + 60
        assert abs(reset_time - expected_reset) <= 1  # Allow 1 second tolerance

    @patch('musigree.app.fastapi_dependencies.get_redis_client')
    @pytest.mark.asyncio
    async def test_rate_limiter_handles_redis_incr_exception(
        self, 
        mock_get_redis: Mock,
        mock_request: Mock,
        mock_response: Mock
    ) -> None:
        """Test that rate limiter handles Redis incr exception gracefully."""
        mock_redis = MagicMock()
        mock_redis.get.return_value = "1"
        mock_redis.ttl.return_value = 30
        mock_redis.incr.side_effect = Exception("Redis incr error")
        mock_get_redis.return_value = mock_redis

        limiter = rate_limiter(max_requests=10, period=60)
        
        # Should not raise exception, continue with graceful degradation
        await limiter(mock_request, mock_response)
        
        assert mock_response.headers["X-RateLimit-Remaining"] == "8"  # 10 - 1 - 1

    @pytest.mark.asyncio
    async def test_rate_limiter_handles_missing_client_info(
        self,
        mock_response: Mock
    ) -> None:
        """Test that rate limiter handles missing client information."""
        # Create request without client
        mock_request = Mock(spec=Request)
        mock_request.url.path = "/test/endpoint"
        mock_request.client = None

        with patch('musigree.app.fastapi_dependencies.get_redis_client') as mock_get_redis:
            mock_redis = MagicMock()
            mock_redis.get.return_value = None
            mock_redis.ttl.return_value = 60
            mock_get_redis.return_value = mock_redis

            limiter = rate_limiter(max_requests=10, period=60)
            
            await limiter(mock_request, mock_response)
            
            # Should use "unknown" as client host
            expected_key = "ratelimit:/test/endpoint:unknown"
            mock_redis.get.assert_called_with(expected_key)

    @pytest.mark.asyncio
    async def test_rate_limiter_handles_client_without_host(
        self,
        mock_response: Mock
    ) -> None:
        """Test that rate limiter handles client without host attribute."""
        # Create request with client but no host attribute
        mock_request = Mock(spec=Request)
        mock_request.url.path = "/test/endpoint"
        mock_request.client = Mock()
        # Simulate client without host attribute
        del mock_request.client.host

        with patch('musigree.app.fastapi_dependencies.get_redis_client') as mock_get_redis:
            mock_redis = MagicMock()
            mock_redis.get.return_value = None
            mock_redis.ttl.return_value = 60
            mock_get_redis.return_value = mock_redis

            limiter = rate_limiter(max_requests=10, period=60)
            
            await limiter(mock_request, mock_response)
            
            # Should use "unknown" as client host
            expected_key = "ratelimit:/test/endpoint:unknown"
            mock_redis.get.assert_called_with(expected_key)

    @patch('musigree.app.fastapi_dependencies.get_redis_client')
    @pytest.mark.asyncio
    async def test_rate_limiter_uses_valid_ttl_from_redis(
        self, 
        mock_get_redis: Mock,
        mock_request: Mock,
        mock_response: Mock
    ) -> None:
        """Test that rate limiter uses valid TTL from Redis."""
        mock_redis = MagicMock()
        mock_redis.get.return_value = "2"
        mock_redis.ttl.return_value = 45  # Valid positive TTL
        mock_get_redis.return_value = mock_redis

        limiter = rate_limiter(max_requests=10, period=60)
        
        await limiter(mock_request, mock_response)
        
        # Should use TTL from Redis (45) instead of period (60)
        reset_time = int(mock_response.headers["X-RateLimit-Reset"])
        expected_reset = int(time.time()) + 45
        assert abs(reset_time - expected_reset) <= 1  # Allow 1 second tolerance

    @patch('musigree.app.fastapi_dependencies.get_redis_client')
    @pytest.mark.asyncio
    async def test_rate_limiter_uses_period_for_invalid_ttl(
        self, 
        mock_get_redis: Mock,
        mock_request: Mock,
        mock_response: Mock
    ) -> None:
        """Test that rate limiter uses period for invalid TTL values."""
        mock_redis = MagicMock()
        mock_redis.get.return_value = "2"
        mock_redis.ttl.return_value = -1  # Invalid TTL
        mock_get_redis.return_value = mock_redis

        limiter = rate_limiter(max_requests=10, period=60)
        
        await limiter(mock_request, mock_response)
        
        # Should use period (60) instead of invalid TTL (-1)
        reset_time = int(mock_response.headers["X-RateLimit-Reset"])
        expected_reset = int(time.time()) + 60
        assert abs(reset_time - expected_reset) <= 1  # Allow 1 second tolerance
