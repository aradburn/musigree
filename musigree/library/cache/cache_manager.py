import json
import logging
from json import JSONDecodeError
from typing import Any

import redis
import fakeredis

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

    def get(self, key: str) -> str | None:
        """Get value from cache for the given key."""
        raise NotImplementedError

    def set(self, key: str, value: str, timeout: int | None = None) -> None:
        """Set value in cache for the given key with optional timeout."""
        raise NotImplementedError

    def incr(self, key: str) -> None:
        """Increment value in cache for the given key."""
        raise NotImplementedError

    def expire(self, key: str, timeout: int) -> None:
        """Set the timeout for the given key."""
        raise NotImplementedError

    def ttl(self, key: str) -> int:
        """Get the timeout for the given key."""
        raise NotImplementedError

    def hgetall(self, key: str) -> dict[str, Any] | None:
        """Get hash value from cache for the given key."""
        raise NotImplementedError

    def hset(self, key: str, value: dict[str, Any], timeout: int | None = None) -> None:
        """Set hash value in cache for the given key with optional timeout."""
        raise NotImplementedError

    def clear(self) -> None:
        """Clear all cache entries."""
        raise NotImplementedError


class SimpleCache(BaseCache):
    """Simple in-memory cache implementation."""

    def __init__(self, threshold: int = 1000000, default_timeout: int = 0):
        self.cache: dict[str, str] = {}
        self.hcache: dict[str, Any] = {}
        self.threshold = threshold
        self.default_timeout = default_timeout

    def get(self, key: str) -> str | None:
        """Get value from cache for the given key."""
        return self.cache.get(key)

    def set(self, key: str, value: str, timeout: int | None = None) -> None:
        """Set value in cache for the given key with optional timeout."""
        # In this simple implementation, we ignore timeout
        self.cache[key] = value
        # If cache exceeds threshold, clear oldest entries (not implemented)

    def incr(self, key: str) -> None:
        """Increment value in cache for the given key."""
        raise NotImplementedError

    def expire(self, key: str, timeout: int) -> None:
        """Set the timeout for the given key."""
        raise NotImplementedError

    def ttl(self, key: str) -> int:
        """Get the timeout for the given key."""
        raise NotImplementedError

    def hgetall(self, key: str) -> dict[str, Any] | None:
        """Get value from cache for the given key."""
        return self.hcache.get(key)

    def hset(self, key: str, value: dict[str, Any], timeout: int | None = None) -> None:
        """Set value in cache for the given key with optional timeout."""
        # In this simple implementation, we ignore timeout
        self.hcache[key] = value
        # If cache exceeds threshold, clear oldest entries (not implemented)

    def clear(self) -> None:
        """Clear all cache entries."""
        self.cache.clear()
        self.hcache.clear()


class RedisCache(BaseCache):
    """Redis-based cache implementation."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        password: str | None = None,
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
        self._client: redis.Redis | fakeredis.FakeRedis | None = None

        try:
            self._client = redis.Redis(
                host=host,
                port=port,
                password=password,
                db=db,
                socket_timeout=1,
            )
            # Test connection
            self._client.ping()
            log.info("Successfully connected to Redis server")
        except Exception as e:
            log.warning(f"Failed to connect to Redis server: {e}. Using FakeRedis instead.")
            self._client = fakeredis.FakeRedis()

    def _get_redis_client(self) -> Any | fakeredis.FakeRedis:
        """Get the Redis client, handles both real Redis and FakeRedis."""
        if self._client is None:
            raise RuntimeError("Redis client not initialized")
        return self._client

    def get(self, key: str) -> str | None:
        """Get value from cache for the given key."""
        redis_client = self._get_redis_client()
        raw_value = redis_client.get(key)

        # Return None if the key doesn't exist
        if raw_value is None:
            return None

        value = raw_value.decode("utf-8") if isinstance(raw_value, bytes) else str(raw_value)

        return value

    def set(self, key: str, value: str, timeout: int | None = None) -> None:
        """Set value in cache for the given key with optional timeout."""
        redis_client = self._get_redis_client()
        timeout = timeout if timeout is not None else self.default_timeout

        # Set in Redis with or without timeout
        if timeout > 0:
            redis_client.setex(name=key, time=timeout, value=value)
        else:
            redis_client.set(name=key, value=value)

    def incr(self, key: str) -> None:
        """Increment value in cache for the given key."""
        redis_client = self._get_redis_client()
        redis_client.incrby(key, 1)

    def expire(self, key: str, timeout: int) -> None:
        """Set the timeout for the given key."""
        redis_client = self._get_redis_client()
        redis_client.expire(key, timeout)

    def ttl(self, key: str) -> int:
        """Get the timeout for the given key."""
        redis_client = self._get_redis_client()
        raw_value = redis_client.ttl(key)

        # Return None if the key doesn't exist
        if raw_value is None:
            return -2

        # Type guard: ensure we have a dict (not an Awaitable)
        # Since this is a synchronous method, hgetall should return a dict
        if not isinstance(raw_value, int):
            return -2

        return int(raw_value)

    def hgetall(self, key: str) -> dict[str, Any] | None:
        """Get hash value from cache for the given key."""
        redis_client = self._get_redis_client()
        raw_value = redis_client.get(key)

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

    def hset(self, key: str, value: dict[str, Any], timeout: int | None = None) -> None:
        """Set value in cache for the given key with optional timeout."""
        redis_client = self._get_redis_client()
        timeout = timeout if timeout is not None else self.default_timeout
        json_str = json.dumps(value)
        # Set in Redis with or without timeout
        if timeout > 0:
            redis_client.setex(name=key, time=timeout, value=json_str)
        else:
            redis_client.set(name=key, value=json_str)

    def clear(self) -> None:
        """Clear all cache entries."""
        redis_client = self._get_redis_client()

        try:
            # Simply flush the entire database
            # This is the most reliable approach across different Redis client implementations
            redis_client.flushdb()
        except Exception as e:
            log.exception(f"Error clearing Redis cache: {e}")


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
    def setup_cache(cls, config: Configuration) -> None:
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
            log.info("Using memory cache")

        elif cache_type == CacheType.REDIS:
            try:
                cls.cache = RedisCache(
                    host="localhost",
                    port=6379,
                    password=None,
                    db=0,
                    default_timeout=60 * 60 * 24 * 7,
                )
                log.info("Using Redis cache")
            except Exception as e:
                log.warning(f"Redis error: {e}. Falling back to memory cache")
                cls.cache = SimpleCache(threshold=1000000, default_timeout=0)
                log.info("Fallback to memory cache")

        else:
            raise ValueError("Invalid CACHE_TYPE in configuration")

    @classmethod
    def shutdown_cache(cls) -> None:
        """
        Clears and shuts down the cache.

        This method clears the cache and sets the cache attribute to None,
        releasing any resources held by the cache.
        """
        if cls.cache is not None:
            cls.cache.clear()
        log.info("Shutdown cache")

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
    def clear(cls) -> None:
        """
        Clears all data from the cache.
        """
        log.debug("Clearing cache")
        if cls.cache is not None:
            cls.cache.clear()

    @staticmethod
    def create_cache_key(domain_name: str, id_: str, field_name: str) -> str:
        # Key is domain:id:field
        return f"{domain_name}{CACHE_KEY_SEPARATOR}{id_}{CACHE_KEY_SEPARATOR}{field_name}"

    @staticmethod
    def create_cache_hkey(domain_name: str, id_: str) -> str:
        # Key is domain:id
        return f"{domain_name}{CACHE_KEY_SEPARATOR}{id_}"
