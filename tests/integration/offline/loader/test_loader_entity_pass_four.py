from typing import AsyncGenerator

import pytest

from musigree import utils
from musigree.exceptions import NotFoundError
from musigree.library.fields.entity_type import EntityType
from musigree.offline.offline_database.entity_repository import EntityRepository
from musigree.offline.offline_database.offline_transaction import offline_transaction
from tests.conftest import AbstractDatabaseTest


# noinspection HttpUrlsUsage
@pytest.mark.parametrize("is_load_offline_data_required", [True], scope="class")
class TestLoaderEntityPassFour(AbstractDatabaseTest):
    @pytest.mark.asyncio
    async def test_loader_entity_pass_four(
        self, offline_database_setup: AsyncGenerator[None, None], is_load_offline_data_required: bool
    ) -> None:
        # GIVEN

        # WHEN
        async with offline_transaction():
            actual = await EntityRepository().count()

        # THEN
        expected = 6216
        assert actual == expected

    @pytest.mark.asyncio
    async def test_artist_record_20702(
        self, offline_database_setup: AsyncGenerator[None, None], is_load_offline_data_required: bool
    ) -> None:
        # GIVEN
        entity_id = 20702
        entity_type = EntityType.ARTIST

        # WHEN
        async with offline_transaction():
            entity_repository = EntityRepository()
            entity = await entity_repository.get_by_entity_id_and_entity_type(
                entity_id, entity_type
            )
            actual = utils.normalize_dict(entity.model_dump(exclude={"id"}))

        # THEN
        expected_entity = {
            "entities": {},
            "entity_id": 20702,
            "entity_type": EntityType.ARTIST,
            "entity_metadata": {
                "name_variations": [
                    "L. Johnson",
                    "L. K. Johnson",
                    "L.K. Johnson",
                    "L.K.J.",
                    'Linton "Kwesi" Johnson',
                    "Linton K. Johnson",
                    "Linton Kwesi-Johnson",
                    "Linton Kwisi Johnson",
                    "Linton Quasi Johnson",
                    "LKJ",
                ],
                "profile": "Linton Kwesi Johnson (aka LKJ) (born 24 August 1952, "
                           + "Chapelton, Jamaica) is a British-based author and dub poet. Johnson's "
                           + "poetry makes clever use of the unstandardised transcription of Jamaican "
                           + 'Patois and, allied to the Jamaican "toasting" tradition, is regarded as a '
                           + "precursor of rap. He became the second living poet, and the only black poet, "
                           + "to be published in the Penguin Classics series.",
                "urls": [
                    "http://www.lkjrecords.com/",
                    "http://lister.ultrakohl.com/homepage/Lkj/lkj.htm",
                    "http://en.wikipedia.org/wiki/Linton_Kwesi_Johnson",
                ],
            },
            "entity_name": "Linton Kwesi Johnson",
            "relation_counts": {"Compiled By": 1, "Compiled On": 1, "DJ Mix": 1},
        }
        expected = utils.normalize_dict(expected_entity)
        assert actual == expected

    @pytest.mark.asyncio
    async def test_artist_record_2239(
        self, offline_database_setup: AsyncGenerator[None, None], is_load_offline_data_required: bool
    ) -> None:
        # GIVEN
        entity_id = 2239
        entity_type = EntityType.ARTIST

        # WHEN
        async with offline_transaction():
            entity_repository = EntityRepository()
            entity = await entity_repository.get_by_entity_id_and_entity_type(
                entity_id, entity_type
            )
            actual = utils.normalize_dict(entity.model_dump(exclude={"id"}))

        # THEN
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
            "entity_type": EntityType.ARTIST,
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
        }
        expected = utils.normalize_dict(expected_entity)
        assert actual == expected

    @pytest.mark.asyncio
    async def test_artist_9999999(self, offline_database_setup: AsyncGenerator[None, None],
                                  is_load_offline_data_required: bool) -> None:
        # GIVEN
        entity_id = 9999999
        entity_type = EntityType.ARTIST

        # WHEN
        async with offline_transaction():
            entity_repository = EntityRepository()
            try:
                entity = await entity_repository.get_by_entity_id_and_entity_type(
                    entity_id, entity_type
                )
            except NotFoundError:
                entity = None

        # THEN
        assert entity is None

    @pytest.mark.asyncio
    async def test_artist_record_12589(
        self, offline_database_setup: AsyncGenerator[None, None], is_load_offline_data_required: bool
    ) -> None:
        # GIVEN
        entity_id = 12589
        entity_type = EntityType.ARTIST

        # WHEN
        async with offline_transaction():
            entity_repository = EntityRepository()
            entity = await entity_repository.get_by_entity_id_and_entity_type(
                entity_id, entity_type
            )
            actual = utils.normalize_dict(entity.model_dump(exclude={"id"}))

        # THEN
        expected_entity = {
            "entities": {
                "members": {
                    "Chris Carter (2)": 83832,
                    "Genesis Breyer P-Orridge": 432137,
                    "Peter Christopherson": 34069,
                },
            },
            "entity_id": 12589,
            "entity_metadata": {
                "name_variations": [
                    "T.G.",
                    "TG",
                    "Throbbing Gristle Ltd",
                    "Trobbing Gristle",
                    "\u30b9\u30ed\u30c3\u30d3\u30f3\u30b0\u30fb\u30b0\u30ea\u30b9\u30eb",
                ],
                "profile": "The first real industrial group, the founders of "
                           + "[l=Industrial Records] and one of the most important electronic music "
                           + "innovators of all time. Growing out of the extreme performance art group "
                           + "[a=COUM Transmissions], TG redefined music and laid a large part of the "
                           + "groundwork for all electronic music that followed. \r\n\r\nFrom their "
                           + "first performances in 1976 to their last gig in San Francisco in 1981 "
                           + '(recorded and released as "Mission Of Dead Souls"), they challenged and '
                           + 'threatend so-called "normal", society - denounced from the floor of the '
                           + 'House of Commons as "Wreckers of Civilisation" as the Coum Transmissions '
                           + '"Prostitution" art show in London\'s ICA (at which TG played their third '
                           + "show) came close to causing riots and set the stage for the punk revolution. "
                           + "\r\n\r\nMusically, they were extreme and uncompromising, using "
                           + "technology to make anti-music, which redefined music for all time. Their "
                           + "experimentation led them to pioneer sampling and looping techniques adopted "
                           + "by many of those who came after. \r\n\r\nThrobbing Gristle officially "
                           + "began at September 3, 1975 and they officially split on June 23, 1981.  "
                           + "After they split, Genesis and Peter formed [a17926=Psychic TV] (and Peter "
                           + "later joining [a660=Coil]) and Chris and Cosey becoming, well, [a29040=Chris "
                           + "& Cosey]. However, they came back together 23 years later in 2004 to plan an "
                           + "ill-fated weekend festival, which became a one-off recording session in "
                           + "London when the festival fell through, releasing a limited TGNOW album of "
                           + "the recordings.\r\n",
                "real_name": "Genesis P-Orridge, Chris Carter, Cosey Fanni Tutti, Peter Christopheron",
                "urls": [
                    "http://www.throbbing-gristle.com/",
                    "http://www.brainwashed.com/tg/",
                    "http://www.myspace.com/throbbinggristle",
                ],
            },
            "entity_name": "Throbbing Gristle",
            "entity_type": EntityType.ARTIST,
            "relation_counts": {
                "Compiled By": 2,
                "Compiled On": 1,
                "DJ Mix": 4,
                "Producer": 1,
                "Remix": 2,
                "Written By": 1,
            },
        }
        expected = utils.normalize_dict(expected_entity)
        assert actual == expected

    @pytest.mark.asyncio
    async def test_label_record_1(self, offline_database_setup: AsyncGenerator[None, None],
                                  is_load_offline_data_required: bool) -> None:
        # GIVEN
        entity_id = 1
        entity_type = EntityType.LABEL

        # WHEN
        async with offline_transaction():
            entity_repository = EntityRepository()
            entity = await entity_repository.get_by_entity_id_and_entity_type(
                entity_id, entity_type
            )
            actual = utils.normalize_dict(entity.model_dump(exclude={"id"}))

        # THEN
        expected_entity = {
            "entities": {},
            "entity_id": 1,
            "entity_type": EntityType.LABEL,
            "entity_metadata": {
                "profile": "Classic Techno label from Detroit, USA.\r\n"
                           + "[b]Label owner:[/b] [a871=Carl Craig].\r\n",
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
        }
        expected = utils.normalize_dict(expected_entity)
        assert actual == expected

    @pytest.mark.asyncio
    async def test_label_record_264170(
        self, offline_database_setup: AsyncGenerator[None, None], is_load_offline_data_required: bool
    ) -> None:
        # GIVEN
        entity_id = 264170
        entity_type = EntityType.LABEL

        # WHEN
        async with offline_transaction():
            entity_repository = EntityRepository()
            entity = await entity_repository.get_by_entity_id_and_entity_type(
                entity_id, entity_type
            )
            actual = utils.normalize_dict(entity.model_dump(exclude={"id"}))

        # THEN
        expected_entity = {
            "entities": {},
            "entity_id": 264170,
            "entity_type": EntityType.LABEL,
            "entity_metadata": {
                "profile": "American mastering studio located in New Windsor, NY. \r\n\r\n"
                           + "Formally located at 2 Engle Street, Tenafly, New Jersey, "
                           + "operations were moved to New Windsor in 2005. "
                           + "Operated by Chief Engineer [a275139=Alan Douches].\n",
                "urls": ["http://www.westwestsidemusic.com/"],
            },
            "entity_name": "West West Side Music",
            "relation_counts": {"Mastered At": 1},
        }
        expected = utils.normalize_dict(expected_entity)
        assert actual == expected

    @pytest.mark.asyncio
    async def test_label_record_99999999(
        self, offline_database_setup: AsyncGenerator[None, None], is_load_offline_data_required: bool
    ) -> None:
        # GIVEN
        entity_id = 99999999
        entity_type = EntityType.LABEL

        # WHEN
        async with offline_transaction():
            entity_repository = EntityRepository()
            try:
                entity = await entity_repository.get_by_entity_id_and_entity_type(
                    entity_id, entity_type
                )
            except NotFoundError:
                entity = None

        # THEN
        assert entity is None

    @pytest.mark.asyncio
    async def test_label_record_2529(
        self, offline_database_setup: AsyncGenerator[None, None], is_load_offline_data_required: bool
    ) -> None:
        # GIVEN
        entity_id = 2529
        entity_type = EntityType.LABEL

        # WHEN
        async with offline_transaction():
            entity_repository = EntityRepository()
            entity = await entity_repository.get_by_entity_id_and_entity_type(
                entity_id, entity_type
            )
            actual = utils.normalize_dict(entity.model_dump(exclude={"id"}))

        # THEN
        expected_entity = {
            "entities": {},
            "entity_id": 2529,
            "entity_metadata": {
                "profile": "Hubba Hubba was a dance music label owned by Utah Saints manager John MacLennan. "
                           + "It had 20 releases between 1991 - 1994 and was then closed down.",
            },
            "entity_name": "Hubba Hubba",
            "entity_type": EntityType.LABEL,
            "relation_counts": {
                "Licensed From": 1,
                "Released On": 1,
            },
        }
        expected = utils.normalize_dict(expected_entity)
        assert actual == expected
