"""
Unit tests for the musigree.app.fastapi_dependencies module.

This module contains comprehensive tests for the utility functions and dependencies
defined in fastapi_dependencies.py, including entity type parsing, entity ID validation,
year range parsing, role filtering, Redis client management, and rate limiting functionality.
"""

import time
from typing import TYPE_CHECKING, Annotated, Any, get_args, get_origin
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from fastapi import Request, Response
from fastapi.routing import APIRoute

from musigree.app.fastapi_api import router as api_router
from musigree.app.fastapi_assets import create_assets_router
from musigree.app.fastapi_dependencies import (
    DEFAULT_BURST_MAX_REQUESTS,
    HEAVY_USAGE_DAILY_PERIOD_SECONDS,
    HEAVY_USAGE_DAILY_REQUEST_THRESHOLD,
    HEAVY_USAGE_HOURLY_PERIOD_SECONDS,
    HEAVY_USAGE_HOURLY_REQUEST_LIMIT,
    SEARCH_BURST_MAX_REQUESTS,
    EntityIdDep,
    EntityTypeDep,
    MaxYearDep,
    MinYearDep,
    OnMobileQuery,
    RolesDep,
    YearBoundsDep,
    _client_host,
    api_rate_limit,
    get_entity_id,
    get_entity_type,
    get_max_year,
    get_min_year,
    get_roles,
    get_year_bounds,
    is_good_bot,
    rate_limiter,
    ui_rate_limit,
)
from musigree.app.fastapi_healthcheck import router as health_router
from musigree.app.fastapi_ui import router as ui_router
from musigree.exceptions import BadRequestError, RateLimitError
from musigree.library.cache.cache_manager import FakeRedisCache
from musigree.library.fields.entity_type import EntityType
from tests.type_helpers import as_object

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


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


class TestGetYearBounds:
    """Test cases for min_year and max_year dependencies."""

    def test_missing_bounds_return_none(self) -> None:
        """Missing query values leave both bounds unset."""
        assert get_min_year(None) is None
        assert get_max_year(None) is None
        assert get_year_bounds(None, None) == (None, None)

    def test_valid_integers(self) -> None:
        """Inclusive bounds are returned unchanged."""
        assert get_min_year(1970) == 1970
        assert get_max_year(1979) == 1979
        assert get_year_bounds(1970, 1979) == (1970, 1979)

    def test_only_one_bound(self) -> None:
        """Either bound may be omitted."""
        assert get_year_bounds(1970, None) == (1970, None)
        assert get_year_bounds(None, 1979) == (None, 1979)

    def test_min_year_greater_than_max_year_raises_bad_request(self) -> None:
        """An inverted range is rejected."""
        with pytest.raises(BadRequestError) as exc_info:
            get_year_bounds(1980, 1970)
        assert exc_info.value.message == "min_year must be less than or equal to max_year"


