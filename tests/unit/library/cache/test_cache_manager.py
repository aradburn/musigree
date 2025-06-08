import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from musigree.library.cache.cache_manager import (
    BaseCache,
    SimpleCache,
    FileSystemCache,
    RedisCache,
    CacheManager,
)
from musigree.config import Configuration
from musigree.constants import CacheType


class TestBaseCache(unittest.TestCase):
    """Test cases for the BaseCache interface."""

    def test_base_cache_methods_not_implemented(self):
        """Test that BaseCache methods raise NotImplementedError."""
        cache = BaseCache()
        
        with self.assertRaises(NotImplementedError):
            cache.get("key")
        
        with self.assertRaises(NotImplementedError):
            cache.set("key", "value")
        
        with self.assertRaises(NotImplementedError):
            cache.delete("key")
        
        with self.assertRaises(NotImplementedError):
            cache.clear()


class TestSimpleCache(unittest.TestCase):
    """Test cases for the SimpleCache implementation."""

    def setUp(self):
        """Set up test fixtures."""
        self.cache = SimpleCache()

    def test_simple_cache_initialization(self):
        """Test SimpleCache initialization with default parameters."""
        cache = SimpleCache()
        self.assertEqual({}, cache.cache)
        self.assertEqual(1000000, cache.threshold)
        self.assertEqual(0, cache.default_timeout)

    def test_simple_cache_initialization_with_params(self):
        """Test SimpleCache initialization with custom parameters."""
        cache = SimpleCache(threshold=500, default_timeout=60)
        self.assertEqual(500, cache.threshold)
        self.assertEqual(60, cache.default_timeout)

    def test_simple_cache_set_and_get(self):
        """Test setting and getting values in SimpleCache."""
        self.cache.set("key1", "value1")
        self.assertEqual("value1", self.cache.get("key1"))

    def test_simple_cache_get_nonexistent(self):
        """Test getting non-existent key returns None."""
        self.assertIsNone(self.cache.get("nonexistent"))

    def test_simple_cache_delete(self):
        """Test deleting keys from SimpleCache."""
        self.cache.set("key1", "value1")
        self.cache.delete("key1")
        self.assertIsNone(self.cache.get("key1"))

    def test_simple_cache_delete_nonexistent(self):
        """Test deleting non-existent key doesn't raise error."""
        # Should not raise an exception
        self.cache.delete("nonexistent")

    def test_simple_cache_clear(self):
        """Test clearing all entries from SimpleCache."""
        self.cache.set("key1", "value1")
        self.cache.set("key2", "value2")
        self.cache.clear()
        self.assertIsNone(self.cache.get("key1"))
        self.assertIsNone(self.cache.get("key2"))
        self.assertEqual({}, self.cache.cache)

    def test_simple_cache_timeout_ignored(self):
        """Test that timeout parameter is ignored in SimpleCache."""
        self.cache.set("key1", "value1", timeout=60)
        self.assertEqual("value1", self.cache.get("key1"))


