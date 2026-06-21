import json
import logging
from collections.abc import Awaitable
from json import JSONDecodeError
from typing import Any

# noinspection PyPackageRequirements
import fakeredis

# noinspection PyPackageRequirements
from redis import asyncio as aioredis

from musigree.config import Configuration
from musigree.constants import CacheType, CACHE_KEY_SEPARATOR

log = logging.getLogger(__name__)

__all__ = [
    "CacheManager",
    "BaseCache",
    "SimpleCache",
    "RedisCache",
    "CacheType",
]


class BaseCache:
    """Base cache class that defines the interface for all cache implementations."""

    async def get(self, key: str) -> str | None:
        """Get value from cache for the given key."""
        raise NotImplementedError

    async def set(self, key: str, value: str, timeout: int | None = None) -> None:
        """Set value in cache for the given key with optional timeout."""
        raise NotImplementedError

    async def incr(self, key: str) -> None:
        """Increment value in cache for the given key."""
        raise NotImplementedError

    async def expire(self, key: str, timeout: int) -> None:
        """Set the timeout for the given key."""
        raise NotImplementedError

    async def ttl(self, key: str) -> int:
        """Get the timeout for the given key."""
        raise NotImplementedError

    async def hgetall(self, key: str) -> dict[str, Any] | None:
        """Get hash value from cache for the given key."""
        raise NotImplementedError

    async def hset(self, key: str, value: dict[str, Any], timeout: int | None = None) -> None:
        """Set hash value in cache for the given key with optional timeout."""
        raise NotImplementedError

    async def clear(self) -> None:
        """Clear all cache entries."""
        raise NotImplementedError

    async def close(self) -> None:
        """Close the cache."""
        raise NotImplementedError

    async def ping(self) -> bool:
        """Ping the cache."""
        raise NotImplementedError


class SimpleCache(BaseCache):
    """Simple in-memory cache implementation."""

    def __init__(self, threshold: int = 1000000, default_timeout: int = 0):
        self.cache: dict[str, str] = {}
        self.hcache: dict[str, Any] = {}
        self.threshold = threshold
        self.default_timeout = default_timeout

    async def get(self, key: str) -> str | None:
        """Get value from cache for the given key."""
        return self.cache.get(key)

    async def set(self, key: str, value: str, timeout: int | None = None) -> None:
        """Set value in cache for the given key with optional timeout."""
        # In this simple implementation, we ignore timeout
        self.cache[key] = value
        # If cache exceeds threshold, clear oldest entries (not implemented)

    async def incr(self, key: str) -> None:
        """Increment value in cache for the given key."""
        raise NotImplementedError

    async def expire(self, key: str, timeout: int) -> None:
        """Set the timeout for the given key."""
        raise NotImplementedError

    async def ttl(self, key: str) -> int:
        """Get the timeout for the given key."""
        raise NotImplementedError

    async def hgetall(self, key: str) -> dict[str, Any] | None:
        """Get value from cache for the given key."""
        return self.hcache.get(key)

    async def hset(self, key: str, value: dict[str, Any], timeout: int | None = None) -> None:
        """Set value in cache for the given key with optional timeout."""
        # In this simple implementation, we ignore timeout
        self.hcache[key] = value
        # If cache exceeds threshold, clear oldest entries (not implemented)

    async def clear(self) -> None:
        """Clear all cache entries."""
        self.cache.clear()
        self.hcache.clear()

    async def close(self) -> None:
        """Close the cache."""
        self.cache.clear()
        self.hcache.clear()


