import pytest

from musigree import utils
from musigree.offline.database.entity_repository import EntityRepository
from musigree.offline.database.offline_transaction import offline_transaction
from musigree.library.fields.entity_type import EntityType
from musigree.runtime.runtime_database.runtime_entity_repository import RuntimeEntityRepository
from musigree.runtime.runtime_database.runtime_transaction import runtime_transaction
from tests.conftest import NotATest


@pytest.mark.parametrize("is_load_offline_data_required", [True], scope="class")
@pytest.mark.parametrize("is_load_runtime_data_required", [True], scope="class")
class TestRuntimeDatabaseEntity(NotATest):
    @pytest.mark.asyncio
    async def test_from_db_01(self, offline_database_setup, runtime_database_setup) -> None:
        # GIVEN
        entity_id = 3
        entity_type = EntityType.ARTIST

        # WHEN
        async with runtime_transaction():
            entity_repository = RuntimeEntityRepository()
            entity = await entity_repository.get_by_entity_id_and_entity_type(
                entity_id, entity_type
            )
            actual = utils.normalize_dict(entity.model_dump())

        # THEN
        expected_entity = {
            "countries": "Belgium",
            "entities": {},
            "entity_id": 3,
            "entity_type": "EntityType.ARTIST",
            "entity_metadata": {
                "name_variations": [
                    "DJ Josh Wink",
                    "DJ Wink",
                    "J Wink",
                    "J. Wink",
                    "J. Wink (DJ  Wink)",
                    "J. Winkelman",
                    "J. Winkelmann",
                    "J.Wink",
                    "J.Winkelman",
                    "Josh",
                    "Josh Wink (DJ Wink)",
                    "Josh Wink Aka Winx",
                    "Josh Winkelman",
                    "Josh Winkelmann",
                    "Josh Winx",
                    "JW",
                    "Unknown Artist",
                    "Winc",
                    "Wink",
                    "Wink (Feat The Interpreters)",
                    "Winks",
                    "Winx",
                    "Winxs",
                ],
                "profile": "After forming [l=Ovum Recordings] as an independent label in October 1994 "
                + "with former partner [a=King Britt], Josh recorded the cult classic 'Liquid Summer'. "
                + "He went on to release singles for a wide variety of revered European labels ranging "
                + "from Belgium's [l=R & S Records] to England's [l=XL Recordings]. In 1995, Wink became "
                + "one of the first DJ-producers to translate his hard work into mainstream success when "
                + "he unleashed a string of classics including 'Don't Laugh'\u00b8 'I'm Ready' and "
                + "'Higher State of Consciousness' that topped charts worldwide. "
                + "More recently he has had massive club hits such as 'How's Your Evening So Far' and "
                + "'Superfreak' but he has also gained a lot of attention trough his remixes for "
                + "[a=FC Kahuna], [a=Paul Oakenfold], [a=Ladytron], [a=Clint Mansell], [a=Sting] "
                + "and [a=Depeche Mode], among others.",
                "real_name": "Joshua Winkelman",
                "urls": [
                    "http://www.joshwink.com/",
                    "http://www.ovum-rec.com/",
                    "http://www.myspace.com/joshwink",
                    "http://www.myspace.com/ovumrecordings",
                    "http://www.deejaybooking.com/joshwink",
                    "http://twitter.com/joshwink1",
                ],
            },
            "entity_name": "Josh Wink",
            "genres": "Electronic",
            "id": 3,
            "relation_counts": {
                "Featuring": 1,
                "Producer": 3,
                "Released On": 1,
                "Remix": 1,
                "Written By": 1,
            },
            "styles": "Techno,Tech House,Acid",
        }
        expected = utils.normalize_dict(expected_entity)
        assert actual == expected

    @pytest.mark.asyncio
    async def test_from_db_02(self, offline_database_setup, runtime_database_setup) -> None:
        # GIVEN
        entity_id = 2239
        entity_type = EntityType.ARTIST

        # WHEN
        async with runtime_transaction():
            entity_repository = RuntimeEntityRepository()
            entity = await entity_repository.get_by_entity_id_and_entity_type(
                entity_id, entity_type
            )
            actual = utils.normalize_dict(entity.model_dump())

        expected_entity = {
            "countries": "UK",
            "entities": {
                "members": {
                    "Daren Seymour": 66803,
                    "Justin Fletcher": 489350,
                    "Mark Clifford": 51674,
                    "Mark Van Hoen": 41103,
                    "Sarah Peacock": 115880,
                }
            },
            "entity_id": 2239,
            "entity_type": "EntityType.ARTIST",
            "entity_metadata": {
                "profile": "British electronic/rock group formed in the early 1990s. "
                + "They are currently signed to Warp Records.",
                "real_name": "Sarah Peacock, Mark Clifford, Darren Seymour & Justin Fletcher",
                "urls": [
                    "http://www.myspace.com/seefeelmyspace",
                    "http://en.wikipedia.org/wiki/Seefeel",
                    "http://www.facebook.com/pages/Seefeel/146206372061290",
                    "http://twitter.com/#!/_Seefeel_",
                    "http://bit.ly/mQ9t3F",
                    "http://www.seefeel.org",
                ],
            },
            "entity_name": "Seefeel",
            "genres": "Electronic",
            "id": 2239,
            "relation_counts": {
                "Compiled On": 15,
                "Copyright": 2,
                "DJ Mix": 7,
                "Design": 1,
                "Designed At": 1,
                "Film Director": 1,
                "Performer": 1,
                "Phonographic Copyright": 2,
                "Producer": 2,
                "Published By": 1,
                "Released On": 1,
                "Remix": 6,
                "Written By": 5,
            },
            "styles": "Leftfield,IDM,Ambient",
        }
        expected = utils.normalize_dict(expected_entity)
        assert actual == expected

    @pytest.mark.asyncio
    async def test_from_db_03(self, offline_database_setup, runtime_database_setup) -> None:
        # GIVEN
        entity_id = 1
        entity_type = EntityType.LABEL

        # WHEN
        async with runtime_transaction():
            entity_repository = RuntimeEntityRepository()
            entity = await entity_repository.get_by_entity_id_and_entity_type(
                entity_id, entity_type
            )
            actual = utils.normalize_dict(entity.model_dump())

        expected_entity = {
            "countries": "US,Belgium",
            "entities": {},
            "entity_id": 1,
            "entity_type": "EntityType.LABEL",
            "entity_metadata": {
                "profile": "Classic Techno label from Detroit, USA.\r\n[b]Label owner:[/b] [a=Carl Craig].\r\n",
                "urls": [
                    "http://www.planet-e.net/",
                    "http://www.myspace.com/planetecom",
                    "http://www.facebook.com/planetedetroit ",
                    "http://twitter.com/planetedetroit",
                    "http://soundcloud.com/planetedetroit",
                ],
            },
            "entity_name": "Planet E",
            "genres": "Electronic",
            "id": 1000000001,
            "relation_counts": {"Released On": 1},
            "styles": "Techno,House,Experimental",
        }
        expected = utils.normalize_dict(expected_entity)
        assert actual == expected

    @pytest.mark.asyncio
    async def test_from_db_04(self, offline_database_setup, runtime_database_setup) -> None:
        # GIVEN
        entity_id = 138147
        entity_type = EntityType.LABEL

        # WHEN
        async with runtime_transaction():
            entity_repository = RuntimeEntityRepository()
            entity = await entity_repository.get_by_entity_id_and_entity_type(
                entity_id, entity_type
            )
            actual = utils.normalize_dict(entity.model_dump())

        expected_entity = {
            "countries": None,
            "entities": {
                "parent_label": {
                    "Warner Music Group": None
                }
            },
            "entity_id": 138147,
            "entity_metadata": {
                "profile": "Music publishing company, and a division of the Warner "
               + "Music Group. \r\n[b]Pre 1987 issues - please use [l51877][/b]\r\nThe "
               + "company traces its origins back to 1811 and the founding of Chappell & "
               + "Company, a music publishing company and instrument shop on London\u2019s "
               + "Bond Street.\r\nWarner/Chappell was created in 1987 when Warner "
               + "Communications purchased Chappell & Co. and is one of the largest music "
               + "publishers with a catalog of more than one million songs and a roster of "
               + "more than 65,000 songwriters.\r\n\r\nAlso credited as \"Warner "
               + "Chappell\".\r\n",
                   "urls": [
                       "http://www.warnerchappell.com/"
                   ]
               },
            "entity_name": "Warner/Chappell",
            "entity_type": "EntityType.LABEL",
            "genres": None,
            "id": 1000138147,
            "relation_counts": {
                "Published By": 2
            },
            "styles": None
        }
        expected = utils.normalize_dict(expected_entity)
        assert actual == expected
