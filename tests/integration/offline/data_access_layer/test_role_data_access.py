import os

import pytest

from musigree.constants import ROOT_DIR
from tests.conftest import AbstractDatabaseTest

TEST_DATA_ROLES_DIR = os.path.join(ROOT_DIR, "tests", "data_roles")
TEST_DATA_ROLES_PATH = os.path.join(TEST_DATA_ROLES_DIR, "test_data_roles.tsv")
TEST_DATA_ROLES_NORMALISED_PATH = os.path.join(
    TEST_DATA_ROLES_DIR, "test_data_roles_normalised.tsv"
)
TEST_DATA_ROLES_OUTPUT_PATH = os.path.join(
    TEST_DATA_ROLES_DIR, "test_data_roles_output.tsv"
)


@pytest.mark.parametrize("is_load_offline_data_required", [True], scope="class")
class TestRoleDataAccess(AbstractDatabaseTest):
    pass

    # @pytest.mark.skip(reason="Skip for now")
    # def test_generate_test_data_file(self):
    #     with open(TEST_DATA_ROLES_NORMALISED_PATH, encoding="utf-8") as csvfile:
    #         # dialect = csv.Sniffer().sniff(csvfile.read(1024), delimiters="\t")
    #         csvfile.seek(0)
    #         csv_reader = csv.DictReader(csvfile, escapechar="\\", delimiter="\t")
    #
    #         with open(
    #             TEST_DATA_ROLES_OUTPUT_PATH, "w", newline="", encoding="utf-8"
    #         ) as output_file:
    #             fieldnames = ["input", "expected"]
    #             # noinspection PyTypeChecker
    #             writer = csv.DictWriter(
    #                 output_file,
    #                 fieldnames=fieldnames,
    #                 # dialect=dialect,
    #                 escapechar="\\",
    #                 quotechar='"',
    #                 delimiter="\t",
    #                 quoting=csv.QUOTE_MINIMAL,
    #                 doublequote=False,
    #             )
    #             writer.writeheader()
    #
    #             for input_row in csv_reader:
    #                 input_row: dict
    #                 input_str = input_row["input"]
    #                 # print(f"in : {input_str}")
    #                 expected_str = RoleDataAccess.find_role(input_str)
    #                 # print(f"out: {expected_str}")
    #                 output_row: dict[str, str] = {
    #                     "input": input_str,
    #                     "expected": expected_str,
    #                 }
    #                 writer.writerow(output_row)
    #                 # print()
