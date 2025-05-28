import unittest
from unittest.mock import Mock, patch

from sqlalchemy import Result

from musigree.exceptions import NotFoundError, UnprocessableError
from musigree.library.fields.entity_type import EntityType
from musigree.runtime.runtime_database.runtime_entity_repository import RuntimeEntityRepository
from musigree.runtime.runtime_database.runtime_entity_table import RuntimeEntityTable
from musigree.runtime.runtime_domain.entity import RuntimeEntityDB
# Import the test utility
from .test_utils import SessionMockHelper


class TestRuntimeEntityRepository(unittest.TestCase):
    """Unit tests for RuntimeEntityRepository class."""

    def setUp(self):
        """Set up test fixtures."""
        self.repository = RuntimeEntityRepository()

    def test_schema_class(self):
        """Test that schema_class is correctly set."""
        # GIVEN/WHEN/THEN
        self.assertEqual(self.repository.schema_class, RuntimeEntityTable)

    @patch.object(RuntimeEntityRepository, 'execute')
    def test_get_by_id_not_found(self, mock_execute):
        """Test retrieving an entity by ID when not found."""
        # GIVEN
        entity_id = 999
        
        mock_result = Mock(spec=Result)
        mock_scalars = Mock()
        mock_scalars.one_or_none.return_value = None
        mock_result.scalars.return_value = mock_scalars
        mock_execute.return_value = mock_result
        
        # WHEN/THEN
        with self.assertRaises(NotFoundError):
            self.repository.get_by_id(entity_id)

    @patch.object(RuntimeEntityRepository, 'execute')
    def test_get_by_id_success(self, mock_execute):
        """Test successfully retrieving an entity by ID."""
        # GIVEN
        entity_id = 1
        mock_instance = Mock()
        mock_instance.id = entity_id
        mock_instance.entity_id = 12345
        mock_instance.entity_type = EntityType.ARTIST
        mock_instance.entity_name = "Test Entity"
        mock_instance.relation_counts = {}
        mock_instance.entity_metadata = {}
        mock_instance.aliases = None
        mock_instance.groups = None
        mock_instance.members = None
        mock_instance.countries = None
        mock_instance.genres = None
        mock_instance.styles = None
        
        mock_result = Mock(spec=Result)
        mock_scalars = Mock()
        mock_scalars.one_or_none.return_value = mock_instance
        mock_result.scalars.return_value = mock_scalars
        mock_execute.return_value = mock_result
        
        # Mock the model validation and domain conversion
        with patch.object(RuntimeEntityDB, 'model_validate') as mock_validate:
            mock_entity_db = Mock()
            mock_domain_entity = Mock()
            mock_entity_db.to_domain.return_value = mock_domain_entity
            mock_validate.return_value = mock_entity_db
            
            # WHEN
            result = self.repository.get_by_id(entity_id)
            
            # THEN
            self.assertEqual(result, mock_domain_entity)
            mock_validate.assert_called_once_with(mock_instance)
            mock_entity_db.to_domain.assert_called_once()

    @patch.object(RuntimeEntityRepository, 'execute')
    def test_count_by_type_success(self, mock_execute):
        """Test successfully counting entities by type."""
        # GIVEN
        entity_type = EntityType.ARTIST
        expected_count = 100
        
        mock_result = Mock(spec=Result)
        mock_result.scalar.return_value = expected_count
        mock_execute.return_value = mock_result
        
        # WHEN
        result = self.repository.count_by_type(entity_type)
        
        # THEN
        self.assertEqual(result, expected_count)

    @patch.object(RuntimeEntityRepository, 'execute')
    def test_count_by_type_non_integer_error(self, mock_execute):
        """Test count_by_type when database returns non-integer."""
        # GIVEN
        entity_type = EntityType.ARTIST
        
        mock_result = Mock(spec=Result)
        mock_result.scalar.return_value = "not_an_integer"
        mock_execute.return_value = mock_result
        
        # WHEN/THEN
        with self.assertRaises(UnprocessableError):
            self.repository.count_by_type(entity_type)

    def test_update_success(self):
        """Test successfully updating an entity."""
        # GIVEN
        entity_id = 1
        payload = {"entity_name": "Updated Name", "genres": "Updated Genre"}
        
        # Create mock result and instance
        mock_result = Mock()
        mock_instance = Mock()
        mock_instance.id = entity_id
        mock_instance.entity_name = "Updated Name"
        mock_instance.genres = "Updated Genre"
        mock_result.scalar_one_or_none.return_value = mock_instance
        
        # Use SessionMockHelper to mock the session
        with SessionMockHelper.mock_runtime_session(
            execute_return_value=mock_result,
            flush_return_value=None
        ) as mock_session:
            # WHEN
            result = self.repository.update(entity_id, payload)
            
            # THEN
            self.assertEqual(result, mock_instance)
            mock_session.execute.assert_called_once()
            mock_session.flush.assert_called_once()

    @patch.object(RuntimeEntityRepository, 'execute')
    def test_delete_by_id_success(self, mock_execute):
        """Test successfully deleting an entity by ID."""
        # GIVEN
        entity_id = 1
        mock_result = Mock(spec=Result)
        mock_execute.return_value = mock_result
        
        # WHEN
        self.repository.delete_by_id(entity_id)
        
        # THEN
        mock_execute.assert_called_once()

    @patch.object(RuntimeEntityRepository, 'execute')
    def test_get_by_entity_id_and_entity_type_not_found(self, mock_execute):
        """Test get_by_entity_id_and_entity_type when entity not found."""
        # GIVEN
        entity_id = 12345
        entity_type = EntityType.ARTIST
        
        mock_result = Mock(spec=Result)
        mock_scalars = Mock()
        mock_scalars.one_or_none.return_value = None
        mock_result.scalars.return_value = mock_scalars
        mock_execute.return_value = mock_result
        
        # WHEN/THEN
        with self.assertRaises(NotFoundError):
            self.repository.get_by_entity_id_and_entity_type(entity_id, entity_type)

    @patch.object(RuntimeEntityRepository, 'execute')
    def test_get_by_entity_id_and_entity_type_success(self, mock_execute):
        """Test successfully getting entity by entity_id and entity_type."""
        # GIVEN
        entity_id = 12345
        entity_type = EntityType.ARTIST
        mock_instance = Mock()
        mock_instance.id = 1
        mock_instance.entity_id = entity_id
        mock_instance.entity_type = entity_type
        mock_instance.entity_name = "Test Artist"
        mock_instance.relation_counts = {}
        mock_instance.entity_metadata = {}
        mock_instance.aliases = None
        mock_instance.groups = None
        mock_instance.members = None
        mock_instance.countries = None
        mock_instance.genres = None
        mock_instance.styles = None
        
        mock_result = Mock(spec=Result)
        mock_scalars = Mock()
        mock_scalars.one_or_none.return_value = mock_instance
        mock_result.scalars.return_value = mock_scalars
        mock_execute.return_value = mock_result
        
        # Mock the model validation and domain conversion
        with patch.object(RuntimeEntityDB, 'model_validate') as mock_validate:
            mock_entity_db = Mock()
            mock_domain_entity = Mock()
            mock_entity_db.to_domain.return_value = mock_domain_entity
            mock_validate.return_value = mock_entity_db
            
            # WHEN
            result = self.repository.get_by_entity_id_and_entity_type(entity_id, entity_type)
            
            # THEN
            self.assertEqual(result, mock_domain_entity)
            mock_validate.assert_called_once_with(mock_instance)
            mock_entity_db.to_domain.assert_called_once()

    @patch.object(RuntimeEntityRepository, 'execute')
    def test_get_by_type_and_name_not_found(self, mock_execute):
        """Test get_by_type_and_name when entity not found."""
        # GIVEN
        entity_type = EntityType.LABEL
        entity_name = "Nonexistent Label"
        
        mock_result = Mock(spec=Result)
        mock_scalars = Mock()
        mock_scalars.one_or_none.return_value = None
        mock_result.scalars.return_value = mock_scalars
        mock_execute.return_value = mock_result
        
        # WHEN/THEN
        with self.assertRaises(NotFoundError):
            self.repository.get_by_type_and_name(entity_type, entity_name)

    @patch.object(RuntimeEntityRepository, 'execute')
    def test_get_by_type_and_name_success(self, mock_execute):
        """Test successfully getting entity by type and name."""
        # GIVEN
        entity_type = EntityType.LABEL
        entity_name = "Capitol Records"
        mock_instance = Mock()
        mock_instance.id = 1
        mock_instance.entity_id = 67890
        mock_instance.entity_type = entity_type
        mock_instance.entity_name = entity_name
        mock_instance.relation_counts = {}
        mock_instance.entity_metadata = {}
        mock_instance.aliases = None
        mock_instance.groups = None
        mock_instance.members = None
        mock_instance.countries = None
        mock_instance.genres = None
        mock_instance.styles = None
        
        mock_result = Mock(spec=Result)
        mock_scalars = Mock()
        mock_scalars.one_or_none.return_value = mock_instance
        mock_result.scalars.return_value = mock_scalars
        mock_execute.return_value = mock_result
        
        # Mock the model validation and domain conversion
        with patch.object(RuntimeEntityDB, 'model_validate') as mock_validate:
            mock_entity_db = Mock()
            mock_domain_entity = Mock()
            mock_entity_db.to_domain.return_value = mock_domain_entity
            mock_validate.return_value = mock_entity_db
            
            # WHEN
            result = self.repository.get_by_type_and_name(entity_type, entity_name)
            
            # THEN
            self.assertEqual(result, mock_domain_entity)
            mock_validate.assert_called_once_with(mock_instance)
            mock_entity_db.to_domain.assert_called_once()

    def test_get_entity_id_by_entity_type_and_entity_name_success(self):
        """Test successfully getting entity_id by type and name."""
        # GIVEN
        entity_type = EntityType.ARTIST
        entity_name = "The Beatles"
        expected_entity_id = 12345
        
        # Create mock result
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = expected_entity_id
        
        # Use SessionMockHelper to mock the session
        with SessionMockHelper.mock_runtime_session(
            execute_return_value=mock_result
        ) as mock_session:
            # WHEN
            result = self.repository.get_entity_id_by_entity_type_and_entity_name(entity_type, entity_name)
            
            # THEN
            self.assertEqual(result, expected_entity_id)
            mock_session.execute.assert_called_once()

    def test_get_id_by_entity_type_and_entity_name_success(self):
        """Test successfully getting internal id by type and name."""
        # GIVEN
        entity_type = EntityType.ARTIST
        entity_name = "The Beatles"
        expected_id = 1
        
        # Create mock result
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = expected_id
        
        # Use SessionMockHelper to mock the session
        with SessionMockHelper.mock_runtime_session(
            execute_return_value=mock_result
        ) as mock_session:
            # WHEN
            result = self.repository.get_id_by_entity_type_and_entity_name(entity_type, entity_name)
            
            # THEN
            self.assertEqual(result, expected_id)
            mock_session.execute.assert_called_once()


if __name__ == '__main__':
    unittest.main() 