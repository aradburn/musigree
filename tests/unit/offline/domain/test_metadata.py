"""
Unit tests for the offline.domain.metadata module.

This module contains comprehensive unit tests for the metadata domain objects,
including MetadataUncommitted and Metadata classes.
"""

from datetime import datetime

import pytest
from pydantic import ValidationError

# noinspection PyProtectedMember
from musigree.offline.domain.metadata import (
    _MetadataBase,
    MetadataUncommitted,
    Metadata,
)


class TestMetadataBase:
    """Test class for _MetadataBase."""

    def test_metadata_base_cannot_be_instantiated_directly(self) -> None:
        """Test that _MetadataBase is intended as a base class."""
        # While we can instantiate it, it's meant to be a base class
        timestamp = datetime.now()
        base = _MetadataBase(
            metadata_key="test_key", metadata_value="test_value", metadata_timestamp=timestamp
        )

        assert base.metadata_key == "test_key"
        assert base.metadata_value == "test_value"
        assert base.metadata_timestamp == timestamp

    def test_metadata_base_validation_error_missing_fields(self) -> None:
        """Test validation error when required fields are missing."""
        with pytest.raises(ValidationError):
            _MetadataBase()  # type: ignore

    def test_metadata_base_validation_error_wrong_type(self) -> None:
        """Test validation error for wrong field types."""
        with pytest.raises(ValidationError):
            _MetadataBase(
                metadata_key=123,  # type: ignore
                metadata_value="test_value",
                metadata_timestamp=datetime.now(),
            )

    def test_metadata_base_string_fields(self) -> None:
        """Test that key and value are properly validated as strings."""
        timestamp = datetime.now()
        metadata = _MetadataBase(
            metadata_key="",  # Empty string should be valid
            metadata_value="",
            metadata_timestamp=timestamp,
        )

        assert metadata.metadata_key == ""
        assert metadata.metadata_value == ""

    def test_metadata_base_datetime_validation(self) -> None:
        """Test datetime field validation."""
        with pytest.raises(ValidationError):
            _MetadataBase(
                metadata_key="test_key",
                metadata_value="test_value",
                metadata_timestamp="not_a_datetime",  # type: ignore
            )


class TestMetadataUncommitted:
    """Test class for MetadataUncommitted."""

    def test_metadata_uncommitted_creation(self) -> None:
        """Test successful creation of MetadataUncommitted."""
        timestamp = datetime.now()
        metadata = MetadataUncommitted(
            metadata_key="user_preference", metadata_value="dark_mode", metadata_timestamp=timestamp
        )

        assert metadata.metadata_key == "user_preference"
        assert metadata.metadata_value == "dark_mode"
        assert metadata.metadata_timestamp == timestamp

    def test_metadata_uncommitted_inherits_from_base(self) -> None:
        """Test that MetadataUncommitted inherits from _MetadataBase."""
        assert issubclass(MetadataUncommitted, _MetadataBase)

    def test_metadata_uncommitted_validation(self) -> None:
        """Test validation behavior of MetadataUncommitted."""
        timestamp = datetime.now()
        metadata = MetadataUncommitted(
            metadata_key="config_key", metadata_value="config_value", metadata_timestamp=timestamp
        )

        # Test attribute access
        assert hasattr(metadata, "metadata_key")
        assert hasattr(metadata, "metadata_value")
        assert hasattr(metadata, "metadata_timestamp")

        # Test that it doesn't have database-specific fields
        assert not hasattr(metadata, "metadata_id")
        assert not hasattr(metadata, "version_id")

    def test_metadata_uncommitted_json_serialization(self) -> None:
        """Test JSON serialization of MetadataUncommitted."""
        timestamp = datetime(2023, 1, 1, 12, 0, 0)
        metadata = MetadataUncommitted(
            metadata_key="test_key", metadata_value="test_value", metadata_timestamp=timestamp
        )

        dumped = metadata.model_dump()

        assert dumped["metadata_key"] == "test_key"
        assert dumped["metadata_value"] == "test_value"
        assert dumped["metadata_timestamp"] == timestamp

    def test_metadata_uncommitted_from_dict(self) -> None:
        """Test creating MetadataUncommitted from dictionary."""
        timestamp = datetime.now()
        data = {
            "metadata_key": "from_dict_key",
            "metadata_value": "from_dict_value",
            "metadata_timestamp": timestamp,
        }

        metadata = MetadataUncommitted.model_validate(data)

        assert metadata.metadata_key == "from_dict_key"
        assert metadata.metadata_value == "from_dict_value"
        assert metadata.metadata_timestamp == timestamp