class TestFileSystemCache(unittest.TestCase):
    """Test cases for the FileSystemCache implementation."""

    def setUp(self):
        """Set up test fixtures with temporary directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.cache = FileSystemCache(self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up the temporary directory
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_filesystem_cache_initialization(self):
        """Test FileSystemCache initialization."""
        self.assertEqual(self.temp_dir, self.cache.cache_dir)
        self.assertEqual(1000000, self.cache.threshold)
        self.assertEqual(0, self.cache.default_timeout)
        self.assertTrue(os.path.exists(self.temp_dir))

    def test_filesystem_cache_initialization_with_params(self):
        """Test FileSystemCache initialization with custom parameters."""
        temp_dir2 = tempfile.mkdtemp()
        try:
            cache = FileSystemCache(temp_dir2, threshold=500, default_timeout=60)
            self.assertEqual(500, cache.threshold)
            self.assertEqual(60, cache.default_timeout)
        finally:
            import shutil
            shutil.rmtree(temp_dir2)

    def test_filesystem_cache_creates_directory(self):
        """Test that FileSystemCache creates directory if it doesn't exist."""
        new_dir = os.path.join(self.temp_dir, "new_cache_dir")
        self.assertFalse(os.path.exists(new_dir))
        
        cache = FileSystemCache(new_dir)
        self.assertTrue(os.path.exists(new_dir))

    def test_filesystem_cache_set_and_get(self):
        """Test setting and getting values in FileSystemCache."""
        self.cache.set("key1", "value1")
        self.assertEqual("value1", self.cache.get("key1"))

    def test_filesystem_cache_get_nonexistent(self):
        """Test getting non-existent key returns None."""
        self.assertIsNone(self.cache.get("nonexistent"))

    def test_filesystem_cache_delete(self):
        """Test deleting keys from FileSystemCache."""
        self.cache.set("key1", "value1")
        self.cache.delete("key1")
        self.assertIsNone(self.cache.get("key1"))

    def test_filesystem_cache_delete_nonexistent(self):
        """Test deleting non-existent key doesn't raise error."""
        # Should not raise an exception
        self.cache.delete("nonexistent")

    def test_filesystem_cache_clear(self):
        """Test clearing all entries from FileSystemCache."""
        self.cache.set("key1", "value1")
        self.cache.set("key2", "value2")
        self.cache.clear()
        self.assertIsNone(self.cache.get("key1"))
        self.assertIsNone(self.cache.get("key2"))

    def test_filesystem_cache_get_filename(self):
        """Test that _get_filename produces consistent filenames."""
        filename1 = self.cache._get_filename("key1")
        filename2 = self.cache._get_filename("key1")
        self.assertEqual(filename1, filename2)
        
        # Different keys should produce different filenames
        filename3 = self.cache._get_filename("key2")
        self.assertNotEqual(filename1, filename3)

    @patch('builtins.open', side_effect=IOError())
    def test_filesystem_cache_io_error_on_set(self, mock_open):
        """Test that IOError on set doesn't raise exception."""
        # Should not raise an exception
        self.cache.set("key1", "value1")

    @patch('builtins.open', side_effect=IOError())
    def test_filesystem_cache_io_error_on_get(self, mock_open):
        """Test that IOError on get returns None."""
        # Create a file first
        with patch('os.path.exists', return_value=True):
            result = self.cache.get("key1")
            self.assertIsNone(result)


class TestRedisCache(unittest.TestCase):
    """Test cases for the RedisCache implementation."""

    @patch('musigree.library.cache.cache_manager.REDIS_AVAILABLE', False)
    def test_redis_cache_no_redis_available(self):
        """Test RedisCache when Redis is not available."""
        with patch('musigree.library.cache.cache_manager.fakeredis') as mock_fakeredis:
            mock_fake_client = MagicMock()
            mock_fakeredis.FakeRedis.return_value = mock_fake_client
            
            cache = RedisCache()
            self.assertEqual(mock_fake_client, cache._client)

    @patch('musigree.library.cache.cache_manager.REDIS_AVAILABLE', True)
    @patch('musigree.library.cache.cache_manager.redis')
    def test_redis_cache_successful_connection(self, mock_redis):
        """Test RedisCache with successful Redis connection."""
        mock_client = MagicMock()
        mock_redis.Redis.return_value = mock_client
        mock_client.ping.return_value = True
        
        cache = RedisCache()
        self.assertEqual(mock_client, cache._client)
        mock_client.ping.assert_called_once()

    @patch('musigree.library.cache.cache_manager.REDIS_AVAILABLE', True)
    @patch('musigree.library.cache.cache_manager.redis')
    @patch('musigree.library.cache.cache_manager.fakeredis')
    def test_redis_cache_connection_failure(self, mock_fakeredis, mock_redis):
        """Test RedisCache falls back to FakeRedis on connection failure."""
        mock_redis.Redis.side_effect = Exception("Connection failed")
        mock_fake_client = MagicMock()
        mock_fakeredis.FakeRedis.return_value = mock_fake_client
        
        cache = RedisCache()
        self.assertEqual(mock_fake_client, cache._client)

    def test_redis_cache_initialization_params(self):
        """Test RedisCache initialization parameters."""
        with patch('musigree.library.cache.cache_manager.fakeredis'):
            cache = RedisCache(
                host="example.com",
                port=6380,
                password="secret",
                db=1,
                default_timeout=600,
                key_prefix="test:",
            )
            self.assertEqual(600, cache.default_timeout)
            self.assertEqual("test:", cache.key_prefix)

    def test_redis_cache_make_key(self):
        """Test key prefixing in RedisCache."""
        with patch('musigree.library.cache.cache_manager.fakeredis'):
            cache = RedisCache(key_prefix="app:")
            self.assertEqual("app:key1", cache._make_key("key1"))

    def test_redis_cache_make_key_no_prefix(self):
        """Test key handling without prefix."""
        with patch('musigree.library.cache.cache_manager.fakeredis'):
            cache = RedisCache()
            self.assertEqual("key1", cache._make_key("key1"))


