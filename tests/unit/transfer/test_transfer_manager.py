from typing import AsyncGenerator, Iterable
from unittest.mock import Mock, patch, AsyncMock

import pytest

from musigree import utils
from musigree.runtime.data_access_layer.entity_details_index import EntityDetailsIndex
from musigree.transfer.transfer_manager import TransferManager


def make_async_gen(items: Iterable[object]) -> AsyncGenerator[object, None]:
    """Build an async generator yielding the given items (empty by default)."""

    async def _gen() -> AsyncGenerator[object, None]:
        for item in items:
            yield item

    return _gen()


class TestTransferManager:
    """Test cases for the TransferManager class."""

    @patch("musigree.transfer.transfer_manager.offline_transaction")
    @patch("musigree.transfer.transfer_manager.RuntimeEntityRepository")
    @patch("musigree.transfer.transfer_manager.runtime_transaction")
    @pytest.mark.asyncio
    async def test_transfer_entity_empty_runtime_table(
        self,
        mock_runtime_transaction: Mock,
        mock_runtime_repo: Mock,
        mock_offline_transaction: Mock,
    ) -> None:
        """Test transfer_entity when runtime table is empty (normal case)."""
        mock_runtime_transaction.return_value.__aenter__ = AsyncMock()
        mock_runtime_transaction.return_value.__aexit__ = AsyncMock()
        mock_offline_transaction.return_value.__aenter__ = AsyncMock()
        mock_offline_transaction.return_value.__aexit__ = AsyncMock()

        mock_runtime_instance = AsyncMock()
        mock_runtime_repo.return_value = mock_runtime_instance
        mock_runtime_instance.count.return_value = 0

        with patch("musigree.transfer.transfer_manager.EntityRepository") as mock_offline_repo:
            mock_offline_instance = AsyncMock()
            mock_offline_repo.return_value = mock_offline_instance
            mock_offline_instance.count.return_value = 0
            # all() is a sync call returning an async generator.
            mock_offline_instance.all = Mock(return_value=make_async_gen([]))

            with patch(
                "musigree.transfer.transfer_manager.RuntimeDatabaseManager"
            ) as mock_db_manager:
                mock_db_manager.get_concurrency_count.return_value = 1

                await TransferManager.transfer_entity()

                mock_runtime_instance.count.assert_called()
                mock_offline_instance.all.assert_called_once()

    @patch("musigree.transfer.transfer_manager.offline_transaction")
    @patch("musigree.transfer.transfer_manager.EntityRepository")
    @patch("musigree.transfer.transfer_manager.RuntimeEntityRepository")
    @patch("musigree.transfer.transfer_manager.runtime_transaction")
    @patch("musigree.transfer.transfer_manager.RuntimeDatabaseManager")
    @pytest.mark.asyncio
    async def test_transfer_entity_non_empty_runtime_table(
        self,
        mock_db_manager: Mock,
        mock_runtime_transaction: Mock,
        mock_runtime_repo: Mock,
        mock_offline_repo: Mock,
        _mock_offline_transaction: Mock,
    ) -> None:
        """Test transfer_entity skips loading when the runtime table is not empty."""
        mock_db_manager.runtime_database_helper = Mock()

        mock_runtime_transaction.return_value.__aenter__ = AsyncMock()
        mock_runtime_transaction.return_value.__aexit__ = AsyncMock()

        mock_runtime_instance = AsyncMock()
        mock_runtime_repo.return_value = mock_runtime_instance
        mock_runtime_instance.count.return_value = 5

        mock_offline_instance = AsyncMock()
        mock_offline_repo.return_value = mock_offline_instance

        # Should return early without raising and without touching offline data.
        await TransferManager.transfer_entity()

        mock_offline_instance.all.assert_not_called()

    @patch("musigree.transfer.transfer_manager.offline_transaction")
    @patch("musigree.transfer.transfer_manager.RuntimeRelationRepository")
    @patch("musigree.transfer.transfer_manager.runtime_transaction")
    @pytest.mark.asyncio
    async def test_transfer_relation_empty_runtime_table(
        self,
        mock_runtime_transaction: Mock,
        mock_runtime_repo: Mock,
        mock_offline_transaction: Mock,
    ) -> None:
        """Test transfer_relation when runtime table is empty (normal case)."""
        mock_runtime_transaction.return_value.__aenter__ = AsyncMock()
        mock_runtime_transaction.return_value.__aexit__ = AsyncMock()
        mock_offline_transaction.return_value.__aenter__ = AsyncMock()
        mock_offline_transaction.return_value.__aexit__ = AsyncMock()

        mock_runtime_instance = AsyncMock()
        mock_runtime_repo.return_value = mock_runtime_instance
        mock_runtime_instance.count.return_value = 0

        with patch("musigree.transfer.transfer_manager.RelationRepository") as mock_offline_repo:
            mock_offline_instance = AsyncMock()
            mock_offline_repo.return_value = mock_offline_instance
            mock_offline_instance.count.return_value = 0
            mock_offline_instance.all = Mock(return_value=make_async_gen([]))

            with patch(
                "musigree.transfer.transfer_manager.RuntimeDatabaseManager"
            ) as mock_db_manager:
                mock_db_manager.get_concurrency_count.return_value = 1

                await TransferManager.transfer_relation()

                mock_runtime_instance.count.assert_called()
                mock_offline_instance.all.assert_called_once()

    @patch("musigree.transfer.transfer_manager.offline_transaction")
    @patch("musigree.transfer.transfer_manager.RelationRepository")
    @patch("musigree.transfer.transfer_manager.RuntimeRelationRepository")
    @patch("musigree.transfer.transfer_manager.runtime_transaction")
    @patch("musigree.transfer.transfer_manager.RuntimeDatabaseManager")
    @pytest.mark.asyncio
    async def test_transfer_relation_non_empty_runtime_table(
        self,
        _mock_runtime_database_manager: Mock,
        mock_runtime_transaction: Mock,
        mock_runtime_repo: Mock,
        mock_offline_repo: Mock,
        mock_offline_transaction: Mock,
    ) -> None:
        """Test transfer_relation skips loading when the runtime table is not empty."""
        mock_runtime_transaction.return_value.__aenter__ = AsyncMock()
        mock_runtime_transaction.return_value.__aexit__ = AsyncMock()
        mock_offline_transaction.return_value.__aenter__ = AsyncMock()
        mock_offline_transaction.return_value.__aexit__ = AsyncMock()

        mock_runtime_instance = AsyncMock()
        mock_runtime_repo.return_value = mock_runtime_instance
        mock_runtime_instance.count.return_value = 3

        mock_offline_instance = AsyncMock()
        mock_offline_repo.return_value = mock_offline_instance

        # Should return early without raising and without reading relations.
        await TransferManager.transfer_relation()

        mock_offline_instance.all.assert_not_called()

    @patch("musigree.transfer.transfer_manager.offline_transaction")
    @patch("musigree.transfer.transfer_manager.RuntimeRoleRepository")
    @patch("musigree.transfer.transfer_manager.RoleRepository")
    @patch("musigree.transfer.transfer_manager.runtime_transaction")
    @pytest.mark.asyncio
    async def test_transfer_role(
        self,
        mock_runtime_transaction: Mock,
        mock_role_repo: Mock,
        mock_runtime_role_repo: Mock,
        mock_offline_transaction: Mock,
    ) -> None:
        """Test transfer_role method."""
        mock_offline_transaction.return_value = AsyncMock()
        mock_runtime_transaction.return_value = AsyncMock()

        # RoleRepository is instantiated inside offline_transaction.
        mock_role_instance = Mock()
        mock_role_repo.return_value = mock_role_instance

        # RuntimeRoleRepository is instantiated inside runtime_transaction.
        mock_runtime_role_instance = AsyncMock()
        mock_runtime_role_repo.return_value = mock_runtime_role_instance
        # Empty runtime role table so the transfer proceeds.
        mock_runtime_role_instance.count.return_value = 0

        mock_roles = [Mock() for _ in range(3)]
        for i, role in enumerate(mock_roles):
            role.model_dump.return_value = {
                "id": i,
                "role_name": f"Role {i}",
                "role_category": 1,
                "role_subcategory": 1,
                "role_category_name": f"Category {i}",
                "role_subcategory_name": f"Subcategory {i}",
            }

        mock_role_instance.all.return_value = make_async_gen(mock_roles)

        with patch("musigree.transfer.transfer_manager.RuntimeRole") as mock_runtime_role_cls:
            mock_runtime_role_cls.side_effect = lambda **kwargs: Mock()

            await TransferManager.transfer_role()

        mock_role_instance.all.assert_called_once()
        assert mock_runtime_role_instance.create.call_count == 3

    @pytest.mark.asyncio
    @patch("musigree.transfer.transfer_manager.offline_transaction")
    @patch("musigree.transfer.transfer_manager.RuntimeStyleRepository")
    @patch("musigree.transfer.transfer_manager.RuntimeGenreRepository")
    @patch("musigree.transfer.transfer_manager.RuntimeCountryRepository")
    @patch("musigree.transfer.transfer_manager.runtime_transaction")
    @patch("musigree.transfer.transfer_manager.RuntimeDatabaseManager")
    async def test_transfer_entity_details(
        self,
        mock_runtime_db_manager: Mock,
        _mock_runtime_transaction: Mock,
        mock_country_repo: Mock,
        mock_genre_repo: Mock,
        mock_style_repo: Mock,
        mock_offline_transaction: Mock,
    ) -> None:
        """Test transfer_entity_details method."""
        mock_offline_transaction.return_value.__aenter__ = AsyncMock()
        mock_offline_transaction.return_value.__aexit__ = AsyncMock()
        _mock_runtime_transaction.return_value.__aenter__ = AsyncMock()
        _mock_runtime_transaction.return_value.__aexit__ = AsyncMock()

        mock_country_instance = AsyncMock()
        mock_genre_instance = AsyncMock()
        mock_style_instance = AsyncMock()
        mock_country_repo.return_value = mock_country_instance
        mock_genre_repo.return_value = mock_genre_instance
        mock_style_repo.return_value = mock_style_instance

        # Empty runtime tables so each detail type is loaded.
        mock_country_instance.count.return_value = 0
        mock_genre_instance.count.return_value = 0
        mock_style_instance.count.return_value = 0

        mock_entity_details = Mock(spec=EntityDetailsIndex)
        mock_entity_details.countries_list = [
            "United States",
            "United Kingdom",
            "Canada",
        ]
        mock_entity_details.genres_list = ["Rock", "Pop", "Jazz"]
        mock_entity_details.styles_list = ["Alternative", "Indie", "Classic"]

        mock_runtime_db_helper = Mock()
        mock_runtime_db_helper.entity_details_index = mock_entity_details
        mock_runtime_db_manager.runtime_database_helper = mock_runtime_db_helper

        await TransferManager.transfer_entity_details()

        assert mock_country_instance.create.call_count == 3
        assert mock_country_instance.commit.call_count == 3
        assert mock_genre_instance.create.call_count == 3
        assert mock_genre_instance.commit.call_count == 3
        assert mock_style_instance.create.call_count == 3
        assert mock_style_instance.commit.call_count == 3

    @pytest.mark.asyncio
    async def test_transfer_load_text_search_index(self) -> None:
        """Test transfer_load_text_search_index method."""
        from pathlib import Path

        with patch("musigree.transfer.transfer_manager.RuntimeDatabaseManager") as mock_db_manager:
            mock_runtime_db_helper = Mock()
            mock_db_manager.runtime_database_helper = mock_runtime_db_helper

            with patch(
                "musigree.transfer.transfer_manager.TextSearchIndex"
            ) as mock_text_search_index_class:
                mock_text_search_index = Mock()
                mock_text_search_index.token_index = {
                    "test_token": [1, 2, 3],
                    "another_token": [4, 5],
                }
                mock_text_search_index_class.load_text_search_index_from_file.return_value = (
                    mock_text_search_index
                )

                with patch(
                    "musigree.transfer.transfer_manager.runtime_transaction"
                ) as mock_runtime_transaction:
                    with patch(
                        "musigree.transfer.transfer_manager.RuntimeTokenRepository"
                    ) as mock_token_repo_class:
                        mock_context_manager = AsyncMock()
                        mock_context_manager.__aenter__.return_value = AsyncMock()
                        mock_context_manager.__aexit__.return_value = None
                        mock_runtime_transaction.return_value = mock_context_manager

                        mock_token_repo = AsyncMock()
                        mock_token_repo_class.return_value = mock_token_repo
                        # Empty runtime token table so the index is loaded.
                        mock_token_repo.count.return_value = 0

                        with (
                            patch.object(
                                utils, "queue_worker_functions", new_callable=AsyncMock
                            ) as mock_queue_worker_functions,
                        ):
                            test_path = Path("/test/path/text_search.data")

                            await TransferManager.transfer_load_text_search_index(test_path)

                            mock_text_search_index_class.load_text_search_index_from_file.assert_called_once_with(
                                test_path
                            )
                            assert (
                                mock_runtime_db_helper.text_search_index == mock_text_search_index
                            )
                            # The 5 token entries are inserted via the worker pool.
                            mock_queue_worker_functions.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_transfer_load_entity_details_index(self) -> None:
        """Test transfer_load_entity_details_index method."""
        from pathlib import Path

        with patch("musigree.transfer.transfer_manager.RuntimeDatabaseManager") as mock_db_manager:
            mock_runtime_db_helper = Mock()
            mock_db_manager.runtime_database_helper = mock_runtime_db_helper

            with patch(
                "musigree.transfer.transfer_manager.EntityDetailsIndex"
            ) as mock_entity_details_index_class:
                mock_entity_details_index = Mock()
                mock_entity_details_index_class.load_entity_details_index_from_file.return_value = (
                    mock_entity_details_index
                )

                test_path = Path("/test/path/entity_details.data")

                await TransferManager.transfer_load_entity_details_index(test_path)

                mock_entity_details_index_class.load_entity_details_index_from_file.assert_called_once_with(
                    test_path
                )
                assert mock_runtime_db_helper.entity_details_index == mock_entity_details_index

    @pytest.mark.asyncio
    async def test_transfer_entity_multithreaded(self) -> None:
        """Test transfer_entity with multithreading enabled."""
        with (
            patch("musigree.transfer.transfer_manager.runtime_transaction"),
            patch("musigree.transfer.transfer_manager.offline_transaction"),
            patch(
                "musigree.transfer.transfer_manager.RuntimeEntityRepository"
            ) as mock_runtime_repo,
            patch("musigree.transfer.transfer_manager.EntityRepository") as mock_offline_repo,
            patch("musigree.transfer.transfer_manager.RuntimeDatabaseManager") as mock_db_manager,
        ):
            mock_runtime_instance = AsyncMock()
            mock_runtime_repo.return_value = mock_runtime_instance
            mock_runtime_instance.count.return_value = 0

            mock_offline_instance = AsyncMock()
            mock_offline_repo.return_value = mock_offline_instance
            mock_offline_instance.count.return_value = 5
            mock_offline_instance.all = Mock(return_value=make_async_gen([]))

            mock_db_manager.get_concurrency_count.return_value = 4
            mock_db_manager.runtime_database_helper = Mock()

            # The test passes if the method completes without throwing an exception.
            await TransferManager.transfer_entity()

    @patch("musigree.transfer.transfer_manager.offline_transaction")
    @patch("musigree.transfer.transfer_manager.RuntimeDatabaseManager")
    @patch("musigree.transfer.transfer_manager.EntityRepository")
    @patch("musigree.transfer.transfer_manager.RuntimeEntityRepository")
    @patch("musigree.transfer.transfer_manager.runtime_transaction")
    @pytest.mark.asyncio
    async def test_transfer_entity_database_error_handling(
        self,
        mock_runtime_transaction: Mock,
        mock_runtime_repo: Mock,
        mock_offline_repo: Mock,
        _mock_db_manager: Mock,
        mock_offline_transaction: Mock,
    ) -> None:
        """Test transfer_entity error handling when database operations fail."""
        mock_runtime_transaction.return_value = AsyncMock()
        mock_offline_transaction.return_value = AsyncMock()

        mock_runtime_instance = AsyncMock()
        mock_offline_instance = AsyncMock()
        mock_runtime_repo.return_value = mock_runtime_instance
        mock_offline_repo.return_value = mock_offline_instance

        # Database error during count operation in the first runtime transaction.
        mock_runtime_instance.count.side_effect = Exception("Database connection failed")

        with pytest.raises(Exception, match="Database connection failed"):
            await TransferManager.transfer_entity()

    @patch("musigree.transfer.transfer_manager.offline_transaction")
    @patch("musigree.transfer.transfer_manager.RuntimeDatabaseManager")
    @patch("musigree.transfer.transfer_manager.EntityRepository")
    @patch("musigree.transfer.transfer_manager.RuntimeEntityRepository")
    @patch("musigree.transfer.transfer_manager.runtime_transaction")
    @pytest.mark.asyncio
    async def test_transfer_entity_with_timeout(
        self,
        mock_runtime_transaction: Mock,
        mock_runtime_repo: Mock,
        mock_offline_repo: Mock,
        mock_db_manager: Mock,
        mock_offline_transaction: Mock,
    ) -> None:
        """Test transfer_entity completes with multi-worker concurrency configured."""
        mock_runtime_transaction.return_value.__aenter__ = AsyncMock()
        mock_runtime_transaction.return_value.__aexit__ = AsyncMock()
        mock_offline_transaction.return_value.__aenter__ = AsyncMock()
        mock_offline_transaction.return_value.__aexit__ = AsyncMock()

        mock_offline_instance = AsyncMock()
        mock_runtime_instance = AsyncMock()
        mock_offline_repo.return_value = mock_offline_instance
        mock_runtime_repo.return_value = mock_runtime_instance

        mock_runtime_instance.count.return_value = 0
        mock_offline_instance.count.return_value = 3
        mock_offline_instance.all = Mock(return_value=make_async_gen([]))

        mock_db_manager.get_concurrency_count.return_value = 2

        # The test passes if the method completes without throwing an exception.
        await TransferManager.transfer_entity()
