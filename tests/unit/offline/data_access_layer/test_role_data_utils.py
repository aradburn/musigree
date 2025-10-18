import csv
import pytest

from musigree.constants import ROOT_DIR
from musigree.offline.data_access_layer.role_data_utils import RoleDataUtils

TEST_DATA_ROLES_DIR = ROOT_DIR / "tests" / "data_roles"
TEST_DATA_ROLES_FILENAME = "test_data_roles.tsv"
TEST_DATA_ROLES_PATH = TEST_DATA_ROLES_DIR / TEST_DATA_ROLES_FILENAME


def test_normalise_01() -> None:
    """Test normalisation of 'Mastered By' role name."""
    input_str = "Mastered By"
    expected_str = "Mastered By"
    actual_str = RoleDataUtils.normalise_role_name(input_str)
    assert expected_str == actual_str


def test_normalise_02a() -> None:
    """Test normalisation of 'Mastered by' role name with lowercase 'by'."""
    input_str = "Mastered by"
    expected_str = "Mastered By"
    actual_str = RoleDataUtils.normalise_role_name(input_str)
    assert expected_str == actual_str


def test_normalise_02b() -> None:
    """Test normalisation of 'Mastered-by' role name with hyphen."""
    input_str = "Mastered-by"
    expected_str = "Mastered By"
    actual_str = RoleDataUtils.normalise_role_name(input_str)
    assert expected_str == actual_str


def test_normalise_03() -> None:
    """Test normalisation of 'Tam-Tam' role name (should remain unchanged)."""
    input_str = "Tam-Tam"
    expected_str = "Tam-Tam"
    actual_str = RoleDataUtils.normalise_role_name(input_str)
    assert expected_str == actual_str


def test_normalise_04() -> None:
    """Test normalisation of 'Tam-tam' role name with lowercase second part."""
    input_str = "Tam-tam"
    expected_str = "Tam-Tam"
    actual_str = RoleDataUtils.normalise_role_name(input_str)
    assert expected_str == actual_str


def test_normalise_05() -> None:
    """Test normalisation of 'tam-tam' role name with all lowercase."""
    input_str = "tam-tam"
    expected_str = "Tam-Tam"
    actual_str = RoleDataUtils.normalise_role_name(input_str)
    assert expected_str == actual_str


def test_normalise_06() -> None:
    """Test normalisation of multiple 'tam-tam' variations in one string."""
    input_str = "Tam-tam tam-Tam Tam-tam"
    expected_str = "Tam-Tam Tam-Tam Tam-Tam"
    actual_str = RoleDataUtils.normalise_role_name(input_str)
    assert expected_str == actual_str


def test_normalise_07() -> None:
    """Test normalisation of 'Oboe d'Amore' role name (should remain unchanged)."""
    input_str = "Oboe d\u0027Amore"
    expected_str = "Oboe d\u0027Amore"
    actual_str = RoleDataUtils.normalise_role_name(input_str)
    assert expected_str == actual_str


def test_normalise_08() -> None:
    """Test normalisation of 'Oboe D'amore' role name with incorrect case."""
    input_str = "Oboe D\u0027amore"
    expected_str = "Oboe d\u0027Amore"
    actual_str = RoleDataUtils.normalise_role_name(input_str)
    assert expected_str == actual_str


def test_normalise_09() -> None:
    """Test normalisation of 'MC' role name (should remain unchanged)."""
    input_str = "MC"
    expected_str = "MC"
    actual_str = RoleDataUtils.normalise_role_name(input_str)
    assert expected_str == actual_str


def test_normalise_10() -> None:
    """Test normalisation of 'DAW' role name (should remain unchanged)."""
    input_str = "DAW"
    expected_str = "DAW"
    actual_str = RoleDataUtils.normalise_role_name(input_str)
    assert expected_str == actual_str


def test_normalise_11() -> None:
    """Test normalisation of 'DJ Mix' role name (should remain unchanged)."""
    input_str = "DJ Mix"
    expected_str = "DJ Mix"
    actual_str = RoleDataUtils.normalise_role_name(input_str)
    assert expected_str == actual_str


def test_normalise_12a() -> None:
    """Test normalisation of 'Tar (Lute)' role name (parentheses removed)."""
    input_str = "Tar (Lute)"
    expected_str = "Tar"
    actual_str = RoleDataUtils.normalise_role_name(input_str)
    assert expected_str == actual_str


def test_normalise_12b() -> None:
    """Test normalisation of 'Tar (lute)' role name (parentheses removed)."""
    input_str = "Tar (lute)"
    expected_str = "Tar"
    actual_str = RoleDataUtils.normalise_role_name(input_str)
    assert expected_str == actual_str


