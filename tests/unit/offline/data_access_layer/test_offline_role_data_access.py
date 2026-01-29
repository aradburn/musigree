"""
Unit tests for the OfflineRoleDataAccess class.

This module contains comprehensive unit tests for the OfflineRoleDataAccess class,
which provides data access functionality for roles in the Musigree offline system.
It tests role name lookup, fuzzy matching, role finding algorithms, and cache management.
"""

import logging
from typing import AsyncGenerator
from unittest.mock import AsyncMock, Mock, patch

import pytest

from musigree.offline.data_access_layer.offline_role_data_access import OfflineRoleDataAccess


class TestRoleNameLookup:
    """Test class for role_name_lookup method."""

    @patch("musigree.offline.data_access_layer.offline_role_data_access.RoleCache")
    def test_role_name_lookup_exact_match(self, mock_role_cache: Mock) -> None:
        """Test role_name_lookup with exact role name match."""
        # Setup
        mock_role_cache.role_name_set = {"Vocals", "Guitar", "Bass"}

        # Test
        result = OfflineRoleDataAccess.role_name_lookup("Vocals")

        # Assertions
        assert result == ("Vocals", 100)

    @patch("musigree.offline.data_access_layer.offline_role_data_access.RoleCache")
    def test_role_name_lookup_case_insensitive_match(self, mock_role_cache: Mock) -> None:
        """Test role_name_lookup with case insensitive match."""
        # Setup
        mock_role_cache.role_name_set = {"Vocals", "Guitar", "Bass"}

        # Test
        result = OfflineRoleDataAccess.role_name_lookup("vocals")

        # Assertions
        assert result == ("Vocals", 100)

    @patch("musigree.offline.data_access_layer.offline_role_data_access.RoleCache")
    def test_role_name_lookup_mixed_case_match(self, mock_role_cache: Mock) -> None:
        """Test role_name_lookup with mixed case match."""
        # Setup
        mock_role_cache.role_name_set = {"Vocals", "Guitar", "Bass"}

        # Test
        result = OfflineRoleDataAccess.role_name_lookup("VoCaLs")

        # Assertions
        assert result == ("Vocals", 100)

    @patch("musigree.offline.data_access_layer.offline_role_data_access.RoleCache")
    def test_role_name_lookup_no_match(self, mock_role_cache: Mock) -> None:
        """Test role_name_lookup with no match found."""
        # Setup
        mock_role_cache.role_name_set = {"Vocals", "Guitar", "Bass"}

        # Test
        result = OfflineRoleDataAccess.role_name_lookup("Drums")

        # Assertions
        assert result is None

    @patch("musigree.offline.data_access_layer.offline_role_data_access.RoleCache")
    def test_role_name_lookup_empty_set(self, mock_role_cache: Mock) -> None:
        """Test role_name_lookup with empty role set."""
        # Setup
        mock_role_cache.role_name_set = set()

        # Test
        result = OfflineRoleDataAccess.role_name_lookup("Vocals")

        # Assertions
        assert result is None


class TestRoleNameFuzzyLookup:
    """Test class for role_name_fuzzy_lookup method."""

    @patch("musigree.offline.data_access_layer.offline_role_data_access.RoleCache")
    @patch("musigree.offline.data_access_layer.offline_role_data_access.process.extractOne")
    def test_role_name_fuzzy_lookup_high_score(
        self, mock_extract_one: Mock, mock_role_cache: Mock
    ) -> None:
        """Test role_name_fuzzy_lookup with high similarity score."""
        # Setup
        mock_role_cache.role_name_set = {"Vocals", "Guitar", "Bass"}
        mock_extract_one.return_value = ("Vocals", 95)

        # Test
        result = OfflineRoleDataAccess.role_name_fuzzy_lookup("Vocal")

        # Assertions
        assert result == ("Vocals", 95)
        mock_extract_one.assert_called_once_with("Vocal", {"Vocals", "Guitar", "Bass"})

    @patch("musigree.offline.data_access_layer.offline_role_data_access.RoleCache")
    @patch("musigree.offline.data_access_layer.offline_role_data_access.process.extractOne")
    def test_role_name_fuzzy_lookup_low_score(
        self, mock_extract_one: Mock, mock_role_cache: Mock
    ) -> None:
        """Test role_name_fuzzy_lookup with low similarity score."""
        # Setup
        mock_role_cache.role_name_set = {"Vocals", "Guitar", "Bass"}
        mock_extract_one.return_value = ("Vocals", 80)

        # Test
        result = OfflineRoleDataAccess.role_name_fuzzy_lookup("Piano")

        # Assertions
        assert result is None
        mock_extract_one.assert_called_once_with("Piano", {"Vocals", "Guitar", "Bass"})

    @patch("musigree.offline.data_access_layer.offline_role_data_access.RoleCache")
    @patch("musigree.offline.data_access_layer.offline_role_data_access.process.extractOne")
    def test_role_name_fuzzy_lookup_exact_threshold(
        self, mock_extract_one: Mock, mock_role_cache: Mock
    ) -> None:
        """Test role_name_fuzzy_lookup with score exactly at threshold."""
        # Setup
        mock_role_cache.role_name_set = {"Vocals", "Guitar", "Bass"}
        mock_extract_one.return_value = ("Guitar", 91)

        # Test
        result = OfflineRoleDataAccess.role_name_fuzzy_lookup("Guitars")

        # Assertions
        assert result == ("Guitar", 91)


