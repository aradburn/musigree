import unittest
from unittest.mock import Mock, patch

from sqlalchemy import Result
from musigree.exceptions import NotFoundError
from musigree.runtime.runtime_database.runtime_relation_repository import RuntimeRelationRepository
from musigree.runtime.runtime_database.runtime_relation_table import RuntimeRelationTable
from musigree.runtime.runtime_domain.relation import RuntimeRelationDB, RuntimeRelationUncommitted, RuntimeRelationInternal

# Import the test utility
from .test_utils import RoleCacheMockHelper, SessionMockHelper


class TestRuntimeRelationRepository(unittest.TestCase):
    """Unit tests for RuntimeRelationRepository class."""

    def setUp(self):
        """Set up test fixtures."""
        self.repository = RuntimeRelationRepository()

    def test_schema_class(self):
        """Test that schema_class is correctly set."""
        # GIVEN/WHEN/THEN
        self.assertEqual(self.repository.schema_class, RuntimeRelationTable)

    @patch.object(RuntimeRelationRepository, 'execute')
    def test_get_success(self, mock_execute):
        """Test successfully retrieving a relation by ID."""
        # GIVEN
        relation_id = 1
        mock_instance = Mock()
        mock_instance.id = relation_id
        mock_instance.subject = 12345
        mock_instance.predicate = 3
        mock_instance.object = 67890
        
        mock_result = Mock(spec=Result)
        mock_scalars = Mock()
        mock_scalars.one_or_none.return_value = mock_instance
        mock_result.scalars.return_value = mock_scalars
        mock_execute.return_value = mock_result
        
        with patch.object(RuntimeRelationDB, 'model_validate') as mock_validate:
            expected_relation = RuntimeRelationDB(
                id=relation_id,
                subject=12345,
                predicate=3,
                object=67890
            )
            mock_validate.return_value = expected_relation
            
            # WHEN
            result = self.repository.get(relation_id)
            
            # THEN
            self.assertEqual(result, expected_relation)
            mock_validate.assert_called_once_with(mock_instance)

    @patch.object(RuntimeRelationRepository, 'execute')
    def test_get_not_found(self, mock_execute):
        """Test retrieving a relation by ID when not found."""
        # GIVEN
        relation_id = 999
        
        mock_result = Mock(spec=Result)
        mock_scalars = Mock()
        mock_scalars.one_or_none.return_value = None
        mock_result.scalars.return_value = mock_scalars
        mock_execute.return_value = mock_result
        
        # WHEN/THEN
        with self.assertRaises(NotFoundError):
            self.repository.get(relation_id)

    @patch.object(RuntimeRelationRepository, 'execute')
    def test_get_id_by_key_success(self, mock_execute):
        """Test successfully retrieving relation ID by key."""
        # GIVEN
        key = {"subject": 12345, "role_id": 3, "object": 67890}
        expected_id = 1
        
        mock_result = Mock(spec=Result)
        mock_result.scalar.return_value = expected_id
        mock_execute.return_value = mock_result
        
        # WHEN
        result = self.repository.get_id_by_key(key)
        
        # THEN
        self.assertEqual(result, expected_id)

    @patch.object(RuntimeRelationRepository, 'execute')
    def test_get_id_by_key_not_found(self, mock_execute):
        """Test get_id_by_key when relation not found."""
        # GIVEN
        key = {"subject": 12345, "role_id": 3, "object": 67890}
        
        mock_result = Mock(spec=Result)
        mock_result.scalar.return_value = None
        mock_execute.return_value = mock_result
        
        # WHEN/THEN
        with self.assertRaises(NotFoundError):
            self.repository.get_id_by_key(key)

    @patch.object(RuntimeRelationRepository, 'execute')
    def test_find_by_id_success(self, mock_execute):
        """Test successfully finding relation by ID with lock."""
        # GIVEN
        relation_id = 1
        mock_instance = Mock()
        mock_instance.id = relation_id
        mock_instance.subject = 12345
        mock_instance.predicate = 3
        mock_instance.object = 67890
        
        mock_result = Mock(spec=Result)
        mock_scalars = Mock()
        mock_scalars.one_or_none.return_value = mock_instance
        mock_result.scalars.return_value = mock_scalars
        mock_execute.return_value = mock_result
        
        with patch.object(RuntimeRelationRepository, '_get_one_by_query') as mock_get_one:
            mock_relation = Mock()
            mock_get_one.return_value = mock_relation
            
            # WHEN
            result = self.repository.find_by_id(relation_id)
            
            # THEN
            self.assertEqual(result, mock_relation)

    @patch.object(RuntimeRelationRepository, 'execute')
    def test_find_by_key_with_role_name(self, mock_execute):
        """Test finding relation by key when role_name is provided."""
        # GIVEN
        key = {"subject": 12345, "role_name": "Producer", "object": 67890}
        role_id = 3
        
        # Use the RoleCacheMockHelper for proper module-specific mocking
        with RoleCacheMockHelper.mock_role_cache_in_module(
            "musigree.runtime.runtime_database.runtime_relation_repository",
            {"Producer": role_id}
        ):
            mock_instance = Mock()
            mock_instance.id = 1
            mock_instance.subject = 12345
            mock_instance.predicate = role_id
            mock_instance.object = 67890
            
            mock_result = Mock(spec=Result)
            mock_scalars = Mock()
            mock_scalars.one_or_none.return_value = mock_instance
            mock_result.scalars.return_value = mock_scalars
            mock_execute.return_value = mock_result
            
            with patch.object(RuntimeRelationRepository, '_get_one_by_query') as mock_get_one:
                mock_relation = Mock()
                mock_get_one.return_value = mock_relation
                
                # WHEN
                result = self.repository.find_by_key(key)
                
                # THEN
                self.assertEqual(result, mock_relation)

    @patch.object(RuntimeRelationRepository, 'execute')
    def test_find_by_entity_success(self, mock_execute):
        """Test successfully finding relations by entity ID."""
        # GIVEN
        entity_id = 12345
        
        mock_instance1 = Mock()
        mock_instance1.id = 1
        mock_instance1.subject = entity_id
        mock_instance1.predicate = 3
        mock_instance1.object = 67890
        
        mock_instance2 = Mock()
        mock_instance2.id = 2
        mock_instance2.subject = 11111
        mock_instance2.predicate = 4
        mock_instance2.object = entity_id
        
        mock_result = Mock(spec=Result)
        mock_scalars = Mock()
        mock_scalars.all.return_value = [mock_instance1, mock_instance2]
        mock_result.scalars.return_value = mock_scalars
        mock_execute.return_value = mock_result
        
        with patch.object(RuntimeRelationRepository, '_get_all_by_query') as mock_get_all:
            mock_relations = [Mock(), Mock()]
            mock_get_all.return_value = mock_relations
            
            # WHEN
            result = self.repository.find_by_entity(entity_id)
            
            # THEN
            self.assertEqual(result, mock_relations)
            self.assertEqual(len(result), 2)

    @patch.object(RuntimeRelationRepository, 'execute')
    def test_find_by_entity_and_roles_success(self, mock_execute):
        """Test successfully finding relations by entity ID and role IDs."""
        # GIVEN
        entity_id = 12345
        role_ids = [3, 4, 5]
        
        mock_instance = Mock()
        mock_instance.id = 1
        mock_instance.subject = entity_id
        mock_instance.predicate = 3
        mock_instance.object = 67890
        
        mock_result = Mock(spec=Result)
        mock_scalars = Mock()
        mock_scalars.all.return_value = [mock_instance]
        mock_result.scalars.return_value = mock_scalars
        mock_execute.return_value = mock_result
        
        with patch.object(RuntimeRelationRepository, '_get_all_by_query') as mock_get_all:
            mock_relations = [Mock()]
            mock_get_all.return_value = mock_relations
            
            # WHEN
            result = self.repository.find_by_entity_and_roles(entity_id, role_ids)
            
            # THEN
            self.assertEqual(result, mock_relations)
            self.assertEqual(len(result), 1)

    @patch('musigree.runtime.runtime_database_manager.RuntimeDatabaseManager')
    def test_create_success(self, mock_db_manager):
        """Test successful creation of a relation."""
        # Setup test data
        role_id = 1
        relation_data = {
            "subject": 1,
            "role_name": "Producer",
            "object": 2,
        }
        
        # Create mock result and instance
        mock_result = Mock()
        mock_instance = Mock()
        mock_result.scalar_one_or_none.return_value = mock_instance
        
        # Use the SessionMockHelper for session mocking
        with SessionMockHelper.mock_runtime_session(
            execute_return_value=mock_result,
            flush_return_value=None
        ) as mock_session:
            # Mock the RoleCache with module-specific mocking
            with RoleCacheMockHelper.mock_role_cache_in_module(
                "musigree.runtime.runtime_database.runtime_relation_repository",
                {"Producer": role_id}
            ):
                # Mock the database manager and its methods
                mock_helper = mock_db_manager.runtime_database_helper
                mock_query = Mock()
                mock_helper.generate_insert_query.return_value = mock_query
                
                # Mock the model validation
                with patch('musigree.runtime.runtime_database.runtime_relation_repository.RuntimeRelationDB') as mock_relation_db:
                    mock_relation_db_instance = Mock()
                    mock_domain_instance = Mock()
                    mock_relation_db_instance.to_domain.return_value = mock_domain_instance
                    mock_relation_db.model_validate.return_value = mock_relation_db_instance
                    
                    # Create the relation
                    relation = RuntimeRelationUncommitted(**relation_data)
                    result = self.repository.create(relation)
                    
                    # Verify the result
                    assert result == mock_domain_instance
                    
                    # Verify the calls
                    expected_relation_dict = {
                        "subject": 1,
                        "object": 2,
                        "predicate": role_id
                    }
                    mock_helper.generate_insert_query.assert_called_once_with(
                        RuntimeRelationTable, expected_relation_dict, False
                    )
                    mock_session.execute.assert_called_once_with(mock_query)
                    mock_session.flush.assert_called_once()
                    mock_relation_db.model_validate.assert_called_once_with(mock_instance)

    @patch.object(RuntimeRelationRepository, 'execute')
    def test_delete_by_entitys_success(self, mock_execute):
        """Test successfully deleting relations by entity ID."""
        # GIVEN
        entity_id = 12345
        mock_result = Mock(spec=Result)
        mock_execute.return_value = mock_result
        
        # WHEN
        self.repository.delete_by_entitys(entity_id)
        
        # THEN
        mock_execute.assert_called_once()

    def test_all_iterator(self):
        """Test the all() iterator method."""
        # Create mock instances with the data that RuntimeRelationDB expects
        mock_instance1 = Mock()
        mock_instance1.id = 1
        mock_instance1.subject = 100
        mock_instance1.predicate = 3  # This will be converted to role name via to_domain()
        mock_instance1.object = 200

        mock_instance2 = Mock()
        mock_instance2.id = 2
        mock_instance2.subject = 101
        mock_instance2.predicate = 4  # This will be converted to role name via to_domain()
        mock_instance2.object = 201

        # Mock the _all method to return our test data
        with patch.object(self.repository, '_all') as mock_all:
            mock_all.return_value = [mock_instance1, mock_instance2]
            
            # Mock RoleCache in the domain module where to_domain() is defined
            role_mappings = {"Producer": 3, "Engineer": 4}
            with RoleCacheMockHelper.mock_role_cache_in_module(
                "musigree.runtime.runtime_domain.relation",
                role_mappings
            ):
                # Execute the method
                result = list(self.repository.all())

                # Verify results
                self.assertEqual(len(result), 2)
                
                # Check that results are RuntimeRelationInternal instances
                for relation in result:
                    self.assertIsInstance(relation, RuntimeRelationInternal)
                
                # Verify the first relation
                self.assertEqual(result[0].id, 1)
                self.assertEqual(result[0].subject, 100)
                self.assertEqual(result[0].role, "Producer")  # Converted from predicate 3
                self.assertEqual(result[0].object, 200)
                
                # Verify the second relation
                self.assertEqual(result[1].id, 2)
                self.assertEqual(result[1].subject, 101)
                self.assertEqual(result[1].role, "Engineer")  # Converted from predicate 4
                self.assertEqual(result[1].object, 201)


if __name__ == '__main__':
    unittest.main() 