def test_normalise_12c() -> None:
    """Test normalisation of 'Tar (drum)' role name (parentheses removed)."""
    input_str = "Tar (drum)"
    expected_str = "Tar"
    actual_str = RoleDataUtils.normalise_role_name(input_str)
    assert expected_str == actual_str


def test_normalise_13() -> None:
    """Test normalisation of 'Written' role name (should remain unchanged)."""
    input_str = "Written"
    expected_str = "Written"
    actual_str = RoleDataUtils.normalise_role_name(input_str)
    assert expected_str == actual_str


def test_normalise_14() -> None:
    """Test normalisation of 'Written-By' role name with hyphen."""
    input_str = "Written-By"
    expected_str = "Written By"
    actual_str = RoleDataUtils.normalise_role_name(input_str)
    assert expected_str == actual_str


def test_normalise_15() -> None:
    """Test normalisation of 'Written By' role name (should remain unchanged)."""
    input_str = "Written By"
    expected_str = "Written By"
    actual_str = RoleDataUtils.normalise_role_name(input_str)
    assert expected_str == actual_str


def test_normalise_16() -> None:
    """Test normalisation of 'Written-by' role name with hyphen and lowercase."""
    input_str = "Written-by"
    expected_str = "Written By"
    actual_str = RoleDataUtils.normalise_role_name(input_str)
    assert expected_str == actual_str


def test_normalise_17a() -> None:
    """Test normalisation of 'A&R' role name (should remain unchanged)."""
    input_str = "A&R"
    expected_str = "A&R"
    actual_str = RoleDataUtils.normalise_role_name(input_str)
    assert expected_str == actual_str


def test_normalise_17b() -> None:
    """Test normalisation of 'A&r' role name (should remain unchanged)."""
    input_str = "A&r"
    expected_str = "A&r"
    actual_str = RoleDataUtils.normalise_role_name(input_str)
    assert expected_str == actual_str


def test_normalise_17c() -> None:
    """Test normalisation of 'A&R' role names list."""
    input_str = "A&R"
    expected_str = ["A&R"]
    actual_str = RoleDataUtils.normalise_role_names(input_str)
    assert expected_str == actual_str


def test_normalise_17d() -> None:
    """Test normalisation of 'A&r' role names list."""
    input_str = "A&r"
    expected_str = ["A&R"]
    actual_str = RoleDataUtils.normalise_role_names(input_str)
    assert expected_str == actual_str


def test_normalise_19() -> None:
    """Test normalisation of 'CGI Artist' role name (should remain unchanged)."""
    input_str = "CGI Artist"
    expected_str = "CGI Artist"
    actual_str = RoleDataUtils.normalise_role_name(input_str)
    assert expected_str == actual_str


def test_normalise_20() -> None:
    """Test normalisation of 'Cgi Artist' role name with incorrect case."""
    input_str = "Cgi Artist"
    expected_str = "CGI Artist"
    actual_str = RoleDataUtils.normalise_role_name(input_str)
    assert expected_str == actual_str


def test_normalise_21() -> None:
    """Test normalisation of 'DJ Mix' role name (should remain unchanged)."""
    input_str = "DJ Mix"
    expected_str = "DJ Mix"
    actual_str = RoleDataUtils.normalise_role_name(input_str)
    assert expected_str == actual_str


def test_normalise_22() -> None:
    """Test normalisation of 'Dj mix' role name with incorrect case."""
    input_str = "Dj mix"
    expected_str = "DJ Mix"
    actual_str = RoleDataUtils.normalise_role_name(input_str)
    assert expected_str == actual_str


def test_normalise_23() -> None:
    """Test normalisation of 'Vibes' role name.

    Actual instrument names are not changed at this point,
    vibes gets changed to vibraphone later on in find_role().
    """
    input_str = "Vibes"
    expected_str = "Vibes"
    actual_str = RoleDataUtils.normalise_role_name(input_str)
    assert expected_str == actual_str


def test_normalise_role_names_1() -> None:
    """Test normalisation of multiple role names separated by 'and'."""
    input_str = "Something and Something Else"
    expected_str = ["Something", "Something Else"]
    actual_str = RoleDataUtils.normalise_role_names(input_str)
    assert expected_str == actual_str


def test_normalise_role_names_2() -> None:
    """Test normalisation of multiple role names separated by '&'."""
    input_str = "Something & Something Else"
    expected_str = ["Something", "Something Else"]
    actual_str = RoleDataUtils.normalise_role_names(input_str)
    assert expected_str == actual_str


def test_normalise_role_names_3() -> None:
    """Test normalisation of three role names separated by 'and'."""
    input_str = "Something and Something Else and More"
    expected_str = ["Something", "Something Else", "More"]
    actual_str = RoleDataUtils.normalise_role_names(input_str)
    assert expected_str == actual_str


