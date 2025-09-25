import os
import shutil
import tempfile
from typing import Generator, cast
from unittest.mock import MagicMock, patch

import pytest

from musigree.constants import CacheType
from musigree.library.cache.cache_manager import (
    BaseCache,
    CacheManager,
    FileSystemCache,
    RedisCache,
    SimpleCache,
)


class TestBaseCache:
    """Test cases for the BaseCache interface."""

    def test_base_cache_methods_not_implemented(self) -> None:
        """Test that BaseCache methods raise NotImplementedError."""
        cache = BaseCache()

        with pytest.raises(NotImplementedError):
            cache.get("key")

        with pytest.raises(NotImplementedError):
            cache.set("key", "value")

        with pytest.raises(NotImplementedError):
            cache.delete("key")

        with pytest.raises(NotImplementedError):
            cache.clear()


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

    def test_simple_cache_set_and_get(self) -> None:
        """Test setting and getting values in SimpleCache."""
        self.cache.set("key1", "value1")
        assert self.cache.get("key1") == "value1"

    def test_simple_cache_get_nonexistent(self) -> None:
        """Test getting non-existent key returns None."""
        assert self.cache.get("nonexistent") is None

    def test_simple_cache_delete(self) -> None:
        """Test deleting keys from SimpleCache."""
        self.cache.set("key1", "value1")
        self.cache.delete("key1")
        assert self.cache.get("key1") is None

    def test_simple_cache_delete_nonexistent(self) -> None:
        """Test deleting non-existent key doesn't raise error."""
        # Should not raise an exception
        self.cache.delete("nonexistent")

    def test_simple_cache_clear(self) -> None:
        """Test clearing all entries from SimpleCache."""
        self.cache.set("key1", "value1")
        self.cache.set("key2", "value2")
        self.cache.clear()
        assert self.cache.get("key1") is None
        assert self.cache.get("key2") is None
        assert self.cache.cache == {}

    def test_simple_cache_timeout_ignored(self) -> None:
        """Test that timeout parameter is ignored in SimpleCache."""
        self.cache.set("key1", "value1", timeout=60)
        assert self.cache.get("key1") == "value1"


class TestFileSystemCache:
    """Test cases for the FileSystemCache implementation."""

    @pytest.fixture(autouse=True)
    def setup_cache(self) -> Generator[None, None, None]:
        """Set up test fixtures with temporary directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.cache = FileSystemCache(self.temp_dir)
        yield
        # Clean up the temporary directory
        shutil.rmtree(self.temp_dir)

    def test_filesystem_cache_initialization(self) -> None:
        """Test FileSystemCache initialization."""
        assert self.cache.cache_dir == self.temp_dir
        assert self.cache.threshold == 1000000
        assert self.cache.default_timeout == 0
        assert os.path.exists(self.temp_dir)

    def test_filesystem_cache_initialization_with_params(self) -> None:
        """Test FileSystemCache initialization with custom parameters."""
        temp_dir2 = tempfile.mkdtemp()
        try:
            cache = FileSystemCache(temp_dir2, threshold=500, default_timeout=60)
            assert cache.threshold == 500
            assert cache.default_timeout == 60
        finally:
            shutil.rmtree(temp_dir2)

    def test_filesystem_cache_creates_directory(self) -> None:
        """Test that FileSystemCache creates directory if it doesn't exist."""
        new_dir = os.path.join(self.temp_dir, "new_cache_dir")
        assert not os.path.exists(new_dir)

        _cache = FileSystemCache(new_dir)
        assert os.path.exists(new_dir)

    def test_filesystem_cache_set_and_get(self) -> None:
        """Test setting and getting values in FileSystemCache."""
        self.cache.set("key1", "value1")
        assert self.cache.get("key1") == "value1"

    def test_filesystem_cache_get_nonexistent(self) -> None:
        """Test getting non-existent key returns None."""
        assert self.cache.get("nonexistent") is None

    def test_filesystem_cache_delete(self) -> None:
        """Test deleting keys from FileSystemCache."""
        self.cache.set("key1", "value1")
        self.cache.delete("key1")
        assert self.cache.get("key1") is None

    def test_filesystem_cache_delete_nonexistent(self) -> None:
        """Test deleting non-existent key doesn't raise error."""
        # Should not raise an exception
        self.cache.delete("nonexistent")

    def test_filesystem_cache_clear(self) -> None:
        """Test clearing all entries from FileSystemCache."""
        self.cache.set("key1", "value1")
        self.cache.set("key2", "value2")
        self.cache.clear()
        assert self.cache.get("key1") is None
        assert self.cache.get("key2") is None

    def test_filesystem_cache_get_filename(self) -> None:
        """Test that _get_filename produces consistent filenames."""
        filename1 = self.cache._get_filename("key1")
        filename2 = self.cache._get_filename("key1")
        assert filename1 == filename2

        # Different keys should produce different filenames
        filename3 = self.cache._get_filename("key2")
        assert filename1 != filename3

    @patch("builtins.open", side_effect=IOError())
    def test_filesystem_cache_io_error_on_set(self, _mock_open: MagicMock) -> None:
        """Test that IOError on set doesn't raise exception."""
        # Should not raise an exception
        self.cache.set("key1", "value1")

    @patch("builtins.open", side_effect=IOError())
    def test_filesystem_cache_io_error_on_get(self, _mock_open: MagicMock) -> None:
        """Test that IOError on get returns None."""
        # Create a file first
        with patch("os.path.exists", return_value=True):
            result = self.cache.get("key1")
            assert result is None


