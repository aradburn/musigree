from musigree import utils
from musigree.offline.database.entity_repository import EntityRepository
from musigree.offline.database.offline_transaction import offline_transaction
from musigree.library.fields.entity_type import EntityType
from tests.integration.offline.database.offline_database_test_case import (
    OfflineDatabaseTestCase,
)


class TestDatabaseEntity(OfflineDatabaseTestCase):
    def test_from_db_01(self):
        # GIVEN
        entity_id = 3
        entity_type = EntityType.ARTIST

        # WHEN
        with offline_transaction():
            entity_repository = EntityRepository()
            entity = entity_repository.get_by_entity_id_and_entity_type(
                entity_id, entity_type
            )
            actual = utils.normalize_dict(entity.model_dump(exclude={"id"}))

        # THEN
        expected_entity = {
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
            "relation_counts": {
                "Featuring": 1,
                "Producer": 3,
                "Released On": 1,
                "Remix": 1,
                "Written By": 1,
            },
            "search_content": "josh wink",
        }
        expected = utils.normalize_dict(expected_entity)
        self.assertEqual(expected, actual)

    def test_from_db_02(self):
        # GIVEN
        entity_id = 2239
        entity_type = EntityType.ARTIST

        # WHEN
        with offline_transaction():
            entity_repository = EntityRepository()
            entity = entity_repository.get_by_entity_id_and_entity_type(
                entity_id, entity_type
            )
            actual = utils.normalize_dict(entity.model_dump(exclude={"id"}))

        expected_entity = {
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
            "search_content": "seefeel",
        }
        expected = utils.normalize_dict(expected_entity)
        self.assertEqual(expected, actual)

    def test_from_db_03(self):
        # GIVEN
        entity_id = 1
        entity_type = EntityType.LABEL

        # WHEN
        with offline_transaction():
            entity_repository = EntityRepository()
            entity = entity_repository.get_by_entity_id_and_entity_type(
                entity_id, entity_type
            )
            actual = utils.normalize_dict(entity.model_dump(exclude={"id"}))

        expected_entity = {
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
            "relation_counts": {"Released On": 1},
            "search_content": "planet e",
        }
        expected = utils.normalize_dict(expected_entity)
        self.assertEqual(expected, actual)
