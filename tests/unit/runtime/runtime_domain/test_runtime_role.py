from musigree.library.fields.role_type import RoleType
from musigree.runtime.runtime_domain.role import (
    RuntimeRole,
    RuntimeRoleJSTree,
    RuntimeRoleJSTreeEntry,
    RuntimeRoleJSTreeState,
    RuntimeRoleJSTreeWrapper,
)


def test_creates_runtime_role_with_valid_data() -> None:
    role = RuntimeRole(
        id=1,
        role_name="Producer",
        role_category=RoleType.Category.PRODUCTION,
        role_subcategory=RoleType.Subcategory.NONE,
        role_category_name="Production",
        role_subcategory_name="None",
    )
    assert role.id == 1
    assert role.role_name == "Producer"
    assert role.role_category == RoleType.Category.PRODUCTION
    assert role.role_subcategory == RoleType.Subcategory.NONE
    assert role.role_category_name == "Production"
    assert role.role_subcategory_name == "None"


def test_creates_runtime_role_jstree_state_with_valid_data() -> None:
    state = RuntimeRoleJSTreeState(opened=True, disabled=False, selected=True)
    assert state.opened is True
    assert state.disabled is False
    assert state.selected is True


def test_creates_runtime_role_jstree_entry_with_valid_data() -> None:
    state = RuntimeRoleJSTreeState(opened=True, disabled=False, selected=True)
    entry = RuntimeRoleJSTreeEntry(
        id="1",
        parent="#",
        text="Root",
        icon="icon.png",
        state=state,
        li_attr={"class": "root"},
        a_attr={"href": "#"},
    )
    assert entry.id == "1"
    assert entry.parent == "#"
    assert entry.text == "Root"
    assert entry.icon == "icon.png"
    assert entry.state == state
    assert entry.li_attr == {"class": "root"}
    assert entry.a_attr == {"href": "#"}


def test_creates_runtime_role_jstree_with_valid_data() -> None:
    state = RuntimeRoleJSTreeState(opened=True, disabled=False, selected=True)
    entry = RuntimeRoleJSTreeEntry(
        id="1",
        parent="#",
        text="Root",
        icon="icon.png",
        state=state,
        li_attr={"class": "root"},
        a_attr={"href": "#"},
    )
    jstree = RuntimeRoleJSTree(data=[entry])
    assert len(jstree.data) == 1
    assert jstree.data[0] == entry


def test_creates_runtime_role_jstree_wrapper_with_valid_data() -> None:
    state = RuntimeRoleJSTreeState(opened=True, disabled=False, selected=True)
    entry = RuntimeRoleJSTreeEntry(
        id="1",
        parent="#",
        text="Root",
        icon="icon.png",
        state=state,
        li_attr={"class": "root"},
        a_attr={"href": "#"},
    )
    jstree = RuntimeRoleJSTree(data=[entry])
    wrapper = RuntimeRoleJSTreeWrapper(
        core=jstree,
        checkbox={"keep_selected_style": False},
        plugins=["checkbox", "search"],
    )
    assert wrapper.core == jstree
    assert wrapper.checkbox == {"keep_selected_style": False}
    assert wrapper.plugins == ["checkbox", "search"]
