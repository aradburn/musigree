from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from musigree.exceptions import DatabaseError
from musigree.runtime.data_access_layer.entity_details_index import EntityDetailsIndex
from musigree.transfer.transfer_manager import TransferManager


class TestTransferManager:
    """Test cases for the TransferManager class."""

    def test_bulk_insert_batch_size(self) -> None:
        """Test that BULK_INSERT_BATCH_SIZE is properly defined."""
        assert hasattr(TransferManager, 'BULK_INSERT_BATCH_SIZE')
        assert isinstance(TransferManager.BULK_INSERT_BATCH_SIZE, int)
        assert TransferManager.BULK_INSERT_BATCH_SIZE > 0

    @patch('musigree.transfer.transfer_manager.RuntimeEntityRepository')
    @patch('musigree.transfer.transfer_manager.EntityRepository')
    @patch('musigree.transfer.transfer_manager.runtime_transaction')
    def test_transfer_entity_empty_runtime_table(self, _mock_transaction: Mock, mock_offline_repo: Mock, mock_runtime_repo: Mock) -> None:
        """Test transfer_entity when runtime table is empty (normal case)."""
        # Setup mocks
        mock_offline_instance = Mock()
        mock_runtime_instance = Mock()
        mock_offline_repo.return_value = mock_offline_instance
        mock_runtime_repo.return_value = mock_runtime_instance
        
        # Mock entity details index
        mock_entity_details = Mock(spec=EntityDetailsIndex)
        mock_entity_details.get_countries_for_id.return_value = []
        mock_entity_details.get_genres_for_id.return_value = []
        mock_entity_details.get_styles_for_id.return_value = []
        
        # Mock empty runtime table
        mock_runtime_instance.count.return_value = 0
        mock_offline_instance.count.return_value = 2
        
        # Mock entities
        mock_entity1 = Mock()
        mock_entity1.id = 1
        mock_entity1.model_dump.return_value = {"id": 1, "name": "Entity 1"}
        mock_entity2 = Mock()
        mock_entity2.id = 2
        mock_entity2.model_dump.return_value = {"id": 2, "name": "Entity 2"}
        mock_offline_instance.all.return_value = [mock_entity1, mock_entity2]
        
        # Mock RuntimeDatabaseManager
        with patch('musigree.transfer.transfer_manager.RuntimeDatabaseManager') as mock_db_manager:
            mock_db_manager.get_concurrency_count.return_value = 1  # Single-threaded
            
            # Mock RuntimeEntity
            with patch('musigree.transfer.transfer_manager.RuntimeEntity') as mock_runtime_entity:
                mock_runtime_entity_instance = Mock()
                mock_runtime_entity_instance.to_db.return_value = Mock()
                mock_runtime_entity_instance.to_db.return_value.model_dump.return_value = {"id": 1, "name": "Entity 1"}
                mock_runtime_entity.return_value = mock_runtime_entity_instance
                
                # Call the method
                TransferManager.transfer_entity(mock_entity_details)
                
                # Verify methods were called
                mock_offline_instance.count.assert_called_once()
                mock_runtime_instance.count.assert_called()
                mock_offline_instance.all.assert_called_once()

    @patch('musigree.transfer.transfer_manager.RuntimeEntityRepository')
    @patch('musigree.transfer.transfer_manager.EntityRepository')
    @patch('musigree.transfer.transfer_manager.runtime_transaction')
    def test_transfer_entity_non_empty_runtime_table(self, _mock_transaction: Mock, mock_offline_repo: Mock, mock_runtime_repo: Mock) -> None:
        """Test transfer_entity raises error when runtime table is not empty."""
        # Setup mocks
        mock_offline_instance = Mock()
        mock_runtime_instance = Mock()
        mock_offline_repo.return_value = mock_offline_instance
        mock_runtime_repo.return_value = mock_runtime_instance
        
        # Mock non-empty runtime table
        mock_runtime_instance.count.return_value = 5  # Not empty
        mock_offline_instance.count.return_value = 10
        
        mock_entity_details = Mock(spec=EntityDetailsIndex)
        
        # Should raise DatabaseError
        with pytest.raises(DatabaseError):
            TransferManager.transfer_entity(mock_entity_details)

    @patch('musigree.transfer.transfer_manager.RuntimeRelationRepository')
    @patch('musigree.transfer.transfer_manager.RelationRepository')
    @patch('musigree.transfer.transfer_manager.runtime_transaction')
    def test_transfer_relation_empty_runtime_table(self, _mock_transaction: Mock, mock_offline_repo: Mock, mock_runtime_repo: Mock) -> None:
        """Test transfer_relation when runtime table is empty (normal case)."""
        # Setup mocks
        mock_offline_instance = Mock()
        mock_runtime_instance = Mock()
        mock_offline_repo.return_value = mock_offline_instance
        mock_runtime_repo.return_value = mock_runtime_instance
        
        # Mock empty runtime table
        mock_runtime_instance.count.return_value = 0
        mock_offline_instance.count.return_value = 2
        
        # Mock relations
        mock_relation1 = Mock()
        mock_relation1.model_dump.return_value = {"id": 1, "source": 1, "target": 2}
        mock_relation2 = Mock()
        mock_relation2.model_dump.return_value = {"id": 2, "source": 2, "target": 3}
        mock_offline_instance.all.return_value = [mock_relation1, mock_relation2]
        
        # Mock RuntimeDatabaseManager
        with patch('musigree.transfer.transfer_manager.RuntimeDatabaseManager') as mock_db_manager:
            mock_db_manager.get_concurrency_count.return_value = 1  # Single-threaded
            
            # Mock RuntimeRelationDB
            with patch('musigree.transfer.transfer_manager.RuntimeRelationDB') as mock_runtime_relation:
                mock_runtime_relation_instance = Mock()
                mock_runtime_relation_instance.model_dump.return_value = {"id": 1, "source": 1, "target": 2}
                mock_runtime_relation.return_value = mock_runtime_relation_instance
                
                # Call the method
                TransferManager.transfer_relation()
                
                # Verify methods were called
                mock_offline_instance.count.assert_called_once()
                mock_runtime_instance.count.assert_called()
                mock_offline_instance.all.assert_called_once()

    @patch('musigree.transfer.transfer_manager.RuntimeRelationRepository')
    @patch('musigree.transfer.transfer_manager.RelationRepository')
    @patch('musigree.transfer.transfer_manager.runtime_transaction')
    def test_transfer_relation_non_empty_runtime_table(self, _mock_transaction: Mock, mock_offline_repo: Mock, mock_runtime_repo: Mock) -> None:
        """Test transfer_relation raises error when runtime table is not empty."""
        # Setup mocks
        mock_offline_instance = Mock()
        mock_runtime_instance = Mock()
        mock_offline_repo.return_value = mock_offline_instance
        mock_runtime_repo.return_value = mock_runtime_instance
        
        # Mock non-empty runtime table
        mock_runtime_instance.count.return_value = 3  # Not empty
        mock_offline_instance.count.return_value = 10
        
        # Should raise DatabaseError
        with pytest.raises(DatabaseError):
            TransferManager.transfer_relation()

    @patch('musigree.transfer.transfer_manager.RuntimeRoleRepository')
    @patch('musigree.transfer.transfer_manager.RoleRepository')
    @patch('musigree.transfer.transfer_manager.runtime_transaction')
    def test_transfer_role(self, _mock_transaction: Mock, mock_offline_repo: Mock, mock_runtime_repo: Mock) -> None:
        """Test transfer_role method."""
        # Setup mocks
        mock_offline_instance = Mock()
        mock_runtime_instance = Mock()
        mock_offline_repo.return_value = mock_offline_instance
        mock_runtime_repo.return_value = mock_runtime_instance
        
        # Mock roles
        mock_role = Mock()
        mock_role.model_dump.return_value = {"id": 1, "name": "Artist"}
        mock_offline_instance.all.return_value = [mock_role]
        
        with patch('musigree.transfer.transfer_manager.RuntimeRole') as mock_runtime_role:
            mock_runtime_role_instance = Mock()
            mock_runtime_role_instance.model_dump.return_value = {"id": 1, "name": "Artist"}
            mock_runtime_role.return_value = mock_runtime_role_instance
            
            # Call the method
            TransferManager.transfer_role()
            
            # Verify basic calls
            mock_offline_instance.all.assert_called_once()

    @patch('musigree.transfer.transfer_manager.StyleRepository')
    @patch('musigree.transfer.transfer_manager.GenreRepository')
    @patch('musigree.transfer.transfer_manager.CountryRepository')
    @patch('musigree.transfer.transfer_manager.runtime_transaction')
    def test_transfer_entity_details(self, _mock_transaction: Mock, mock_country_repo: Mock, mock_genre_repo: Mock, mock_style_repo: Mock) -> None:
        """Test transfer_entity_details method."""
        # Setup mocks
        mock_entity_details = Mock(spec=EntityDetailsIndex)
        
        mock_country_instance = Mock()
        mock_genre_instance = Mock()
        mock_style_instance = Mock()
        
        mock_country_repo.return_value = mock_country_instance
        mock_genre_repo.return_value = mock_genre_instance
        mock_style_repo.return_value = mock_style_instance
        
        # Mock the list attributes directly (not methods)
        mock_entity_details.countries_list = ["USA", "Canada"]
        mock_entity_details.genres_list = ["Rock", "Jazz"]
        mock_entity_details.styles_list = ["Classic Rock", "Alternative"]
        
        # Call the method
        TransferManager.transfer_entity_details(mock_entity_details)
        
        # Verify repositories were created
        mock_country_repo.assert_called_once()
        mock_genre_repo.assert_called_once()
        mock_style_repo.assert_called_once()

    @patch('musigree.transfer.transfer_manager.RuntimeDatabaseManager')
    @patch('musigree.transfer.transfer_manager.ReleaseDataAccess')
    @patch('musigree.transfer.transfer_manager.ReleaseRepository')
    @patch('musigree.transfer.transfer_manager.TransferManager.transfer_entity_details')
    @patch('musigree.transfer.transfer_manager.TransferManager.transfer_role')
    @patch('musigree.transfer.transfer_manager.TransferManager.transfer_relation')
    @patch('musigree.transfer.transfer_manager.TransferManager.transfer_entity')
    def test_transfer_all(self, mock_transfer_entity: Mock, mock_transfer_relation: Mock, 
                         mock_transfer_role: Mock, mock_transfer_entity_details: Mock,
                          _mock_release_repo: Mock, mock_release_data_access: Mock,
                         mock_runtime_db_manager: Mock) -> None:
        """Test transfer_all method orchestrates all transfers."""
        # Setup mocks
        mock_data_directory = Path("/test/data")
        mock_entity_details = Mock(spec=EntityDetailsIndex)
        
        # Mock RuntimeDatabaseManager
        mock_runtime_db_helper = Mock()
        mock_runtime_db_manager.runtime_database_helper = mock_runtime_db_helper
        
        # Mock ReleaseDataAccess
        mock_release_data_access.create_entity_details_index.return_value = mock_entity_details
        
        # Call the method
        TransferManager.transfer_all(mock_data_directory)
        
        # Verify database setup
        mock_runtime_db_helper.drop_tables.assert_called_once()
        mock_runtime_db_helper.create_tables.assert_called_once()
        
        # Verify all transfer methods were called
        mock_transfer_role.assert_called_once()
        mock_transfer_entity_details.assert_called_once_with(mock_entity_details)
        mock_transfer_entity.assert_called_once_with(mock_entity_details)
        mock_transfer_relation.assert_called_once()

    def test_transfer_wait_for_worker(self) -> None:
        """Test transfer_wait_for_worker method."""
        # Create a mock worker with proper exitcode
        mock_worker = Mock()
        mock_worker.join.return_value = None
        mock_worker.terminate.return_value = None
        mock_worker.exitcode = 0  # Set exitcode to a proper integer
        
        # Should not raise any exceptions
        TransferManager.transfer_wait_for_worker(mock_worker)
        
        # Verify methods were called
        mock_worker.join.assert_called_once()
        mock_worker.terminate.assert_called_once()

    @patch('musigree.transfer.transfer_manager.RuntimeDatabaseManager')
    @patch('musigree.transfer.transfer_manager.TransferWorkerEntityInserter')
    @patch('musigree.transfer.transfer_manager.EntityRepository')
    @patch('musigree.transfer.transfer_manager.RuntimeEntityRepository')
    @patch('musigree.transfer.transfer_manager.runtime_transaction')
    def test_transfer_entity_multithreaded(self, _mock_transaction: Mock, mock_runtime_repo: Mock, mock_offline_repo: Mock,
                                          mock_worker_class: Mock, mock_db_manager: Mock) -> None:
        """Test transfer_entity with multithreading enabled."""
        # Setup mocks for multithreading
        mock_db_manager.get_concurrency_count.return_value = 4  # Multi-threaded
        
        mock_offline_instance = Mock()
        mock_runtime_instance = Mock()
        mock_offline_repo.return_value = mock_offline_instance
        mock_runtime_repo.return_value = mock_runtime_instance
        
        mock_entity_details = Mock(spec=EntityDetailsIndex)
        mock_entity_details.get_countries_for_id.return_value = []
        mock_entity_details.get_genres_for_id.return_value = []
        mock_entity_details.get_styles_for_id.return_value = []
        
        # Mock empty runtime table and large offline data
        mock_runtime_instance.count.return_value = 0
        mock_offline_instance.count.return_value = TransferManager.BULK_INSERT_BATCH_SIZE + 10
        
        # Create many mock entities to trigger batching
        mock_entities = []
        for i in range(TransferManager.BULK_INSERT_BATCH_SIZE + 10):
            mock_entity = Mock()
            mock_entity.id = i
            mock_entity.model_dump.return_value = {"id": i, "name": f"Entity {i}"}
            mock_entities.append(mock_entity)
        mock_offline_instance.all.return_value = mock_entities
        
        # Mock worker with proper exitcode
        mock_worker = Mock()
        mock_worker.start.return_value = None
        mock_worker.join.return_value = None
        mock_worker.terminate.return_value = None
        mock_worker.exitcode = 0  # Set exitcode to a proper integer
        mock_worker_class.return_value = mock_worker
        
        with patch('musigree.transfer.transfer_manager.RuntimeEntity') as mock_runtime_entity:
            mock_runtime_entity_instance = Mock()
            mock_runtime_entity_instance.to_db.return_value = Mock()
            mock_runtime_entity_instance.to_db.return_value.model_dump.return_value = {"id": 1}
            mock_runtime_entity.return_value = mock_runtime_entity_instance
            
            # Call the method
            TransferManager.transfer_entity(mock_entity_details)
            
            # Verify worker was created and started
            assert mock_worker_class.called
            assert mock_worker.start.called

    @patch('musigree.transfer.transfer_manager.RuntimeDatabaseManager')
    @patch('musigree.transfer.transfer_manager.RuntimeEntityRepository')
    @patch('musigree.transfer.transfer_manager.EntityRepository')
    def test_transfer_entity_database_error_handling(self, mock_offline_repo: Mock, mock_runtime_repo: Mock, mock_db_manager: Mock) -> None:
        """Test transfer_entity handles database errors properly."""
        # Setup mocks
        mock_db_manager.get_concurrency_count.return_value = 1  # Single-threaded
        
        mock_offline_instance = Mock()
        mock_runtime_instance = Mock()
        mock_offline_repo.return_value = mock_offline_instance
        mock_runtime_repo.return_value = mock_runtime_instance
        
        mock_entity_details = Mock(spec=EntityDetailsIndex)
        mock_entity_details.get_countries_for_id.return_value = []
        mock_entity_details.get_genres_for_id.return_value = []
        mock_entity_details.get_styles_for_id.return_value = []
        
        # Mock empty runtime table
        mock_runtime_instance.count.return_value = 0
        mock_offline_instance.count.return_value = 1
        
        # Mock entity
        mock_entity = Mock()
        mock_entity.id = 1
        mock_entity.model_dump.return_value = {"id": 1, "name": "Entity 1"}
        mock_offline_instance.all.return_value = [mock_entity]
        
        # Mock save_all to raise DatabaseError
        mock_runtime_instance.save_all.side_effect = DatabaseError()
        
        with patch('musigree.transfer.transfer_manager.RuntimeEntity') as mock_runtime_entity:
            with patch('musigree.transfer.transfer_manager.runtime_transaction'):
                mock_runtime_entity_instance = Mock()
                mock_runtime_entity_instance.to_db.return_value = Mock()
                mock_runtime_entity_instance.to_db.return_value.model_dump.return_value = {"id": 1}
                mock_runtime_entity.return_value = mock_runtime_entity_instance
                
                # Should re-raise DatabaseError
                with pytest.raises(DatabaseError):
                    TransferManager.transfer_entity(mock_entity_details) 