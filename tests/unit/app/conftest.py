"""
Pytest configuration and fixtures for app unit tests.

Provides an async cache mock so that rate_limiter and other code that awaits
cache methods (get, ttl, incr, expire) do not trigger "coroutine must be awaited"
or "MagicMock can't be used in 'await' expression" warnings when tests use
TestClient without patching the cache.
"""
from typing import Any, Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def cache_mock_with_async_methods(
    get_return: object = None,
    ttl_return: int = 60,
) -> MagicMock:
    """
    Build a cache mock whose get/ttl/incr/expire are AsyncMocks so await works.

    Use this when patching CacheManager.get_cache so the rate_limiter dependency
    does not raise or warn when awaiting cache methods.
    """
    cache = MagicMock()
    cache.get = AsyncMock(return_value=get_return)
    cache.ttl = AsyncMock(return_value=ttl_return)
    cache.incr = AsyncMock()
    cache.expire = AsyncMock()
    cache.hgetall = AsyncMock(return_value=None)
    cache.hset = AsyncMock()
    return cache


@pytest.fixture(autouse=True)
def async_cache_for_rate_limiter() -> Generator[None, Any, None]:
    """
    Ensure CacheManager.get_cache returns a mock whose async methods are awaitable.

    Any test that uses the real app (e.g. TestClient) and hits endpoints using the
    rate limiter will get this cache by default, avoiding RuntimeWarnings from
    awaiting MagicMock. Tests that need specific cache behavior can still patch
    get_cache and set return_value to a mock that includes AsyncMock for
    get/ttl/incr/expire (or use cache_mock_with_async_methods()).
    """
    cache = cache_mock_with_async_methods()
    with patch("musigree.library.cache.cache_manager.CacheManager.get_cache", return_value=cache):
        yield