class TestCacheManager(unittest.TestCase):
    """Test cases for the CacheManager class."""

    def tearDown(self):
        """Clean up after each test."""
        # Reset the cache manager
        if hasattr(CacheManager, 'cache'):
            CacheManager.shutdown_cache()

    @patch('musigree.library.cache.cache_manager.SimpleCache')
    def test_cache_manager_setup_simple_cache(self, mock_simple_cache):
        """Test CacheManager setup with simple cache."""
        config = MagicMock()
        config.CACHE_TYPE = CacheType.MEMORY

        mock_cache_instance = MagicMock()
        mock_simple_cache.return_value = mock_cache_instance

        CacheManager.setup_cache(config)

        mock_simple_cache.assert_called_once_with(threshold=1000000, default_timeout=0)
        self.assertEqual(mock_cache_instance, CacheManager.cache)

    @patch('musigree.library.cache.cache_manager.FileSystemCache')
    @patch('musigree.library.cache.cache_manager.os.path.exists')
    @patch('musigree.library.cache.cache_manager.os.makedirs')
    def test_cache_manager_setup_filesystem_cache(self, mock_makedirs, mock_exists, mock_fs_cache):
        """Test CacheManager setup with filesystem cache."""
        config = MagicMock()
        config.CACHE_TYPE = CacheType.FILESYSTEM

        mock_cache_instance = MagicMock()
        mock_fs_cache.return_value = mock_cache_instance
        mock_exists.return_value = False

        CacheManager.setup_cache(config)

        mock_makedirs.assert_called_once()
        mock_fs_cache.assert_called_once()
        self.assertEqual(mock_cache_instance, CacheManager.cache)

    @patch('musigree.library.cache.cache_manager.RedisCache')
    def test_cache_manager_setup_redis_cache(self, mock_redis_cache):
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
        self.assertEqual(mock_cache_instance, CacheManager.cache)

    def test_cache_manager_shutdown_cache(self):
        """Test CacheManager cache shutdown."""
        # Set up a cache first
        mock_cache = MagicMock()
        CacheManager.cache = mock_cache

        CacheManager.shutdown_cache()

        mock_cache.clear.assert_called_once()
        # Note: The current implementation doesn't delete the cache attribute

    def test_cache_manager_get_cache_when_set(self):
        """Test CacheManager get_cache returns cache when set."""
        mock_cache = MagicMock()
        CacheManager.cache = mock_cache

        result = CacheManager.get_cache()

        self.assertEqual(mock_cache, result)

    def test_cache_manager_get_cache_when_not_set(self):
        """Test CacheManager get_cache raises error when cache not set."""
        # Ensure cache is not set
        if hasattr(CacheManager, 'cache'):
            delattr(CacheManager, 'cache')

        with self.assertRaises(AttributeError):
            CacheManager.get_cache()

    def test_cache_manager_clear(self):
        """Test CacheManager clear method."""
        mock_cache = MagicMock()
        CacheManager.cache = mock_cache

        CacheManager.clear()

        mock_cache.clear.assert_called_once()


if __name__ == "__main__":
    unittest.main() 