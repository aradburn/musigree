import csv
import json
import logging
from abc import abstractmethod
from pathlib import Path
from typing import Any, Callable

from musigree.constants import INSTRUMENTS_DATA_FILENAMES, HS_INSTRUMENTS_FILENAME
from musigree.exceptions import DatabaseError
from musigree.library.fields.entity_type import EntityType
from musigree.library.fields.role_type import RoleType
from musigree.offline.data_access_layer.role_data_access import RoleDataAccess
from musigree.offline.data_access_layer.role_data_utils import RoleDataUtils
from musigree.offline.database.offline_transaction import offline_transaction
from musigree.offline.database.role_repository import RoleRepository
from musigree.offline.domain.instruments import HornbostelSachs
from musigree.offline.domain.role import (
    RoleUncommitted,
)
from musigree.offline.loader.loader_base import LoaderBase
from musigree.offline.loader.loader_utils import LoaderUtils

log = logging.getLogger(__name__)


class LoaderRole(LoaderBase):
    # CLASS METHODS

    @classmethod
    async def load_roles_into_database(
        cls, roles_directory: Path, instruments_directory: Path
    ) -> None:
        log.info("Loading initial roles ")

        # Read from each source of roles and save into database, deduplicating role names as we go
        file_roles = cls.load_roles_from_files(roles_directory)
        await cls.save_roles(file_roles)

        hornbostel_sachs_roles = cls.load_hornbostel_sachs_instruments(
            instruments_directory
        )
        await cls.save_roles(hornbostel_sachs_roles)

        wikipedia_roles = cls.load_wikipedia_instruments(instruments_directory)
        await cls.save_roles(wikipedia_roles)

        # Load back in all roles from database
        # TODO check if needed
        await RoleDataAccess.load_all_roles_into_cache()
        log.debug("Initial roles loaded OK")

    @classmethod
    def load_wikipedia_instruments(
        cls, instruments_directory: Path
    ) -> list[RoleUncommitted]:
        log.info("Loading Wikipedia instruments")

        roles = []
        loaded_count = 0

        # Load wikipedia data
        for filename in INSTRUMENTS_DATA_FILENAMES:
            instruments_path = instruments_directory / filename
            log.debug(f"Loading from: {instruments_path}")
            with open(instruments_path) as csvfile:
                dialect = csv.Sniffer().sniff(csvfile.read(1024))
                csvfile.seek(0)
                csv_reader = csv.DictReader(csvfile, dialect=dialect)

                for row in csv_reader:
                    instrument_name: str = row["Instrument"]
                    instrument_class: str = row["Classification"]
                    normalised_role_name_list = RoleDataUtils.normalise_role_names(
                        instrument_name
                    )

                    for normalised_role_name in normalised_role_name_list:
                        category_id = RoleType.Category.INSTRUMENTS
                        category_name = RoleType.category_names[category_id]
                        subcategory_id = RoleType.hornbostel_sachs_to_subcategory(
                            instrument_class
                        )
                        subcategory_name = RoleType.subcategory_names[subcategory_id]
                        new_role = RoleUncommitted(
                            role_name=normalised_role_name,
                            role_category=category_id,
                            role_subcategory=subcategory_id,
                            role_category_name=category_name,
                            role_subcategory_name=subcategory_name,
                        )
                        roles.append(new_role)
                        loaded_count += 1

        log.debug(f"Loaded {loaded_count} roles")
        return roles

    @classmethod
    def load_hornbostel_sachs_instruments(
        cls, instruments_directory: Path
    ) -> list[RoleUncommitted]:
        # Load Hornbostel Sachs instrument data
        log.info("Load Hornbostel Sachs instrument data")

        roles = []
        loaded_count = 0

        hs_filename = instruments_directory / HS_INSTRUMENTS_FILENAME
        with open(hs_filename) as f:
            json_data = json.load(f)
            instruments_data = HornbostelSachs(**json_data)

            for key, instrument_entry in instruments_data.root.items():
                instrument_class_key = key[0]
                value = instruments_data.root.get(instrument_class_key)
                if value is not None:
                    instrument_class = value.label
                else:
                    instrument_class = "Unknown"
                category_id = RoleType.Category.INSTRUMENTS
                category_name = RoleType.category_names[category_id]
                subcategory_id = RoleType.hornbostel_sachs_to_subcategory(
                    instrument_class
                )
                subcategory_name = RoleType.subcategory_names[subcategory_id]

                for instrument_name in instrument_entry.instruments:
                    normalised_role_name_list = RoleDataUtils.normalise_role_names(
                        instrument_name
                    )

                    for normalised_role_name in normalised_role_name_list:
                        new_role = RoleUncommitted(
                            role_name=normalised_role_name,
                            role_category=category_id,
                            role_subcategory=subcategory_id,
                            role_category_name=category_name,
                            role_subcategory_name=subcategory_name,
                        )
                        roles.append(new_role)
                        loaded_count += 1

        log.debug(f"Loaded {loaded_count} roles")
        return roles

    @classmethod
    def load_roles_from_files(cls, roles_directory: Path) -> list[RoleUncommitted]:
        log.info("Loading roles from files")

        roles = []
        loaded_count = 0

        role_paths = LoaderUtils.get_role_paths(roles_directory)
        for role_path in role_paths:
            log.debug(f"Loading from: {role_path}")
            with open(role_path, encoding="utf-8") as csvfile:
                dialect = csv.Sniffer().sniff(csvfile.read(1024))
                csvfile.seek(0)
                csv_reader = csv.DictReader(csvfile, dialect=dialect)

                for row in csv_reader:
                    # row: dict
                    role_name = row["name"]
                    normalised_role_name_list = RoleDataUtils.normalise_role_names(
                        role_name
                    )

                    for normalised_role_name in normalised_role_name_list:
                        category_str: str = row["category"]
                        category_id = RoleType.Category[category_str]
                        category_enum = RoleType.Category(category_id)
                        category_name = RoleType.category_names[category_id]
                        if row["subcategory"]:
                            subcategory_str: str = row["subcategory"]
                            subcategory_id = RoleType.Subcategory[subcategory_str]
                            subcategory_enum = RoleType.Subcategory(subcategory_id)
                        else:
                            subcategory_id = RoleType.Subcategory.NONE
                            subcategory_enum = RoleType.Subcategory.NONE
                        subcategory_name = RoleType.subcategory_names[subcategory_id]

                        # Add new role
                        new_role = RoleUncommitted(
                            role_name=normalised_role_name,
                            role_category=category_enum,
                            role_subcategory=subcategory_enum,
                            role_category_name=category_name,
                            role_subcategory_name=subcategory_name,
                        )
                        roles.append(new_role)
                        loaded_count += 1

        log.debug(f"Loaded {loaded_count} roles")
        return roles

    @classmethod
    async def save_roles(cls, roles: list[RoleUncommitted]) -> int:
        log.debug("Adding roles to RoleRepository")
        if roles is None or len(roles) == 0:
            return 0

        role_repository = RoleRepository()

        async with offline_transaction():

            try:
                await role_repository.create_bulk(roles, on_conflict_do_nothing=True)
                await role_repository.commit()
            except DatabaseError:
                await role_repository.rollback()

        log.debug(f"Added {len(roles)} roles")
        return len(roles)

    # @classmethod
    # async def save_roles(cls, roles: list[RoleUncommitted]) -> int:
    #     log.debug("Adding roles to RoleRepository")
    #     bulk_inserts = []
    #     names = set()
    #     async with offline_transaction():
    #         added_count = 0
    #         role_repository = RoleRepository()
    #
    #         for role_uncommitted in roles:
    #             if role_uncommitted.role_name not in names:
    #                 names.add(role_uncommitted.role_name)
    #                 # Check if the role already exists in the database
    #                 # If it does not, add it to the bulk inserts
    #                 try:
    #                     await role_repository.get_by_name(
    #                         name=role_uncommitted.role_name
    #                     )
    #                 except NotFoundError:
    #                     # Add new role
    #                     bulk_inserts.append(role_uncommitted.model_dump())
    #                     added_count += 1
    #
    #         await role_repository.save_all(bulk_inserts)
    #         """Insert the roles."""
    #         await role_repository.commit()
    #
    #     log.debug(f"Added {added_count} roles")
    #     return added_count

    # noinspection Mypy
    @staticmethod
    def get_insert_worker_function() -> Callable[[list[dict[str, Any]], int, int], None]:  # type: ignore
        pass

    # noinspection Mypy
    @staticmethod
    def get_update_worker_function() -> Callable[[list[dict[str, Any]], int, int], None]:  # type: ignore
        pass

    # noinspection Mypy
    @staticmethod
    def get_delete_worker_function() -> Callable[[list[int], int, int], None]:  # type: ignore
        pass

    # noinspection Mypy
    @classmethod
    @abstractmethod
    async def get_set_of_ids(cls, entity_type: EntityType | None) -> set[int]:  # type: ignore
        pass