class TestFindRole:
    """Test class for find_role method."""

    @patch("musigree.offline.data_access_layer.offline_role_data_access.OfflineRoleDataAccess.find_role_inner")
    @patch("musigree.offline.data_access_layer.offline_role_data_access.log")
    def test_find_role_direct_match(self, mock_log: Mock, mock_find_role_inner: Mock) -> None:
        """Test find_role with direct match on first try."""
        # Setup
        mock_find_role_inner.return_value = ("Vocals", 100)

        # Test
        result = OfflineRoleDataAccess.find_role("Vocals")

        # Assertions
        assert result == "Vocals"
        mock_find_role_inner.assert_called_with("Vocals")
        mock_log.debug.assert_not_called()

    @patch("musigree.offline.data_access_layer.offline_role_data_access.OfflineRoleDataAccess.find_role_inner")
    @patch("musigree.offline.data_access_layer.offline_role_data_access.log")
    def test_find_role_no_match(self, mock_log: Mock, mock_find_role_inner: Mock) -> None:
        """Test find_role with no match found."""
        # Setup
        mock_find_role_inner.return_value = None

        # Test
        result = OfflineRoleDataAccess.find_role("Unknown Role")

        # Assertions
        assert result is None
        mock_log.debug.assert_called_once_with("role not found: Unknown Role")

    @patch("musigree.offline.data_access_layer.offline_role_data_access.OfflineRoleDataAccess.find_role_inner")
    def test_find_role_with_word_breakdown(self, mock_find_role_inner: Mock) -> None:
        """Test find_role with word breakdown algorithm."""

        # Setup - create a function that returns None except for specific cases
        def mock_find_role_inner_func(role_name: str) -> tuple[str, int] | None:
            if role_name == "Lead Vocals":
                return "Vocals", 95
            return None

        mock_find_role_inner.side_effect = mock_find_role_inner_func

        # Test
        result = OfflineRoleDataAccess.find_role("Lead Vocals Guitar")

        # Assertions
        assert result == "Vocals"
        assert mock_find_role_inner.call_count >= 2

    @patch("musigree.offline.data_access_layer.offline_role_data_access.OfflineRoleDataAccess.find_role_inner")
    def test_find_role_low_score_threshold(self, mock_find_role_inner: Mock) -> None:
        """Test find_role with score below threshold."""
        # Setup
        mock_find_role_inner.return_value = ("Vocals", 85)  # Below 90 threshold

        # Test
        result = OfflineRoleDataAccess.find_role("Vocal Performance")

        # Assertions
        assert result is None

    @patch("musigree.offline.data_access_layer.offline_role_data_access.OfflineRoleDataAccess.find_role_inner")
    def test_find_role_complex_sentence_split(self, mock_find_role_inner: Mock) -> None:
        """Test find_role with complex sentence that gets split."""
        # Setup - simulate a very long role name that needs splitting
        long_role_name = "Very Long Complex Role Name With Many Words That Should Be Split"

        def mock_find_role_inner_func(role_name: str) -> tuple[str, int] | None:
            if "Very Long Complex Role Name With" in role_name:
                return "Vocals", 95
            return None

        mock_find_role_inner.side_effect = mock_find_role_inner_func

        # Test
        result = OfflineRoleDataAccess.find_role(long_role_name)

        # Assertions
        assert result == "Vocals"


