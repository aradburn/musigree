from musigree import utils
from musigree.offline.database.role_repository import RoleRepository
from musigree.offline.database.offline_transaction import offline_transaction
from tests.integration.offline.database.offline_database_test_case import (
    OfflineDatabaseTestCase,
)


class TestDatabaseRole(OfflineDatabaseTestCase):
    def test_from_db_01(self):
        name = "Acoustic Bass"
        with offline_transaction():
            role_repository = RoleRepository()
            role = role_repository.get_by_name(name)
            actual = utils.normalize_dict(role.model_dump(exclude={"id"}))

        expected_role = {
            "role_category": "Category.INSTRUMENTS",
            "role_category_name": "Instruments",
            "role_name": "Acoustic Bass",
            "role_subcategory": "Subcategory.STRINGED_INSTRUMENTS",
            "role_subcategory_name": "String Instruments",
        }
        expected = utils.normalize_dict(expected_role)
        self.assertEqual(expected, actual)

    def test_from_db_02(self):
        name = "Mezzo-Soprano Vocals"
        with offline_transaction():
            role_repository = RoleRepository()
            role = role_repository.get_by_name(name)
            actual = utils.normalize_dict(role.model_dump(exclude={"id"}))

        expected_role = {
            "role_category": "Category.VOCAL",
            "role_category_name": "Vocal",
            "role_name": "Mezzo-Soprano Vocals",
            "role_subcategory": "Subcategory.NONE",
            "role_subcategory_name": "None",
        }
        expected = utils.normalize_dict(expected_role)
        self.assertEqual(expected, actual)