class TestRedisCache:
    """Test cases for the RedisCache implementation."""

    @patch("musigree.library.cache.cache_manager.REDIS_AVAILABLE", False)
    def test_redis_cache_no_redis_available(self) -> None:
        """Test RedisCache when Redis is not available."""
        with patch("musigree.library.cache.cache_manager.fakeredis") as mock_fakeredis:
            mock_fake_client = MagicMock()
            mock_fakeredis.FakeRedis.return_value = mock_fake_client

            cache = RedisCache()
            assert cache._client == mock_fake_client

    @patch("musigree.library.cache.cache_manager.REDIS_AVAILABLE", True)
    @patch("musigree.library.cache.cache_manager.redis")
    def test_redis_cache_successful_connection(self, mock_redis: MagicMock) -> None:
        """Test RedisCache with successful Redis connection."""
        mock_client = MagicMock()
        mock_redis.Redis.return_value = mock_client
        mock_client.ping.return_value = True

        cache = RedisCache()
        assert cache._client == mock_client
        mock_client.ping.assert_called_once()

    @patch("musigree.library.cache.cache_manager.REDIS_AVAILABLE", True)
    @patch("musigree.library.cache.cache_manager.redis")
    @patch("musigree.library.cache.cache_manager.fakeredis")
    def test_redis_cache_connection_failure(
        self, mock_fakeredis: MagicMock, mock_redis: MagicMock
    ) -> None:
        """Test RedisCache falls back to FakeRedis on connection failure."""
        mock_redis.Redis.side_effect = Exception("Connection failed")
        mock_fake_client = MagicMock()
        mock_fakeredis.FakeRedis.return_value = mock_fake_client

        cache = RedisCache()
        assert cache._client == mock_fake_client

    @pytest.mark.skip("Skipping RedisCache tests that require a real Redis server.")
    def test_redis_cache_initialization_params(self) -> None:
        """Test RedisCache initialization parameters."""
        with patch("musigree.library.cache.cache_manager.fakeredis"):
            cache = RedisCache(
                host="example.com",
                port=6380,
                password="secret",
                db=1,
                default_timeout=600,
                key_prefix="test:",
            )
            assert cache.default_timeout == 600
            assert cache.key_prefix == "test:"

    def test_redis_cache_make_key(self) -> None:
        """Test key prefixing in RedisCache."""
        with patch("musigree.library.cache.cache_manager.fakeredis"):
            cache = RedisCache(key_prefix="app:")
            assert cache._make_key("key1") == "app:key1"

    def test_redis_cache_make_key_no_prefix(self) -> None:
        """Test key handling without prefix."""
        with patch("musigree.library.cache.cache_manager.fakeredis"):
            cache = RedisCache()
            assert cache._make_key("key1") == "key1"