class TestGetRoles:
    """Test cases for the get_roles function."""

    @patch("musigree.library.cache.role_cache.RoleCache")
    def test_get_roles_none_returns_empty(self, mock_role_cache: Mock) -> None:
        """Test that None input returns an empty set."""
        mock_role_cache.role_category_to_role_name_lookup = {}
        mock_role_cache.role_name_to_role_id_lookup = {}

        result = get_roles(None)
        assert result == set()

    @patch("musigree.library.cache.role_cache.RoleCache")
    def test_get_roles_empty_string_returns_empty(self, mock_role_cache: Mock) -> None:
        """Test that empty string returns an empty set."""
        mock_role_cache.role_category_to_role_name_lookup = {}
        mock_role_cache.role_name_to_role_id_lookup = {}

        result = get_roles("")
        assert result == set()

    @patch("musigree.library.cache.role_cache.RoleCache")
    def test_get_roles_direct_role_name_lookup(self, mock_role_cache: Mock) -> None:
        """Test that direct role name is found in lookup."""
        mock_role_cache.role_category_to_role_name_lookup = {}
        mock_role_cache.role_name_to_role_id_lookup = {"Producer": 1}

        result = get_roles("Producer")
        assert result == {"Producer"}

    @patch("musigree.library.cache.role_cache.RoleCache")
    def test_get_roles_category_lookup_with_valid_entries(self, mock_role_cache: Mock) -> None:
        """Test that role category lookup works with valid role entries."""
        mock_role_cache.role_category_to_role_name_lookup = {"Production": ["Producer", "Co-Producer"]}
        mock_role_cache.role_name_to_role_id_lookup = {"Producer": 1, "Co-Producer": 2}

        result = get_roles("Production")
        assert result == {"Co-Producer", "Producer"}

    @patch("musigree.library.cache.role_cache.RoleCache")
    def test_get_roles_category_lookup_with_invalid_entries(self, mock_role_cache: Mock) -> None:
        """Test that role category lookup skips invalid role entries."""
        mock_role_cache.role_category_to_role_name_lookup = {"Production": ["Producer", "InvalidRole"]}
        mock_role_cache.role_name_to_role_id_lookup = {
            "Producer": 1
            # InvalidRole is not in role_name_to_role_id_lookup
        }

        result = get_roles("Production")
        assert result == {"Producer"}

    @patch("musigree.library.cache.role_cache.RoleCache")
    def test_get_roles_comma_separated_roles(self, mock_role_cache: Mock) -> None:
        """Test that comma-separated roles are properly parsed."""
        mock_role_cache.role_category_to_role_name_lookup = {}
        mock_role_cache.role_name_to_role_id_lookup = {"Producer": 1, "Director": 2}

        result = get_roles("Producer,Director")
        assert result == {"Director", "Producer"}

    @patch("musigree.library.cache.role_cache.RoleCache")
    def test_get_roles_escaped_commas(self, mock_role_cache: Mock) -> None:
        """Test that escaped commas in role names are handled correctly."""
        mock_role_cache.role_category_to_role_name_lookup = {}
        mock_role_cache.role_name_to_role_id_lookup = {"A&R, Producer": 1, "Director": 2}

        result = get_roles("A&R\\, Producer,Director")
        assert result == {"A&R, Producer", "Director"}

    @patch("musigree.library.cache.role_cache.RoleCache")
    def test_get_roles_not_found_returns_empty(self, mock_role_cache: Mock) -> None:
        """Test that roles not found in lookup return an empty set."""
        mock_role_cache.role_category_to_role_name_lookup = {}
        mock_role_cache.role_name_to_role_id_lookup = {}

        result = get_roles("NonExistentRole")
        assert result == set()


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

    @pytest.mark.asyncio
    async def test_rate_limiter_allows_request_within_limit(self, mock_request: Mock, mock_response: Mock) -> None:
        """Test that rate limiter allows request within limit."""
        with patch("musigree.app.fastapi_dependencies.CacheManager.get_cache") as mock_get_cache:
            mock_cache = MagicMock()
            mock_cache.get = AsyncMock(return_value="5")  # Current requests
            mock_cache.ttl = AsyncMock(return_value=30)
            mock_cache.incr = AsyncMock()
            mock_cache.expire = AsyncMock()
            mock_get_cache.return_value = mock_cache

            limiter = rate_limiter(max_requests=10, period=60)

            # Should not raise an exception
            await limiter(mock_request, mock_response)

            # Verify cache operations
            cache_key = "ratelimit:/test/endpoint:127.0.0.1"
            mock_cache.get.assert_called_once_with(cache_key)
            mock_cache.incr.assert_called_once_with(cache_key)
            mock_cache.expire.assert_not_called()  # Not called since current_requests > 0

            # Verify response headers
            assert mock_response.headers["X-RateLimit-Limit"] == "10"
            assert mock_response.headers["X-RateLimit-Remaining"] == "4"  # 10 - 5 - 1
            assert "X-RateLimit-Reset" in mock_response.headers

    @pytest.mark.asyncio
    async def test_rate_limiter_raises_error_when_limit_exceeded(self, mock_request: Mock, mock_response: Mock) -> None:
        """Test that rate limiter raises RateLimitError when limit exceeded."""
        with patch("musigree.app.fastapi_dependencies.CacheManager.get_cache") as mock_get_cache:
            mock_cache = MagicMock()
            mock_cache.get = AsyncMock(return_value="10")  # Current requests equal to limit
            mock_cache.ttl = AsyncMock(return_value=30)
            mock_cache.incr = AsyncMock()
            mock_cache.expire = AsyncMock()
            mock_get_cache.return_value = mock_cache

            limiter = rate_limiter(max_requests=10, period=60)

            with pytest.raises(RateLimitError):
                await limiter(mock_request, mock_response)

            # Should not increment when limit exceeded
            mock_cache.incr.assert_not_called()

    @pytest.mark.asyncio
    async def test_rate_limiter_handles_none_redis_value(self, mock_request: Mock, mock_response: Mock) -> None:
        """Test that rate limiter handles None value from cache."""
        with patch("musigree.app.fastapi_dependencies.CacheManager.get_cache") as mock_get_cache:
            mock_cache = MagicMock()
            mock_cache.get = AsyncMock(return_value=None)
            mock_cache.ttl = AsyncMock(return_value=60)
            mock_cache.incr = AsyncMock()
            mock_cache.expire = AsyncMock()
            mock_get_cache.return_value = mock_cache

            limiter = rate_limiter(max_requests=10, period=60)

            await limiter(mock_request, mock_response)

            # Should set expiration for new key
            cache_key = "ratelimit:/test/endpoint:127.0.0.1"
            mock_cache.expire.assert_called_once_with(cache_key, 60)
            assert mock_response.headers["X-RateLimit-Remaining"] == "9"  # 10 - 0 - 1

    @pytest.mark.asyncio
    async def test_rate_limiter_handles_bytes_redis_value(self, mock_request: Mock, mock_response: Mock) -> None:
        """Test that rate limiter handles bytes value from cache."""
        with patch("musigree.app.fastapi_dependencies.CacheManager.get_cache") as mock_get_cache:
            mock_cache = MagicMock()
            mock_cache.get = AsyncMock(return_value=b"3")  # Bytes value (defensive check in implementation)
            mock_cache.ttl = AsyncMock(return_value=45)
            mock_cache.incr = AsyncMock()
            mock_cache.expire = AsyncMock()
            mock_get_cache.return_value = mock_cache

            limiter = rate_limiter(max_requests=10, period=60)

            await limiter(mock_request, mock_response)

            assert mock_response.headers["X-RateLimit-Remaining"] == "6"  # 10 - 3 - 1

    @pytest.mark.asyncio
    async def test_rate_limiter_handles_invalid_redis_value_types(
        self, mock_request: Mock, mock_response: Mock
    ) -> None:
        """Test that rate limiter handles invalid cache value types gracefully."""
        with patch("musigree.app.fastapi_dependencies.CacheManager.get_cache") as mock_get_cache:
            mock_cache = MagicMock()
            # Simulate a value that can't be converted to int
            mock_cache.get = AsyncMock(return_value="invalid_number")
            mock_cache.ttl = AsyncMock(return_value=60)
            mock_cache.incr = AsyncMock()
            mock_cache.expire = AsyncMock()
            mock_get_cache.return_value = mock_cache

            limiter = rate_limiter(max_requests=10, period=60)

            await limiter(mock_request, mock_response)

            # Should default to 0 current requests
            assert mock_response.headers["X-RateLimit-Remaining"] == "9"  # 10 - 0 - 1

    @pytest.mark.asyncio
    async def test_rate_limiter_handles_redis_get_exception(self, mock_request: Mock, mock_response: Mock) -> None:
        """Test that rate limiter handles cache get exception gracefully."""
        with patch("musigree.app.fastapi_dependencies.CacheManager.get_cache") as mock_get_cache:
            mock_cache = MagicMock()
            mock_cache.get = AsyncMock(side_effect=Exception("Cache connection error"))
            mock_cache.ttl = AsyncMock(return_value=60)
            mock_cache.incr = AsyncMock()
            mock_cache.expire = AsyncMock()
            mock_get_cache.return_value = mock_cache

            limiter = rate_limiter(max_requests=10, period=60)

            # Should not raise exception, fallback to allowing request
            await limiter(mock_request, mock_response)

            assert mock_response.headers["X-RateLimit-Remaining"] == "9"  # Fallback values

    @pytest.mark.asyncio
    async def test_rate_limiter_handles_redis_ttl_exception(self, mock_request: Mock, mock_response: Mock) -> None:
        """Test that rate limiter handles cache TTL exception gracefully."""
        with patch("musigree.app.fastapi_dependencies.CacheManager.get_cache") as mock_get_cache:
            mock_cache = MagicMock()
            mock_cache.get = AsyncMock(return_value="1")
            mock_cache.ttl = AsyncMock(side_effect=Exception("Cache TTL error"))
            mock_cache.incr = AsyncMock()
            mock_cache.expire = AsyncMock()
            mock_get_cache.return_value = mock_cache

            limiter = rate_limiter(max_requests=10, period=60)

            await limiter(mock_request, mock_response)

            # Should use period as fallback TTL
            reset_time = int(mock_response.headers["X-RateLimit-Reset"])
            expected_reset = int(time.time()) + 60
            assert abs(reset_time - expected_reset) <= 1  # Allow 1 second tolerance

    @pytest.mark.asyncio
    async def test_rate_limiter_handles_redis_incr_exception(self, mock_request: Mock, mock_response: Mock) -> None:
        """Test that rate limiter handles cache incr exception gracefully."""
        with patch("musigree.app.fastapi_dependencies.CacheManager.get_cache") as mock_get_cache:
            mock_cache = MagicMock()
            mock_cache.get = AsyncMock(return_value="1")
            mock_cache.ttl = AsyncMock(return_value=30)
            mock_cache.incr = AsyncMock(side_effect=Exception("Cache incr error"))
            mock_cache.expire = AsyncMock()
            mock_get_cache.return_value = mock_cache

            limiter = rate_limiter(max_requests=10, period=60)

            # Should not raise exception, continue with graceful degradation
            await limiter(mock_request, mock_response)

            assert mock_response.headers["X-RateLimit-Remaining"] == "8"  # 10 - 1 - 1

    @pytest.mark.asyncio
    async def test_rate_limiter_handles_missing_client_info(self, mock_response: Mock) -> None:
        """Test that rate limiter handles missing client information."""
        # Create request without client
        mock_request = Mock(spec=Request)
        mock_request.url.path = "/test/endpoint"
        mock_request.client = None

        with patch("musigree.app.fastapi_dependencies.CacheManager.get_cache") as mock_get_cache:
            mock_cache = MagicMock()
            mock_cache.get = AsyncMock(return_value=None)
            mock_cache.ttl = AsyncMock(return_value=60)
            mock_cache.incr = AsyncMock()
            mock_cache.expire = AsyncMock()
            mock_get_cache.return_value = mock_cache

            limiter = rate_limiter(max_requests=10, period=60)

            await limiter(mock_request, mock_response)

            # Should use "unknown" as client host
            expected_key = "ratelimit:/test/endpoint:unknown"
            mock_cache.get.assert_called_with(expected_key)

    @pytest.mark.asyncio
    async def test_rate_limiter_handles_client_without_host(self, mock_response: Mock) -> None:
        """Test that rate limiter handles client without host attribute."""
        # Create request with client but no host attribute
        mock_request = Mock(spec=Request)
        mock_request.url.path = "/test/endpoint"
        mock_request.client = Mock()
        # Simulate client without host attribute
        del mock_request.client.host

        with patch("musigree.app.fastapi_dependencies.CacheManager.get_cache") as mock_get_cache:
            mock_cache = MagicMock()
            mock_cache.get = AsyncMock(return_value=None)
            mock_cache.ttl = AsyncMock(return_value=60)
            mock_cache.incr = AsyncMock()
            mock_cache.expire = AsyncMock()
            mock_get_cache.return_value = mock_cache

            limiter = rate_limiter(max_requests=10, period=60)

            await limiter(mock_request, mock_response)

            # Should use "unknown" as client host
            expected_key = "ratelimit:/test/endpoint:unknown"
            mock_cache.get.assert_called_with(expected_key)

    @pytest.mark.asyncio
    async def test_rate_limiter_uses_valid_ttl_from_redis(self, mock_request: Mock, mock_response: Mock) -> None:
        """Test that rate limiter uses valid TTL from cache."""
        with patch("musigree.app.fastapi_dependencies.CacheManager.get_cache") as mock_get_cache:
            mock_cache = MagicMock()
            mock_cache.get = AsyncMock(return_value="2")
            mock_cache.ttl = AsyncMock(return_value=45)  # Valid positive TTL
            mock_cache.incr = AsyncMock()
            mock_cache.expire = AsyncMock()
            mock_get_cache.return_value = mock_cache

            limiter = rate_limiter(max_requests=10, period=60)

            await limiter(mock_request, mock_response)

            # Should use TTL from cache (45) instead of period (60)
            reset_time = int(mock_response.headers["X-RateLimit-Reset"])
            expected_reset = int(time.time()) + 45
            assert abs(reset_time - expected_reset) <= 1  # Allow 1 second tolerance

    @pytest.mark.asyncio
    async def test_rate_limiter_uses_period_for_invalid_ttl(self, mock_request: Mock, mock_response: Mock) -> None:
        """Test that rate limiter uses period for invalid TTL values."""
        with patch("musigree.app.fastapi_dependencies.CacheManager.get_cache") as mock_get_cache:
            mock_cache = MagicMock()
            mock_cache.get = AsyncMock(return_value="2")
            mock_cache.ttl = AsyncMock(return_value=-1)  # Invalid TTL
            mock_cache.incr = AsyncMock()
            mock_cache.expire = AsyncMock()
            mock_get_cache.return_value = mock_cache

            limiter = rate_limiter(max_requests=10, period=60)

            await limiter(mock_request, mock_response)

            # Should use period (60) instead of invalid TTL (-1)
            reset_time = int(mock_response.headers["X-RateLimit-Reset"])
            expected_reset = int(time.time()) + 60
            assert abs(reset_time - expected_reset) <= 1  # Allow 1 second tolerance

    @pytest.mark.asyncio
    async def test_rate_limiter_handles_none_ttl(self, mock_request: Mock, mock_response: Mock) -> None:
        """Test that rate limiter handles None TTL from cache."""
        with patch("musigree.app.fastapi_dependencies.CacheManager.get_cache") as mock_get_cache:
            mock_cache = MagicMock()
            mock_cache.get = AsyncMock(return_value="2")
            mock_cache.ttl = AsyncMock(return_value=None)  # None TTL
            mock_cache.incr = AsyncMock()
            mock_cache.expire = AsyncMock()
            mock_get_cache.return_value = mock_cache

            limiter = rate_limiter(max_requests=10, period=60)

            await limiter(mock_request, mock_response)

            # Should use period (60) instead of None TTL
            reset_time = int(mock_response.headers["X-RateLimit-Reset"])
            expected_reset = int(time.time()) + 60
            assert abs(reset_time - expected_reset) <= 1  # Allow 1 second tolerance

    @pytest.mark.asyncio
    async def test_rate_limiter_increments_request_count(self, mock_request: Mock, mock_response: Mock) -> None:
        """Test that rate limiter increments request count correctly."""
        with patch("musigree.app.fastapi_dependencies.CacheManager.get_cache") as mock_get_cache:
            mock_cache = MagicMock()
            mock_cache.get = AsyncMock(return_value="3")
            mock_cache.ttl = AsyncMock(return_value=30)
            mock_cache.incr = AsyncMock()
            mock_cache.expire = AsyncMock()
            mock_get_cache.return_value = mock_cache

            limiter = rate_limiter(max_requests=10, period=60)

            await limiter(mock_request, mock_response)

            cache_key = "ratelimit:/test/endpoint:127.0.0.1"
            mock_cache.incr.assert_called_once_with(cache_key)
            assert mock_response.headers["X-RateLimit-Remaining"] == "6"  # 10 - 3 - 1

    @pytest.mark.asyncio
    async def test_rate_limiter_sets_expire_for_new_key(self, mock_request: Mock, mock_response: Mock) -> None:
        """Test that rate limiter sets expiration for new cache keys."""
        with patch("musigree.app.fastapi_dependencies.CacheManager.get_cache") as mock_get_cache:
            mock_cache = MagicMock()
            mock_cache.get = AsyncMock(return_value=None)  # New key
            mock_cache.ttl = AsyncMock(return_value=None)
            mock_cache.incr = AsyncMock()
            mock_cache.expire = AsyncMock()
            mock_get_cache.return_value = mock_cache

            limiter = rate_limiter(max_requests=10, period=60)

            await limiter(mock_request, mock_response)

            cache_key = "ratelimit:/test/endpoint:127.0.0.1"
            mock_cache.incr.assert_called_once_with(cache_key)
            mock_cache.expire.assert_called_once_with(cache_key, 60)

    @pytest.mark.asyncio
    async def test_rate_limiter_enforces_limit_at_boundary(self, mock_request: Mock, mock_response: Mock) -> None:
        """Test that rate limiter enforces limit exactly at the boundary."""
        with patch("musigree.app.fastapi_dependencies.CacheManager.get_cache") as mock_get_cache:
            mock_cache = MagicMock()
            mock_cache.get = AsyncMock(return_value="9")  # One less than limit
            mock_cache.ttl = AsyncMock(return_value=30)
            mock_cache.incr = AsyncMock()
            mock_cache.expire = AsyncMock()
            mock_get_cache.return_value = mock_cache

            limiter = rate_limiter(max_requests=10, period=60)

            # Should allow this request (9 + 1 = 10, which is at limit)
            await limiter(mock_request, mock_response)

            assert mock_response.headers["X-RateLimit-Remaining"] == "0"  # 10 - 9 - 1
            mock_cache.incr.assert_called_once()

    @pytest.mark.asyncio
    async def test_rate_limiter_enforces_limit_when_exceeded(self, mock_request: Mock, mock_response: Mock) -> None:
        """Test that rate limiter raises error when limit is exceeded."""
        with patch("musigree.app.fastapi_dependencies.CacheManager.get_cache") as mock_get_cache:
            mock_cache = MagicMock()
            mock_cache.get = AsyncMock(return_value="11")  # Exceeds limit
            mock_cache.ttl = AsyncMock(return_value=30)
            mock_cache.incr = AsyncMock()
            mock_cache.expire = AsyncMock()
            mock_get_cache.return_value = mock_cache

            limiter = rate_limiter(max_requests=10, period=60)

            with pytest.raises(RateLimitError):
                await limiter(mock_request, mock_response)

            # Should not increment when limit exceeded
            mock_cache.incr.assert_not_called()