class TestFindRoleInner:
    """Test class for find_role_inner method."""

    def test_find_role_inner_none_input(self) -> None:
        """Test find_role_inner with None input."""
        result = OfflineRoleDataAccess.find_role_inner(None)
        assert result is None

    def test_find_role_inner_empty_string(self) -> None:
        """Test find_role_inner with empty string input."""
        result = OfflineRoleDataAccess.find_role_inner("")
        assert result is None

    @patch(
        "musigree.offline.data_access_layer.offline_role_data_access.OfflineRoleDataAccess.substitute_role_alternatives"
    )
    @patch("musigree.offline.data_access_layer.offline_role_data_access.OfflineRoleDataAccess.role_name_lookup")
    def test_find_role_inner_direct_lookup_success(
        self, mock_lookup: Mock, mock_substitute: Mock
    ) -> None:
        """Test find_role_inner with successful direct lookup."""
        # Setup
        mock_substitute.return_value = "Vocals"
        mock_lookup.return_value = ("Vocals", 100)

        # Test
        result = OfflineRoleDataAccess.find_role_inner("vocals")

        # Assertions
        assert result == ("Vocals", 100)
        mock_substitute.assert_called_once_with("vocals")
        mock_lookup.assert_called_once_with("Vocals")

    @patch(
        "musigree.offline.data_access_layer.offline_role_data_access.OfflineRoleDataAccess.substitute_role_alternatives"
    )
    @patch("musigree.offline.data_access_layer.offline_role_data_access.OfflineRoleDataAccess.role_name_lookup")
    @patch(
        "musigree.offline.data_access_layer.offline_role_data_access.OfflineRoleDataAccess.role_name_fuzzy_lookup"
    )
    def test_find_role_inner_fuzzy_lookup_fallback(
        self, mock_fuzzy: Mock, mock_lookup: Mock, mock_substitute: Mock
    ) -> None:
        """Test find_role_inner with fuzzy lookup fallback."""
        # Setup
        mock_substitute.return_value = "Vocal Performance"
        mock_lookup.return_value = None
        mock_fuzzy.return_value = ("Vocals", 95)

        # Test
        result = OfflineRoleDataAccess.find_role_inner("Vocal Performance")

        # Assertions
        assert result == ("Vocals", 95)
        mock_substitute.assert_called_once_with("Vocal Performance")
        mock_lookup.assert_called_once_with("Vocal Performance")
        mock_fuzzy.assert_called_once_with("Vocal Performance")

    @patch(
        "musigree.offline.data_access_layer.offline_role_data_access.OfflineRoleDataAccess.substitute_role_alternatives"
    )
    @patch("musigree.offline.data_access_layer.offline_role_data_access.OfflineRoleDataAccess.role_name_lookup")
    @patch(
        "musigree.offline.data_access_layer.offline_role_data_access.OfflineRoleDataAccess.role_name_fuzzy_lookup"
    )
    def test_find_role_inner_no_match(
        self, mock_fuzzy: Mock, mock_lookup: Mock, mock_substitute: Mock
    ) -> None:
        """Test find_role_inner with no match found."""
        # Setup
        mock_substitute.return_value = "Unknown Role"
        mock_lookup.return_value = None
        mock_fuzzy.return_value = None

        # Test
        result = OfflineRoleDataAccess.find_role_inner("Unknown Role")

        # Assertions
        assert result is None
        mock_substitute.assert_called_once_with("Unknown Role")
        mock_lookup.assert_called_once_with("Unknown Role")
        mock_fuzzy.assert_called_once_with("Unknown Role")


