"""
Unit tests for the loader_base module.

This module contains comprehensive unit tests for the LoaderBase class,
which provides the foundation for data loading operations in the offline system.
"""

import gzip
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest
from sqlalchemy.exc import DataError

from musigree.library.fields.entity_type import EntityType
from musigree.offline.loader.loader_base import LoaderBase
from musigree.offline.loader.parser_base import ParserBase
from musigree.offline.offline_database.base_repository import BaseRepository


class ConcreteLoaderBase(LoaderBase):
    """Concrete implementation of LoaderBase for testing."""

    @staticmethod
    def get_insert_worker_function() -> Mock:
        """Mock implementation of get_insert_worker_function."""
        return Mock()

    @staticmethod
    def get_update_worker_function() -> Mock:
        """Mock implementation of get_update_worker_function."""
        return Mock()

    @staticmethod
    def get_delete_worker_function() -> Mock:
        """Mock implementation of get_delete_worker_function."""
        return Mock()

    @classmethod
    async def get_set_of_ids(cls, entity_type: EntityType | None) -> set[int]:
        """Mock implementation of get_set_of_ids."""
        return {1, 2, 3}


class TestLoaderBase:
    """Test class for LoaderBase."""

    def test_is_abstract_class(self) -> None:
        """Test that LoaderBase is an abstract class."""
        with pytest.raises(TypeError):
            # noinspection PyAbstractClass
            LoaderBase()  # type: ignore

    def test_concrete_implementation_can_be_instantiated(self) -> None:
        """Test that a concrete implementation can be instantiated."""
        loader = ConcreteLoaderBase()
        assert isinstance(loader, LoaderBase)

    def test_tags_to_fields_mapping_default(self) -> None:
        """Test default value of _tags_to_fields_mapping."""
        assert LoaderBase._tags_to_fields_mapping is None

    def test_tags_to_fields_mapping_can_be_set(self) -> None:
        """Test that _tags_to_fields_mapping can be modified."""
        original_mapping = LoaderBase._tags_to_fields_mapping

        try:
            test_mapping = {"test_tag": {"field": "value"}}
            LoaderBase._tags_to_fields_mapping = test_mapping
            assert LoaderBase._tags_to_fields_mapping == test_mapping
        finally:
            # Restore original value
            LoaderBase._tags_to_fields_mapping = original_mapping


class TestProcessXml:
    """Test class for process_xml method."""

    @pytest.fixture
    def mock_parser(self) -> Mock:
        """Fixture for mock parser."""
        parser = Mock(spec=ParserBase)
        parser.tags_to_fields.return_value = {"id": 1, "name": "test"}
        return parser

    @pytest.fixture
    def mock_xml_content(self) -> bytes:
        """Fixture for mock XML content."""
        xml_content = b'<root><artist id="1"><name>Test Artist</name></artist></root>'
        return gzip.compress(xml_content)

    @patch("musigree.offline.loader.loader_base.ParserUtils.iterparse")
    @patch("musigree.offline.loader.loader_base.gzip.GzipFile")
    def test_process_xml_success(
        self, mock_gzip: Mock, mock_iterparse: Mock, mock_parser: Mock
    ) -> None:
        """Test successful XML processing."""
        # Setup
        mock_element = Mock()
        mock_element.get.return_value = "1"
        mock_iterparse.return_value = [mock_element]
        mock_file = Mock()
        mock_gzip.return_value.__enter__.return_value = mock_file

        # Execute
        result = list(LoaderBase.process_xml(mock_parser, "test.xml.gz", "artist", []))

        # Verify
        assert len(result) == 1
        assert result[0] == {"id": 1, "name": "test"}
        mock_gzip.assert_called_once_with("test.xml.gz", "r")
        mock_iterparse.assert_called_once_with(mock_file, "artist")
        mock_parser.tags_to_fields.assert_called_once_with(mock_element)

    @patch("musigree.offline.loader.loader_base.ParserUtils.iterparse")
    @patch("musigree.offline.loader.loader_base.gzip.GzipFile")
    def test_process_xml_with_skip_without(
        self, mock_gzip: Mock, mock_iterparse: Mock, mock_parser: Mock
    ) -> None:
        """Test XML processing with skip_without filtering."""
        # Setup
        mock_element1 = Mock()
        mock_element2 = Mock()
        mock_iterparse.return_value = [mock_element1, mock_element2]
        mock_file = Mock()
        mock_gzip.return_value.__enter__.return_value = mock_file

        # First element has required field, second doesn't
        mock_parser.tags_to_fields.side_effect = [
            {"id": 1, "name": "test", "required_field": "value"},
            {"id": 2, "name": "test2", "required_field": None},
        ]

        # Execute
        result = list(
            LoaderBase.process_xml(mock_parser, "test.xml.gz", "artist", ["required_field"])
        )

        # Verify - only first element should be returned
        assert len(result) == 1
        assert result[0] == {"id": 1, "name": "test", "required_field": "value"}

    @patch("musigree.offline.loader.loader_base.ParserUtils.iterparse")
    @patch("musigree.offline.loader.loader_base.gzip.GzipFile")
    def test_process_xml_data_error(
        self, mock_gzip: Mock, mock_iterparse: Mock, mock_parser: Mock
    ) -> None:
        """Test XML processing with DataError."""
        # Setup
        mock_element = Mock()
        mock_iterparse.return_value = [mock_element]
        mock_file = Mock()
        mock_gzip.return_value.__enter__.return_value = mock_file
        mock_parser.tags_to_fields.side_effect = DataError("statement", "params", Exception("orig"))  # type: ignore

        # Execute & Verify
        with pytest.raises(DataError):
            list(LoaderBase.process_xml(mock_parser, "test.xml.gz", "artist", []))

    @patch("musigree.offline.loader.loader_base.ParserUtils.iterparse")
    @patch("musigree.offline.loader.loader_base.gzip.GzipFile")
    def test_process_xml_empty_result(
        self, mock_gzip: Mock, mock_iterparse: Mock, mock_parser: Mock
    ) -> None:
        """Test XML processing with empty result."""
        # Setup
        mock_iterparse.return_value = []
        mock_file = Mock()
        mock_gzip.return_value.__enter__.return_value = mock_file

        # Execute
        result = list(LoaderBase.process_xml(mock_parser, "test.xml.gz", "artist", []))

        # Verify
        assert result == []