class TestHeavyUsageRateLimit:
    """Daily threshold keeps the burst limit, then switches to an hourly cap."""

    @pytest.fixture
    def mock_request(self) -> Mock:
        """Create a mock FastAPI Request object."""
        request = Mock(spec=Request)
        request.url.path = "/api/roles"
        request.client = Mock()
        request.client.host = "127.0.0.1"
        return request

    @pytest.fixture
    def mock_response(self) -> Mock:
        """Create a mock FastAPI Response object."""
        response = Mock(spec=Response)
        response.headers = {}
        return response

    @pytest.fixture
    async def fake_cache(self) -> AsyncIterator[FakeRedisCache]:
        """Provide an isolated in-memory Redis stand-in."""
        cache = FakeRedisCache()
        try:
            yield cache
        finally:
            await cache.close()

    async def test_under_daily_threshold_keeps_burst_limit(
        self,
        fake_cache: FakeRedisCache,
        mock_request: Mock,
        mock_response: Mock,
    ) -> None:
        """A client below 1000 requests a day still uses the route burst limit."""
        await fake_cache.set("ratelimit:daily:127.0.0.1", "5", timeout=HEAVY_USAGE_DAILY_PERIOD_SECONDS)
        limiter = rate_limiter(
            max_requests=DEFAULT_BURST_MAX_REQUESTS,
            period=60,
            enforce_heavy_usage_limit=True,
        )

        with patch("musigree.app.fastapi_dependencies.CacheManager.get_cache", return_value=fake_cache):
            await limiter(mock_request, mock_response)

        assert mock_response.headers["X-RateLimit-Limit"] == str(DEFAULT_BURST_MAX_REQUESTS)
        assert mock_response.headers["X-RateLimit-Daily-Limit"] == str(HEAVY_USAGE_DAILY_REQUEST_THRESHOLD)
        assert mock_response.headers["X-RateLimit-Daily-Remaining"] == str(HEAVY_USAGE_DAILY_REQUEST_THRESHOLD - 6)
        assert await fake_cache.get("ratelimit:daily:127.0.0.1") == "6"

    async def test_request_at_daily_threshold_still_uses_burst_limit(
        self,
        fake_cache: FakeRedisCache,
        mock_request: Mock,
        mock_response: Mock,
    ) -> None:
        """The 1000th request of the day is still on the normal burst limit."""
        await fake_cache.set(
            "ratelimit:daily:127.0.0.1",
            str(HEAVY_USAGE_DAILY_REQUEST_THRESHOLD - 1),
            timeout=HEAVY_USAGE_DAILY_PERIOD_SECONDS,
        )
        limiter = rate_limiter(max_requests=DEFAULT_BURST_MAX_REQUESTS, period=60, enforce_heavy_usage_limit=True)

        with patch("musigree.app.fastapi_dependencies.CacheManager.get_cache", return_value=fake_cache):
            await limiter(mock_request, mock_response)

        assert mock_response.headers["X-RateLimit-Limit"] == str(DEFAULT_BURST_MAX_REQUESTS)
        assert mock_response.headers["X-RateLimit-Daily-Remaining"] == "0"
        assert await fake_cache.get("ratelimit:daily:127.0.0.1") == str(HEAVY_USAGE_DAILY_REQUEST_THRESHOLD)

    async def test_over_daily_threshold_limits_to_hourly_cap(
        self,
        fake_cache: FakeRedisCache,
        mock_request: Mock,
        mock_response: Mock,
    ) -> None:
        """After 1000 requests in a day, the next requests are limited to 500 per hour."""
        await fake_cache.set(
            "ratelimit:daily:127.0.0.1",
            str(HEAVY_USAGE_DAILY_REQUEST_THRESHOLD),
            timeout=HEAVY_USAGE_DAILY_PERIOD_SECONDS,
        )
        await fake_cache.set("ratelimit:hourly:127.0.0.1", "10", timeout=HEAVY_USAGE_HOURLY_PERIOD_SECONDS)
        limiter = rate_limiter(max_requests=DEFAULT_BURST_MAX_REQUESTS, period=60, enforce_heavy_usage_limit=True)

        with patch("musigree.app.fastapi_dependencies.CacheManager.get_cache", return_value=fake_cache):
            await limiter(mock_request, mock_response)

        assert mock_response.headers["X-RateLimit-Limit"] == str(HEAVY_USAGE_HOURLY_REQUEST_LIMIT)
        assert mock_response.headers["X-RateLimit-Remaining"] == str(HEAVY_USAGE_HOURLY_REQUEST_LIMIT - 11)
        assert mock_response.headers["X-RateLimit-Daily-Remaining"] == "0"
        assert await fake_cache.get("ratelimit:hourly:127.0.0.1") == "11"

    async def test_hourly_cap_rejects_without_counting_the_request(
        self,
        fake_cache: FakeRedisCache,
        mock_request: Mock,
        mock_response: Mock,
    ) -> None:
        """A request over the hourly cap is rejected and does not move the counters."""
        await fake_cache.set(
            "ratelimit:daily:127.0.0.1",
            str(HEAVY_USAGE_DAILY_REQUEST_THRESHOLD),
            timeout=HEAVY_USAGE_DAILY_PERIOD_SECONDS,
        )
        await fake_cache.set(
            "ratelimit:hourly:127.0.0.1",
            str(HEAVY_USAGE_HOURLY_REQUEST_LIMIT),
            timeout=HEAVY_USAGE_HOURLY_PERIOD_SECONDS,
        )
        limiter = rate_limiter(max_requests=DEFAULT_BURST_MAX_REQUESTS, period=60, enforce_heavy_usage_limit=True)

        with (
            patch("musigree.app.fastapi_dependencies.CacheManager.get_cache", return_value=fake_cache),
            pytest.raises(RateLimitError) as error,
        ):
            await limiter(mock_request, mock_response)

        assert error.value.headers["X-RateLimit-Limit"] == str(HEAVY_USAGE_HOURLY_REQUEST_LIMIT)
        assert error.value.headers["X-RateLimit-Remaining"] == "0"
        assert await fake_cache.get("ratelimit:daily:127.0.0.1") == str(HEAVY_USAGE_DAILY_REQUEST_THRESHOLD)
        assert await fake_cache.get("ratelimit:hourly:127.0.0.1") == str(HEAVY_USAGE_HOURLY_REQUEST_LIMIT)
        assert await fake_cache.get("ratelimit:/api/roles:127.0.0.1") is None

    async def test_burst_limit_still_rejects_low_daily_usage(
        self,
        fake_cache: FakeRedisCache,
        mock_request: Mock,
        mock_response: Mock,
    ) -> None:
        """The per-route burst limit still applies before the daily threshold."""
        await fake_cache.set(
            "ratelimit:/api/roles:127.0.0.1",
            str(DEFAULT_BURST_MAX_REQUESTS),
            timeout=60,
        )
        limiter = rate_limiter(max_requests=DEFAULT_BURST_MAX_REQUESTS, period=60, enforce_heavy_usage_limit=True)

        with (
            patch("musigree.app.fastapi_dependencies.CacheManager.get_cache", return_value=fake_cache),
            pytest.raises(RateLimitError),
        ):
            await limiter(mock_request, mock_response)

        assert await fake_cache.get("ratelimit:daily:127.0.0.1") is None
        assert mock_response.headers["X-RateLimit-Limit"] == str(DEFAULT_BURST_MAX_REQUESTS)

    async def test_daily_counter_is_shared_across_routes(
        self,
        fake_cache: FakeRedisCache,
        mock_request: Mock,
        mock_response: Mock,
    ) -> None:
        """Routes share one daily counter for the client."""
        limiter = rate_limiter(max_requests=DEFAULT_BURST_MAX_REQUESTS, period=60, enforce_heavy_usage_limit=True)

        with patch("musigree.app.fastapi_dependencies.CacheManager.get_cache", return_value=fake_cache):
            await limiter(mock_request, mock_response)
            mock_request.url.path = "/api/random"
            await limiter(mock_request, mock_response)

        assert await fake_cache.get("ratelimit:daily:127.0.0.1") == "2"
        assert await fake_cache.get("ratelimit:/api/roles:127.0.0.1") == "1"
        assert await fake_cache.get("ratelimit:/api/random:127.0.0.1") == "1"

    async def test_search_burst_is_higher_than_other_routes(
        self,
        fake_cache: FakeRedisCache,
        mock_request: Mock,
        mock_response: Mock,
    ) -> None:
        """Search keeps its higher per-minute limit until the daily threshold."""
        await fake_cache.set("ratelimit:/api/search/beatles:127.0.0.1", "60", timeout=60)
        mock_request.url.path = "/api/search/beatles"

        with patch("musigree.app.fastapi_dependencies.CacheManager.get_cache", return_value=fake_cache):
            await api_rate_limit(mock_request, mock_response)

        assert mock_response.headers["X-RateLimit-Limit"] == str(SEARCH_BURST_MAX_REQUESTS)

        mock_request.url.path = "/api/roles"
        mock_response.headers = {}
        await fake_cache.set("ratelimit:/api/roles:127.0.0.1", str(DEFAULT_BURST_MAX_REQUESTS), timeout=60)
        with (
            patch("musigree.app.fastapi_dependencies.CacheManager.get_cache", return_value=fake_cache),
            pytest.raises(RateLimitError),
        ):
            await api_rate_limit(mock_request, mock_response)

    async def test_sustained_cache_error_still_allows_burst_request(
        self,
        mock_request: Mock,
        mock_response: Mock,
    ) -> None:
        """A cache failure while reading the daily counter does not block a normal request."""

        async def get(key: str) -> str | None:
            if key.startswith("ratelimit:daily:") or key.startswith("ratelimit:hourly:"):
                raise ConnectionError("cache down")
            return None

        cache = MagicMock()
        cache.get = AsyncMock(side_effect=get)
        cache.ttl = AsyncMock(return_value=60)
        cache.incr = AsyncMock()
        cache.expire = AsyncMock()
        limiter = rate_limiter(max_requests=DEFAULT_BURST_MAX_REQUESTS, period=60, enforce_heavy_usage_limit=True)

        with patch("musigree.app.fastapi_dependencies.CacheManager.get_cache", return_value=cache):
            await limiter(mock_request, mock_response)

        assert mock_response.headers["X-RateLimit-Limit"] == str(DEFAULT_BURST_MAX_REQUESTS)


