import json
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from musigree.constants import CacheType
from musigree.library.cache.cache_manager import (
    BaseCache,
    CacheManager,
    RedisCache,
    SimpleCache,
)


class TestBaseCache:
    """Test cases for the BaseCache interface."""

    @pytest.mark.asyncio
    async def test_base_cache_methods_not_implemented(self) -> None:
        """Test that BaseCache methods raise NotImplementedError."""
        cache = BaseCache()

        with pytest.raises(NotImplementedError):
            await cache.get("key")

        with pytest.raises(NotImplementedError):
            await cache.set("key", "value")

        with pytest.raises(NotImplementedError):
            await cache.hgetall("key")

        with pytest.raises(NotImplementedError):
            await cache.hset("key", {"field": "value"})

        with pytest.raises(NotImplementedError):
            await cache.incr("key")

        with pytest.raises(NotImplementedError):
            await cache.expire("key", 60)

        with pytest.raises(NotImplementedError):
            await cache.ttl("key")

        with pytest.raises(NotImplementedError):
            await cache.clear()

        with pytest.raises(NotImplementedError):
            await cache.close()

        with pytest.raises(NotImplementedError):
            await cache.ping()


class TestSimpleCache:
    """Test cases for the SimpleCache implementation."""

    @pytest.fixture(autouse=True)
    def setup_cache(self) -> None:
        """Set up test fixtures."""
        self.cache = SimpleCache()

    def test_simple_cache_initialization(self) -> None:
        """Test SimpleCache initialization with default parameters."""
        cache = SimpleCache()
        assert cache.cache == {}
        assert cache.threshold == 1000000
        assert cache.default_timeout == 0

    def test_simple_cache_initialization_with_params(self) -> None:
        """Test SimpleCache initialization with custom parameters."""
        cache = SimpleCache(threshold=500, default_timeout=60)
        assert cache.threshold == 500
        assert cache.default_timeout == 60

    @pytest.mark.asyncio
    async def test_simple_cache_set_and_get(self) -> None:
        """Test setting and getting values in SimpleCache."""
        await self.cache.set("key1", "value1")
        assert await self.cache.get("key1") == "value1"

    @pytest.mark.asyncio
    async def test_simple_cache_get_nonexistent(self) -> None:
        """Test getting non-existent key returns None."""
        assert await self.cache.get("nonexistent") is None

    @pytest.mark.asyncio
    async def test_simple_cache_clear(self) -> None:
        """Test clearing all entries from SimpleCache."""
        await self.cache.set("key1", "value1")
        await self.cache.set("key2", "value2")
        await self.cache.clear()
        assert await self.cache.get("key1") is None
        assert await self.cache.get("key2") is None
        assert self.cache.cache == {}

    @pytest.mark.asyncio
    async def test_simple_cache_timeout_ignored(self) -> None:
        """Test that timeout parameter is ignored in SimpleCache."""
        await self.cache.set("key1", "value1", timeout=60)
        assert await self.cache.get("key1") == "value1"

    @pytest.mark.asyncio
    async def test_simple_cache_hgetall(self) -> None:
        """Test getting hash values from SimpleCache."""
        assert await self.cache.hgetall("nonexistent") is None
        test_dict = {"field1": "value1", "field2": "value2"}
        await self.cache.hset("hash_key", test_dict)
        result = await self.cache.hgetall("hash_key")
        assert result == test_dict

    @pytest.mark.asyncio
    async def test_simple_cache_hset(self) -> None:
        """Test setting hash values in SimpleCache."""
        test_dict = {"field1": "value1", "field2": "value2"}
        await self.cache.hset("hash_key", test_dict)
        assert await self.cache.hgetall("hash_key") == test_dict

    @pytest.mark.asyncio
    async def test_simple_cache_hset_timeout_ignored(self) -> None:
        """Test that timeout parameter is ignored in SimpleCache hset."""
        test_dict = {"field1": "value1"}
        await self.cache.hset("hash_key", test_dict, timeout=60)
        assert await self.cache.hgetall("hash_key") == test_dict

    @pytest.mark.asyncio
    async def test_simple_cache_clear_clears_hash_cache(self) -> None:
        """Test that clear() clears both regular and hash cache."""
        await self.cache.set("key1", "value1")
        await self.cache.hset("hash_key", {"field1": "value1"})
        await self.cache.clear()
        assert await self.cache.get("key1") is None
        assert await self.cache.hgetall("hash_key") is None

    @pytest.mark.asyncio
    async def test_simple_cache_incr_not_implemented(self) -> None:
        """Test that incr method raises NotImplementedError in SimpleCache."""
        with pytest.raises(NotImplementedError):
            await self.cache.incr("key")

    @pytest.mark.asyncio
    async def test_simple_cache_expire_not_implemented(self) -> None:
        """Test that expire method raises NotImplementedError in SimpleCache."""
        with pytest.raises(NotImplementedError):
            await self.cache.expire("key", 60)

    @pytest.mark.asyncio
    async def test_simple_cache_ttl_not_implemented(self) -> None:
        """Test that ttl method raises NotImplementedError in SimpleCache."""
        with pytest.raises(NotImplementedError):
            await self.cache.ttl("key")

    @pytest.mark.asyncio
    async def test_simple_cache_close_clears_entries(self) -> None:
        """Test that close() clears both regular and hash cache."""
        await self.cache.set("key1", "value1")
        await self.cache.hset("hash_key", {"field1": "value1"})
        await self.cache.close()
        assert await self.cache.get("key1") is None
        assert await self.cache.hgetall("hash_key") is None


