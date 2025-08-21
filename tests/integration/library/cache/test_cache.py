from musigree.config import (
    SqliteTestConfiguration,
    SqliteDevelopmentConfiguration,
    PostgresDevelopmentConfiguration,
)
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

        print(f"test cache: {cache}")

        assert cache is not None
        CacheManager.shutdown_cache()

    def test_02(self) -> None:
        cache_key = "test_key"
        CacheManager.setup_cache(SqliteTestConfiguration())

        cache = CacheManager.get_cache()

        print(f"test cache: {cache}")
        assert cache is not None
        data = {
            "aaa": 111,
            "bbb": "222",
            "ccc": [333, 444],
        }
        cache.set(cache_key, data)
        actual = cache.get(cache_key)
        expected = data
        assert actual == expected

    def test_03(self) -> None:
        cache_key = "test_key"
        CacheManager.setup_cache(SqliteTestConfiguration())

        cache = CacheManager.get_cache()

        print(f"test cache: {cache}")
        assert cache is not None
        data = {
            "aaa": 111,
            "bbb": "222",
            "ccc": [333, 444],
        }
        cache.set(cache_key, data)
        actual = cache.get(cache_key)
        expected = data
        assert actual == expected

        cache.set(cache_key, None)
        actual = cache.get(cache_key)
        expected_none = None
        assert actual == expected_none

    def test_04(self) -> None:
        CacheManager.setup_cache(SqliteDevelopmentConfiguration())

        cache = CacheManager.get_cache()

        print(f"test cache: {cache}")

        assert cache is not None
        CacheManager.shutdown_cache()

    def test_05(self) -> None:
        cache_key = "test_key"
        CacheManager.setup_cache(SqliteDevelopmentConfiguration())

        cache = CacheManager.get_cache()

        print(f"test cache: {cache}")
        assert cache is not None
        data = {
            "aaa": 111,
            "bbb": "222",
            "ccc": [333, 444],
        }
        cache.set(cache_key, data)
        actual = cache.get(cache_key)
        expected = data
        assert actual == expected

    def test_06(self) -> None:
        cache_key = "test_key"
        CacheManager.setup_cache(SqliteDevelopmentConfiguration())

        cache = CacheManager.get_cache()

        print(f"test cache: {cache}")
        assert cache is not None
        data = {
            "aaa": 111,
            "bbb": "222",
            "ccc": [333, 444],
        }
        cache.set(cache_key, data)
        actual = cache.get(cache_key)
        expected = data
        assert actual == expected

        cache.set(cache_key, None)
        actual = cache.get(cache_key)
        expected_none = None
        assert actual == expected_none

    def test_postgres_01(self) -> None:
        CacheManager.setup_cache(PostgresDevelopmentConfiguration())

        cache = CacheManager.get_cache()

        print(f"test cache: {cache}")

        assert cache is not None
        CacheManager.shutdown_cache()

    def test_postgres_02(self) -> None:
        cache_key = "test_key"
        CacheManager.setup_cache(PostgresDevelopmentConfiguration())

        cache = CacheManager.get_cache()

        print(f"test cache: {cache}")
        assert cache is not None
        data = {
            "aaa": 111,
            "bbb": "222",
            "ccc": [333, 444],
        }
        cache.set(cache_key, data)
        actual = cache.get(cache_key)
        expected = data
        assert actual == expected

    def test_postgres_03(self) -> None:
        cache_key = "test_key"
        CacheManager.setup_cache(PostgresDevelopmentConfiguration())

        cache = CacheManager.get_cache()

        print(f"test cache: {cache}")
        assert cache is not None
        data = {
            "aaa": 111,
            "bbb": "222",
            "ccc": [333, 444],
        }
        cache.set(cache_key, data)
        actual = cache.get(cache_key)
        expected = data
        assert actual == expected

        cache.set(cache_key, None)
        actual = cache.get(cache_key)
        expected_none = None
        assert actual == expected_none
