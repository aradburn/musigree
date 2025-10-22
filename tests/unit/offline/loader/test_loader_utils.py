"""Unit tests for LoaderUtils class."""

import os
from pathlib import Path
from unittest.mock import patch, MagicMock


from musigree.offline.loader.loader_utils import LoaderUtils


class TestLoaderUtils:
    """Test cases for LoaderUtils class."""

    @patch("musigree.offline.loader.loader_utils.glob.glob")
    def test_get_xml_path_with_date(self, mock_glob: MagicMock) -> None:
        """Test get_xml_path with a specific date."""
        # Arrange
        test_directory = Path("/test/data")
        test_tag = "artist"
        test_date = "20231215"
        mock_glob.return_value = ["discogs_20231215_artists.xml.gz"]

        # Act
        result = LoaderUtils.get_xml_path(test_directory, test_tag, test_date)

        # Assert
        mock_glob.assert_called_once_with(
            "discogs_20231215_artists.xml.gz", root_dir=test_directory
        )
        expected_path = os.path.join(str(test_directory), "discogs_20231215_artists.xml.gz")
        assert result == expected_path

    @patch("musigree.offline.loader.loader_utils.glob.glob")
    def test_get_xml_path_without_date(self, mock_glob: MagicMock) -> None:
        """Test get_xml_path without a date."""
        # Arrange
        test_directory = Path("/test/data")
        test_tag = "release"
        mock_glob.return_value = ["discogs__releases.xml.gz"]

        # Act
        result = LoaderUtils.get_xml_path(test_directory, test_tag, "")

        # Assert
        mock_glob.assert_called_once_with("discogs__releases.xml.gz", root_dir=test_directory)
        expected_path = os.path.join(str(test_directory), "discogs__releases.xml.gz")
        assert result == expected_path

    @patch("musigree.offline.loader.loader_utils.glob.glob")
    def test_get_xml_path_multiple_files(self, mock_glob: MagicMock) -> None:
        """Test get_xml_path when multiple files match the pattern."""
        # Arrange
        test_directory = Path("/test/data")
        test_tag = "label"
        test_date = "20231215"
        mock_glob.return_value = [
            "discogs_20231214_labels.xml.gz",
            "discogs_20231215_labels.xml.gz",
            "discogs_20231216_labels.xml.gz",
        ]

        # Act
        result = LoaderUtils.get_xml_path(test_directory, test_tag, test_date)

        # Assert
        # Should return the last file in sorted order
        expected_path = os.path.join(str(test_directory), "discogs_20231216_labels.xml.gz")
        assert result == expected_path

    @patch("musigree.offline.loader.loader_utils.glob.glob")
    def test_get_role_paths(self, mock_glob: MagicMock) -> None:
        """Test get_role_paths method."""
        # Arrange
        test_directory = Path("/test/roles")
        mock_glob.return_value = [
            "acting_literary_and_spoken.csv",
            "companies.csv",
            "conducting_and_leading.csv",
        ]

        # Act
        result = LoaderUtils.get_role_paths(test_directory)

        # Assert
        mock_glob.assert_called_once_with("*.csv", root_dir=test_directory)
        expected_paths = [
            os.path.join(str(test_directory), "acting_literary_and_spoken.csv"),
            os.path.join(str(test_directory), "companies.csv"),
            os.path.join(str(test_directory), "conducting_and_leading.csv"),
        ]
        assert result == expected_paths

    @patch("musigree.offline.loader.loader_utils.glob.glob")
    def test_get_role_paths_no_files(self, mock_glob: MagicMock) -> None:
        """Test get_role_paths when no CSV files found."""
        # Arrange
        test_directory = Path("/test/empty")
        mock_glob.return_value = []

        # Act
        result = LoaderUtils.get_role_paths(test_directory)

        # Assert
        assert result == []

    @patch("musigree.offline.loader.loader_utils.ParserUtils")
    @patch("musigree.offline.loader.loader_utils.gzip.GzipFile")
    @patch.object(LoaderUtils, "get_xml_path")
    def test_get_iterator(
        self, mock_get_xml_path: MagicMock, mock_gzip_file: MagicMock, mock_parser_utils: MagicMock
    ) -> None:
        """Test get_iterator method."""
        # Arrange
        test_directory = Path("/test/data")
        test_tag = "artist"
        test_date = "20231215"
        test_file_path = "/test/data/discogs_20231215_artists.xml.gz"

        mock_get_xml_path.return_value = test_file_path
        mock_file_pointer = MagicMock()
        mock_gzip_file.return_value = mock_file_pointer

        mock_raw_iterator = MagicMock()
        mock_clean_iterator = MagicMock()
        mock_parser_utils.iterparse.return_value = mock_raw_iterator
        mock_parser_utils.clean_elements.return_value = mock_clean_iterator

        # Act
        result = LoaderUtils.get_iterator(test_directory, test_tag, test_date)

        # Assert
        mock_get_xml_path.assert_called_once_with(test_directory, test_tag, test_date)
        mock_gzip_file.assert_called_once_with(test_file_path, "r")
        mock_parser_utils.iterparse.assert_called_once_with(mock_file_pointer, test_tag)
        mock_parser_utils.clean_elements.assert_called_once_with(mock_raw_iterator)
        assert result == mock_clean_iterator