class TestRedisCache:
    """Test cases for the RedisCache implementation."""

    @patch("musigree.library.cache.cache_manager.aioredis")
    def test_redis_cache_no_redis_available(self, mock_aioredis: MagicMock) -> None:
        """Test RedisCache when Redis is not available leaves _client None."""
        mock_aioredis.ConnectionPool.from_url.side_effect = Exception("Connection failed")

        cache = RedisCache()
        assert cache._client is None

    @patch("musigree.library.cache.cache_manager.aioredis")
    def test_redis_cache_successful_connection(self, mock_aioredis: MagicMock) -> None:
        """Test RedisCache with successful Redis connection."""
        mock_pool = MagicMock()
        mock_client = MagicMock()
        mock_aioredis.ConnectionPool.from_url.return_value = mock_pool
        mock_aioredis.Redis.from_pool.return_value = mock_client

        cache = RedisCache()
        assert cache._client == mock_client

    @patch("musigree.library.cache.cache_manager.aioredis")
    def test_redis_cache_connection_failure(self, mock_aioredis: MagicMock) -> None:
        """Test RedisCache leaves _client None on connection failure."""
        mock_aioredis.ConnectionPool.from_url.side_effect = Exception("Connection failed")

        cache = RedisCache()
        assert cache._client is None

    @patch("musigree.library.cache.cache_manager.aioredis")
    def test_redis_cache_initialization_params(self, mock_aioredis: MagicMock) -> None:
        """Test RedisCache initialization parameters when connection fails."""
        mock_aioredis.ConnectionPool.from_url.side_effect = Exception("Connection failed")
        cache = RedisCache(
            host="example.com",
            port=6380,
            password="secret",
            db=1,
            default_timeout=600,
        )
        assert cache.default_timeout == 600
        assert cache._client is None