class RedisCache(BaseCache):
    """Redis-based cache implementation."""

    def __init__(
        self,
        username: str | None = None,
        password: str | None = None,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        default_timeout: int = 300,
    ) -> None:
        """Initialize Redis cache.

        Args:
            host: Redis server hostname
            port: Redis server port
            password: Redis server password
            db: Redis database number
            default_timeout: Default cache timeout in seconds
        """
        self.default_timeout = default_timeout
        self._client: aioredis.Redis | fakeredis.FakeRedis | None = None

        try:
            if username is not None and password is not None:
                redis_url = f"redis://{username}:{password}@{host}:{port}/{db}"
            else:
                redis_url = f"redis://{host}:{port}/{db}"
            log.info(f"Redis server: {redis_url}")
            pool = aioredis.ConnectionPool.from_url(redis_url)
            self._client = aioredis.Redis.from_pool(pool)
        except Exception as e:
            log.warning(f"Failed to connect to Redis server: {e}")

    def _get_redis_client(self) -> aioredis.Redis | fakeredis.FakeRedis:
        """Get the Redis client, handles both real Redis and FakeRedis."""
        if self._client is None:
            raise RuntimeError("Redis client not initialized")
        return self._client

    async def ping(self) -> bool:
        """Ping the server."""
        redis_client = self._get_redis_client()
        ping_result = redis_client.ping()
        if isinstance(ping_result, Awaitable):
            return await ping_result
        return bool(ping_result)

    async def get(self, key: str) -> str | None:
        """Get value from cache for the given key."""
        redis_client = self._get_redis_client()
        raw_value = await redis_client.get(key)

        # Return None if the key doesn't exist
        if raw_value is None:
            return None

        value = raw_value.decode("utf-8") if isinstance(raw_value, bytes) else str(raw_value)

        return value

    async def set(self, key: str, value: str, timeout: int | None = None) -> None:
        """Set value in cache for the given key with optional timeout."""
        redis_client = self._get_redis_client()
        timeout = timeout if timeout is not None else self.default_timeout

        # Set in Redis with or without timeout
        if timeout > 0:
            await redis_client.setex(name=key, time=timeout, value=value)
        else:
            await redis_client.set(name=key, value=value)

    async def incr(self, key: str) -> None:
        """Increment value in cache for the given key."""
        redis_client = self._get_redis_client()
        await redis_client.incrby(key, 1)

    async def expire(self, key: str, timeout: int) -> None:
        """Set the timeout for the given key."""
        redis_client = self._get_redis_client()
        await redis_client.expire(key, timeout)

    async def ttl(self, key: str) -> int:
        """Get the timeout for the given key."""
        redis_client = self._get_redis_client()
        raw_value = await redis_client.ttl(key)

        # Return None if the key doesn't exist
        if raw_value is None:
            return -2

        # Type guard: ensure we have a dict (not an Awaitable)
        # Since this is a synchronous method, hgetall should return a dict
        if not isinstance(raw_value, int):
            return -2

        return int(raw_value)

    async def hgetall(self, key: str) -> dict[str, Any] | None:
        """Get hash value from cache for the given key."""
        redis_client = self._get_redis_client()
        raw_value = await redis_client.get(key)

        # Return None if the key doesn't exist
        if raw_value is None:
            return None

        # Type guard: ensure we have a dict (not an Awaitable)
        # Since this is a synchronous method, hgetall should return a dict
        if not (isinstance(raw_value, bytes) or isinstance(raw_value, str)):
            return None

        json_value = raw_value.decode("utf-8") if isinstance(raw_value, bytes) else str(raw_value)
        result: dict[str, Any] | None
        try:
            result = json.loads(json_value)
        except JSONDecodeError:
            result = None
        return result

    async def hset(self, key: str, value: dict[str, Any], timeout: int | None = None) -> None:
        """Set value in cache for the given key with optional timeout."""
        redis_client = self._get_redis_client()
        timeout = timeout if timeout is not None else self.default_timeout
        json_str = json.dumps(value)
        # Set in Redis with or without timeout
        if timeout > 0:
            await redis_client.setex(name=key, time=timeout, value=json_str)
        else:
            await redis_client.set(name=key, value=json_str)

    async def clear(self) -> None:
        """Clear all cache entries."""
        redis_client = self._get_redis_client()

        try:
            # Simply flush the entire database
            # This is the most reliable approach across different Redis client implementations
            await redis_client.flushdb()
        except Exception as e:
            log.exception(f"Error clearing Redis cache: {e}")

    async def close(self) -> None:
        """Close the cache."""
        redis_client = self._get_redis_client()

        try:
            # Simply flush the entire database
            # This is the most reliable approach across different Redis client implementations
            await redis_client.flushdb()
        except Exception as e:
            log.exception(f"Error clearing Redis cache: {e}")


class FakeRedisCache(RedisCache):
    """Fake Redis-based cache implementation."""

    # noinspection PyMissingConstructor
    def __init__(self) -> None:
        # Initialize Fake Redis cache.
        self._client = fakeredis.FakeRedis()


