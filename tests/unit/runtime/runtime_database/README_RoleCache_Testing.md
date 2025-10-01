# RoleCache Testing Guide

This guide explains how to properly mock RoleCache interactions in tests using the `RoleCacheMockHelper` utility.

## Overview

The `RoleCache` class is a central component in the Musigree system that provides various mappings and lookups for role-related information. When testing code that interacts with `RoleCache`, it's important to mock it properly to ensure consistent and reliable tests.

## The RoleCacheMockHelper Utility

The `RoleCacheMockHelper` class in `test_utils.py` provides standardized mocking patterns for `RoleCache` interactions. It handles all the complex setup required to mock the various attributes of `RoleCache`.

### Key RoleCache Attributes

The `RoleCache` class has several important attributes that need to be mocked:

-   `role_name_to_role_id_lookup`: Dict[str, int] - Maps role names to IDs
-   `role_id_to_role_name_lookup`: Dict[int, str] - Maps role IDs to names
-   `role_name_set`: Set[str] - Set of all role names
-   `role_id_to_role_category_lookup`: Dict[int, RoleType.Category] - Maps IDs to categories
-   `role_category_to_role_name_lookup`: Dict[str, list[str]] - Maps categories to role lists

## Usage Patterns

### 1. Basic Context Manager (Recommended)

For most tests, use the context manager approach:

```python
from tests.unit.runtime.runtime_database.test_utils import RoleCacheMockHelper

def test_something_with_role_cache():
    role_mappings = {"Producer": 1, "Engineer": 2}

    with RoleCacheMockHelper.mock_role_cache(role_mappings):
        # Test code that uses RoleCache
        result = some_function_that_uses_role_cache()
        assert result is not None
```

### 2. Module-Specific Mocking

When the module imports `RoleCache` directly (like `from musigree.library.cache.role_cache import RoleCache`), you need to patch it at the module level:

```python
def test_module_specific_role_cache():
    role_mappings = {"Producer": 1, "Engineer": 2}

    with RoleCacheMockHelper.mock_role_cache_in_module(
        "musigree.runtime.runtime_database.runtime_relation_repository",
        role_mappings
    ):
        # Test code that uses RoleCache in that specific module
        result = repository.find_by_key({"role_name": "Producer", "subject": 1, "object": 2})
        assert result is not None
```

### 3. With Role Categories

When testing code that uses role categories:

```python
def test_with_role_categories():
    role_mappings = {"Producer": 1, "Engineer": 2}
    role_categories = {1: "Production", 2: "Technical"}

    with RoleCacheMockHelper.mock_role_cache_with_categories(
        role_mappings, role_categories
    ):
        # Test code that uses both role lookups and categories
        mapping = RoleEntry.get_multiselect_mapping()
        assert "Production" in mapping
```

### 4. Using @patch Decorator

When you need more control or are using existing `@patch` decorators:

```python
from unittest.mock import patch

@patch('musigree.library.cache.role_cache.RoleCache')
def test_with_patch_decorator(mock_role_cache):
    RoleCacheMockHelper.setup_role_cache_mock(
        mock_role_cache,
        {"Producer": 1, "Engineer": 2}
    )
    # Test code here
```

### 5. Multiple Modules

When testing code that spans multiple modules that import RoleCache:

```python
def test_multiple_modules():
    modules = [
        "musigree.runtime.runtime_database.runtime_relation_repository",
        "musigree.runtime.data_access_layer.runtime_relation_data_access"
    ]
    role_mappings = {"Producer": 1, "Engineer": 2}

    with RoleCacheMockHelper.mock_role_cache_multiple_modules(modules, role_mappings):
        # Test code that uses RoleCache across multiple modules
        pass
```

## Predefined Role Mappings

The utility provides several predefined role mappings for common test scenarios:

```python
from tests.unit.runtime.runtime_database.test_utils import (
    COMMON_TEST_ROLES,
    PRODUCTION_ROLES,
    INSTRUMENT_ROLES,
    VOCAL_ROLES
)

# Use predefined roles
with RoleCacheMockHelper.mock_role_cache(COMMON_TEST_ROLES):
    # Test with Producer, Engineer, Vocalist, Guitarist, Drummer
    pass

with RoleCacheMockHelper.mock_role_cache(PRODUCTION_ROLES):
    # Test with Producer, Executive Producer, Co-Producer
    pass
```

## Common Patterns by Module

### Runtime Relation Repository Tests

```python
def test_runtime_relation_repository():
    with RoleCacheMockHelper.mock_role_cache_in_module(
        "musigree.runtime.runtime_database.runtime_relation_repository",
        {"Producer": 1}
    ):
        # Test repository methods that use role_name lookups
        pass
```

### Role Entry Tests

```python
def test_role_entry():
    role_mappings = {"Producer": 1, "Engineer": 2}
    role_categories = {1: "Production", 2: "Technical"}

    with RoleCacheMockHelper.mock_role_cache_in_module(
        "musigree.runtime.data_access_layer.role_entry",
        role_mappings
    ) as mock_cache:
        mock_cache.role_id_to_role_category_lookup = role_categories
        # Test RoleEntry.get_multiselect_mapping()
        pass
```

### Runtime Role Repository Tests

```python
def test_runtime_role_repository():
    # These typically don't need RoleCache mocking since they manage roles
    # But if they do interact with cache, use:
    with RoleCacheMockHelper.mock_role_cache_in_module(
        "musigree.runtime.runtime_database.runtime_role_repository",
        {"Producer": 1}
    ):
        pass
```

## Best Practices

1. **Use module-specific mocking** when the module imports RoleCache directly
2. **Use the context manager approach** for cleaner test code
3. **Use predefined role mappings** when possible to maintain consistency
4. **Set up role categories** when testing code that uses `role_id_to_role_category_lookup`
5. **Keep role mappings simple** - use small, focused datasets for each test
6. **Document the role mappings** used in complex tests

## Troubleshooting

### KeyError: 'RoleName'

This usually means the RoleCache mock isn't being applied correctly. Check:

1. Are you using the right module path for `mock_role_cache_in_module`?
2. Is the role name spelled correctly in your test data?
3. Are you setting up the mock before the code that uses it runs?

### Empty Results

If your test returns empty results when you expect data:

1. Check that `role_id_to_role_category_lookup` is set up if needed
2. Verify that the role mappings include all the roles your test code expects
3. Make sure the mock is active during the entire test execution

### Import Errors

If you get import errors for the test utility:

```python
# Make sure you're importing from the correct path
from tests.unit.runtime.runtime_database.test_utils import RoleCacheMockHelper
```

## Examples from the Codebase

See these files for working examples:

-   `tests/unit/runtime/runtime_database/test_runtime_relation_repository.py`
-   `tests/unit/runtime/data_access_layer/test_role_entry.py`

These demonstrate the proper usage patterns for different scenarios.