class TestCacheManager:
    """Test cases for the CacheManager class."""

    @pytest.fixture(autouse=True)
    async def cleanup_cache(self) -> AsyncGenerator[None, None]:
        """Clean up after each test."""
        yield
        # Reset the cache manager
        if hasattr(CacheManager, "cache") and CacheManager.cache is not None:
            # Check if it's a real cache instance (has async methods) or a mock
            if hasattr(CacheManager.cache, "clear") and callable(CacheManager.cache.clear):
                try:
                    await CacheManager.shutdown_cache()
                except (TypeError, AttributeError):
                    # If it's a mock that can't be awaited, just set to None
                    CacheManager.cache = None
            else:
                CacheManager.cache = None

    @patch("musigree.library.cache.cache_manager.SimpleCache")
    @pytest.mark.asyncio
    async def test_cache_manager_setup_simple_cache(self, mock_simple_cache: MagicMock) -> None:
        """Test CacheManager setup with simple cache."""
        config = MagicMock()
        config.CACHE_TYPE = CacheType.MEMORY

        mock_cache_instance = MagicMock()
        mock_simple_cache.return_value = mock_cache_instance

        await CacheManager.setup_cache(config)

        mock_simple_cache.assert_called_once_with(threshold=1000000, default_timeout=0)
        assert CacheManager.cache == mock_cache_instance

    @patch("musigree.library.cache.cache_manager.RedisCache")
    @pytest.mark.asyncio
    async def test_cache_manager_setup_redis_cache(self, mock_redis_cache: MagicMock) -> None:
        """Test CacheManager setup with Redis cache."""
        config = MagicMock()
        config.CACHE_TYPE = CacheType.REDIS
        config.REDIS_USERNAME = "test_user"
        config.REDIS_PASSWORD = "test_pass"
        config.REDIS_HOST = "test_host"
        config.REDIS_PORT = 8888

        mock_cache_instance = MagicMock()
        mock_cache_instance.ping = AsyncMock(return_value=True)
        mock_redis_cache.return_value = mock_cache_instance

        await CacheManager.setup_cache(config)

        mock_redis_cache.assert_called_once_with(
            username="test_user",
            password="test_pass",
            host="test_host",
            port=8888,
            db=0,
            default_timeout=60 * 60 * 24 * 7,
        )
        assert CacheManager.cache == mock_cache_instance

    @patch("musigree.library.cache.cache_manager.SimpleCache")
    @patch("musigree.library.cache.cache_manager.RedisCache")
    @pytest.mark.asyncio
    async def test_cache_manager_setup_redis_cache_fallback(
        self, mock_redis_cache: MagicMock, mock_simple_cache: MagicMock
    ) -> None:
        """Test CacheManager setup with Redis cache falling back to SimpleCache on error."""
        config = MagicMock()
        config.CACHE_TYPE = CacheType.REDIS
        config.REDIS_USERNAME = "test_user"
        config.REDIS_PASSWORD = "test_pass"
        config.REDIS_HOST = None
        config.REDIS_PORT = None

        mock_redis_cache.side_effect = Exception("Redis connection failed")
        mock_simple_cache_instance = MagicMock()
        mock_simple_cache.return_value = mock_simple_cache_instance

        await CacheManager.setup_cache(config)

        mock_redis_cache.assert_called_once_with(
            username="test_user",
            password="test_pass",
            host="localhost",
            port=6379,
            db=0,
            default_timeout=60 * 60 * 24 * 7,
        )
        mock_simple_cache.assert_called_once_with(threshold=1000000, default_timeout=0)
        assert CacheManager.cache == mock_simple_cache_instance

    @pytest.mark.asyncio
    async def test_cache_manager_shutdown_cache(self) -> None:
        """Test CacheManager cache shutdown."""
        # Set up a cache first
        mock_cache = MagicMock()
        mock_cache.clear = AsyncMock()
        mock_cache.close = AsyncMock()
        CacheManager.cache = mock_cache

        await CacheManager.shutdown_cache()

        mock_cache.clear.assert_called_once()
        mock_cache.close.assert_called_once()
        # Note: The current implementation doesn't delete the cache attribute

    def test_cache_manager_get_cache_when_set(self) -> None:
        """Test CacheManager get_cache returns cache when set."""
        mock_cache = MagicMock()
        CacheManager.cache = mock_cache

        result = CacheManager.get_cache()

        assert result == mock_cache

    def test_cache_manager_get_cache_when_not_set(self) -> None:
        """Test CacheManager get_cache raises error when cache not set."""
        # Ensure cache is not set
        CacheManager.cache = None

        with pytest.raises(ValueError, match="Invalid cache"):
            CacheManager.get_cache()

    @pytest.mark.asyncio
    async def test_cache_manager_clear(self) -> None:
        """Test CacheManager clear method."""
        mock_cache = MagicMock()
        mock_cache.clear = AsyncMock()
        CacheManager.cache = mock_cache

        await CacheManager.clear()

        mock_cache.clear.assert_called_once()