class TestLoaderPassOneManager:
    """Test class for loader_pass_one_manager method."""

    @pytest.fixture
    def mock_repository(self) -> Mock:
        """Fixture for mock repository."""
        repo = Mock(spec=BaseRepository)
        repo.count = AsyncMock(side_effect=[100, 105])  # initial and final counts
        return repo

    @pytest.fixture
    def mock_parser(self) -> Mock:
        """Fixture for mock parser."""
        return Mock(spec=ParserBase)

    @patch("musigree.offline.loader.loader_base.offline_transaction")
    @patch("musigree.offline.loader.loader_base.LoaderUtils.get_xml_path")
    @patch("musigree.offline.loader.loader_base.LoaderBase.process_xml")
    @patch("musigree.offline.loader.loader_base.utils.generator_with_id_accumulator")
    @patch("musigree.offline.loader.loader_base.utils.batched")
    @patch("musigree.offline.loader.loader_base.utils.worker_generator")
    @patch("musigree.offline.loader.loader_base.utils.queue_worker_functions")
    @patch("musigree.offline.loader.loader_base.OfflineDatabaseManager.get_concurrency_count")
    async def test_loader_pass_one_manager_bulk_inserts(
        self,
        mock_concurrency: Mock,
        _mock_queue_worker: AsyncMock,
        mock_worker_gen: Mock,
        mock_batched: Mock,
        mock_gen_with_id: Mock,
        mock_process_xml: Mock,
        mock_get_xml_path: Mock,
        mock_transaction: AsyncMock,
        mock_repository: Mock,
        mock_parser: Mock,
    ) -> None:
        """Test loader_pass_one_manager with bulk inserts."""
        # Setup
        mock_transaction.return_value.__aenter__.return_value = None
        mock_concurrency.return_value = 2
        mock_get_xml_path.return_value = "test.xml.gz"
        mock_process_xml.return_value = [{"id": 1, "name": "test"}]
        mock_gen_with_id.return_value = [{"id": 1, "name": "test"}]
        mock_batched.side_effect = lambda x, size: [list(x)]
        mock_worker_gen.return_value = []

        with patch.object(ConcreteLoaderBase, "get_set_of_ids", return_value={1, 2, 3}):
            with patch.object(
                ConcreteLoaderBase, "get_insert_worker_function"
            ) as mock_insert_worker:
                with patch.object(
                    ConcreteLoaderBase, "get_delete_worker_function"
                ) as mock_delete_worker:
                    mock_insert_worker.return_value = Mock()
                    mock_delete_worker.return_value = Mock()

                    # Execute
                    result = await ConcreteLoaderBase.loader_pass_one_manager(
                        mock_repository,
                        mock_parser,
                        Path("/test"),
                        "2023-01-01",
                        "artist",
                        "id",
                        [],
                        is_bulk_inserts=True,
                    )

                    # Verify
                    assert (
                        result == 0
                    )  # processed_count starts at 0 and isn't updated in the current logic
                    mock_repository.count.assert_called()
                    mock_get_xml_path.assert_called_once_with(Path("/test"), "artist", "2023-01-01")
                    mock_insert_worker.assert_called_once()

    @patch("musigree.offline.loader.loader_base.offline_transaction")
    @patch("musigree.offline.loader.loader_base.LoaderUtils.get_xml_path")
    @patch("musigree.offline.loader.loader_base.LoaderBase.process_xml")
    @patch("musigree.offline.loader.loader_base.utils.generator_with_id_accumulator")
    @patch("musigree.offline.loader.loader_base.utils.batched")
    @patch("musigree.offline.loader.loader_base.utils.worker_generator")
    @patch("musigree.offline.loader.loader_base.utils.queue_worker_functions")
    @patch("musigree.offline.loader.loader_base.OfflineDatabaseManager.get_concurrency_count")
    async def test_loader_pass_one_manager_updates(
        self,
        mock_concurrency: Mock,
        _mock_queue_worker: AsyncMock,
        mock_worker_gen: Mock,
        mock_batched: Mock,
        mock_gen_with_id: Mock,
        mock_process_xml: Mock,
        mock_get_xml_path: Mock,
        mock_transaction: AsyncMock,
        mock_repository: Mock,
        mock_parser: Mock,
    ) -> None:
        """Test loader_pass_one_manager with updates."""
        # Setup
        mock_transaction.return_value.__aenter__.return_value = None
        mock_concurrency.return_value = 2
        mock_get_xml_path.return_value = "test.xml.gz"
        mock_process_xml.return_value = [{"id": 1, "name": "test"}]
        mock_gen_with_id.return_value = [{"id": 1, "name": "test"}]
        mock_batched.side_effect = lambda x, size: [list(x)]
        mock_worker_gen.return_value = []

        with patch.object(ConcreteLoaderBase, "get_set_of_ids", return_value={1, 2, 3}):
            with patch.object(
                ConcreteLoaderBase, "get_update_worker_function"
            ) as mock_update_worker:
                with patch.object(
                    ConcreteLoaderBase, "get_delete_worker_function"
                ) as mock_delete_worker:
                    mock_update_worker.return_value = Mock()
                    mock_delete_worker.return_value = Mock()

                    # Execute
                    result = await ConcreteLoaderBase.loader_pass_one_manager(
                        mock_repository,
                        mock_parser,
                        Path("/test"),
                        "2023-01-01",
                        "artist",
                        "id",
                        [],
                        is_bulk_inserts=False,
                    )

                    # Verify
                    assert result == 0
                    mock_update_worker.assert_called_once()

    @patch("musigree.offline.loader.loader_base.offline_transaction")
    @patch("musigree.offline.loader.loader_base.LoaderUtils.get_xml_path")
    @patch("musigree.offline.loader.loader_base.LoaderBase.process_xml")
    @patch("musigree.offline.loader.loader_base.utils.generator_with_id_accumulator")
    @patch("musigree.offline.loader.loader_base.utils.batched")
    @patch("musigree.offline.loader.loader_base.utils.worker_generator")
    @patch("musigree.offline.loader.loader_base.utils.queue_worker_functions")
    @patch("musigree.offline.loader.loader_base.OfflineDatabaseManager.get_concurrency_count")
    async def test_loader_pass_one_manager_with_deletions(
        self,
        mock_concurrency: Mock,
        mock_queue_worker: AsyncMock,
        mock_worker_gen: Mock,
        mock_batched: Mock,
        mock_gen_with_id: Mock,
        mock_process_xml: Mock,
        mock_get_xml_path: Mock,
        mock_transaction: AsyncMock,
        mock_repository: Mock,
        mock_parser: Mock,
    ) -> None:
        """Test loader_pass_one_manager with records to delete."""
        # Setup
        mock_transaction.return_value.__aenter__.return_value = None
        mock_concurrency.return_value = 2
        mock_get_xml_path.return_value = "test.xml.gz"
        mock_process_xml.return_value = [{"id": 1, "name": "test"}]
        mock_gen_with_id.return_value = [{"id": 1, "name": "test"}]
        mock_batched.side_effect = lambda x, size: [list(x)]
        mock_worker_gen.return_value = []

        # Set up scenario where database has IDs {1, 2, 3} but XML only has {1}
        # So IDs {2, 3} should be deleted
        with patch.object(ConcreteLoaderBase, "get_set_of_ids", return_value={1, 2, 3}):
            with patch.object(
                ConcreteLoaderBase, "get_update_worker_function"
            ) as mock_update_worker:
                with patch.object(
                    ConcreteLoaderBase, "get_delete_worker_function"
                ) as mock_delete_worker:
                    mock_update_worker.return_value = Mock()
                    mock_delete_worker.return_value = Mock()

                    # Execute
                    result = await ConcreteLoaderBase.loader_pass_one_manager(
                        mock_repository,
                        mock_parser,
                        Path("/test"),
                        "2023-01-01",
                        "artist",
                        "id",
                        [],
                        is_bulk_inserts=False,
                    )

                    # Verify
                    assert result == 0
                    mock_delete_worker.assert_called_once()
                    # Should call queue_worker_functions twice: once for updates, once for deletes
                    assert mock_queue_worker.call_count == 2

    async def test_get_set_of_ids_abstract_method(self) -> None:
        """Test that get_set_of_ids is properly implemented in concrete class."""
        result = await ConcreteLoaderBase.get_set_of_ids(EntityType.ARTIST)
        assert result == {1, 2, 3}

    def test_worker_functions_abstract_methods(self) -> None:
        """Test that worker function getters are properly implemented."""
        insert_worker = ConcreteLoaderBase.get_insert_worker_function()
        update_worker = ConcreteLoaderBase.get_update_worker_function()
        delete_worker = ConcreteLoaderBase.get_delete_worker_function()

        assert insert_worker is not None
        assert update_worker is not None
        assert delete_worker is not None
