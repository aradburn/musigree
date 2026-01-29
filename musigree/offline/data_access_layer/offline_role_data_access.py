import functools
import logging
import re
from collections import deque

from rapidfuzz import process

from musigree.library.cache.role_cache import RoleCache
from musigree.logging_config import LOGGING_TRACE
from musigree.offline.data_access_layer.role_data_utils import RoleDataUtils
from musigree.offline.offline_database.offline_transaction import offline_transaction
from musigree.offline.offline_database.role_repository import RoleRepository

log = logging.getLogger(__name__)


class OfflineRoleDataAccess:
    @staticmethod
    def role_name_lookup(role_name: str) -> tuple[str, int] | None:
        if role_name in RoleCache.role_name_set:
            return role_name, 100
        else:
            # Match lower case versions, but return correct name
            role_name_lower = role_name.lower()
            for name in RoleCache.role_name_set:
                if role_name_lower == name.lower():
                    return name, 100
        return None

    @staticmethod
    def role_name_fuzzy_lookup(role_name: str) -> tuple[str, int] | None:
        top_role_name = process.extractOne(
            role_name,
            RoleCache.role_name_set,
            # score_hint=90,
        )
        if top_role_name is not None and top_role_name[1] > 90:
            return top_role_name[0], int(top_role_name[1])
        else:
            return None

    @staticmethod
    def find_role(role_name: str) -> str | None:
        # Role name has already been normalised

        # Keep track of best candidate so far
        top_candidate = ""
        top_score = 0

        # Using a breadth-first breakdown of words in role_name
        queue: deque = deque()
        queue.append(role_name)

        while queue:
            queued_role_name: str = queue.popleft()

            # find if we have a match
            found_role_name = OfflineRoleDataAccess.find_role_inner(queued_role_name)
            if found_role_name is not None:
                if found_role_name[1] > top_score:
                    top_candidate = found_role_name[0]
                    top_score = found_role_name[1]

            # Remove each word in turn and add to queue
            word_list = queued_role_name.split(" ")
            if len(word_list) < 5:
                # Start from far end
                word_list.reverse()
                for word in word_list:
                    # Remove word
                    processed_role_name = queued_role_name.replace(word, "")
                    processed_role_name = re.sub(r" {2}", " ", processed_role_name)
                    processed_role_name = processed_role_name.strip()

                    if processed_role_name != "":
                        # Add to queue
                        queue.append(processed_role_name)
            else:
                # Long sentence makes processing too complex, so split in two
                word_list_part_one = word_list[: len(word_list) // 2]
                word_list_part_two = word_list[len(word_list) // 2 :]
                part_1 = " ".join(word_list_part_one)
                part_2 = " ".join(word_list_part_two)
                queue.append(part_1)
                queue.append(part_2)

        if top_candidate != "" and top_score > 90:
            return top_candidate
        else:
            log.debug(f"role not found: {role_name}")
            return None

    @staticmethod
    @functools.lru_cache(maxsize=100000)
    def find_role_inner(role_name: str | None) -> tuple[str, int] | None:
        if role_name is None or role_name == "":
            return None

        role_name = OfflineRoleDataAccess.substitute_role_alternatives(role_name)

        lookup_result = OfflineRoleDataAccess.role_name_lookup(role_name)
        if lookup_result is not None:
            return lookup_result

        top_role_name = OfflineRoleDataAccess.role_name_fuzzy_lookup(role_name)
        if top_role_name is not None:
            return top_role_name

        return None

    @staticmethod
    def substitute_role_alternatives(role_name: str) -> str:
        # Replacements
        role_name_lower = role_name.lower()
        for alt in RoleDataUtils.ALTERNATIVES.items():
            if role_name_lower == alt[0]:
                return alt[1]
        return role_name

    @staticmethod
    async def load_all_roles_into_cache() -> None:
        """
        Loads all roles from the offline database and populates the cache.

        This method retrieves all roles from the database and populates various
        cache structures for efficient role lookups. It clears existing cache
        data before loading new data.

        The method populates the following cache structures:
        - role_id_to_role_name_lookup: Maps role IDs to role names
        - role_id_to_role_category_lookup: Maps role IDs to role categories
        - role_name_to_role_id_lookup: Maps role names to role IDs
        - role_name_set: Set of all role names

        After loading the roles, it logs the number of roles loaded.
        """
        log.debug("Loading roles from offline RoleRepository")
        RoleCache.role_id_to_role_name_lookup.clear()
        RoleCache.role_id_to_role_category_lookup.clear()
        RoleCache.role_name_to_role_id_lookup.clear()
        RoleCache.role_name_set.clear()

        async with offline_transaction():
            role_repository = RoleRepository()
            roles = []
            async for role in role_repository.all():
                roles.append(role)
            for role in roles:
                RoleCache.role_id_to_role_name_lookup[role.id] = role.role_name
                RoleCache.role_id_to_role_category_lookup[role.id] = role.role_category

        RoleCache.role_name_to_role_id_lookup = {
            v: k for k, v in RoleCache.role_id_to_role_name_lookup.items()
        }
        for role_name in RoleCache.role_id_to_role_name_lookup.values():
            RoleCache.role_name_set.add(role_name)
        if LOGGING_TRACE:
            sorted_list = sorted(RoleCache.role_name_set)
            for item in sorted_list:
                log.debug(f"{item}")
        log.debug(f"Loaded {len(RoleCache.role_name_to_role_id_lookup)} roles from RoleRepository")