class TestRedisCacheMethods:
    """Test cases for RedisCache methods that need more coverage."""

    @pytest.fixture
    def redis_cache(self) -> RedisCache:
        """Create a RedisCache instance for testing with a mock client."""
        with patch("musigree.library.cache.cache_manager.aioredis") as mock_aioredis:
            mock_aioredis.ConnectionPool.from_url.side_effect = Exception("Connection failed")
            mock_client = MagicMock()
            cache = RedisCache()
            cache._client = mock_client
            return cache

    def test_get_redis_client_not_initialized(self) -> None:
        """Test _get_redis_client when client is None."""
        cache = RedisCache.__new__(RedisCache)  # Create without calling __init__
        cache._client = None

        with pytest.raises(RuntimeError, match="Redis client not initialized"):
            cache._get_redis_client()

    @pytest.mark.asyncio
    async def test_get_value_not_found(self, redis_cache: RedisCache) -> None:
        """Test get method when key doesn't exist."""
        assert redis_cache._client is not None
        mock_client: MagicMock = redis_cache._client  # type: ignore[assignment]
        mock_client.get = AsyncMock(return_value=None)

        result = await redis_cache.get("nonexistent_key")

        assert result is None
        mock_client.get.assert_called_once_with("nonexistent_key")

    @pytest.mark.asyncio
    async def test_get_value_bytes(self, redis_cache: RedisCache) -> None:
        """Test get method when Redis returns bytes value."""
        assert redis_cache._client is not None
        mock_client: MagicMock = redis_cache._client  # type: ignore[assignment]
        mock_client.get = AsyncMock(return_value=b"bytes_value")

        result = await redis_cache.get("test_key")

        # bytes decoded
        assert result == "bytes_value"
        mock_client.get.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_get_value_string(self, redis_cache: RedisCache) -> None:
        """Test get method when Redis returns string value."""
        assert redis_cache._client is not None
        mock_client: MagicMock = redis_cache._client  # type: ignore[assignment]
        mock_client.get = AsyncMock(return_value="string_value")

        result = await redis_cache.get("test_key")

        assert result == "string_value"
        mock_client.get.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_get_redis_client_exception(self, redis_cache: RedisCache) -> None:
        """Test get method when Redis client raises exception."""
        assert redis_cache._client is not None
        mock_client: MagicMock = redis_cache._client  # type: ignore[assignment]
        mock_client.get = AsyncMock(side_effect=Exception("Redis error"))

        # Implementation doesn't catch exceptions in get()
        with pytest.raises(Exception, match="Redis error"):
            await redis_cache.get("test_key")

    @pytest.mark.asyncio
    async def test_set_with_timeout(self, redis_cache: RedisCache) -> None:
        """Test set method with custom timeout."""
        assert redis_cache._client is not None
        mock_client: MagicMock = redis_cache._client  # type: ignore[assignment]
        mock_client.setex = AsyncMock()
        await redis_cache.set("test_key", "test_value", timeout=3600)

        mock_client.setex.assert_called_once_with(name="test_key", time=3600, value="test_value")

    @pytest.mark.asyncio
    async def test_set_without_timeout(self, redis_cache: RedisCache) -> None:
        """Test set method without timeout."""
        assert redis_cache._client is not None
        mock_client: MagicMock = redis_cache._client  # type: ignore[assignment]
        mock_client.set = AsyncMock()
        redis_cache.default_timeout = 0
        await redis_cache.set("test_key", "test_value")

        mock_client.set.assert_called_once_with(name="test_key", value="test_value")

    @pytest.mark.asyncio
    async def test_set_with_exception(self, redis_cache: RedisCache) -> None:
        """Test set method when Redis client raises exception."""
        assert redis_cache._client is not None
        mock_client: MagicMock = redis_cache._client  # type: ignore[assignment]
        mock_client.setex = AsyncMock(side_effect=Exception("Redis error"))

        # Implementation doesn't catch exceptions in set()
        with pytest.raises(Exception, match="Redis error"):
            await redis_cache.set("test_key", "test_value", timeout=3600)

    @pytest.mark.asyncio
    async def test_clear_success(self, redis_cache: RedisCache) -> None:
        """Test clear method success."""
        assert redis_cache._client is not None
        mock_client: MagicMock = redis_cache._client  # type: ignore[assignment]
        mock_client.flushdb = AsyncMock()
        await redis_cache.clear()

        mock_client.flushdb.assert_called_once()

    @pytest.mark.asyncio
    async def test_clear_with_exception(self, redis_cache: RedisCache) -> None:
        """Test clear method when Redis client raises exception."""
        assert redis_cache._client is not None
        mock_client: MagicMock = redis_cache._client  # type: ignore[assignment]
        mock_client.flushdb = AsyncMock(side_effect=Exception("Redis error"))

        # Should not raise exception
        await redis_cache.clear()

    @pytest.mark.asyncio
    async def test_hgetall_value_not_found(self, redis_cache: RedisCache) -> None:
        """Test hgetall method when key doesn't exist."""
        assert redis_cache._client is not None
        mock_client: MagicMock = redis_cache._client  # type: ignore[assignment]
        mock_client.get = AsyncMock(return_value=None)

        result = await redis_cache.hgetall("nonexistent_key")

        assert result is None
        mock_client.get.assert_called_once_with("nonexistent_key")

    @pytest.mark.asyncio
    async def test_hgetall_value_bytes(self, redis_cache: RedisCache) -> None:
        """Test hgetall method when Redis returns bytes keys/values."""
        assert redis_cache._client is not None
        mock_client: MagicMock = redis_cache._client  # type: ignore[assignment]
        mock_client.get = AsyncMock(return_value=json.dumps({"key1": "value1", "key2": "value2"}).encode("utf-8"))

        result = await redis_cache.hgetall("test_key")

        assert result == {"key1": "value1", "key2": "value2"}
        mock_client.get.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_hgetall_value_string(self, redis_cache: RedisCache) -> None:
        """Test hgetall method when Redis returns string keys/values."""
        assert redis_cache._client is not None
        mock_client: MagicMock = redis_cache._client  # type: ignore[assignment]
        mock_client.get = AsyncMock(return_value=json.dumps({"key1": "value1", "key2": "value2"}))

        result = await redis_cache.hgetall("test_key")

        assert result == {"key1": "value1", "key2": "value2"}
        mock_client.get.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_hgetall_not_dict(self, redis_cache: RedisCache) -> None:
        """Test hgetall method when Redis returns non-dict value."""
        assert redis_cache._client is not None
        mock_client: MagicMock = redis_cache._client  # type: ignore[assignment]
        mock_client.get = AsyncMock(return_value="not_a_dict")

        result = await redis_cache.hgetall("test_key")

        assert result is None
        mock_client.get.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_hgetall_non_string_or_bytes(self, redis_cache: RedisCache) -> None:
        """Test hgetall method when Redis returns non-string/bytes value."""
        assert redis_cache._client is not None
        mock_client: MagicMock = redis_cache._client  # type: ignore[assignment]
        mock_client.get = AsyncMock(return_value={"not": "string_or_bytes"})

        result = await redis_cache.hgetall("test_key")

        assert result is None
        mock_client.get.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_hset_with_timeout(self, redis_cache: RedisCache) -> None:
        """Test hset method with custom timeout."""
        assert redis_cache._client is not None
        mock_client: MagicMock = redis_cache._client  # type: ignore[assignment]
        mock_client.setex = AsyncMock()
        test_dict = {"field1": "value1", "field2": "value2"}
        await redis_cache.hset("test_key", test_dict, timeout=3600)

        mock_client.setex.assert_called_once_with(name="test_key", time=3600, value=json.dumps(test_dict))

    @pytest.mark.asyncio
    async def test_hset_without_timeout(self, redis_cache: RedisCache) -> None:
        """Test hset method without timeout."""
        assert redis_cache._client is not None
        mock_client: MagicMock = redis_cache._client  # type: ignore[assignment]
        mock_client.set = AsyncMock()
        redis_cache.default_timeout = 0
        test_dict = {"field1": "value1"}
        await redis_cache.hset("test_key", test_dict)

        mock_client.set.assert_called_once_with(name="test_key", value=json.dumps(test_dict))

    @pytest.mark.asyncio
    async def test_hset_with_exception(self, redis_cache: RedisCache) -> None:
        """Test hset method when Redis client raises exception."""
        assert redis_cache._client is not None
        mock_client: MagicMock = redis_cache._client  # type: ignore[assignment]
        mock_client.setex = AsyncMock(side_effect=Exception("Redis error"))

        # Implementation doesn't catch exceptions in hset()
        with pytest.raises(Exception, match="Redis error"):
            await redis_cache.hset("test_key", {"field1": "value1"}, timeout=3600)

    @patch("musigree.library.cache.cache_manager.aioredis")
    def test_redis_cache_ping_failure(self, mock_aioredis: MagicMock) -> None:
        """Test RedisCache __init__ does not call ping; client is set on success."""
        mock_pool = MagicMock()
        mock_client = MagicMock()
        mock_aioredis.ConnectionPool.from_url.return_value = mock_pool
        mock_aioredis.Redis.from_pool.return_value = mock_client
        mock_client.ping.side_effect = Exception("Ping failed")

        cache = RedisCache()
        assert cache._client == mock_client

    @pytest.mark.asyncio
    async def test_incr_success(self, redis_cache: RedisCache) -> None:
        """Test incr method success."""
        assert redis_cache._client is not None
        mock_client: MagicMock = redis_cache._client  # type: ignore[assignment]
        mock_client.incrby = AsyncMock()
        await redis_cache.incr("test_key")

        mock_client.incrby.assert_called_once_with("test_key", 1)

    @pytest.mark.asyncio
    async def test_incr_with_exception(self, redis_cache: RedisCache) -> None:
        """Test incr method when Redis client raises exception."""
        assert redis_cache._client is not None
        mock_client: MagicMock = redis_cache._client  # type: ignore[assignment]
        mock_client.incrby = AsyncMock(side_effect=Exception("Redis error"))

        # Implementation doesn't catch exceptions in incr()
        with pytest.raises(Exception, match="Redis error"):
            await redis_cache.incr("test_key")

    @pytest.mark.asyncio
    async def test_expire_success(self, redis_cache: RedisCache) -> None:
        """Test expire method success."""
        assert redis_cache._client is not None
        mock_client: MagicMock = redis_cache._client  # type: ignore[assignment]
        mock_client.expire = AsyncMock()
        await redis_cache.expire("test_key", 3600)

        mock_client.expire.assert_called_once_with("test_key", 3600)

    @pytest.mark.asyncio
    async def test_expire_with_exception(self, redis_cache: RedisCache) -> None:
        """Test expire method when Redis client raises exception."""
        assert redis_cache._client is not None
        mock_client: MagicMock = redis_cache._client  # type: ignore[assignment]
        mock_client.expire = AsyncMock(side_effect=Exception("Redis error"))

        # Implementation doesn't catch exceptions in expire()
        with pytest.raises(Exception, match="Redis error"):
            await redis_cache.expire("test_key", 3600)

    @pytest.mark.asyncio
    async def test_ttl_key_exists(self, redis_cache: RedisCache) -> None:
        """Test ttl method when key exists."""
        assert redis_cache._client is not None
        mock_client: MagicMock = redis_cache._client  # type: ignore[assignment]
        mock_client.ttl = AsyncMock(return_value=3600)

        result = await redis_cache.ttl("test_key")

        assert result == 3600
        mock_client.ttl.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_ttl_key_not_exists(self, redis_cache: RedisCache) -> None:
        """Test ttl method when key doesn't exist."""
        assert redis_cache._client is not None
        mock_client: MagicMock = redis_cache._client  # type: ignore[assignment]
        mock_client.ttl = AsyncMock(return_value=None)

        result = await redis_cache.ttl("test_key")

        assert result == -2
        mock_client.ttl.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_ttl_key_no_expiry(self, redis_cache: RedisCache) -> None:
        """Test ttl method when key has no expiry."""
        assert redis_cache._client is not None
        mock_client: MagicMock = redis_cache._client  # type: ignore[assignment]
        mock_client.ttl = AsyncMock(return_value=-1)

        result = await redis_cache.ttl("test_key")

        assert result == -1
        mock_client.ttl.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_ttl_non_int_value(self, redis_cache: RedisCache) -> None:
        """Test ttl method when Redis returns non-int value."""
        assert redis_cache._client is not None
        mock_client: MagicMock = redis_cache._client  # type: ignore[assignment]
        mock_client.ttl = AsyncMock(return_value="not_an_int")

        result = await redis_cache.ttl("test_key")

        assert result == -2
        mock_client.ttl.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_ttl_with_exception(self, redis_cache: RedisCache) -> None:
        """Test ttl method when Redis client raises exception."""
        assert redis_cache._client is not None
        mock_client: MagicMock = redis_cache._client  # type: ignore[assignment]
        mock_client.ttl.side_effect = Exception("Redis error")

        # Implementation doesn't catch exceptions in ttl()
        with pytest.raises(Exception, match="Redis error"):
            await redis_cache.ttl("test_key")


