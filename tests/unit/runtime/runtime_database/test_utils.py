"""
Test utilities for runtime database tests.

This module provides common utilities and mocking patterns for testing
runtime database components, particularly for RoleCache interactions and
database session management.

Examples:
    # Using context manager for simple role lookup tests:
    with RoleCacheMockHelper.mock_role_cache({"Producer": 1, "Engineer": 2}):
        # Test code that uses RoleCache.role_name_to_role_id_lookup
        pass
    
    # Using with @patch decorator:
    @patch('musigree.library.cache.role_cache.RoleCache')
    def test_something(self, mock_role_cache):
        RoleCacheMockHelper.setup_role_cache_mock(mock_role_cache, {"Producer": 1})
        # Test code here
    
    # Using predefined common roles:
    with RoleCacheMockHelper.mock_role_cache(COMMON_TEST_ROLES):
        # Test with Producer, Engineer, Vocalist, Guitarist, Drummer
        pass
        
    # For modules that import RoleCache directly:
    with RoleCacheMockHelper.mock_role_cache_in_module(
        "musigree.runtime.runtime_database.runtime_relation_repository",
        {"Producer": 1}
    ):
        # Test code that uses RoleCache in that specific module
        pass
        
    # For session mocking:
    with SessionMockHelper.mock_runtime_session():
        # Test code that uses CTX_RUNTIME_SESSION
        pass
        
    # For combined role cache and session mocking:
    with SessionMockHelper.mock_runtime_session_and_role_cache({"Producer": 1}):
        # Test code that uses both session and role cache
        pass
"""

from contextlib import contextmanager
from typing import Dict, Any, List
from unittest.mock import Mock, patch


class SessionMockHelper:
    """
    Helper class for mocking database session interactions in tests.
    
    This class provides standardized mocking patterns for database sessions
    to ensure consistent behavior across all tests that interact with
    the runtime database session context.
    """
    
    @staticmethod
    def create_mock_session(
        execute_return_value: Any | None = None,
        flush_return_value: Any | None = None,
        commit_return_value: Any | None = None,
        rollback_return_value: Any | None = None,
        add_return_value: Any | None = None,
        add_all_return_value: Any | None = None,
        refresh_return_value: Any | None = None,
        close_return_value: Any | None = None,
        **additional_methods
    ) -> Mock:
        """
        Create a mock session with common database methods.
        
        Args:
            execute_return_value: Return value for session.execute()
            flush_return_value: Return value for session.flush()
            commit_return_value: Return value for session.commit()
            rollback_return_value: Return value for session.rollback()
            add_return_value: Return value for session.add()
            add_all_return_value: Return value for session.add_all()
            refresh_return_value: Return value for session.refresh()
            close_return_value: Return value for session.close()
            **additional_methods: Additional methods to add to the mock
            
        Returns:
            Mock: A configured mock session object
        """
        mock_session = Mock()
        
        # Set up common session methods
        if execute_return_value is not None:
            mock_session.execute.return_value = execute_return_value
        if flush_return_value is not None:
            mock_session.flush.return_value = flush_return_value
        if commit_return_value is not None:
            mock_session.commit.return_value = commit_return_value
        if rollback_return_value is not None:
            mock_session.rollback.return_value = rollback_return_value
        if add_return_value is not None:
            mock_session.add.return_value = add_return_value
        if add_all_return_value is not None:
            mock_session.add_all.return_value = add_all_return_value
        if refresh_return_value is not None:
            mock_session.refresh.return_value = refresh_return_value
        if close_return_value is not None:
            mock_session.close.return_value = close_return_value
            
        # Add any additional methods
        for method_name, return_value in additional_methods.items():
            setattr(mock_session, method_name, Mock(return_value=return_value))
            
        return mock_session
    
    @staticmethod
    @contextmanager
    def mock_runtime_session(
        execute_return_value: Any | None = None,
        flush_return_value: Any | None = None,
        **session_kwargs
    ):
        """
        Context manager for mocking CTX_RUNTIME_SESSION.
        
        Args:
            execute_return_value: Return value for session.execute()
            flush_return_value: Return value for session.flush()
            **session_kwargs: Additional session method configurations
            
        Usage:
            with SessionMockHelper.mock_runtime_session():
                # Test code that uses CTX_RUNTIME_SESSION
                pass
        """
        mock_session = SessionMockHelper.create_mock_session(
            execute_return_value=execute_return_value,
            flush_return_value=flush_return_value,
            **session_kwargs
        )
        
        with patch('musigree.runtime.runtime_database.runtime_session.CTX_RUNTIME_SESSION') as mock_ctx:
            mock_ctx.get.return_value = mock_session
            yield mock_session
    
    @staticmethod
    @contextmanager
    def mock_runtime_session_in_module(
        module_path: str,
        execute_return_value: Any | None = None,
        flush_return_value: Any | None = None,
        **session_kwargs
    ):
        """
        Context manager for mocking CTX_RUNTIME_SESSION in a specific module.
        
        Args:
            module_path: The full module path where CTX_RUNTIME_SESSION is imported
            execute_return_value: Return value for session.execute()
            flush_return_value: Return value for session.flush()
            **session_kwargs: Additional session method configurations
            
        Usage:
            with SessionMockHelper.mock_runtime_session_in_module(
                "musigree.runtime.runtime_database.runtime_relation_repository"
            ):
                # Test code that uses CTX_RUNTIME_SESSION in that module
                pass
        """
        mock_session = SessionMockHelper.create_mock_session(
            execute_return_value=execute_return_value,
            flush_return_value=flush_return_value,
            **session_kwargs
        )
        
        patch_path = f"{module_path}.CTX_RUNTIME_SESSION"
        
        with patch(patch_path) as mock_ctx:
            mock_ctx.get.return_value = mock_session
            yield mock_session
    
    @staticmethod
    @contextmanager
    def mock_runtime_session_and_role_cache(
        role_mappings: Dict[str, int],
        execute_return_value: Any | None = None,
        flush_return_value: Any | None = None,
        **session_kwargs
    ):
        """
        Context manager for mocking both CTX_RUNTIME_SESSION and RoleCache.
        
        Args:
            role_mappings: Dictionary mapping role names to role IDs
            execute_return_value: Return value for session.execute()
            flush_return_value: Return value for session.flush()
            **session_kwargs: Additional session method configurations
            
        Usage:
            with SessionMockHelper.mock_runtime_session_and_role_cache({"Producer": 1}):
                # Test code that uses both session and role cache
                pass
        """
        with SessionMockHelper.mock_runtime_session(
            execute_return_value=execute_return_value,
            flush_return_value=flush_return_value,
            **session_kwargs
        ) as mock_session:
            with RoleCacheMockHelper.mock_role_cache(role_mappings):
                yield mock_session


