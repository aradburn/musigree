"""
This module provides data access functionality for master data records within the Musigree offline system.

It defines the `OfflineMasterDataAccess` class, which offers methods for resolving
master record references. It is designed to be used during the offline data loading process.

Key functionalities include:
    - Resolving master references: replacing master record refrences with the master record title.
    - Logging of debug and error messages during the data access operations.

The `OfflineMasterDataAccess` class interacts with `MasterRepository` for database
operations and `CacheManager` for caching.

The `Master` class from `musigree.offline.offline_domain` is used
to represent master data record.
"""

import logging

from musigree.offline.offline_database.master_repository import MasterRepository

log = logging.getLogger(__name__)
"""
The logger for the OfflineMasterDataAccess module.
"""


class OfflineMasterDataAccess:
    """
    Provides data access functionality for master records within the Musigree offline system.

    This class offers methods for resolving master references.
    """

    @staticmethod
    async def get_master_title_from_master_id(master_id: int) -> str:
        """
        Resolves master title references.

        Args:
            master_id (int): The master_id.

        Returns:
            str: Master record title.

        """
        master_repository = MasterRepository()
        master = await master_repository.get_by_id(master_id)
        return master.title