class TestMetadata:
    """Test class for Metadata."""

    def test_metadata_creation(self) -> None:
        """Test successful creation of Metadata."""
        timestamp = datetime.now()
        metadata = Metadata(
            metadata_key="config_key",
            metadata_value="config_value",
            metadata_timestamp=timestamp,
            metadata_id=1,
        )

        assert metadata.metadata_key == "config_key"
        assert metadata.metadata_value == "config_value"
        assert metadata.metadata_timestamp == timestamp
        assert metadata.metadata_id == 1
        assert metadata.version_id == 1  # Default value

    def test_metadata_creation_with_version(self) -> None:
        """Test Metadata creation with custom version."""
        timestamp = datetime.now()
        metadata = Metadata(
            metadata_key="config_key",
            metadata_value="config_value",
            metadata_timestamp=timestamp,
            metadata_id=1,
            version_id=3,
        )

        assert metadata.version_id == 3

    def test_metadata_inherits_from_base(self) -> None:
        """Test that Metadata inherits from _MetadataBase."""
        assert issubclass(Metadata, _MetadataBase)

    def test_metadata_default_version_id(self) -> None:
        """Test that version_id defaults to 1."""
        timestamp = datetime.now()
        metadata = Metadata(
            metadata_key="test_key",
            metadata_value="test_value",
            metadata_timestamp=timestamp,
            metadata_id=42,
        )

        assert metadata.version_id == 1

    def test_metadata_to_domain(self) -> None:
        """Test to_domain method returns self."""
        timestamp = datetime.now()
        metadata = Metadata(
            metadata_key="test_key",
            metadata_value="test_value",
            metadata_timestamp=timestamp,
            metadata_id=1,
        )

        domain_obj = metadata.to_domain()

        assert domain_obj is metadata
        assert isinstance(domain_obj, Metadata)

    def test_metadata_to_db(self) -> None:
        """Test to_db method returns self."""
        timestamp = datetime.now()
        metadata = Metadata(
            metadata_key="test_key",
            metadata_value="test_value",
            metadata_timestamp=timestamp,
            metadata_id=1,
        )

        db_obj = metadata.to_db()

        assert db_obj is metadata
        assert isinstance(db_obj, Metadata)

    def test_metadata_validation_missing_id(self) -> None:
        """Test validation error when metadata_id is missing."""
        timestamp = datetime.now()

        with pytest.raises(ValidationError):
            Metadata(
                metadata_key="test_key",
                metadata_value="test_value",
                metadata_timestamp=timestamp,
                # metadata_id is missing
            )  # type: ignore

    def test_metadata_validation_wrong_id_type(self) -> None:
        """Test validation error for wrong metadata_id type."""
        timestamp = datetime.now()

        with pytest.raises(ValidationError):
            Metadata(
                metadata_key="test_key",
                metadata_value="test_value",
                metadata_timestamp=timestamp,
                metadata_id="not_an_int",  # type: ignore
            )

    def test_metadata_json_serialization(self) -> None:
        """Test JSON serialization of Metadata."""
        timestamp = datetime(2023, 1, 1, 12, 0, 0)
        metadata = Metadata(
            metadata_key="test_key",
            metadata_value="test_value",
            metadata_timestamp=timestamp,
            metadata_id=1,
            version_id=2,
        )

        dumped = metadata.model_dump()

        assert dumped["metadata_key"] == "test_key"
        assert dumped["metadata_value"] == "test_value"
        assert dumped["metadata_timestamp"] == timestamp
        assert dumped["metadata_id"] == 1
        assert dumped["version_id"] == 2

    def test_metadata_from_dict(self) -> None:
        """Test creating Metadata from dictionary."""
        timestamp = datetime.now()
        data = {
            "metadata_key": "from_dict_key",
            "metadata_value": "from_dict_value",
            "metadata_timestamp": timestamp,
            "metadata_id": 100,
            "version_id": 5,
        }

        metadata = Metadata.model_validate(data)

        assert metadata.metadata_key == "from_dict_key"
        assert metadata.metadata_value == "from_dict_value"
        assert metadata.metadata_timestamp == timestamp
        assert metadata.metadata_id == 100
        assert metadata.version_id == 5


class TestMetadataComparison:
    """Test class for comparing Metadata and MetadataUncommitted."""

    def test_metadata_vs_uncommitted_structure(self) -> None:
        """Test structural differences between Metadata and MetadataUncommitted."""
        timestamp = datetime.now()

        uncommitted = MetadataUncommitted(
            metadata_key="test_key", metadata_value="test_value", metadata_timestamp=timestamp
        )

        committed = Metadata(
            metadata_key="test_key",
            metadata_value="test_value",
            metadata_timestamp=timestamp,
            metadata_id=1,
        )

        # Both should have base fields
        assert uncommitted.metadata_key == committed.metadata_key
        assert uncommitted.metadata_value == committed.metadata_value
        assert uncommitted.metadata_timestamp == committed.metadata_timestamp

        # Only committed should have ID fields
        assert hasattr(committed, "metadata_id")
        assert hasattr(committed, "version_id")
        assert not hasattr(uncommitted, "metadata_id")
        assert not hasattr(uncommitted, "version_id")

    def test_conversion_workflow(self) -> None:
        """Test typical workflow from uncommitted to committed metadata."""
        timestamp = datetime.now()

        # Start with uncommitted metadata
        uncommitted = MetadataUncommitted(
            metadata_key="workflow_test",
            metadata_value="initial_value",
            metadata_timestamp=timestamp,
        )

        # Simulate saving to database (would add ID)
        committed = Metadata(
            metadata_key=uncommitted.metadata_key,
            metadata_value=uncommitted.metadata_value,
            metadata_timestamp=uncommitted.metadata_timestamp,
            metadata_id=123,
        )

        assert committed.metadata_key == "workflow_test"
        assert committed.metadata_value == "initial_value"
        assert committed.metadata_timestamp == timestamp
        assert committed.metadata_id == 123
        assert committed.version_id == 1

    def test_metadata_update_scenario(self) -> None:
        """Test updating metadata (version increment scenario)."""
        timestamp = datetime.now()
        new_timestamp = datetime.now()

        original = Metadata(
            metadata_key="update_test",
            metadata_value="original_value",
            metadata_timestamp=timestamp,
            metadata_id=1,
            version_id=1,
        )

        updated = Metadata(
            metadata_key=original.metadata_key,
            metadata_value="updated_value",
            metadata_timestamp=new_timestamp,
            metadata_id=original.metadata_id,
            version_id=original.version_id + 1,
        )

        assert updated.metadata_key == original.metadata_key
        assert updated.metadata_value == "updated_value"
        assert updated.metadata_id == original.metadata_id
        assert updated.version_id == 2