class RoleCacheMockHelper:
    """
    Helper class for mocking RoleCache interactions in tests.
    
    This class provides standardized mocking patterns for RoleCache
    to ensure consistent behavior across all tests that interact
    with role lookups.
    
    The RoleCache class has several important attributes that need to be mocked:
    - role_name_to_role_id_lookup: Dict[str, int] - Maps role names to IDs
    - role_id_to_role_name_lookup: Dict[int, str] - Maps role IDs to names  
    - role_name_set: Set[str] - Set of all role names
    - role_id_to_role_category_lookup: Dict[int, RoleType.Category] - Maps IDs to categories
    - role_category_to_role_name_lookup: Dict[str, list[str]] - Maps categories to role lists
    """
    
    @staticmethod
    def create_role_cache_data(role_mappings: Dict[str, int]) -> Dict[str, Any]:
        """
        Create mock data for RoleCache with proper bidirectional mappings.
        
        Args:
            role_mappings: Dictionary mapping role names to role IDs
            
        Returns:
            Dictionary containing all the mock cache data structures
        """
        role_name_to_id = role_mappings.copy()
        role_id_to_name = {v: k for k, v in role_mappings.items()}
        role_name_set = set(role_mappings.keys())
        
        return {
            'role_name_to_role_id_lookup': role_name_to_id,
            'role_id_to_role_name_lookup': role_id_to_name,
            'role_name_set': role_name_set,
            'role_id_to_role_category_lookup': {},  # Can be extended if needed
            'role_category_to_role_name_lookup': {},  # Can be extended if needed
        }
    
    @staticmethod
    @contextmanager
    def mock_role_cache(role_mappings: Dict[str, int]):
        """
        Context manager for mocking RoleCache with specified role mappings.
        
        This is the recommended way to mock RoleCache for most tests as it
        automatically sets up all the required attributes and cleans up afterwards.
        
        Args:
            role_mappings: Dictionary mapping role names to role IDs
            
        Usage:
            with RoleCacheMockHelper.mock_role_cache({"Producer": 1, "Engineer": 2}):
                # Test code that uses RoleCache
                result = some_function_that_uses_role_cache()
                assert result is not None
        """
        cache_data = RoleCacheMockHelper.create_role_cache_data(role_mappings)
        
        with patch('musigree.library.cache.role_cache.RoleCache') as mock_role_cache:
            # Set up all the cache attributes
            for attr_name, attr_value in cache_data.items():
                setattr(mock_role_cache, attr_name, attr_value)
            
            yield mock_role_cache
    
    @staticmethod
    @contextmanager
    def mock_role_cache_in_module(module_path: str, role_mappings: Dict[str, int]):
        """
        Context manager for mocking RoleCache in a specific module.
        
        Use this when the module imports RoleCache directly and you need to
        patch it at the module level.
        
        Args:
            module_path: The full module path where RoleCache is imported
            role_mappings: Dictionary mapping role names to role IDs
            
        Usage:
            with RoleCacheMockHelper.mock_role_cache_in_module(
                "musigree.runtime.runtime_database.runtime_relation_repository",
                {"Producer": 1}
            ):
                # Test code that uses RoleCache in that module
                pass
        """
        cache_data = RoleCacheMockHelper.create_role_cache_data(role_mappings)
        patch_path = f"{module_path}.RoleCache"
        
        with patch(patch_path) as mock_role_cache:
            # Set up all the cache attributes
            for attr_name, attr_value in cache_data.items():
                setattr(mock_role_cache, attr_name, attr_value)
            
            yield mock_role_cache
    
    @staticmethod
    @contextmanager
    def mock_role_cache_multiple_modules(
        module_paths: List[str], 
        role_mappings: Dict[str, int]
    ):
        """
        Context manager for mocking RoleCache in multiple modules simultaneously.
        
        Args:
            module_paths: List of module paths where RoleCache is imported
            role_mappings: Dictionary mapping role names to role IDs
            
        Usage:
            modules = [
                "musigree.runtime.runtime_database.runtime_relation_repository",
                "musigree.runtime.data_access_layer.runtime_relation_data_access"
            ]
            with RoleCacheMockHelper.mock_role_cache_multiple_modules(
                modules, {"Producer": 1}
            ):
                # Test code here
                pass
        """
        cache_data = RoleCacheMockHelper.create_role_cache_data(role_mappings)
        
        # Create patch contexts for all modules
        patches = []
        for module_path in module_paths:
            patch_path = f"{module_path}.RoleCache"
            patches.append(patch(patch_path))
        
        # Enter all patches
        mock_caches = []
        for p in patches:
            mock_cache = p.__enter__()
            # Set up all the cache attributes
            for attr_name, attr_value in cache_data.items():
                setattr(mock_cache, attr_name, attr_value)
            mock_caches.append(mock_cache)

        # noinspection PyUnreachableCode
        try:
            yield mock_caches
        finally:
            # Exit all patches in reverse order
            for p in reversed(patches):
                p.__exit__(None, None, None)
    
    @staticmethod
    def setup_role_cache_mock(mock_role_cache: Mock, role_mappings: Dict[str, int]):
        """
        Set up a RoleCache mock with the specified role mappings.
        
        Use this when you already have a mock object (e.g., from @patch decorator)
        and need to configure it with role data.
        
        Args:
            mock_role_cache: The mock RoleCache object to configure
            role_mappings: Dictionary mapping role names to role IDs
            
        Usage:
            @patch('musigree.library.cache.role_cache.RoleCache')
            def test_something(self, mock_role_cache):
                RoleCacheMockHelper.setup_role_cache_mock(
                    mock_role_cache, 
                    {"Producer": 1, "Engineer": 2}
                )
                # Test code here
        """
        cache_data = RoleCacheMockHelper.create_role_cache_data(role_mappings)
        
        for attr_name, attr_value in cache_data.items():
            setattr(mock_role_cache, attr_name, attr_value)
    
    @staticmethod
    def create_role_cache_with_categories(
        role_mappings: Dict[str, int], 
        role_categories: Dict[int, Any]
    ) -> Dict[str, Any]:
        """
        Create mock data for RoleCache including role categories.
        
        Args:
            role_mappings: Dictionary mapping role names to role IDs
            role_categories: Dictionary mapping role IDs to categories
            
        Returns:
            Dictionary containing all the mock cache data structures including categories
        """
        cache_data = RoleCacheMockHelper.create_role_cache_data(role_mappings)
        cache_data['role_id_to_role_category_lookup'] = role_categories.copy()
        return cache_data
    
    @staticmethod
    @contextmanager
    def mock_role_cache_with_categories(
        role_mappings: Dict[str, int], 
        role_categories: Dict[int, Any]
    ):
        """
        Context manager for mocking RoleCache with role mappings and categories.
        
        Args:
            role_mappings: Dictionary mapping role names to role IDs
            role_categories: Dictionary mapping role IDs to categories
            
        Usage:
            role_mappings = {"Producer": 1, "Engineer": 2}
            role_categories = {1: "Production", 2: "Technical"}
            with RoleCacheMockHelper.mock_role_cache_with_categories(
                role_mappings, role_categories
            ):
                # Test code that uses both role lookups and categories
                pass
        """
        cache_data = RoleCacheMockHelper.create_role_cache_with_categories(
            role_mappings, role_categories
        )
        
        with patch('musigree.library.cache.role_cache.RoleCache') as mock_role_cache:
            # Set up all the cache attributes
            for attr_name, attr_value in cache_data.items():
                setattr(mock_role_cache, attr_name, attr_value)
            
            yield mock_role_cache


# Common role mappings for tests
COMMON_TEST_ROLES = {
    "Producer": 1,
    "Engineer": 2,
    "Vocalist": 3,
    "Guitarist": 4,
    "Drummer": 5,
}

# Role mappings for specific test scenarios
PRODUCTION_ROLES = {
    "Producer": 1,
    "Executive Producer": 2,
    "Co-Producer": 3,
}

INSTRUMENT_ROLES = {
    "Guitarist": 10,
    "Bassist": 11,
    "Drummer": 12,
    "Keyboardist": 13,
}

VOCAL_ROLES = {
    "Vocalist": 20,
    "Lead Vocals": 21,
    "Backing Vocals": 22,
}

# Default role mappings (alias for COMMON_TEST_ROLES)
DEFAULT_ROLE_MAPPINGS = COMMON_TEST_ROLES.copy() 