class TestSubstituteRoleAlternatives:
    """Test class for substitute_role_alternatives method."""

    @patch("musigree.offline.data_access_layer.offline_role_data_access.RoleDataUtils")
    def test_substitute_role_alternatives_match_found(self, mock_role_data_utils: Mock) -> None:
        """Test substitute_role_alternatives with alternative found."""
        # Setup
        mock_role_data_utils.ALTERNATIVES = {"singer": "Vocals", "guitarist": "Guitar"}

        # Test
        result = OfflineRoleDataAccess.substitute_role_alternatives("Singer")

        # Assertions
        assert result == "Vocals"

    @patch("musigree.offline.data_access_layer.offline_role_data_access.RoleDataUtils")
    def test_substitute_role_alternatives_no_match(self, mock_role_data_utils: Mock) -> None:
        """Test substitute_role_alternatives with no alternative found."""
        # Setup
        mock_role_data_utils.ALTERNATIVES = {"singer": "Vocals", "guitarist": "Guitar"}

        # Test
        result = OfflineRoleDataAccess.substitute_role_alternatives("Drums")

        # Assertions
        assert result == "Drums"

    @patch("musigree.offline.data_access_layer.offline_role_data_access.RoleDataUtils")
    def test_substitute_role_alternatives_case_insensitive(
        self, mock_role_data_utils: Mock
    ) -> None:
        """Test substitute_role_alternatives with case insensitive matching."""
        # Setup
        mock_role_data_utils.ALTERNATIVES = {"singer": "Vocals", "guitarist": "Guitar"}

        # Test
        result = OfflineRoleDataAccess.substitute_role_alternatives("SINGER")

        # Assertions
        assert result == "Vocals"

    @patch("musigree.offline.data_access_layer.offline_role_data_access.RoleDataUtils")
    def test_substitute_role_alternatives_empty_alternatives(
        self, mock_role_data_utils: Mock
    ) -> None:
        """Test substitute_role_alternatives with empty alternatives."""
        # Setup
        mock_role_data_utils.ALTERNATIVES = {}

        # Test
        result = OfflineRoleDataAccess.substitute_role_alternatives("Singer")

        # Assertions
        assert result == "Singer"


