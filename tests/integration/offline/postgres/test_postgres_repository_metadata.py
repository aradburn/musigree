"""Tests for MetadataRepository with Postgres backend using pytest fixtures."""

from tests.integration.offline.offline_database.test_repository_metadata import (
    TestRepositoryMetadata,
)


class TestPostgresRepositoryMetadata(TestRepositoryMetadata):
    # Run all tests in TestRepositoryMetadata
    pass