def _dependency_calls(dependant: Any) -> list[Any]:
    """Return every nested dependency callable on a route."""
    calls: list[Any] = []
    for sub_dependant in dependant.dependencies:
        calls.append(sub_dependant.call)
        calls.extend(_dependency_calls(sub_dependant))
    return calls


def _route_is_rate_limited(route: APIRoute) -> bool:
    """Return whether the route runs a rate-limiter dependency."""
    return any(getattr(call, "is_rate_limiter", False) for call in _dependency_calls(route.dependant))


class TestEveryRouteIsRateLimited:
    """Data routes must declare a rate limiter. Health and the asset helper stay open."""

    # Static file mounts are not API routes. Limiting them at the API burst
    # size would block a normal page, which loads many scripts and images.
    EXEMPT_PATHS = frozenset({"/health", "/context"})

    def test_application_routes_are_rate_limited_or_explicitly_exempt(self) -> None:
        """Every HTTP route is rate limited unless it is on the exempt list."""
        assets_router, _templates = create_assets_router(Mock(PRODUCTION=False))
        routes = [
            route
            for router in (api_router, ui_router, health_router, assets_router)
            for route in router.routes
            if isinstance(route, APIRoute)
        ]
        assert routes

        unlimited = sorted(route.path for route in routes if not _route_is_rate_limited(route))
        assert set(unlimited) == self.EXEMPT_PATHS

        limited_paths = {route.path for route in routes if _route_is_rate_limited(route)}
        assert "/api/search/{search_string}" in limited_paths
        assert "/api/{entity_type_str}/network/{entity_id}" in limited_paths
        assert "/api/{entity_type_str}/details/{entity_id}" in limited_paths
        assert "/api/{entity_type_str}/relations/{entity_id}" in limited_paths
        assert "/api/random" in limited_paths
        assert "/api/roles" in limited_paths
        assert "/" in limited_paths
        assert "/artist/{entity_id}" in limited_paths
        assert "/label/{entity_id}" in limited_paths


