import os

import pytest

from musigree.constants import ROOT_DIR
from tests.conftest import AbstractDatabaseTest

TEST_DATA_ROLES_DIR = os.path.join(ROOT_DIR, "tests", "data_roles")
TEST_DATA_ROLES_PATH = os.path.join(TEST_DATA_ROLES_DIR, "test_data_roles.tsv")
TEST_DATA_ROLES_NORMALISED_PATH = os.path.join(
    TEST_DATA_ROLES_DIR, "test_data_roles_normalised.tsv"
)
TEST_DATA_ROLES_OUTPUT_PATH = os.path.join(TEST_DATA_ROLES_DIR, "test_data_roles_output.tsv")


@pytest.mark.parametrize("is_load_offline_data_required", [True], scope="class")
class TestRoleDataAccess(AbstractDatabaseTest):
    pass
