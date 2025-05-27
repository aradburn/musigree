import unittest
from unittest.mock import Mock, patch, MagicMock
from collections.abc import Iterator

from sqlalchemy import Result
from musigree.exceptions import NotFoundError
from musigree.runtime.runtime_database.style_repository import StyleRepository
from musigree.runtime.runtime_database.style_table import StyleTable
from musigree.runtime.runtime_domain.style import Style


class TestStyleRepository(unittest.TestCase):
    """Unit tests for StyleRepository class."""

    def setUp(self):
        """Set up test fixtures."""
        self.repository = StyleRepository()

    def test_schema_class(self):
        """Test that schema_class is correctly set."""
        # GIVEN/WHEN/THEN
        self.assertEqual(self.repository.schema_class, StyleTable)

    @patch.object(StyleRepository, '_all')
    def test_all(self, mock_all):
        """Test retrieving all styles."""
        # GIVEN
        mock_instance1 = Mock()
        mock_instance1.id = 1
        mock_instance1.style_name = "Electronic"
        
        mock_instance2 = Mock()
        mock_instance2.id = 2
        mock_instance2.style_name = "Rock"
        
        mock_all.return_value = [mock_instance1, mock_instance2]
        
        with patch.object(Style, 'model_validate') as mock_validate:
            mock_validate.side_effect = [
                Style(id=1, style_name="Electronic"),
                Style(id=2, style_name="Rock")
            ]
            
            # WHEN
            result = list(self.repository.all())
            
            # THEN
            self.assertEqual(len(result), 2)
            self.assertIsInstance(result[0], Style)
            self.assertIsInstance(result[1], Style)
            self.assertEqual(result[0].style_name, "Electronic")
            self.assertEqual(result[1].style_name, "Rock")

    @patch.object(StyleRepository, 'execute')
    def test_get_success(self, mock_execute):
        """Test successfully retrieving a style by ID."""
        # GIVEN
        style_id = 1
        mock_instance = Mock()
        mock_instance.id = style_id
        mock_instance.style_name = "Electronic"
        
        mock_result = Mock(spec=Result)
        mock_scalars = Mock()
        mock_scalars.one_or_none.return_value = mock_instance
        mock_result.scalars.return_value = mock_scalars
        mock_execute.return_value = mock_result
        
        with patch.object(Style, 'model_validate') as mock_validate:
            expected_style = Style(id=style_id, style_name="Electronic")
            mock_validate.return_value = expected_style
            
            # WHEN
            result = self.repository.get(style_id)
            
            # THEN
            self.assertEqual(result, expected_style)
            mock_validate.assert_called_once_with(mock_instance)

    @patch.object(StyleRepository, 'execute')
    def test_get_not_found(self, mock_execute):
        """Test retrieving a style by ID when not found."""
        # GIVEN
        style_id = 999
        
        mock_result = Mock(spec=Result)
        mock_scalars = Mock()
        mock_scalars.one_or_none.return_value = None
        mock_result.scalars.return_value = mock_scalars
        mock_execute.return_value = mock_result
        
        # WHEN/THEN
        with self.assertRaises(NotFoundError):
            self.repository.get(style_id)

    @patch.object(StyleRepository, 'execute')
    def test_get_by_name_success(self, mock_execute):
        """Test successfully retrieving a style by name."""
        # GIVEN
        style_name = "Electronic"
        mock_instance = Mock()
        mock_instance.id = 1
        mock_instance.style_name = style_name
        
        mock_result = Mock(spec=Result)
        mock_scalars = Mock()
        mock_scalars.one_or_none.return_value = mock_instance
        mock_result.scalars.return_value = mock_scalars
        mock_execute.return_value = mock_result
        
        with patch.object(Style, 'model_validate') as mock_validate:
            expected_style = Style(id=1, style_name=style_name)
            mock_validate.return_value = expected_style
            
            # WHEN
            result = self.repository.get_by_name(style_name)
            
            # THEN
            self.assertEqual(result, expected_style)
            mock_validate.assert_called_once_with(mock_instance)

    @patch.object(StyleRepository, 'execute')
    def test_get_by_name_not_found(self, mock_execute):
        """Test retrieving a style by name when not found."""
        # GIVEN
        style_name = "NonexistentStyle"
        
        mock_result = Mock(spec=Result)
        mock_scalars = Mock()
        mock_scalars.one_or_none.return_value = None
        mock_result.scalars.return_value = mock_scalars
        mock_execute.return_value = mock_result
        
        # WHEN/THEN
        with self.assertRaises(NotFoundError):
            self.repository.get_by_name(style_name)

    @patch.object(StyleRepository, '_save')
    def test_create(self, mock_save):
        """Test creating a new style."""
        # GIVEN
        style = Style(id=1, style_name="Electronic")
        mock_instance = Mock()
        mock_instance.id = 1
        mock_instance.style_name = "Electronic"
        mock_save.return_value = mock_instance
        
        with patch.object(Style, 'model_validate') as mock_validate:
            expected_style = Style(id=1, style_name="Electronic")
            mock_validate.return_value = expected_style
            
            # WHEN
            result = self.repository.create(style)
            
            # THEN
            self.assertEqual(result, expected_style)
            mock_save.assert_called_once_with(style.model_dump())
            mock_validate.assert_called_once_with(mock_instance) 