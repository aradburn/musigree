"""
Unit tests for OfflineMasterDataAccess.
"""

from unittest.mock import AsyncMock, patch

import pytest

from musigree.offline.data_access_layer.offline_master_data_access import (
    OfflineMasterDataAccess,
)
from musigree.offline.offline_domain.master import Master


class TestOfflineMasterDataAccess:
    """Tests for OfflineMasterDataAccess."""

    @pytest.mark.asyncio
    async def test_get_master_title_from_master_id_returns_title(self) -> None:
        """get_master_title_from_master_id returns the master title."""
        master = Master(
            master_id=100,
            title="Expected Title",
            year=2020,
            main_release="123",
            data_quality="Complete",
        )
        with patch(
            "musigree.offline.data_access_layer.offline_master_data_access.MasterRepository"
        ) as mock_repo_cls:
            mock_repo = AsyncMock()
            mock_repo.get_by_id = AsyncMock(return_value=master)
            mock_repo_cls.return_value = mock_repo

            result = await OfflineMasterDataAccess.get_master_title_from_master_id(100)

            assert result == "Expected Title"
            mock_repo.get_by_id.assert_called_once_with(100)
