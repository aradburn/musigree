import unittest
from xml.etree import ElementTree

from musigree.runtime.data_access_layer.role_entry import RoleEntry


class TestRoleEntry(unittest.TestCase):
    def test_role_entry_from_element_1(self):
        element = ElementTree.fromstring("<test></test>")
        element.text = (
            "Shekere [Xequere, Original Musician], Guiro [Original Musician], "
            "Claves [Original Musician]"
        )
        roles = RoleEntry.from_element(element)
        self.assertListEqual(
            roles,
            [
                RoleEntry(name="Shekere", detail="Xequere, Original Musician"),
                RoleEntry(name="Guiro", detail="Original Musician"),
                RoleEntry(name="Claves", detail="Original Musician"),
            ],
        )

    def test_role_entry_from_element_2(self):
        element = ElementTree.fromstring("<test></test>")
        element.text = (
            "Co-producer, Arranged By, Directed By, Other [Guided By], "
            "Other [Created By]"
        )
        roles = RoleEntry.from_element(element)
        assert roles == [
            RoleEntry(name="Co-producer"),
            RoleEntry(name="Arranged By"),
            RoleEntry(name="Directed By"),
            RoleEntry(name="Other", detail="Guided By"),
            RoleEntry(name="Other", detail="Created By"),
        ]

    def test_role_entry_from_element_3(self):
        element = ElementTree.fromstring("<test></test>")
        element.text = (
            "Organ [Original Musician], " "Electric Piano [Rhodes, Original Musician]"
        )
        roles = RoleEntry.from_element(element)
        assert roles == [
            RoleEntry(
                name="Organ",
                detail="Original Musician",
            ),
            RoleEntry(
                name="Electric Piano",
                detail="Rhodes, Original Musician",
            ),
        ]

    def test_role_entry_from_element_4(self):
        element = ElementTree.fromstring("<test></test>")
        element.text = "Photography By ['hats' And 'spray' Photos By]"
        roles = RoleEntry.from_element(element)
        assert roles == [
            RoleEntry(
                name="Photography By",
                detail="'hats' And 'spray' Photos By",
            ),
        ]

    def test_role_entry_from_element_5(self):
        element = ElementTree.fromstring("<test></test>")
        element.text = "Strings "
        roles = RoleEntry.from_element(element)
        assert roles == [
            RoleEntry(name="Strings"),
        ]

    def test_role_entry_from_element_6(self):
        element = ElementTree.fromstring("<test></test>")
        element.text = "Piano, Synthesizer [Moog], Programmed By"
        roles = RoleEntry.from_element(element)
        assert roles == [
            RoleEntry(name="Piano"),
            RoleEntry(name="Synthesizer", detail="Moog"),
            RoleEntry(name="Programmed By"),
        ]

    def test_role_entry_from_element_7(self):
        element = ElementTree.fromstring("<test></test>")
        element.text = "Percussion [Misc.]"
        roles = RoleEntry.from_element(element)
        assert roles == [
            RoleEntry(name="Percussion", detail="Misc."),
        ]

    def test_role_entry_from_element_8(self):
        element = ElementTree.fromstring("<test></test>")
        element.text = 'Painting [Uncredited; Detail Of <i>"The Transfiguration"</i>]'
        roles = RoleEntry.from_element(element)
        assert roles == [
            RoleEntry(
                name="Painting",
                detail='Uncredited; Detail Of <i>"The Transfiguration"</i>',
            ),
        ]

    def test_role_entry_from_element_9(self):
        element = ElementTree.fromstring("<test></test>")
        element.text = "Composed By, Words By [elemented By], Producer"
        roles = RoleEntry.from_element(element)
        assert roles == [
            RoleEntry(name="Composed By"),
            RoleEntry(name="Words By", detail="elemented By"),
            RoleEntry(name="Producer"),
        ]

    def test_role_entry_from_element_10(self):
        element = ElementTree.fromstring("<test></test>")
        element.text = "Engineer [Remix] [Assistant], Producer"
        roles = RoleEntry.from_element(element)
        assert roles == [
            RoleEntry(name="Engineer", detail="Remix, Assistant"),
            RoleEntry(name="Producer"),
        ]

    def test_role_entry_from_element_11(self):
        element = ElementTree.fromstring("<test></test>")
        element.text = "Performer [Enigmatic [K] Voice, Moog, Korg Vocoder], Lyrics By"
        roles = RoleEntry.from_element(element)
        assert roles == [
            RoleEntry(
                name="Performer", detail="Enigmatic [K] Voice, Moog, Korg Vocoder"
            ),
            RoleEntry(name="Lyrics By"),
        ]
