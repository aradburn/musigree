import pytest

from musigree.config import (
    SqliteTestConfiguration,
    SqliteDevelopmentConfiguration,
    PostgresDevelopmentConfiguration,
)
from musigree.constants import CACHE_ENTRY_IS_NULL, CACHE_KEY_SEPARATOR
from musigree.library.cache.cache_manager import CacheManager
from musigree.logging_config import setup_logging, shutdown_logging


class TestCache:
    @classmethod
    def setup_class(cls) -> None:
        setup_logging(is_testing=True)

    @classmethod
    def teardown_class(cls) -> None:
        shutdown_logging()

    def test_01(self) -> None:
        CacheManager.setup_cache(SqliteTestConfiguration())

        cache = CacheManager.get_cache()

        assert cache is not None
        CacheManager.shutdown_cache()

    def test_02(self) -> None:
        cache_key = "test_key"
        CacheManager.setup_cache(SqliteTestConfiguration())

        cache = CacheManager.get_cache()

        assert cache is not None
        data = {
            "aaa": 111,
            "bbb": "222",
            "ccc": [333, 444],
        }
        cache.hset(cache_key, data)
        actual = cache.hgetall(cache_key)
        expected = data
        assert actual == expected

    def test_03(self) -> None:
        cache_key = "test_key"
        CacheManager.setup_cache(SqliteTestConfiguration())

        cache = CacheManager.get_cache()

        assert cache is not None
        data = {
            "aaa": 111,
            "bbb": "222",
            "ccc": [333, 444],
        }
        cache.hset(cache_key, data)
        actual = cache.hgetall(cache_key)
        expected = data
        assert actual == expected

        data = {
            "xxx": 111,
            "yyy": "222",
            "zzz": [333, 444],
        }
        cache.hset(cache_key, data)
        actual = cache.hgetall(cache_key)
        expected = data
        assert actual == expected

    def test_04(self) -> None:
        CacheManager.setup_cache(SqliteDevelopmentConfiguration())

        cache = CacheManager.get_cache()

        assert cache is not None
        CacheManager.shutdown_cache()

    def test_05(self) -> None:
        cache_key = "test_key"
        CacheManager.setup_cache(SqliteDevelopmentConfiguration())

        cache = CacheManager.get_cache()

        assert cache is not None
        data = {
            "aaa": 111,
            "bbb": "222",
            "ccc": [333, 444],
        }
        cache.hset(cache_key, data)
        actual = cache.hgetall(cache_key)
        expected = data
        assert actual == expected

    def test_06(self) -> None:
        cache_key = "test_key"
        CacheManager.setup_cache(SqliteDevelopmentConfiguration())

        cache = CacheManager.get_cache()

        assert cache is not None
        data = {
            "aaa": 111,
            "bbb": "222",
            "ccc": [333, 444],
        }
        cache.hset(cache_key, data)
        actual = cache.hgetall(cache_key)
        expected = data
        assert actual == expected

    def test_07(self) -> None:
        cache_key = "test_key"
        CacheManager.setup_cache(SqliteTestConfiguration())

        cache = CacheManager.get_cache()

        assert cache is not None

        cache.set(cache_key, "TEST")
        actual = cache.get(cache_key)
        expected = "TEST"
        assert actual == expected

        cache.set(cache_key, "TEST UPDATED")
        actual = cache.get(cache_key)
        expected = "TEST UPDATED"
        assert actual == expected

    def test_08(self) -> None:
        cache_key = "test_key"
        CacheManager.setup_cache(SqliteTestConfiguration())

        cache = CacheManager.get_cache()

        assert cache is not None

        cache.set(cache_key, CACHE_ENTRY_IS_NULL)
        actual = cache.get(cache_key)
        expected = CACHE_ENTRY_IS_NULL
        assert actual == expected

    def test_postgres_01(self) -> None:
        CacheManager.setup_cache(PostgresDevelopmentConfiguration())

        cache = CacheManager.get_cache()

        assert cache is not None
        CacheManager.shutdown_cache()

    def test_postgres_02(self) -> None:
        cache_key = "test_key"
        CacheManager.setup_cache(PostgresDevelopmentConfiguration())

        cache = CacheManager.get_cache()

        assert cache is not None
        data = {
            "aaa": 111,
            "bbb": "222",
            "ccc": [333, 444],
        }
        cache.hset(cache_key, data)
        actual = cache.hgetall(cache_key)
        expected = data
        assert actual == expected

    def test_postgres_03(self) -> None:
        cache_key = "test_key"
        CacheManager.setup_cache(PostgresDevelopmentConfiguration())

        cache = CacheManager.get_cache()

        assert cache is not None
        data = {
            "aaa": 111,
            "bbb": "222",
            "ccc": [333, 444],
        }
        cache.hset(cache_key, data)
        actual = cache.hgetall(cache_key)
        expected = data
        assert actual == expected

    def test_get_cache_when_not_set(self) -> None:
        """Test that get_cache raises ValueError when cache is not initialized."""
        CacheManager.cache = None
        with pytest.raises(ValueError, match="Invalid cache"):
            CacheManager.get_cache()

    def test_get_nonexistent_key(self) -> None:
        """Test getting a non-existent key returns None."""
        CacheManager.setup_cache(SqliteTestConfiguration())
        cache = CacheManager.get_cache()
        assert cache is not None

        result = cache.get("nonexistent_key")
        assert result is None

    def test_hgetall_nonexistent_key(self) -> None:
        """Test getting a non-existent hash key returns None."""
        CacheManager.setup_cache(SqliteTestConfiguration())
        cache = CacheManager.get_cache()
        assert cache is not None

        result = cache.hgetall("nonexistent_hash_key")
        assert result is None

    def test_clear_cache(self) -> None:
        """Test clearing the cache removes all entries."""
        CacheManager.setup_cache(SqliteTestConfiguration())
        cache = CacheManager.get_cache()
        assert cache is not None

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.hset("hash_key", {"field1": "value1"})

        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"
        assert cache.hgetall("hash_key") == {"field1": "value1"}

        cache.clear()

        assert cache.get("key1") is None
        assert cache.get("key2") is None
        assert cache.hgetall("hash_key") is None

    def test_cache_manager_clear(self) -> None:
        """Test CacheManager.clear method."""
        CacheManager.setup_cache(SqliteTestConfiguration())
        cache = CacheManager.get_cache()
        assert cache is not None

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.hset("hash_key", {"field1": "value1"})

        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"
        assert cache.hgetall("hash_key") == {"field1": "value1"}

        CacheManager.clear()

        assert cache.get("key1") is None
        assert cache.get("key2") is None
        assert cache.hgetall("hash_key") is None

    def test_cache_manager_clear_no_cache(self) -> None:
        """Test CacheManager.clear when cache is None."""
        CacheManager.cache = None
        # Should not raise an exception
        CacheManager.clear()

    def test_shutdown_cache_clears_cache(self) -> None:
        """Test that shutdown_cache clears the cache."""
        CacheManager.setup_cache(SqliteTestConfiguration())
        cache = CacheManager.get_cache()
        assert cache is not None

        cache.set("key1", "value1")
        cache.hset("hash_key", {"field1": "value1"})

        assert cache.get("key1") == "value1"
        assert cache.hgetall("hash_key") == {"field1": "value1"}

        CacheManager.shutdown_cache()

        # After shutdown, cache should be cleared
        # Note: shutdown_cache doesn't set cache to None, it just clears it
        if CacheManager.cache is not None:
            assert CacheManager.cache.get("key1") is None
            assert CacheManager.cache.hgetall("hash_key") is None

    def test_create_cache_key(self) -> None:
        """Test create_cache_key method."""
        domain_name = "domain"
        id_ = "123"
        field_name = "field"

        key = CacheManager.create_cache_key(domain_name, id_, field_name)
        expected = f"{domain_name}{CACHE_KEY_SEPARATOR}{id_}{CACHE_KEY_SEPARATOR}{field_name}"
        assert key == expected

    def test_create_cache_hkey(self) -> None:
        """Test create_cache_hkey method."""
        domain_name = "domain"
        id_ = "123"

        key = CacheManager.create_cache_hkey(domain_name, id_)
        expected = f"{domain_name}{CACHE_KEY_SEPARATOR}{id_}"
        assert key == expected

    def test_set_with_timeout(self) -> None:
        """Test set method with timeout parameter."""
        CacheManager.setup_cache(PostgresDevelopmentConfiguration())
        cache = CacheManager.get_cache()
        assert cache is not None

        cache_key = "timeout_key"
        cache.set(cache_key, "value_with_timeout", timeout=60)
        result = cache.get(cache_key)
        assert result == "value_with_timeout"

    def test_hset_with_timeout(self) -> None:
        """Test hset method with timeout parameter."""
        CacheManager.setup_cache(PostgresDevelopmentConfiguration())
        cache = CacheManager.get_cache()
        assert cache is not None

        cache_key = "timeout_hash_key"
        data = {"field1": "value1", "field2": "value2"}
        cache.hset(cache_key, data, timeout=60)
        result = cache.hgetall(cache_key)
        assert result == data

    def test_incr_redis(self) -> None:
        """Test incr method with Redis cache."""
        CacheManager.setup_cache(PostgresDevelopmentConfiguration())
        cache = CacheManager.get_cache()
        assert cache is not None

        cache_key = "counter_key"
        cache.set(cache_key, "0")
        cache.incr(cache_key)
        result = cache.get(cache_key)
        # After incr, value should be "1" (as string)
        assert result == "1"

        cache.incr(cache_key)
        result = cache.get(cache_key)
        assert result == "2"

    def test_expire_redis(self) -> None:
        """Test expire method with Redis cache."""
        CacheManager.setup_cache(PostgresDevelopmentConfiguration())
        cache = CacheManager.get_cache()
        assert cache is not None

        cache_key = "expire_key"
        cache.set(cache_key, "value")
        cache.expire(cache_key, 60)
        # TTL should be set (exact value may vary, but should be > 0)
        ttl = cache.ttl(cache_key)
        assert ttl > 0

    def test_ttl_redis(self) -> None:
        """Test ttl method with Redis cache."""
        CacheManager.setup_cache(PostgresDevelopmentConfiguration())
        cache = CacheManager.get_cache()
        assert cache is not None

        cache_key = "ttl_key"
        # Non-existent key should return -2
        ttl = cache.ttl("nonexistent_key")
        assert ttl == -2

        # Key without expiry should return -1 (for Redis)
        cache.set(cache_key, "value", timeout=0)
        ttl = cache.ttl(cache_key)
        # For keys without expiry, Redis returns -1
        assert ttl == -1

        # Key with expiry should return positive value
        cache.set(cache_key, "value", timeout=60)
        ttl = cache.ttl(cache_key)
        assert ttl > 0

    def test_multiple_operations_sequence(self) -> None:
        """Test multiple cache operations in sequence."""
        CacheManager.setup_cache(SqliteTestConfiguration())
        cache = CacheManager.get_cache()
        assert cache is not None

        # Set multiple keys
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.hset("hash1", {"a": 1, "b": 2})
        cache.hset("hash2", {"x": 10, "y": 20})

        # Verify all keys
        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"
        assert cache.hgetall("hash1") == {"a": 1, "b": 2}
        assert cache.hgetall("hash2") == {"x": 10, "y": 20}

        # Update values
        cache.set("key1", "updated_value1")
        cache.hset("hash1", {"a": 100, "b": 200})

        # Verify updates
        assert cache.get("key1") == "updated_value1"
        assert cache.get("key2") == "value2"
        assert cache.hgetall("hash1") == {"a": 100, "b": 200}
        assert cache.hgetall("hash2") == {"x": 10, "y": 20}

    def test_postgres_clear(self) -> None:
        """Test clear with Postgres configuration."""
        CacheManager.setup_cache(PostgresDevelopmentConfiguration())
        cache = CacheManager.get_cache()
        assert cache is not None

        cache.set("key1", "value1")
        cache.hset("hash_key", {"field": "value"})

        cache.clear()

        assert cache.get("key1") is None
        assert cache.hgetall("hash_key") is None

    def test_postgres_multiple_hash_operations(self) -> None:
        """Test multiple hash operations with Postgres configuration."""
        CacheManager.setup_cache(PostgresDevelopmentConfiguration())
        cache = CacheManager.get_cache()
        assert cache is not None

        cache_key1 = "hash_key1"
        cache_key2 = "hash_key2"

        data1 = {"a": 1, "b": 2}
        data2 = {"x": 10, "y": 20}

        cache.hset(cache_key1, data1)
        cache.hset(cache_key2, data2)

        assert cache.hgetall(cache_key1) == data1
        assert cache.hgetall(cache_key2) == data2

        # Update one hash
        data1_updated = {"a": 100, "b": 200, "c": 300}
        cache.hset(cache_key1, data1_updated)

        assert cache.hgetall(cache_key1) == data1_updated
        assert cache.hgetall(cache_key2) == data2

    def test_postgres_set_get_various_types(self) -> None:
        """Test set/get with various value types using Postgres configuration."""
        CacheManager.setup_cache(PostgresDevelopmentConfiguration())
        cache = CacheManager.get_cache()
        assert cache is not None

        # Test string values
        cache.set("str_key", "string_value")
        result = cache.get("str_key")
        assert result == "string_value"

        # Test numeric string
        cache.set("num_key", "12345")
        result = cache.get("num_key")
        assert result == "12345"

        # Test special characters
        cache.set("special_key", "value with spaces and !@#$%")
        result = cache.get("special_key")
        assert result == "value with spaces and !@#$%"

    def test_postgres_hash_complex_data(self) -> None:
        """Test hash operations with complex nested data structures."""
        CacheManager.setup_cache(PostgresDevelopmentConfiguration())
        cache = CacheManager.get_cache()
        assert cache is not None

        cache_key = "complex_hash"
        complex_data = {
            "string": "value",
            "number": 123,
            "list": [1, 2, 3, "a", "b"],
            "nested": {"inner": "data", "count": 42},
            "boolean": True,
            "null_value": None,
        }

        cache.hset(cache_key, complex_data)
        result = cache.hgetall(cache_key)

        assert result == complex_data