class TestGoodBotWhitelist:
    """Search, citation, preview, and uptime bots skip the hourly cap."""

    @pytest.fixture
    def mock_request(self) -> Mock:
        """Create a mock FastAPI Request object."""
        request = Mock(spec=Request)
        request.url.path = "/api/roles"
        request.client = Mock()
        request.client.host = "127.0.0.1"
        request.headers = {}
        return request

    @pytest.fixture
    def mock_response(self) -> Mock:
        """Create a mock FastAPI Response object."""
        response = Mock(spec=Response)
        response.headers = {}
        return response

    @pytest.fixture
    async def fake_cache(self) -> AsyncIterator[FakeRedisCache]:
        """Provide an isolated in-memory Redis stand-in."""
        cache = FakeRedisCache()
        try:
            yield cache
        finally:
            await cache.close()

    # noinspection HttpUrlsUsage
    @pytest.mark.parametrize(
        "user_agent",
        [
            "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
            "Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (Applebot/0.1)",
            "DuckDuckBot/1.1; (+http://duckduckgo.com/duckduckbot.html)",
            "Mozilla/5.0 (compatible; OAI-SearchBot/1.0; +https://openai.com/searchbot)",
            "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; PerplexityBot/1.0",
            "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; ChatGPT-User/1.0",
            "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; Claude-User/1.0",
            "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; Claude-SearchBot/1.0; +searchbot@anthropic.com)",
            "facebookexternalhit/1.1",
            "Twitterbot/1.0",
            "LinkedInBot/1.0",
            "Mozilla/5.0 (compatible; UptimeRobot/2.0; http://www.uptimerobot.com/)",
            "Pingdom.com_bot_version_1.4_(http://www.pingdom.com/)",
        ],
    )
    def test_indexing_and_monitor_bots_are_whitelisted(self, user_agent: str) -> None:
        """Bots that send visitors or check uptime skip the heavy-usage policy."""
        assert is_good_bot(user_agent)

    @pytest.mark.parametrize(
        "user_agent",
        [
            None,
            "",
            "Mozilla/5.0",
            "python-requests/2.32.0",
            "curl/8.7.1",
            "Mozilla/5.0 (compatible; GPTBot/1.2; +https://openai.com/gptbot)",
            "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; ClaudeBot/1.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (Applebot-Extended/1.0)",
            "Mozilla/5.0 (compatible; Bytespider; https://zhanzhang.toutiao.com/)",
            "CCBot/2.0 (https://commoncrawl.org/faq/)",
            "Meta-ExternalAgent/1.1",
            "Mozilla/5.0 (compatible; AhrefsBot/7.0; +http://ahrefs.com/robot/)",
            "Mozilla/5.0 (compatible; SemrushBot/7~bl; +http://www.semrush.com/bot.html)",
            "Mozilla/5.0 (compatible; MJ12bot/v1.4.8; http://mj12bot.com/)",
            "Mozilla/5.0 (compatible; DotBot/1.2; +https://opensiteexplorer.org/dotbot)",
        ],
    )
    def test_training_scrapers_and_anonymous_clients_stay_limited(self, user_agent: str | None) -> None:
        """Training crawlers and clients without a known bot name keep the strict policy."""
        assert not is_good_bot(user_agent)

    async def test_good_bot_skips_hourly_cap(
        self,
        fake_cache: FakeRedisCache,
        mock_request: Mock,
        mock_response: Mock,
    ) -> None:
        """A whitelisted bot over the daily threshold still uses the per-minute burst."""
        await fake_cache.set(
            "ratelimit:daily:127.0.0.1",
            str(HEAVY_USAGE_DAILY_REQUEST_THRESHOLD),
            timeout=HEAVY_USAGE_DAILY_PERIOD_SECONDS,
        )
        await fake_cache.set(
            "ratelimit:hourly:127.0.0.1",
            str(HEAVY_USAGE_HOURLY_REQUEST_LIMIT),
            timeout=HEAVY_USAGE_HOURLY_PERIOD_SECONDS,
        )
        mock_request.headers = {"user-agent": "Mozilla/5.0 (compatible; Googlebot/2.1)"}

        with patch("musigree.app.fastapi_dependencies.CacheManager.get_cache", return_value=fake_cache):
            await api_rate_limit(mock_request, mock_response)

        assert mock_response.headers["X-RateLimit-Limit"] == str(DEFAULT_BURST_MAX_REQUESTS)
        assert "X-RateLimit-Daily-Limit" not in mock_response.headers
        assert await fake_cache.get("ratelimit:daily:127.0.0.1") == str(HEAVY_USAGE_DAILY_REQUEST_THRESHOLD)
        assert await fake_cache.get("ratelimit:hourly:127.0.0.1") == str(HEAVY_USAGE_HOURLY_REQUEST_LIMIT)

    async def test_training_bot_keeps_hourly_cap(
        self,
        fake_cache: FakeRedisCache,
        mock_request: Mock,
        mock_response: Mock,
    ) -> None:
        """A training crawler over the daily threshold is limited to 500 requests an hour."""
        await fake_cache.set(
            "ratelimit:daily:127.0.0.1",
            str(HEAVY_USAGE_DAILY_REQUEST_THRESHOLD),
            timeout=HEAVY_USAGE_DAILY_PERIOD_SECONDS,
        )
        await fake_cache.set(
            "ratelimit:hourly:127.0.0.1",
            str(HEAVY_USAGE_HOURLY_REQUEST_LIMIT),
            timeout=HEAVY_USAGE_HOURLY_PERIOD_SECONDS,
        )
        mock_request.headers = {"user-agent": "Mozilla/5.0 (compatible; GPTBot/1.2)"}

        with (
            patch("musigree.app.fastapi_dependencies.CacheManager.get_cache", return_value=fake_cache),
            pytest.raises(RateLimitError) as error,
        ):
            await api_rate_limit(mock_request, mock_response)

        assert error.value.headers["X-RateLimit-Limit"] == str(HEAVY_USAGE_HOURLY_REQUEST_LIMIT)

    async def test_good_bot_still_uses_standard_burst(
        self,
        fake_cache: FakeRedisCache,
        mock_request: Mock,
        mock_response: Mock,
    ) -> None:
        """A whitelisted bot is still limited to the standard per-minute burst."""
        await fake_cache.set(
            "ratelimit:/api/roles:127.0.0.1",
            str(DEFAULT_BURST_MAX_REQUESTS),
            timeout=60,
        )
        mock_request.headers = {"user-agent": "UptimeRobot/2.0"}

        with (
            patch("musigree.app.fastapi_dependencies.CacheManager.get_cache", return_value=fake_cache),
            pytest.raises(RateLimitError) as error,
        ):
            await api_rate_limit(mock_request, mock_response)

        assert error.value.headers["X-RateLimit-Limit"] == str(DEFAULT_BURST_MAX_REQUESTS)

    async def test_good_bot_search_uses_standard_burst_not_search_burst(
        self,
        fake_cache: FakeRedisCache,
        mock_request: Mock,
        mock_response: Mock,
    ) -> None:
        """Search requests from a whitelisted bot use the standard burst, not the higher search burst."""
        await fake_cache.set("ratelimit:/api/search/beatles:127.0.0.1", str(DEFAULT_BURST_MAX_REQUESTS), timeout=60)
        mock_request.url.path = "/api/search/beatles"
        mock_request.headers = {"user-agent": "Mozilla/5.0 (compatible; Googlebot/2.1)"}

        with (
            patch("musigree.app.fastapi_dependencies.CacheManager.get_cache", return_value=fake_cache),
            pytest.raises(RateLimitError) as error,
        ):
            await api_rate_limit(mock_request, mock_response)

        assert error.value.headers["X-RateLimit-Limit"] == str(DEFAULT_BURST_MAX_REQUESTS)

    async def test_good_bot_page_request_skips_hourly_cap(
        self,
        fake_cache: FakeRedisCache,
        mock_request: Mock,
        mock_response: Mock,
    ) -> None:
        """A whitelisted bot loading an HTML page also skips the hourly cap."""
        await fake_cache.set(
            "ratelimit:hourly:127.0.0.1",
            str(HEAVY_USAGE_HOURLY_REQUEST_LIMIT),
            timeout=HEAVY_USAGE_HOURLY_PERIOD_SECONDS,
        )
        await fake_cache.set(
            "ratelimit:daily:127.0.0.1",
            str(HEAVY_USAGE_DAILY_REQUEST_THRESHOLD),
            timeout=HEAVY_USAGE_DAILY_PERIOD_SECONDS,
        )
        mock_request.url.path = "/artist/1"
        mock_request.headers = {"user-agent": "facebookexternalhit/1.1"}

        with patch("musigree.app.fastapi_dependencies.CacheManager.get_cache", return_value=fake_cache):
            await ui_rate_limit(mock_request, mock_response)

        assert mock_response.headers["X-RateLimit-Limit"] == str(DEFAULT_BURST_MAX_REQUESTS)
        assert await fake_cache.get("ratelimit:daily:127.0.0.1") == str(HEAVY_USAGE_DAILY_REQUEST_THRESHOLD)