class TestCacheManager:
    """Test cases for the CacheManager class."""

    @pytest.fixture(autouse=True)
    def cleanup_cache(self) -> Generator[None, None, None]:
        """Clean up after each test."""
        yield
        # Reset the cache manager
        if hasattr(CacheManager, "cache"):
            CacheManager.shutdown_cache()

    @patch("musigree.library.cache.cache_manager.SimpleCache")
    def test_cache_manager_setup_simple_cache(
        self, mock_simple_cache: MagicMock
    ) -> None:
        """Test CacheManager setup with simple cache."""
        config = MagicMock()
        config.CACHE_TYPE = CacheType.MEMORY

        mock_cache_instance = MagicMock()
        mock_simple_cache.return_value = mock_cache_instance

        CacheManager.setup_cache(config)

        mock_simple_cache.assert_called_once_with(threshold=1000000, default_timeout=0)
        assert CacheManager.cache == mock_cache_instance

    @patch("musigree.library.cache.cache_manager.FileSystemCache")
    @patch("musigree.library.cache.cache_manager.os.path.exists")
    @patch("musigree.library.cache.cache_manager.os.makedirs")
    def test_cache_manager_setup_filesystem_cache(
        self, mock_makedirs: MagicMock, mock_exists: MagicMock, mock_fs_cache: MagicMock
    ) -> None:
        """Test CacheManager setup with filesystem cache."""
        config = MagicMock()
        config.CACHE_TYPE = CacheType.FILESYSTEM

        mock_cache_instance = MagicMock()
        mock_fs_cache.return_value = mock_cache_instance
        mock_exists.return_value = False

        CacheManager.setup_cache(config)

        mock_makedirs.assert_called_once()
        mock_fs_cache.assert_called_once()
        assert CacheManager.cache == mock_cache_instance

    @patch("musigree.library.cache.cache_manager.RedisCache")
    def test_cache_manager_setup_redis_cache(self, mock_redis_cache: MagicMock) -> None:
        """Test CacheManager setup with Redis cache."""
        config = MagicMock()
        config.CACHE_TYPE = CacheType.REDIS

        mock_cache_instance = MagicMock()
        mock_redis_cache.return_value = mock_cache_instance

        CacheManager.setup_cache(config)

        mock_redis_cache.assert_called_once_with(
            host="localhost",
            port=6379,
            password=None,
            db=0,
            default_timeout=60 * 60 * 24 * 7,
            key_prefix="musigree:",
        )
        assert CacheManager.cache == mock_cache_instance

    def test_cache_manager_shutdown_cache(self) -> None:
        """Test CacheManager cache shutdown."""
        # Set up a cache first
        mock_cache = MagicMock()
        CacheManager.cache = mock_cache

        CacheManager.shutdown_cache()

        mock_cache.clear.assert_called_once()
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
        if hasattr(CacheManager, "cache"):
            delattr(CacheManager, "cache")

        with pytest.raises(AttributeError):
            CacheManager.get_cache()

    def test_cache_manager_clear(self) -> None:
        """Test CacheManager clear method."""
        mock_cache = MagicMock()
        CacheManager.cache = mock_cache

        CacheManager.clear()

        mock_cache.clear.assert_called_once()


