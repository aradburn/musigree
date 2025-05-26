import logging
import os
import pickle
import tempfile
from typing import Any, Dict, Optional

# Add Redis import with error handling
try:
    # noinspection PyUnresolvedReferences
    import redis

    # noinspection PyUnresolvedReferences
    import fakeredis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from musigree.config import Configuration
from musigree.constants import CacheType

log = logging.getLogger(__name__)

__all__ = [
    "CacheManager",
]


class BaseCache:
    """Base cache class that defines the interface for all cache implementations."""

    def get(self, key: str) -> Any:
        """Get value from cache for the given key."""
        raise NotImplementedError

    def set(self, key: str, value: Any, timeout: Optional[int] = None) -> None:
        """Set value in cache for the given key with optional timeout."""
        raise NotImplementedError

    def delete(self, key: str) -> None:
        """Delete key from cache."""
        raise NotImplementedError

    def clear(self) -> None:
        """Clear all cache entries."""
        raise NotImplementedError


class SimpleCache(BaseCache):
    """Simple in-memory cache implementation."""

    def __init__(self, threshold: int = 1000000, default_timeout: int = 0):
        self.cache: Dict[str, Any] = {}
        self.threshold = threshold
        self.default_timeout = default_timeout

    def get(self, key: str) -> Any:
        """Get value from cache for the given key."""
        return self.cache.get(key)

    def set(self, key: str, value: Any, timeout: Optional[int] = None) -> None:
        """Set value in cache for the given key with optional timeout."""
        # In this simple implementation, we ignore timeout
        self.cache[key] = value
        # If cache exceeds threshold, clear oldest entries (not implemented)

    def delete(self, key: str) -> None:
        """Delete key from cache."""
        if key in self.cache:
            del self.cache[key]

    def clear(self) -> None:
        """Clear all cache entries."""
        self.cache.clear()


class FileSystemCache(BaseCache):
    """File system based cache implementation."""

    def __init__(
        self, cache_dir: str, threshold: int = 1000000, default_timeout: int = 0
    ):
        self.cache_dir = cache_dir
        self.threshold = threshold
        self.default_timeout = default_timeout
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)

    def _get_filename(self, key: str) -> str:
        """Get filename for the given key."""
        import hashlib

        hashed_key = hashlib.md5(key.encode()).hexdigest()
        return os.path.join(self.cache_dir, hashed_key)

    def get(self, key: str) -> Any:
        """Get value from cache for the given key."""
        filename = self._get_filename(key)
        if os.path.exists(filename):
            try:
                with open(filename, "rb") as f:
                    return pickle.load(f)
            except (IOError, pickle.PickleError):
                return None
        return None

    def set(self, key: str, value: Any, timeout: Optional[int] = None) -> None:
        """Set value in cache for the given key with optional timeout."""
        filename = self._get_filename(key)
        try:
            with open(filename, "wb") as f:
                # noinspection PyTypeChecker
                pickle.dump(value, f, pickle.HIGHEST_PROTOCOL)
        except (IOError, pickle.PickleError):
            pass

    def delete(self, key: str) -> None:
        """Delete key from cache."""
        filename = self._get_filename(key)
        if os.path.exists(filename):
            os.remove(filename)

    def clear(self) -> None:
        """Clear all cache entries."""
        for filename in os.listdir(self.cache_dir):
            file_path = os.path.join(self.cache_dir, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)


