import unittest
from unittest.mock import Mock, patch

from sqlalchemy import Result
from musigree.exceptions import NotFoundError
from musigree.runtime.runtime_database.runtime_role_repository import RuntimeRoleRepository
from musigree.runtime.runtime_database.runtime_role_table import RuntimeRoleTable
from musigree.runtime.runtime_domain.role import RuntimeRole


class TestRuntimeRoleRepository(unittest.TestCase):
    """Unit tests for RuntimeRoleRepository class."""

    def setUp(self):
        """Set up test fixtures."""
        self.repository = RuntimeRoleRepository()

    def test_schema_class(self):
        """Test that schema_class is correctly set."""
        # GIVEN/WHEN/THEN
        self.assertEqual(self.repository.schema_class, RuntimeRoleTable)

    @patch.object(RuntimeRoleRepository, 'execute')
    def test_get_success(self, mock_execute):
        """Test successfully retrieving a role by ID."""
        # GIVEN
        role_id = 1
        mock_instance = Mock()
        mock_instance.id = role_id
        mock_instance.role_name = "Producer"
        mock_instance.role_category = "PRODUCTION"
        mock_instance.role_subcategory = "NONE"
        
        mock_result = Mock(spec=Result)
        mock_scalars = Mock()
        mock_scalars.one_or_none.return_value = mock_instance
        mock_result.scalars.return_value = mock_scalars
        mock_execute.return_value = mock_result
        
        with patch.object(RuntimeRole, 'model_validate') as mock_validate:
            expected_role = Mock()
            mock_validate.return_value = expected_role
            
            # WHEN
            result = self.repository.get(role_id)
            
            # THEN
            self.assertEqual(result, expected_role)
            mock_validate.assert_called_once_with(mock_instance)

    @patch.object(RuntimeRoleRepository, 'execute')
    def test_get_not_found(self, mock_execute):
        """Test retrieving a role by ID when not found."""
        # GIVEN
        role_id = 999
        
        mock_result = Mock(spec=Result)
        mock_scalars = Mock()
        mock_scalars.one_or_none.return_value = None
        mock_result.scalars.return_value = mock_scalars
        mock_execute.return_value = mock_result
        
        # WHEN/THEN
        with self.assertRaises(NotFoundError):
            self.repository.get(role_id)

    @patch('musigree.runtime.runtime_database.runtime_role_repository.CacheManager')
    @patch.object(RuntimeRoleRepository, 'execute')
    def test_get_by_name_from_cache(self, mock_execute, mock_cache_manager):
        """Test successfully retrieving a role by name from cache."""
        # GIVEN
        role_name = "Producer"
        cached_role = Mock()
        
        mock_cache = Mock()
        mock_cache.get.return_value = cached_role
        mock_cache_manager.get_cache.return_value = mock_cache
        
        # WHEN
        result = self.repository.get_by_name(role_name)
        
        # THEN
        self.assertEqual(result, cached_role)
        mock_cache.get.assert_called_once_with(f"ROLE-{role_name}")
        mock_execute.assert_not_called()

    @patch('musigree.runtime.runtime_database.runtime_role_repository.CacheManager')
    @patch.object(RuntimeRoleRepository, 'execute')
    def test_get_by_name_from_database(self, mock_execute, mock_cache_manager):
        """Test retrieving a role by name from database when not in cache."""
        # GIVEN
        role_name = "Producer"
        mock_instance = Mock()
        mock_instance.id = 1
        mock_instance.role_name = role_name
        mock_instance.role_category = "PRODUCTION"
        mock_instance.role_subcategory = "NONE"
        
        mock_cache = Mock()
        mock_cache.get.return_value = None  # Not in cache
        mock_cache_manager.get_cache.return_value = mock_cache
        
        mock_result = Mock(spec=Result)
        mock_scalars = Mock()
        mock_scalars.one_or_none.return_value = mock_instance
        mock_result.scalars.return_value = mock_scalars
        mock_execute.return_value = mock_result
        
        with patch.object(RuntimeRole, 'model_validate') as mock_validate:
            expected_role = Mock()
            mock_validate.return_value = expected_role
            
            # WHEN
            result = self.repository.get_by_name(role_name)
            
            # THEN
            self.assertEqual(result, expected_role)
            mock_cache.get.assert_called_once_with(f"ROLE-{role_name}")
            mock_cache.set.assert_called_once_with(f"ROLE-{role_name}", expected_role)
            mock_validate.assert_called_once_with(mock_instance)

    @patch('musigree.runtime.runtime_database.runtime_role_repository.CacheManager')
    @patch.object(RuntimeRoleRepository, 'execute')
    def test_get_by_name_not_found(self, mock_execute, mock_cache_manager):
        """Test get_by_name when role not found in database."""
        # GIVEN
        role_name = "NonexistentRole"
        
        mock_cache = Mock()
        mock_cache.get.return_value = None  # Not in cache
        mock_cache_manager.get_cache.return_value = mock_cache
        
        mock_result = Mock(spec=Result)
        mock_scalars = Mock()
        mock_scalars.one_or_none.return_value = None
        mock_result.scalars.return_value = mock_scalars
        mock_execute.return_value = mock_result
        
        # WHEN/THEN
        with self.assertRaises(NotFoundError):
            self.repository.get_by_name(role_name)

    @patch('musigree.runtime.runtime_database.runtime_role_repository.CacheManager')
    @patch.object(RuntimeRoleRepository, 'execute')
    def test_get_by_name_cache_failure(self, mock_execute, mock_cache_manager):
        """Test get_by_name when cache fails - exception should propagate."""
        # GIVEN
        role_name = "Producer"
        
        mock_cache = Mock()
        mock_cache.get.side_effect = Exception("Cache error")  # Cache fails
        mock_cache_manager.get_cache.return_value = mock_cache
        
        # WHEN/THEN
        # The current implementation doesn't handle cache failures gracefully,
        # so the exception should propagate up
        with self.assertRaises(Exception) as context:
            self.repository.get_by_name(role_name)
        
        self.assertEqual(str(context.exception), "Cache error")
        # Database should not be called since cache failure prevents fallback
        mock_execute.assert_not_called()

    @patch.object(RuntimeRoleRepository, '_save')
    def test_create_success(self, mock_save):
        """Test successfully creating a new role."""
        # GIVEN
        role_data = {
            "role_name": "Producer",
            "role_category": "PRODUCTION",
            "role_subcategory": "NONE",
            "role_category_name": "Production",
            "role_subcategory_name": "None"
        }
        mock_role = Mock()
        mock_role.model_dump.return_value = role_data
        
        mock_instance = Mock()
        mock_instance.id = 1
        mock_instance.role_name = "Producer"
        mock_instance.role_category = "PRODUCTION"
        mock_instance.role_subcategory = "NONE"
        mock_save.return_value = mock_instance
        
        with patch.object(RuntimeRole, 'model_validate') as mock_validate:
            expected_role = Mock()
            mock_validate.return_value = expected_role
            
            # WHEN
            result = self.repository.create(mock_role)
            
            # THEN
            self.assertEqual(result, expected_role)
            mock_save.assert_called_once_with(role_data)
            mock_validate.assert_called_once_with(mock_instance)

    @patch.object(RuntimeRoleRepository, '_all')
    def test_all_iterator(self, mock_all):
        """Test the all() iterator method."""
        # GIVEN
        mock_instance1 = Mock()
        mock_instance1.id = 1
        mock_instance1.role_name = "Producer"
        mock_instance1.role_category = "PRODUCTION"
        
        mock_instance2 = Mock()
        mock_instance2.id = 2
        mock_instance2.role_name = "Vocalist"
        mock_instance2.role_category = "VOCAL"
        
        mock_all.return_value = [mock_instance1, mock_instance2]
        
        with patch.object(RuntimeRole, 'model_validate') as mock_validate:
            mock_validate.side_effect = [
                Mock(id=1, role_name="Producer"),
                Mock(id=2, role_name="Vocalist")
            ]
            
            # WHEN
            result = list(self.repository.all())
            
            # THEN
            self.assertEqual(len(result), 2)
            self.assertEqual(mock_validate.call_count, 2)
            mock_validate.assert_any_call(mock_instance1)
            mock_validate.assert_any_call(mock_instance2)

    def test_cache_key_format(self):
        """Test that cache key format is correct."""
        # GIVEN
        role_name = "Test Role"
        expected_key = f"ROLE-{role_name}"
        
        with patch('musigree.runtime.runtime_database.runtime_role_repository.CacheManager') as mock_cache_manager:
            with patch.object(RuntimeRoleRepository, 'execute'):
                mock_cache = Mock()
                mock_cache.get.return_value = Mock()  # Return cached value
                mock_cache_manager.get_cache.return_value = mock_cache
                
                # WHEN
                self.repository.get_by_name(role_name)
                
                # THEN
                mock_cache.get.assert_called_once_with(expected_key)


if __name__ == '__main__':
    unittest.main() 