class TestLoadAllRolesIntoCache:
    """Test class for load_all_roles_into_cache method."""

    @pytest.fixture
    def mock_role(self) -> Mock:
        """Fixture for mock role object."""
        role = Mock()
        role.id = 1
        role.role_name = "Vocals"
        role.role_category = "Performance"
        return role

    @patch("musigree.offline.data_access_layer.offline_role_data_access.RoleCache")
    @patch("musigree.offline.data_access_layer.offline_role_data_access.offline_transaction")
    @patch("musigree.offline.data_access_layer.offline_role_data_access.RoleRepository")
    @patch("musigree.offline.data_access_layer.offline_role_data_access.log")
    async def test_load_all_roles_into_cache_success(
        self,
        mock_log: Mock,
        mock_role_repository_class: Mock,
        mock_transaction: Mock,
        mock_role_cache: Mock,
        mock_role: Mock,
    ) -> None:
        """Test load_all_roles_into_cache with successful loading."""
        # Setup
        mock_role.id = 1
        mock_role.role_name = "Vocals"
        mock_role.role_category = "Performance"

        async def async_roles_iterator() -> AsyncGenerator[Mock, None]:
            yield mock_role

        mock_repository = Mock()
        mock_repository.all.return_value = async_roles_iterator()
        mock_role_repository_class.return_value = mock_repository

        # Setup cache mocks
        mock_role_cache.role_id_to_role_name_lookup = {}
        mock_role_cache.role_id_to_role_category_lookup = {}
        mock_role_cache.role_name_to_role_id_lookup = {}
        mock_role_cache.role_name_set = set()

        # Mock the transaction context
        mock_transaction.return_value.__aenter__ = AsyncMock()
        mock_transaction.return_value.__aexit__ = AsyncMock()

        # Test
        await OfflineRoleDataAccess.load_all_roles_into_cache()

        # Assertions
        mock_log.debug.assert_any_call("Loading roles from offline RoleRepository")
        # The async generator now works correctly and returns 1 role
        mock_log.debug.assert_any_call("Loaded 1 roles from RoleRepository")

        # Verify method completed without error
        # In a real scenario, the cache would be populated

    @patch("musigree.offline.data_access_layer.offline_role_data_access.RoleCache")
    @patch("musigree.offline.data_access_layer.offline_role_data_access.offline_transaction")
    @patch("musigree.offline.data_access_layer.offline_role_data_access.RoleRepository")
    @patch("musigree.offline.data_access_layer.offline_role_data_access.log")
    async def test_load_all_roles_into_cache_empty_database(
        self,
        mock_log: Mock,
        mock_role_repository_class: Mock,
        mock_transaction: Mock,
        mock_role_cache: Mock,
    ) -> None:
        """Test load_all_roles_into_cache with empty database."""

        # Setup
        # noinspection PyUnreachableCode
        async def async_roles_iterator() -> AsyncGenerator[Mock, None]:
            return
            # noinspection PyTypeChecker
            yield  # This line will never be reached, but makes it a proper async generator

        mock_repository = Mock()
        mock_repository.all.return_value = async_roles_iterator()
        mock_role_repository_class.return_value = mock_repository

        # Setup cache mocks
        mock_role_cache.role_id_to_role_name_lookup = {}
        mock_role_cache.role_id_to_role_category_lookup = {}
        mock_role_cache.role_name_to_role_id_lookup = {}
        mock_role_cache.role_name_set = set()

        # Mock the transaction context
        mock_transaction.return_value.__aenter__ = AsyncMock()
        mock_transaction.return_value.__aexit__ = AsyncMock()

        # Test
        await OfflineRoleDataAccess.load_all_roles_into_cache()

        # Assertions
        mock_log.debug.assert_any_call("Loading roles from offline RoleRepository")
        mock_log.debug.assert_any_call("Loaded 0 roles from RoleRepository")

        # Verify caches are empty
        assert len(mock_role_cache.role_id_to_role_name_lookup) == 0
        assert len(mock_role_cache.role_id_to_role_category_lookup) == 0

    @patch("musigree.offline.data_access_layer.offline_role_data_access.RoleCache")
    @patch("musigree.offline.data_access_layer.offline_role_data_access.offline_transaction")
    @patch("musigree.offline.data_access_layer.offline_role_data_access.RoleRepository")
    async def test_load_all_roles_into_cache_multiple_roles(
        self,
        mock_role_repository_class: Mock,
        mock_transaction: Mock,
        mock_role_cache: Mock,
    ) -> None:
        """Test load_all_roles_into_cache with multiple roles."""
        # Setup multiple roles
        role1 = Mock()
        role1.id = 1
        role1.role_name = "Vocals"
        role1.role_category = "Performance"

        role2 = Mock()
        role2.id = 2
        role2.role_name = "Guitar"
        role2.role_category = "Instruments"

        async def async_roles_iterator() -> AsyncGenerator[Mock, None]:
            for role in [role1, role2]:
                yield role

        mock_repository = Mock()
        mock_repository.all.return_value = async_roles_iterator()
        mock_role_repository_class.return_value = mock_repository

        # Setup cache mocks
        mock_role_cache.role_id_to_role_name_lookup = {}
        mock_role_cache.role_id_to_role_category_lookup = {}
        mock_role_cache.role_name_to_role_id_lookup = {}
        mock_role_cache.role_name_set = set()

        # Mock the transaction context
        mock_transaction.return_value.__aenter__ = AsyncMock()
        mock_transaction.return_value.__aexit__ = AsyncMock()

        # Test
        await OfflineRoleDataAccess.load_all_roles_into_cache()

        # Assertions - The async generator now works correctly and processes both roles
        # The cache should be populated with both roles
        assert len(mock_role_cache.role_id_to_role_name_lookup) == 2
        assert mock_role_cache.role_id_to_role_name_lookup[1] == "Vocals"
        assert mock_role_cache.role_id_to_role_name_lookup[2] == "Guitar"

        # The reverse lookup and name set should also be populated
        assert len(mock_role_cache.role_name_to_role_id_lookup) == 2
        assert mock_role_cache.role_name_to_role_id_lookup["Vocals"] == 1
        assert mock_role_cache.role_name_to_role_id_lookup["Guitar"] == 2
        assert len(mock_role_cache.role_name_set) == 2
        assert "Vocals" in mock_role_cache.role_name_set
        assert "Guitar" in mock_role_cache.role_name_set


class TestLogging:
    """Test class for logging behavior."""

    def test_logger_exists(self) -> None:
        """Test that the module logger is properly configured."""
        from musigree.offline.data_access_layer.offline_role_data_access import log

        assert isinstance(log, logging.Logger)
        assert log.name == "musigree.offline.data_access_layer.offline_role_data_access"


class TestCacheIntegration:
    """Test class for cache functionality integration."""

    def test_lru_cache_decorator_on_find_role_inner(self) -> None:
        """Test that find_role_inner has LRU cache decorator."""
        # Verify the method has the cache attribute (indicating it's cached)
        assert hasattr(OfflineRoleDataAccess.find_role_inner, "cache_info")

        # Get cache info to verify it's working
        cache_info = OfflineRoleDataAccess.find_role_inner.cache_info()
        assert hasattr(cache_info, "hits")
        assert hasattr(cache_info, "misses")
        assert hasattr(cache_info, "maxsize")
        assert cache_info.maxsize == 100000