class RedisCache(BaseCache):
    """Redis-based cache implementation."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        password: Optional[str] = None,
        db: int = 0,
        default_timeout: int = 300,
        key_prefix: Optional[str] = None,
    ):
        """Initialize Redis cache.

        Args:
            host: Redis server hostname
            port: Redis server port
            password: Redis server password
            db: Redis database number
            default_timeout: Default cache timeout in seconds
            key_prefix: Prefix for all keys in this cache
        """
        self.default_timeout = default_timeout
        self.key_prefix = key_prefix or ""
        self._client = None

        if not REDIS_AVAILABLE:
            log.warning("Redis package not installed. Using FakeRedis instead.")
            self._client = fakeredis.FakeRedis()
            return

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
            log.warning(
                f"Failed to connect to Redis server: {e}. Using FakeRedis instead."
            )
            self._client = fakeredis.FakeRedis()

    def _get_redis_client(self):
        """Get the Redis client, handles both real Redis and FakeRedis."""
        if self._client is None:
            raise RuntimeError("Redis client not initialized")
        return self._client

    def _make_key(self, key: str) -> str:
        """Add prefix to key."""
        return f"{self.key_prefix}{key}"

    def get(self, key: str) -> Any:
        """Get value from cache for the given key."""
        redis_client = self._get_redis_client()
        key = self._make_key(key)

        try:
            # Get the value from Redis
            value = redis_client.get(key)

            # Return None if the key doesn't exist
            if value is None:
                return None

            # Convert to bytes if necessary (handles different Redis client implementations)
            if not isinstance(value, bytes):
                # This case should not happen but we handle it anyway
                log.warning(f"Unexpected non-bytes value from Redis for key {key}")
                return None

            # Unpickle the value
            return pickle.loads(value)
        except Exception as e:
            log.exception(f"Error getting key {key} from Redis cache: {e}")
            return None

    def set(self, key: str, value: Any, timeout: Optional[int] = None) -> None:
        """Set value in cache for the given key with optional timeout."""
        redis_client = self._get_redis_client()
        key = self._make_key(key)
        timeout = timeout if timeout is not None else self.default_timeout

        try:
            # Pickle the value
            value_bytes = pickle.dumps(value, pickle.HIGHEST_PROTOCOL)

            # Set in Redis with or without timeout
            if timeout > 0:
                redis_client.setex(name=key, time=timeout, value=value_bytes)
            else:
                redis_client.set(name=key, value=value_bytes)
        except Exception as e:
            log.exception(f"Error setting key {key} in Redis cache: {e}")

    def delete(self, key: str) -> None:
        """Delete key from cache."""
        redis_client = self._get_redis_client()
        key = self._make_key(key)

        try:
            redis_client.delete(key)
        except Exception as e:
            log.exception(f"Error deleting key {key} from Redis cache: {e}")

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

    cache: Optional[BaseCache] = None

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
        cls.cache = None

        # Based on configuration, use a different cache setup.
        cache_type = config.CACHE_TYPE
        if cache_type == CacheType.MEMORY:
            cls.cache = SimpleCache(threshold=1000000, default_timeout=0)
            log.info("Using memory cache")

        elif cache_type == CacheType.FILESYSTEM:
            file_cache_path = os.path.join(tempfile.gettempdir(), "musigree", "cache")
            file_cache_threshold = 1024 * 1024 * 20
            file_cache_timeout = 60 * 60 * 24 * 7
            if not os.path.exists(file_cache_path):
                os.makedirs(file_cache_path)
            cls.cache = FileSystemCache(
                file_cache_path,
                default_timeout=file_cache_timeout,
                threshold=file_cache_threshold,
            )
            log.info("Using filesystem cache")

        elif cache_type == CacheType.REDIS:
            try:
                cls.cache = RedisCache(
                    host="localhost",
                    port=6379,
                    password=None,
                    db=0,
                    default_timeout=60 * 60 * 24 * 7,
                    key_prefix="musigree:",
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
        cls.cache = None
        log.info("Shutdown cache")

    @classmethod
    def get_cache(cls) -> Optional[BaseCache]:
        """
        Returns the current cache instance.

        Returns:
            Optional[BaseCache]: The current cache instance, or None if not initialized.
        """
        return cls.cache

    @classmethod
    def clear(cls) -> None:
        """
        Clears all data from the cache.
        """
        log.debug("Clearing cache")
        if cls.cache is not None:
            cls.cache.clear()