class TestCacheManagerUncoveredMethods:
    """Test cases for CacheManager methods that need more coverage."""

    @pytest.fixture(autouse=True)
    async def cleanup_cache(self) -> AsyncGenerator[None, None]:
        """Clean up after each test."""
        yield
        # Reset the cache manager
        if hasattr(CacheManager, "cache") and CacheManager.cache is not None:
            # Check if it's a real cache instance (has async methods) or a mock
            if hasattr(CacheManager.cache, "clear") and callable(CacheManager.cache.clear):
                try:
                    await CacheManager.shutdown_cache()
                except (TypeError, AttributeError):
                    # If it's a mock that can't be awaited, just set to None
                    CacheManager.cache = None
            else:
                CacheManager.cache = None

    @pytest.mark.asyncio
    async def test_setup_cache_invalid_type(self) -> None:
        """Test CacheManager setup_cache with invalid cache type."""
        config = MagicMock()
        config.CACHE_TYPE = "invalid_type"

        with pytest.raises(ValueError, match="Invalid CACHE_TYPE in configuration"):
            await CacheManager.setup_cache(config)

    @pytest.mark.asyncio
    async def test_cache_manager_clear_no_cache(self) -> None:
        """Test CacheManager clear when no cache is set."""
        # Ensure cache is not set
        CacheManager.cache = None

        # Should not raise exception, just do nothing
        await CacheManager.clear()

    def test_create_cache_key(self) -> None:
        """Test CacheManager create_cache_key method."""
        from musigree.constants import CACHE_KEY_SEPARATOR

        result = CacheManager.create_cache_key("domain", "123", "field")
        expected = f"domain{CACHE_KEY_SEPARATOR}123{CACHE_KEY_SEPARATOR}field"
        assert result == expected

    def test_create_cache_hkey(self) -> None:
        """Test CacheManager create_cache_hkey method."""
        from musigree.constants import CACHE_KEY_SEPARATOR

        result = CacheManager.create_cache_hkey("domain", "123")
        expected = f"domain{CACHE_KEY_SEPARATOR}123"
        assert result == expected

# Note: pytest automatically discovers and runs tests, so no main block is needed