class TestRedisCacheMethods:
    """Test cases for RedisCache methods that need more coverage."""

    @pytest.fixture
    def redis_cache(self) -> RedisCache:
        """Create a RedisCache instance for testing."""
        with patch("musigree.library.cache.cache_manager.REDIS_AVAILABLE", False):
            with patch("musigree.library.cache.cache_manager.fakeredis") as mock_fakeredis:
                mock_fake_client = MagicMock()
                mock_fakeredis.FakeRedis.return_value = mock_fake_client
                cache = RedisCache()
                # Override the _client attribute with our mock for testing
                cache._client = mock_fake_client
                return cache

    def test_get_redis_client_not_initialized(self) -> None:
        """Test _get_redis_client when client is None."""
        cache = RedisCache.__new__(RedisCache)  # Create without calling __init__
        cache._client = None

        with pytest.raises(RuntimeError, match="Redis client not initialized"):
            cache._get_redis_client()

    def test_make_key(self, redis_cache: RedisCache) -> None:
        """Test _make_key method."""
        result = redis_cache._make_key("test_key")
        assert result == f"{redis_cache.key_prefix}test_key"

    def test_get_value_not_found(self, redis_cache: RedisCache) -> None:
        """Test get method when key doesn't exist."""
        mock_client = cast(MagicMock, redis_cache._client)
        mock_client.get.return_value = None

        result = redis_cache.get("nonexistent_key")

        assert result is None
        mock_client.get.assert_called_once()

    def test_get_value_non_bytes(self, redis_cache: RedisCache) -> None:
        """Test get method when Redis returns non-bytes value."""
        mock_client = cast(MagicMock, redis_cache._client)
        mock_client.get.return_value = "string_value"  # Not bytes

        result = redis_cache.get("test_key")

        assert result is None

    def test_get_value_pickle_error(self, redis_cache: RedisCache) -> None:
        """Test get method when pickle.loads raises exception."""
        mock_client = cast(MagicMock, redis_cache._client)
        mock_client.get.return_value = b"invalid_pickle_data"

        with patch("pickle.loads", side_effect=Exception("Pickle error")):
            result = redis_cache.get("test_key")

        assert result is None

    def test_get_redis_client_exception(self, redis_cache: RedisCache) -> None:
        """Test get method when Redis client raises exception."""
        mock_client = cast(MagicMock, redis_cache._client)
        mock_client.get.side_effect = Exception("Redis error")

        result = redis_cache.get("test_key")

        assert result is None

    def test_set_with_timeout(self, redis_cache: RedisCache) -> None:
        """Test set method with custom timeout."""
        redis_cache.set("test_key", "test_value", timeout=3600)

        mock_client = cast(MagicMock, redis_cache._client)
        mock_client.setex.assert_called_once()
        call_args = mock_client.setex.call_args
        assert call_args[1]["name"] == f"{redis_cache.key_prefix}test_key"
        assert call_args[1]["time"] == 3600

    def test_set_without_timeout(self, redis_cache: RedisCache) -> None:
        """Test set method without timeout."""
        redis_cache.default_timeout = 0
        redis_cache.set("test_key", "test_value")

        mock_client = cast(MagicMock, redis_cache._client)
        mock_client.set.assert_called_once()

    def test_set_with_exception(self, redis_cache: RedisCache) -> None:
        """Test set method when Redis client raises exception."""
        mock_client = cast(MagicMock, redis_cache._client)
        mock_client.setex.side_effect = Exception("Redis error")

        # Should not raise exception
        redis_cache.set("test_key", "test_value", timeout=3600)

    def test_delete_success(self, redis_cache: RedisCache) -> None:
        """Test delete method success."""
        redis_cache.delete("test_key")

        mock_client = cast(MagicMock, redis_cache._client)
        mock_client.delete.assert_called_once_with(f"{redis_cache.key_prefix}test_key")

    def test_delete_with_exception(self, redis_cache: RedisCache) -> None:
        """Test delete method when Redis client raises exception."""
        mock_client = cast(MagicMock, redis_cache._client)
        mock_client.delete.side_effect = Exception("Redis error")

        # Should not raise exception
        redis_cache.delete("test_key")

    def test_clear_success(self, redis_cache: RedisCache) -> None:
        """Test clear method success."""
        redis_cache.clear()

        mock_client = cast(MagicMock, redis_cache._client)
        mock_client.flushdb.assert_called_once()

    def test_clear_with_exception(self, redis_cache: RedisCache) -> None:
        """Test clear method when Redis client raises exception."""
        mock_client = cast(MagicMock, redis_cache._client)
        mock_client.flushdb.side_effect = Exception("Redis error")

        # Should not raise exception
        redis_cache.clear()

    @patch("musigree.library.cache.cache_manager.REDIS_AVAILABLE", True)
    @patch("musigree.library.cache.cache_manager.redis")
    @patch("musigree.library.cache.cache_manager.fakeredis")
    def test_redis_cache_ping_failure(
        self, mock_fakeredis: MagicMock, mock_redis: MagicMock
    ) -> None:
        """Test RedisCache when ping() fails after successful connection."""
        mock_client = MagicMock()
        mock_redis.Redis.return_value = mock_client
        mock_client.ping.side_effect = Exception("Ping failed")
        
        mock_fake_client = MagicMock()
        mock_fakeredis.FakeRedis.return_value = mock_fake_client

        cache = RedisCache()
        assert cache._client == mock_fake_client


class TestCacheManagerUncoveredMethods:
    """Test cases for CacheManager methods that need more coverage."""

    @pytest.fixture(autouse=True)
    def cleanup_cache(self) -> Generator[None, None, None]:
        """Clean up after each test."""
        yield
        # Reset the cache manager
        if hasattr(CacheManager, "cache"):
            CacheManager.shutdown_cache()

    def test_setup_cache_invalid_type(self) -> None:
        """Test CacheManager setup_cache with invalid cache type."""
        config = MagicMock()
        config.CACHE_TYPE = "invalid_type"

        with pytest.raises(ValueError, match="Invalid CACHE_TYPE in configuration"):
            CacheManager.setup_cache(config)

    @patch("musigree.library.cache.cache_manager.FileSystemCache")
    @patch("musigree.library.cache.cache_manager.os.path.exists")
    @patch("musigree.library.cache.cache_manager.os.makedirs")
    def test_cache_manager_setup_filesystem_cache_directory_exists(
        self, mock_makedirs: MagicMock, mock_exists: MagicMock, mock_fs_cache: MagicMock
    ) -> None:
        """Test CacheManager setup with filesystem cache when directory already exists."""
        config = MagicMock()
        config.CACHE_TYPE = CacheType.FILESYSTEM

        mock_cache_instance = MagicMock()
        mock_fs_cache.return_value = mock_cache_instance
        mock_exists.return_value = True  # Directory already exists

        CacheManager.setup_cache(config)

        mock_makedirs.assert_not_called()  # Should not create directory
        mock_fs_cache.assert_called_once()
        assert CacheManager.cache == mock_cache_instance

    def test_cache_manager_clear_no_cache(self) -> None:
        """Test CacheManager clear when no cache is set."""
        # Ensure cache is not set
        if hasattr(CacheManager, "cache"):
            delattr(CacheManager, "cache")

        with pytest.raises(AttributeError):
            CacheManager.clear()


# Note: pytest automatically discovers and runs tests, so no main block is needed
