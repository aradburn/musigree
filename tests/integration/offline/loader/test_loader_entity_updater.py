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
class TestLoaderEntityUpdater(AbstractDatabaseTest):
    @pytest.mark.asyncio
    async def test_artist_record_updated(
        self,
        offline_database_setup: AsyncGenerator[None, None],
        offline_database_update: AsyncGenerator[None, None], is_load_offline_data_required: bool
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
            "entity_type": "EntityType.ARTIST",
            "entity_metadata": {
                "name_variations": [
                    "L. Johnson",
                    "L. K. Johnson",
                    "L.K. Johnson",
                    "L.K.J.",
                    "LKJ",
                    'Linton "Kwesi" Johnson',
                    "Linton K. Johnson",
                    "Linton Kwesi-Johnson",
                    "Linton Kwisi Johnson",
                    "Linton Quasi Johnson",
                    "LKJ",
                ],
                "profile": "(Test Updated) Linton Kwesi Johnson (aka LKJ) (born 24 August 1952, "
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
    async def test_artist_record_not_updated(
        self,
        offline_database_setup: AsyncGenerator[None, None],
        offline_database_update: AsyncGenerator[None, None], is_load_offline_data_required: bool
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
        }
        expected = utils.normalize_dict(expected_entity)
        assert actual == expected

    @pytest.mark.asyncio
    async def test_artist_record_inserted(
        self,
        offline_database_setup: AsyncGenerator[None, None],
        offline_database_update: AsyncGenerator[None, None], is_load_offline_data_required: bool
    ) -> None:
        # GIVEN
        entity_id = 9999999
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
            "entities": {"groups": {"Test Group": None}},
            "entity_id": 9999999,
            "entity_metadata": {
                "name_variations": ["Test Test", "DJ TEST"],
                "profile": "Test Profile",
                "real_name": "Test 9999999",
                "urls": ["http://www.test.com/", "http://www.testtest.com/"],
            },
            "entity_name": "New Test Artist",
            "entity_type": EntityType.ARTIST,
            "relation_counts": {},
        }
        expected = utils.normalize_dict(expected_entity)
        assert actual == expected

    @pytest.mark.asyncio
    async def test_artist_record_deleted(
        self,
        offline_database_setup: AsyncGenerator[None, None],
        offline_database_update: AsyncGenerator[None, None], is_load_offline_data_required: bool
    ) -> None:
        # GIVEN
        entity_id = 12589
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
    async def test_label_record_updated(
        self,
        offline_database_setup: AsyncGenerator[None, None],
        offline_database_update: AsyncGenerator[None, None], is_load_offline_data_required: bool
    ) -> None:
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
            "entity_type": "EntityType.LABEL",
            "entity_metadata": {
                "profile": "(Test Update) Classic Techno label from Detroit, USA.\r\n"
                           + "[b]Label owner:[/b] [a871=Carl Craig].\r\n",
                "urls": [
                    "http://www.planet-e.net/",
                    "http://www.myspace.com/planetecom",
                    "http://www.facebook.com/planetedetroit ",
                    "http://twitter.com/planetedetroit",
                    "http://soundcloud.com/planetedetroit",
                ],
            },
            "entity_name": "Planet E (Test Update)",
            "relation_counts": {"Released On": 1},
        }
        expected = utils.normalize_dict(expected_entity)
        assert actual == expected

    @pytest.mark.asyncio
    async def test_label_record_not_updated(
        self,
        offline_database_setup: AsyncGenerator[None, None],
        offline_database_update: AsyncGenerator[None, None], is_load_offline_data_required: bool
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
            "entity_type": "EntityType.LABEL",
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
    async def test_label_record_inserted(
        self,
        offline_database_setup: AsyncGenerator[None, None],
        offline_database_update: AsyncGenerator[None, None], is_load_offline_data_required: bool
    ) -> None:
        # GIVEN
        entity_id = 99999999
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
            "entity_id": 99999999,
            "entity_metadata": {
                "profile": "Test Profile",
                "urls": ["http://www.test.net/", "http://www.testtest.com"],
            },
            "entity_name": "New Label Test",
            "entity_type": EntityType.LABEL,
            "relation_counts": {},
        }
        expected = utils.normalize_dict(expected_entity)
        assert actual == expected

    @pytest.mark.asyncio
    async def test_label_record_deleted(
        self,
        offline_database_setup: AsyncGenerator[None, None],
        offline_database_update: AsyncGenerator[None, None], is_load_offline_data_required: bool
    ) -> None:
        # GIVEN
        entity_id = 2529
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
