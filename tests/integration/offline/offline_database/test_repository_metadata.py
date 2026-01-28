"""Tests for MetadataRepository with async/await and pytest fixtures."""

import datetime
from typing import AsyncGenerator

import pytest

from musigree import utils
from musigree.offline.offline_database.metadata_repository import MetadataRepository
from musigree.offline.offline_database.offline_transaction import offline_transaction
from musigree.offline.offline_domain.metadata import Metadata, MetadataUncommitted
from tests.conftest import AbstractDatabaseTest


@pytest.mark.parametrize("is_load_offline_data_required", [False], scope="class")
class TestRepositoryMetadata(AbstractDatabaseTest):
    @pytest.mark.asyncio
    async def test_create_metadata(
        self, offline_database_setup: AsyncGenerator[None, None], is_load_offline_data_required: bool
    ) -> None:
        """Test creating metadata in the repository.

        Args:
            offline_database_setup: Pytest fixture for runtime_database setup.
        """
        # GIVEN
        timestamp = datetime.datetime(year=2024, month=6, day=1)
        metadata = MetadataUncommitted(
            metadata_key="key1",
            metadata_value="value1",
            metadata_timestamp=timestamp,
        )

        # WHEN
        async with offline_transaction():
            repository = MetadataRepository()
            created_metadata = await repository.create(metadata)
            actual = utils.normalize_dict(
                created_metadata.model_dump(exclude={"metadata_timestamp"})
            )

        # THEN
        expected_relation = Metadata(
            metadata_id=1,
            version_id=1,
            metadata_key="key1",
            metadata_value="value1",
            metadata_timestamp=timestamp,
        )
        expected = utils.normalize_dict(
            expected_relation.model_dump(exclude={"metadata_timestamp"})
        )
        assert actual == expected

    @pytest.mark.asyncio
    async def test_get_metadata_by_key(
        self, offline_database_setup: AsyncGenerator[None, None], is_load_offline_data_required: bool
    ) -> None:
        """Test retrieving metadata by key from the repository.

        Args:
            offline_database_setup: Pytest fixture for runtime_database setup.
        """
        # GIVEN
        timestamp = datetime.datetime(year=2024, month=6, day=1)
        metadata = MetadataUncommitted(
            metadata_key="key2",
            metadata_value="value2",
            metadata_timestamp=timestamp,
        )

        # WHEN
        async with offline_transaction():
            repository = MetadataRepository()
            created_metadata = await repository.create(metadata)
            retrieved_metadata = await repository.get_by_key(key="key2")

        # THEN
        assert created_metadata == retrieved_metadata
