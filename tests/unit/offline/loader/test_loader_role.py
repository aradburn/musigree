"""
Unit tests for the LoaderRole class.

This module contains comprehensive unit tests for the LoaderRole class,
which handles loading role data from various sources including files,
Wikipedia instruments, and Hornbostel Sachs classification system.
It tests file loading, data parsing, role creation, and database operations.
"""

from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch, mock_open

import pytest

from musigree.offline.domain.role import RoleUncommitted
from musigree.offline.loader.loader_role import LoaderRole


class TestLoaderRole:
    """Test class for LoaderRole."""

    @patch(
        "musigree.offline.loader.loader_role.RoleDataAccess.load_all_roles_into_cache"
    )
    @patch.object(LoaderRole, "save_roles")
    @patch.object(LoaderRole, "load_wikipedia_instruments")
    @patch.object(LoaderRole, "load_hornbostel_sachs_instruments")
    @patch.object(LoaderRole, "load_roles_from_files")
    async def test_load_roles_into_database_success(
        self,
        mock_load_roles_from_files: Mock,
        mock_load_hornbostel_sachs: Mock,
        mock_load_wikipedia: Mock,
        mock_save_roles: AsyncMock,
        mock_load_cache: AsyncMock,
    ) -> None:
        """Test successful loading of roles into database."""
        # Setup
        roles_directory = Path("/test/roles")
        instruments_directory = Path("/test/instruments")

        file_roles = [Mock()]
        hs_roles = [Mock()]
        wiki_roles = [Mock()]

        mock_load_roles_from_files.return_value = file_roles
        mock_load_hornbostel_sachs.return_value = hs_roles
        mock_load_wikipedia.return_value = wiki_roles

        # Execute
        await LoaderRole.load_roles_into_database(
            roles_directory, instruments_directory
        )

        # Verify
        mock_load_roles_from_files.assert_called_once_with(roles_directory)
        mock_load_hornbostel_sachs.assert_called_once_with(instruments_directory)
        mock_load_wikipedia.assert_called_once_with(instruments_directory)

        # Verify save_roles called for each set of roles
        assert mock_save_roles.call_count == 3
        mock_save_roles.assert_any_call(file_roles)
        mock_save_roles.assert_any_call(hs_roles)
        mock_save_roles.assert_any_call(wiki_roles)

        mock_load_cache.assert_called_once()

    @patch(
        "musigree.offline.loader.loader_role.INSTRUMENTS_DATA_FILENAMES",
        ["test_instruments.csv"],
    )
    @patch("musigree.offline.loader.loader_role.RoleDataUtils.normalise_role_names")
    @patch("musigree.offline.loader.loader_role.open", new_callable=mock_open)
    @patch("musigree.offline.loader.loader_role.csv.DictReader")
    @patch("musigree.offline.loader.loader_role.csv.Sniffer")
    def test_load_wikipedia_instruments_success(
        self,
        mock_sniffer: Mock,
        mock_dict_reader: Mock,
        mock_file_open: Mock,
        mock_normalise: Mock,
    ) -> None:
        """Test successful loading of Wikipedia instruments."""
        # Setup
        instruments_directory = Path("/test/instruments")

        # Mock CSV data
        mock_dialect = Mock()
        mock_sniffer_instance = Mock()
        mock_sniffer_instance.sniff.return_value = mock_dialect
        mock_sniffer.return_value = mock_sniffer_instance

        mock_rows = [
            {"Instrument": "Guitar", "Classification": "321.322"},
            {"Instrument": "Piano", "Classification": "314.122"},
        ]
        mock_dict_reader.return_value = mock_rows

        # Mock file reading
        mock_file_obj = Mock()
        mock_file_obj.read.return_value = "sample,data\n"
        mock_file_obj.seek = Mock()
        mock_file_open.return_value.__enter__.return_value = mock_file_obj

        # Mock role name normalization - return single item lists as that's what the real function does
        mock_normalise.return_value = ["normalized_instrument"]

        # Mock RoleType methods
        from musigree.library.fields.role_type import RoleType

        with (
            patch.object(
                RoleType,
                "hornbostel_sachs_to_subcategory",
                return_value=RoleType.Subcategory.STRINGED_INSTRUMENTS,
            ),
            patch.object(
                RoleType,
                "category_names",
                {RoleType.Category.INSTRUMENTS: "Instruments"},
            ),
            patch.object(
                RoleType,
                "subcategory_names",
                {RoleType.Subcategory.STRINGED_INSTRUMENTS: "String Instruments"},
            ),
        ):
            # Execute
            result = LoaderRole.load_wikipedia_instruments(instruments_directory)

        # Verify
        assert len(result) == 2
        assert all(isinstance(role, RoleUncommitted) for role in result)

        # Verify file operations
        assert mock_file_open.call_count >= 1  # At least one file opened
        mock_normalise.assert_called()

    @patch("musigree.offline.loader.loader_role.open", new_callable=mock_open)
    @patch("musigree.offline.loader.loader_role.json.load")
    def test_load_hornbostel_sachs_instruments_success(
        self, mock_json_load: Mock, mock_file_open: Mock
    ) -> None:
        """Test successful loading of Hornbostel Sachs instruments."""
        # Setup
        instruments_directory = Path("/test/instruments")

        # Mock JSON data that matches the HornbostelSachs structure
        mock_hs_data = {
            "1": {
                "Label": "Idiophone",
                "Instruments": ["idiophone", "bell"],
                "Description": "Test description",
            }
        }
        mock_json_load.return_value = mock_hs_data

        # Execute
        result = LoaderRole.load_hornbostel_sachs_instruments(instruments_directory)

        # Verify
        assert isinstance(result, list)
        assert all(isinstance(role, RoleUncommitted) for role in result)

        # Verify file was opened
        mock_file_open.assert_called_once()
        mock_json_load.assert_called_once()

    @patch("musigree.offline.loader.loader_role.LoaderUtils.get_role_paths")
    @patch("musigree.offline.loader.loader_role.open", new_callable=mock_open)
    @patch("musigree.offline.loader.loader_role.csv.DictReader")
    @patch("musigree.offline.loader.loader_role.csv.Sniffer")
    @patch("musigree.offline.loader.loader_role.RoleDataUtils.normalise_role_names")
    def test_load_roles_from_files_success(
        self,
        mock_normalise: Mock,
        mock_sniffer: Mock,
        mock_dict_reader: Mock,
        mock_file_open: Mock,
        mock_get_role_paths: Mock,
    ) -> None:
        """Test successful loading of roles from files."""
        # Setup
        roles_directory = Path("/test/roles")
        mock_get_role_paths.return_value = ["/test/roles/test.csv"]

        # Mock CSV setup
        mock_dialect = Mock()
        mock_sniffer_instance = Mock()
        mock_sniffer_instance.sniff.return_value = mock_dialect
        mock_sniffer.return_value = mock_sniffer_instance

        # Mock CSV data
        mock_rows = [
            {
                "name": "Guitar",
                "category": "INSTRUMENTS",
                "subcategory": "STRINGED_INSTRUMENTS",
            }
        ]
        mock_dict_reader.return_value = mock_rows

        # Mock file reading
        mock_file_obj = Mock()
        mock_file_obj.read.return_value = "sample,data\n"
        mock_file_obj.seek = Mock()
        mock_file_open.return_value.__enter__.return_value = mock_file_obj

        # Mock role name normalization
        mock_normalise.return_value = ["guitar"]

        # Execute
        result = LoaderRole.load_roles_from_files(roles_directory)

        # Verify
        mock_get_role_paths.assert_called_once_with(roles_directory)
        assert len(result) == 1
        assert isinstance(result[0], RoleUncommitted)

    @patch("musigree.offline.loader.loader_role.offline_transaction")
    @patch("musigree.offline.loader.loader_role.RoleRepository")
    async def test_save_roles_success(
        self, mock_role_repository: Mock, mock_transaction: Mock
    ) -> None:
        """Test successful saving of roles to database."""
        # Setup
        mock_session = AsyncMock()
        mock_transaction.return_value.__aenter__.return_value = mock_session
        mock_transaction.return_value.__aexit__.return_value = None

        mock_repo_instance = AsyncMock()
        mock_role_repository.return_value = mock_repo_instance

        from musigree.library.fields.role_type import RoleType

        roles = [
            RoleUncommitted(
                role_name="test_role_1",
                role_category=RoleType.Category.INSTRUMENTS,
                role_subcategory=RoleType.Subcategory.STRINGED_INSTRUMENTS,
                role_category_name="Instruments",
                role_subcategory_name="String",
            ),
            RoleUncommitted(
                role_name="test_role_2",
                role_category=RoleType.Category.INSTRUMENTS,
                role_subcategory=RoleType.Subcategory.STRINGED_INSTRUMENTS,
                role_category_name="Instruments",
                role_subcategory_name="String",
            ),
        ]

        # Execute
        result = await LoaderRole.save_roles(roles)

        # Verify
        mock_transaction.assert_called_once()
        mock_role_repository.assert_called_once()

        # Verify create and commit were called for each role
        assert mock_repo_instance.create.call_count == 2
        assert mock_repo_instance.commit.call_count == 2
        assert result == 2  # Number of roles added

    @patch("musigree.offline.loader.loader_role.offline_transaction")
    @patch("musigree.offline.loader.loader_role.RoleRepository")
    async def test_save_roles_empty_list(
        self, mock_role_repository: Mock, mock_transaction: Mock
    ) -> None:
        """Test saving empty list of roles."""
        # Setup
        mock_session = AsyncMock()
        mock_transaction.return_value.__aenter__.return_value = mock_session
        mock_transaction.return_value.__aexit__.return_value = None

        mock_repo_instance = AsyncMock()
        mock_role_repository.return_value = mock_repo_instance

        # Execute
        result = await LoaderRole.save_roles([])

        # Verify
        mock_transaction.assert_called_once()
        mock_role_repository.assert_called_once()
        # No create/commit calls should be made for empty list
        mock_repo_instance.create.assert_not_called()
        mock_repo_instance.commit.assert_not_called()
        assert result == 0  # Number of roles added

    def test_load_hornbostel_sachs_instruments_file_not_found(self) -> None:
        """Test loading Hornbostel Sachs instruments when file doesn't exist."""
        # Setup
        instruments_directory = Path("/nonexistent/path")

        # Execute & Verify
        with patch(
            "musigree.offline.loader.loader_role.open", side_effect=FileNotFoundError
        ):
            with pytest.raises(FileNotFoundError):
                LoaderRole.load_hornbostel_sachs_instruments(instruments_directory)

    @patch("musigree.offline.loader.loader_role.RoleDataUtils.normalise_role_names")
    @patch("musigree.offline.loader.loader_role.open", new_callable=mock_open)
    @patch("musigree.offline.loader.loader_role.csv.DictReader")
    @patch("musigree.offline.loader.loader_role.csv.Sniffer")
    def test_load_wikipedia_instruments_empty_csv(
        self,
        mock_sniffer: Mock,
        mock_dict_reader: Mock,
        mock_file_open: Mock,
        mock_normalise: Mock,
    ) -> None:
        """Test loading Wikipedia instruments with empty CSV file."""
        # Setup
        instruments_directory = Path("/test/instruments")

        # Mock CSV setup
        mock_dialect = Mock()
        mock_sniffer_instance = Mock()
        mock_sniffer_instance.sniff.return_value = mock_dialect
        mock_sniffer.return_value = mock_sniffer_instance

        # Mock empty CSV data
        mock_dict_reader.return_value = []

        mock_file_obj = Mock()
        mock_file_obj.read.return_value = ""
        mock_file_obj.seek = Mock()
        mock_file_open.return_value.__enter__.return_value = mock_file_obj

        # Execute
        result = LoaderRole.load_wikipedia_instruments(instruments_directory)

        # Verify
        assert result == []
        mock_normalise.assert_not_called()