class CacheManager:
    """
    Manages the application's cache system.

    This class provides a centralized way to configure, access, and clear the cache.
    It supports different cache types such as memory, filesystem, and Redis.

    Attributes:
        cache (BaseCache | None): The active cache instance. It can be None if the cache is not yet initialized.
    """

    cache: BaseCache | None = None

    @classmethod
    async def setup_cache(cls, config: Configuration) -> None:
        """
        Initializes the cache based on the provided configuration.

        The cache type is determined by the 'CACHE_TYPE' key in the config dictionary.
        Supported cache types are:
            - CacheType.MEMORY: Uses a SimpleCache for in-memory caching.
            - CacheType.FILESYSTEM: Uses a FileSystemCache for file-based caching.
            - CacheType.REDIS: Uses a RedisCache for caching in a Redis server.

        Args:
            config (Configuration): A Configuration dictionary containing the application's configuration.
                           The 'CACHE_TYPE' key is used to determine the cache type.

        Raises:
            ValueError: If an invalid 'CACHE_TYPE' is provided in the configuration.
        """

        # Based on configuration, use a different cache setup.
        cache_type = config.CACHE_TYPE
        # noinspection PyUnreachableCode
        if cache_type == CacheType.MEMORY:
            cls.cache = SimpleCache(threshold=1000000, default_timeout=0)
            # log.info("Using memory cache")

        elif cache_type == CacheType.REDIS:
            try:
                cls.cache = RedisCache(
                    username=None if config.REDIS_USERNAME == "" else config.REDIS_USERNAME,
                    password=None if config.REDIS_PASSWORD == "" else config.REDIS_PASSWORD,
                    host="localhost" if config.REDIS_HOST is None else config.REDIS_HOST,
                    port=6379 if config.REDIS_PORT is None else config.REDIS_PORT,
                    db=0,
                    default_timeout=60 * 60 * 24 * 7,
                )
                log.info("Using Redis cache")

                # Test connection
                if cls.cache is not None:
                    ping_result = await cls.cache.ping()
                    if ping_result:
                        log.info("Successfully connected to Redis server")
                    else:
                        log.info("Cannot ping Redis cache")
                else:
                    cls.cache = FakeRedisCache()
                    # Test connection
                    if cls.cache is not None:
                        ping_result = await cls.cache.ping()
                        if ping_result:
                            log.info("Successfully connected to Fake Redis cache")
                        else:
                            log.info("Cannot ping Fake Redis cache")
                    else:
                        log.info("Cannot connect to Fake Redis cache")
            except Exception as e:
                log.warning(f"Redis error: {e}. Falling back to memory cache")
                cls.cache = SimpleCache(threshold=1000000, default_timeout=0)
                log.info("Fallback to memory cache")

        else:
            raise ValueError("Invalid CACHE_TYPE in configuration")

    @classmethod
    async def clear_cache(cls) -> None:
        """
        Clears the cache.

        This method clears the cache releasing any resources held by the cache.
        """
        if cls.cache is not None:
            await cls.cache.clear()
        log.debug("Cache cleared")

    @classmethod
    async def shutdown_cache(cls) -> None:
        """
        Shuts down the cache.

        This method shuts down the cache.
        """
        if cls.cache is not None:
            await cls.cache.close()
        # log.info("Shutdown cache")

    @classmethod
    def get_cache(cls) -> BaseCache:
        """
        Returns the current cache instance.

        Returns:
            BaseCache | None: The current cache instance, or None if not initialized.
        """
        if cls.cache is None:
            raise ValueError("Invalid cache")
        return cls.cache

    @classmethod
    async def clear(cls) -> None:
        """
        Clears all data from the cache.
        """
        log.debug("Clearing cache")
        if cls.cache is not None:
            await cls.cache.clear()

    @staticmethod
    def create_cache_key(domain_name: str, id_: str, field_name: str) -> str:
        # Key is domain:id:field
        return f"{domain_name}{CACHE_KEY_SEPARATOR}{id_}{CACHE_KEY_SEPARATOR}{field_name}"

    @staticmethod
    def create_cache_hkey(domain_name: str, id_: str) -> str:
        # Key is domain:id
        return f"{domain_name}{CACHE_KEY_SEPARATOR}{id_}"