class TestClientAddress:
    """Rate-limit buckets follow the visitor, not the reverse proxy."""

    def _request(self, peer: str | None, headers: dict[str, str] | None = None) -> Mock:
        request = Mock(spec=Request)
        if peer is None:
            request.client = None
        else:
            request.client = Mock()
            request.client.host = peer
        request.headers = headers or {}
        return request

    def test_public_peer_is_the_visitor(self) -> None:
        """A direct connection uses the socket address and ignores a spoofed forwarding header."""
        request = self._request("203.0.113.9", {"x-forwarded-for": "198.51.100.20"})
        assert _client_host(request) == "203.0.113.9"

    def test_private_proxy_uses_the_forwarded_visitor(self) -> None:
        """A Docker or localhost proxy contributes the visitor from X-Forwarded-For."""
        request = self._request("172.18.0.5", {"x-forwarded-for": "203.0.113.50"})
        assert _client_host(request) == "203.0.113.50"

    def test_spoofed_forwarded_entry_is_not_the_visitor(self) -> None:
        """The address appended by the proxy is the visitor; an earlier value is not."""
        request = self._request(
            "10.0.1.8",
            {"x-forwarded-for": "198.51.100.20, 203.0.113.50"},
        )
        assert _client_host(request) == "203.0.113.50"

    def test_two_visitors_behind_one_proxy_are_distinct(self) -> None:
        """Browsers behind the same proxy receive separate rate-limit identities."""
        first = self._request("172.18.0.5", {"x-forwarded-for": "203.0.113.10"})
        second = self._request("172.18.0.5", {"x-forwarded-for": "203.0.113.11"})
        assert _client_host(first) == "203.0.113.10"
        assert _client_host(second) == "203.0.113.11"
        assert _client_host(first) != _client_host(second)

    def test_private_proxy_uses_x_real_ip_without_forwarded_for(self) -> None:
        """X-Real-IP supplies the visitor when the proxy does not send X-Forwarded-For."""
        request = self._request("192.168.1.2", {"x-real-ip": "203.0.113.80"})
        assert _client_host(request) == "203.0.113.80"

    def test_forwarded_port_is_removed(self) -> None:
        """A port on the forwarded address is not part of the rate-limit identity."""
        request = self._request("127.0.0.1", {"x-forwarded-for": "203.0.113.50:54432"})
        assert _client_host(request) == "203.0.113.50"

    def test_ipv6_visitor_behind_proxy(self) -> None:
        """An IPv6 visitor behind a private proxy keeps that address."""
        request = self._request("172.18.0.5", {"x-forwarded-for": "[2001:db8::5]:443"})
        assert _client_host(request) == "2001:db8::5"

    def test_localhost_without_forwarding_stays_localhost(self) -> None:
        """A local request with no forwarding header remains the local peer."""
        request = self._request("127.0.0.1")
        assert _client_host(request) == "127.0.0.1"

    def test_missing_client_is_unknown(self) -> None:
        """A request with no socket peer has no address to bucket."""
        assert _client_host(self._request(None)) == "unknown"

    @pytest.mark.asyncio
    async def test_rate_limiter_keys_visitors_separately_behind_one_proxy(self) -> None:
        """The burst counter for one visitor does not include another visitor on the same proxy."""
        with patch("musigree.app.fastapi_dependencies.CacheManager.get_cache") as mock_get_cache:
            mock_cache = MagicMock()
            mock_cache.get = AsyncMock(return_value=None)
            mock_cache.ttl = AsyncMock(return_value=60)
            mock_cache.incr = AsyncMock()
            mock_cache.expire = AsyncMock()
            mock_get_cache.return_value = mock_cache

            limiter = rate_limiter(max_requests=10, period=60)
            first = self._request("172.18.0.5", {"x-forwarded-for": "203.0.113.10"})
            second = self._request("172.18.0.5", {"x-forwarded-for": "203.0.113.11"})
            first.url.path = "/api/roles"
            second.url.path = "/api/roles"
            response = Mock(spec=Response)
            response.headers = {}

            await limiter(first, response)
            await limiter(second, response)

        keys = [call.args[0] for call in mock_cache.get.await_args_list]
        assert "ratelimit:/api/roles:203.0.113.10" in keys
        assert "ratelimit:/api/roles:203.0.113.11" in keys
        assert "ratelimit:/api/roles:172.18.0.5" not in keys


