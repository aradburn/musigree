# import logging
# from typing import List
#
# import pytest
#
# from musigree.app.app import create_app, shutdown_application
# from musigree.config import SqliteTestConfiguration, ALL_RUNTIME_DATABASE_TABLE_NAMES
# from musigree.offline.domain.role import RoleUncommitted
# from musigree.offline.loader.loader_role import LoaderRole
# from musigree.runtime.runtime_database.runtime_role_repository import (
#     RuntimeRoleRepository,
# )
# from musigree.runtime.runtime_database.runtime_transaction import transaction
# from musigree.runtime.runtime_database_manager import RuntimeDatabaseManager
# from musigree.runtime.runtime_domain.role import RuntimeRole
#
# log = logging.getLogger(__name__)


# @pytest.fixture(scope="class")
# def app():
#     log.debug("pytest app fixture")
#     _config = SqliteTestConfiguration()
#     # _config = PostgresTestConfiguration()
#     app = create_app(_config)
#     app.config.update(
#         {
#             "TESTING": True,
#         }
#     )
#
#     # For testing, drop and recreate all tables
#     RuntimeDatabaseManager.runtime_db_helper.drop_tables(
#         ALL_RUNTIME_DATABASE_TABLE_NAMES
#     )
#     RuntimeDatabaseManager.runtime_db_helper.create_tables(
#         ALL_RUNTIME_DATABASE_TABLE_NAMES
#     )
#
#     def save_roles(roles: List[RoleUncommitted]) -> None:
#         log.debug(f"Adding roles to RuntimeRoleRepository")
#         runtime_role_repository = RuntimeRoleRepository()
#
#         role_id = 0
#         with transaction():
#             for role in roles:
#                 role_dict = role.model_dump()
#                 role_dict.update(id=role_id)
#                 runtime_role = RuntimeRole(**role_dict)
#                 runtime_role_repository.create(runtime_role)
#                 role_id += 1
#
#     # Load roles from file
#     # Read from each source of roles and save into database, deduplicating role names as we go
#     roles: List[RoleUncommitted] = []
#
#     file_roles = LoaderRole.load_roles_from_files()
#     roles.extend(file_roles)
#
#     hornbostel_sachs_roles = LoaderRole.load_hornbostel_sachs_instruments()
#     roles.extend(hornbostel_sachs_roles)
#
#     wikipedia_roles = LoaderRole.load_wikipedia_instruments()
#     roles.extend(wikipedia_roles)
#
#     save_roles(roles)
#
#     RuntimeDatabaseManager.runtime_db_helper.load_tables()
#
#     yield app
#
#     # clean up / reset resources here
#     shutdown_application()
#
#
# @pytest.fixture(scope="class")
# def client(app):
#     log.debug("pytest client fixture")
#     return app.test_client()


# @pytest.fixture()
# def runner(app):
#     return app.test_cli_runner()
