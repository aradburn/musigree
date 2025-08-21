from xml.etree.ElementTree import Element

from musigree.runtime.data_access_layer.role_entry import RoleEntry
from tests.unit.runtime.runtime_database.test_utils import RoleCacheMockHelper


def test_creates_role_entry_with_valid_data() -> None:
    role_entry = RoleEntry(name="Producer", detail="Music Production")
    assert role_entry.name == "Producer"
    assert role_entry.detail == "Music Production"


def test_creates_role_entry_with_no_detail() -> None:
    role_entry = RoleEntry(name="Producer", detail=None)
    assert role_entry.name == "Producer"
    assert role_entry.detail is None


def test_creates_role_entry_from_text_with_detail() -> None:
    role_entry = RoleEntry.from_text("Producer [Music Production]")
    assert role_entry.name == "Producer"
    assert role_entry.detail == "Music Production"


def test_creates_role_entry_from_text_without_detail() -> None:
    role_entry = RoleEntry.from_text("Producer")
    assert role_entry.name == "Producer"
    assert role_entry.detail is None


def test_creates_role_entry_from_element_with_valid_data() -> None:
    class MockElement(Element):
        text = "Producer [Music Production], Engineer [Sound Engineering]"

    elements = RoleEntry.from_element(MockElement("role"))
    assert len(elements) == 2
    assert elements[0].name == "Producer"
    assert elements[0].detail == "Music Production"
    assert elements[1].name == "Engineer"
    assert elements[1].detail == "Sound Engineering"


def test_creates_role_entry_from_element_with_no_text() -> None:
    class MockElement(Element):
        text = None

    elements = RoleEntry.from_element(MockElement("role"))
    assert elements == []


def test_creates_role_entry_from_element_with_empty_text() -> None:
    class MockElement(Element):
        text = ""

    elements = RoleEntry.from_element(MockElement("role"))
    assert elements == []


def test_creates_multiselect_mapping_with_valid_data() -> None:
    # Use the RoleCacheMockHelper for consistent module-specific mocking
    role_mappings = {"Producer": 1, "Engineer": 2}
    role_categories = {1: "Music", 2: "Sound"}

    with RoleCacheMockHelper.mock_role_cache_in_module(
        "musigree.runtime.data_access_layer.role_entry", role_mappings
    ) as mock_cache:
        # Set up the role category lookup
        mock_cache.role_id_to_role_category_lookup = role_categories

        mapping = RoleEntry.get_multiselect_mapping()
        assert mapping == {"Music": ["Producer"], "Sound": ["Engineer"]}


def test_checks_equality_of_role_entries() -> None:
    role_entry1 = RoleEntry(name="Producer", detail="Music Production")
    role_entry2 = RoleEntry(name="Producer", detail="Music Production")
    assert role_entry1 == role_entry2


def test_checks_inequality_of_role_entries() -> None:
    role_entry1 = RoleEntry(name="Producer", detail="Music Production")
    role_entry2 = RoleEntry(name="Engineer", detail="Sound Engineering")
    assert role_entry1 != role_entry2