class TestAnnotatedDependencies:
    """Shared Annotated aliases follow current FastAPI dependency style."""

    def test_entity_type_dep_wraps_get_entity_type(self) -> None:
        assert get_origin(EntityTypeDep) is Annotated
        assert get_args(EntityTypeDep)[1].dependency is get_entity_type

    def test_entity_id_dep_wraps_get_entity_id(self) -> None:
        assert get_origin(EntityIdDep) is Annotated
        assert get_args(EntityIdDep)[1].dependency is get_entity_id

    def test_year_bounds_dep_wraps_get_year_bounds(self) -> None:
        assert get_origin(YearBoundsDep) is Annotated
        assert get_args(YearBoundsDep)[1].dependency is get_year_bounds

    def test_min_year_dep_wraps_get_min_year(self) -> None:
        min_year_dep = as_object(MinYearDep)
        assert get_origin(min_year_dep) is Annotated
        assert get_args(min_year_dep)[1].dependency is get_min_year

    def test_max_year_dep_wraps_get_max_year(self) -> None:
        max_year_dep = as_object(MaxYearDep)
        assert get_origin(max_year_dep) is Annotated
        assert get_args(max_year_dep)[1].dependency is get_max_year

    def test_roles_dep_wraps_get_roles(self) -> None:
        assert get_origin(RolesDep) is Annotated
        assert get_args(RolesDep)[1].dependency is get_roles

    def test_on_mobile_query_is_optional_boolean(self) -> None:
        assert get_origin(OnMobileQuery) is Annotated
        origin, query = get_args(OnMobileQuery)
        assert origin is bool
        assert query.description == "Whether the request is from a mobile device"