def test_normalise_role_names_4() -> None:
    """Test normalisation of role names with mixed 'and' and '&' separators."""
    input_str = "Something and Something Else and More & more"
    expected_str = ["Something", "Something Else", "More", "More"]
    actual_str = RoleDataUtils.normalise_role_names(input_str)
    assert expected_str == actual_str


def test_normalise_role_names_5() -> None:
    """Test normalisation of 'Written by & vibes' role names."""
    input_str = "Written by & vibes"
    expected_str = ["Written By", "Vibes"]
    actual_str = RoleDataUtils.normalise_role_names(input_str)
    assert expected_str == actual_str


def test_normalise_role_names_6() -> None:
    """Test normalisation of 'Artwork & Package Design By' role names."""
    input_str = "Artwork & Package Design By"
    expected_str = ["Artwork", "Package Design By"]
    actual_str = RoleDataUtils.normalise_role_names(input_str)
    assert expected_str == actual_str


@pytest.mark.skip(reason="not used")
def test_normalise_role_names_from_test_file() -> None:
    """Test normalisation of role names from test data file.

    This test is skipped as it's not currently used.
    """
    with open(TEST_DATA_ROLES_PATH, encoding="utf-8") as csvfile:
        dialect = csv.Sniffer().sniff(csvfile.read(1024))
        csvfile.seek(0)
        csv_reader = csv.DictReader(csvfile, dialect=dialect, escapechar="\\")

        for row in csv_reader:
            input_str: str = row["input"]
            expected_1_str: str | None = row["expected_1"]
            if expected_1_str == "":
                expected_1_str = None
            if expected_1_str is not None:
                expected_1_str = expected_1_str.replace('\\"', '"')
            expected_2_str: str | None = row["expected_2"]
            if expected_2_str == "":
                expected_2_str = None
            if expected_2_str is not None:
                expected_2_str = expected_2_str.replace('\\"', '"')
            expected_3_str: str | None = row["expected_3"]
            if expected_3_str == "":
                expected_3_str = None
            if expected_3_str is not None:
                expected_3_str = expected_3_str.replace('\\"', '"')
            expected_4_str: str | None = row["expected_4"]
            if expected_4_str == "":
                expected_4_str = None
            if expected_4_str is not None:
                expected_4_str = expected_4_str.replace('\\"', '"')
            expected_5_str: str | None = row["expected_5"]
            if expected_5_str == "":
                expected_5_str = None
            if expected_5_str is not None:
                expected_5_str = expected_5_str.replace('\\"', '"')
            print(f"input: {input_str}, expected_1: {expected_1_str}, expected_2: {expected_2_str}")
            normalised_role_name_list = RoleDataUtils.normalise_role_names(input_str)
            actual_1_str = (
                normalised_role_name_list[0]
                if len(normalised_role_name_list) > 0 and len(normalised_role_name_list[0]) > 0
                else None
            )
            print(f"      actual_1: {actual_1_str}")
            actual_2_str = (
                normalised_role_name_list[1]
                if len(normalised_role_name_list) > 1 and len(normalised_role_name_list[1]) > 0
                else None
            )
            actual_3_str = (
                normalised_role_name_list[2]
                if len(normalised_role_name_list) > 2 and len(normalised_role_name_list[2]) > 0
                else None
            )
            actual_4_str = (
                normalised_role_name_list[3]
                if len(normalised_role_name_list) > 3 and len(normalised_role_name_list[3]) > 0
                else None
            )
            actual_5_str = (
                normalised_role_name_list[4]
                if len(normalised_role_name_list) > 4 and len(normalised_role_name_list[4]) > 0
                else None
            )
            print(f"      actual_2: {actual_2_str}")
            assert expected_1_str == actual_1_str
            assert expected_2_str == actual_2_str
            assert expected_3_str == actual_3_str
            assert expected_4_str == actual_4_str
            assert expected_5_str == actual_5_str


# def test_generate_test_data_file():
#     with open(TEST_DATA_ROLES_NORMALISED_PATH, encoding="utf-8") as csvfile:
#         dialect = csv.Sniffer().sniff(csvfile.read(1024))
#         csvfile.seek(0)
#         csv_reader = csv.DictReader(csvfile, dialect=dialect, escapechar="\\")
#
#         with open(
#             TEST_DATA_ROLES_OUTPUT_PATH, "w", newline="", encoding="utf-8"
#         ) as output_file:
#             fieldnames = ["input", "expected"]
#             writer = csv.DictWriter(
#                 output_file,
#                 fieldnames=fieldnames,
#                 dialect=dialect,
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
#                 print(f"{input_str}")
#                 output_row: dict[str, str] = {"input": input_str}
#                 writer.writerow(output_row)
