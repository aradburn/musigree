from typing import AsyncGenerator

import pytest

from musigree import utils
from musigree.library.fields.entity_id import to_entity_internal_id
from musigree.library.fields.entity_type import EntityType
from musigree.offline.data_access_layer.relation_data_access import RelationDataAccess
from musigree.offline.database.relation_repository import RelationRepository
from musigree.offline.database.offline_transaction import offline_transaction
from tests.conftest import AbstractDatabaseTest


@pytest.mark.parametrize("is_load_offline_data_required", [True], scope="class")
class TestLoaderRelationPassOne(AbstractDatabaseTest):
    @pytest.mark.asyncio
    async def test_loader_relation_pass_one(
        self, offline_database_setup: AsyncGenerator[None, None]
    ) -> None:
        # GIVEN

        # WHEN
        async with offline_transaction():
            relation_repository = RelationRepository()
            actual = await relation_repository.count()

        # THEN
        expected = 28932
        assert actual == expected

    @pytest.mark.asyncio
    async def test_relation_01(
        self, offline_database_setup: AsyncGenerator[None, None]
    ) -> None:
        # GIVEN
        entity_one_id = 42
        entity_one_type = EntityType.ARTIST
        entity_two_id = 41
        entity_two_type = EntityType.ARTIST
        role = "Producer"

        id_1 = to_entity_internal_id(entity_one_id, entity_one_type)
        id_2 = to_entity_internal_id(entity_two_id, entity_two_type)
        key = dict(
            subject=id_1,
            role=role,
            object=id_2,
        )

        # WHEN
        async with offline_transaction():
            relation_repository = RelationRepository()
            relation = await RelationDataAccess.get_relation_by_key(
                relation_repository,
                key,
            )
            assert relation is not None
            actual = utils.normalize_dict(relation.model_dump(exclude={"id"}))

        # THEN
        expected_relation = {
            "entity_one_id": 42,
            "entity_one_type": EntityType.ARTIST,
            "entity_two_id": 41,
            "entity_two_type": EntityType.ARTIST,
            "releases": {
                "1000619": 2003,
                "1054046": None,
                "1099482": 2001,
                "11216": 1998,
                "1141130": None,
                "1169229": 2007,
                "1195788": 2005,
                "1203976": 1997,
                "1203978": 1993,
                "1257383": 2008,
                "1265276": 2008,
                "135858": 2002,
                "1377682": 1997,
                "13939": 1997,
                "1530077": 2002,
                "1530086": 2006,
                "157": 1994,
                "168639": 2003,
                "1741441": None,
                "1774969": 1999,
                "197416": 2003,
                "2009213": 1998,
                "2012450": 2006,
                "21351": 1999,
                "2188879": 2002,
                "2191313": 2010,
                "2276345": 2002,
                "2291695": 1994,
                "2317370": 2009,
                "239832": 1996,
                "2493": 1993,
                "2502": 1994,
                "251157": 2001,
                "25492": 1994,
                "26454": 1994,
                "26455": 1994,
                "2776338": 2001,
                "292020": 2004,
                "29372": 1992,
                "29373": 1992,
                "29900": 1993,
                "30187": 1994,
                "30188": 1994,
                "3066": 2001,
                "315067": 1992,
                "33098": 1995,
                "33099": 1996,
                "3392955": 2005,
                "34629": 2002,
                "3564784": 1992,
                "3674448": 1999,
                "36895": 2002,
                "383794": 1994,
                "398252": 1997,
                "4030071": 2012,
                "426323": 2005,
                "435111": 2005,
                "491787": 1997,
                "51735": 1994,
                "51766": 1994,
                "539874": 1995,
                "549": 1992,
                "571561": 1998,
                "66011": 1997,
                "708572": 1997,
                "752745": 1993,
                "790582": 1994,
                "793894": 1994,
                "81009": 1991,
                "826408": 2006,
                "870851": 2005,
                "8816": 1994,
            },
            "role": "Producer",
        }

        expected = utils.normalize_dict(expected_relation)
        assert actual == expected

    @pytest.mark.asyncio
    async def test_relation_02(
        self, offline_database_setup: AsyncGenerator[None, None]
    ) -> None:
        # GIVEN
        entity_one_id = 49
        entity_one_type = EntityType.ARTIST
        entity_two_id = 23528
        entity_two_type = EntityType.LABEL
        role = "Released On"

        id_1 = to_entity_internal_id(entity_one_id, entity_one_type)
        id_2 = to_entity_internal_id(entity_two_id, entity_two_type)
        key = dict(
            subject=id_1,
            role=role,
            object=id_2,
        )

        # WHEN
        async with offline_transaction():
            relation_repository = RelationRepository()
            relation = await RelationDataAccess.get_relation_by_key(
                relation_repository,
                key,
            )
            assert relation is not None
            actual = utils.normalize_dict(relation.model_dump(exclude={"id"}))

        # THEN
        expected_relation = {
            "entity_one_id": 49,
            "entity_one_type": EntityType.ARTIST,
            "entity_two_id": 23528,
            "entity_two_type": EntityType.LABEL,
            "releases": {
                "162": 1996,
                "1829266": 2004,
            },
            "role": "Released On",
        }

        expected = utils.normalize_dict(expected_relation)
        assert actual == expected

    @pytest.mark.asyncio
    async def test_relation_03(
        self, offline_database_setup: AsyncGenerator[None, None]
    ) -> None:
        # GIVEN
        entity_one_id = 300407
        entity_one_type = EntityType.ARTIST
        entity_two_id = 41
        entity_two_type = EntityType.ARTIST
        role = "Producer"

        id_1 = to_entity_internal_id(entity_one_id, entity_one_type)
        id_2 = to_entity_internal_id(entity_two_id, entity_two_type)
        key = dict(
            subject=id_1,
            role=role,
            object=id_2,
        )

        # WHEN
        async with offline_transaction():
            relation_repository = RelationRepository()
            relation = await RelationDataAccess.get_relation_by_key(
                relation_repository,
                key,
            )
            assert relation is not None
            actual = utils.normalize_dict(relation.model_dump(exclude={"id"}))

        # THEN
        expected_relation = {
            "entity_one_id": 300407,
            "entity_one_type": EntityType.ARTIST,
            "entity_two_id": 41,
            "entity_two_type": EntityType.ARTIST,
            "releases": {
                "1000619": 2003,
                "1054046": None,
                "1099482": 2001,
                "11216": 1998,
                "1141130": None,
                "1169229": 2007,
                "1195788": 2005,
                "1203976": 1997,
                "1203978": 1993,
                "1257383": 2008,
                "1265276": 2008,
                "135858": 2002,
                "1377682": 1997,
                "13939": 1997,
                "1530077": 2002,
                "1530086": 2006,
                "157": 1994,
                "168639": 2003,
                "1741441": None,
                "1774969": 1999,
                "197416": 2003,
                "2009213": 1998,
                "2012450": 2006,
                "21351": 1999,
                "2188879": 2002,
                "2191313": 2010,
                "2276345": 2002,
                "2291695": 1994,
                "2317370": 2009,
                "239832": 1996,
                "2493": 1993,
                "2502": 1994,
                "251157": 2001,
                "25492": 1994,
                "26454": 1994,
                "26455": 1994,
                "2776338": 2001,
                "292020": 2004,
                "29372": 1992,
                "29373": 1992,
                "29900": 1993,
                "30187": 1994,
                "30188": 1994,
                "3066": 2001,
                "315067": 1992,
                "33098": 1995,
                "33099": 1996,
                "3392955": 2005,
                "34629": 2002,
                "3564784": 1992,
                "3674448": 1999,
                "36895": 2002,
                "383794": 1994,
                "398252": 1997,
                "4030071": 2012,
                "426323": 2005,
                "435111": 2005,
                "51735": 1994,
                "51766": 1994,
                "539874": 1995,
                "549": 1992,
                "571561": 1998,
                "66011": 1997,
                "708572": 1997,
                "752745": 1993,
                "790582": 1994,
                "793894": 1994,
                "81009": 1991,
                "826408": 2006,
                "870851": 2005,
                "8816": 1994,
            },
            "role": "Producer",
        }

        expected = utils.normalize_dict(expected_relation)
        assert actual == expected

    @pytest.mark.asyncio
    async def test_relation_04(
        self, offline_database_setup: AsyncGenerator[None, None]
    ) -> None:
        # GIVEN
        entity_one_id = 586589
        entity_one_type = EntityType.ARTIST
        entity_two_id = 41
        entity_two_type = EntityType.ARTIST
        role = "Design"

        id_1 = to_entity_internal_id(entity_one_id, entity_one_type)
        id_2 = to_entity_internal_id(entity_two_id, entity_two_type)
        key = dict(
            subject=id_1,
            role=role,
            object=id_2,
        )

        # WHEN
        async with offline_transaction():
            relation_repository = RelationRepository()
            relation = await RelationDataAccess.get_relation_by_key(
                relation_repository,
                key,
            )
            assert relation is not None
            actual = utils.normalize_dict(relation.model_dump(exclude={"id"}))

        # THEN
        expected_relation = {
            "entity_one_id": 586589,
            "entity_one_type": EntityType.ARTIST,
            "entity_two_id": 41,
            "entity_two_type": EntityType.ARTIST,
            "releases": {
                "1141130": None,
                "1195788": 2005,
                "1530086": 2006,
                "2291695": 1994,
                "2493": 1993,
                "29900": 1993,
                "539874": 1995,
                "8816": 1994,
            },
            "role": "Design",
        }

        expected = utils.normalize_dict(expected_relation)
        assert actual == expected

    @pytest.mark.asyncio
    async def test_relation_05(
        self, offline_database_setup: AsyncGenerator[None, None]
    ) -> None:
        # GIVEN
        key = dict(
            subject=661,
            object=658,
            role="Remix",
        )

        # WHEN
        async with offline_transaction():
            relation_repository = RelationRepository()
            relation = await RelationDataAccess.get_relation_by_key(
                relation_repository,
                key,
            )
            assert relation is not None
            actual = utils.normalize_dict(relation.model_dump(exclude={"id"}))

        # THEN
        expected_relation = {
            "entity_one_id": 661,
            "entity_one_type": EntityType.ARTIST,
            "entity_two_id": 658,
            "entity_two_type": EntityType.ARTIST,
            "releases": {
                "1158822": 1995,
                "1340225": 1995,
                "2030225": 2009,
                "241185": 1995,
                "328058": 1997,
                "380": 1995,
            },
            "role": "Remix",
        }

        expected = utils.normalize_dict(expected_relation)
        assert actual == expected

    @pytest.mark.asyncio
    async def test_relation_06(
        self, offline_database_setup: AsyncGenerator[None, None]
    ) -> None:
        # GIVEN
        key = dict(
            subject=21209,
            object=3771,
            role="Compiled By",
        )

        # WHEN
        async with offline_transaction():
            relation_repository = RelationRepository()
            relation = await RelationDataAccess.get_relation_by_key(
                relation_repository,
                key,
            )
            assert relation is not None
            actual = utils.normalize_dict(relation.model_dump(exclude={"id"}))

        # THEN
        expected_relation = {
            "entity_one_id": 21209,
            "entity_one_type": EntityType.ARTIST,
            "entity_two_id": 3771,
            "entity_two_type": EntityType.ARTIST,
            "releases": {
                "1112162": 1996,
                "1112454": 1996,
                "17268": 1994,
                "63148": 1994,
            },
            "role": "Compiled By",
        }

        expected = utils.normalize_dict(expected_relation)
        assert actual == expected

    @pytest.mark.asyncio
    async def test_relation_07(
        self, offline_database_setup: AsyncGenerator[None, None]
    ) -> None:
        # GIVEN
        key = dict(
            subject=335173,
            object=41,
            role="Mastered By",
        )

        # WHEN
        async with offline_transaction():
            relation_repository = RelationRepository()
            relation = await RelationDataAccess.get_relation_by_key(
                relation_repository,
                key,
            )
            assert relation is not None
            actual = utils.normalize_dict(relation.model_dump(exclude={"id"}))

        # THEN
        expected_relation = {
            "entity_one_id": 335173,
            "entity_one_type": EntityType.ARTIST,
            "entity_two_id": 41,
            "entity_two_type": EntityType.ARTIST,
            "releases": {
                "1255104": 2008,
                "1257383": 2008,
                "1265276": 2008,
                "1265680": 2008,
                "130115": 2003,
                "130319": 2003,
                "156930": 2003,
                "2191313": 2010,
                "2192053": 2010,
                "2316777": None,
                "2346144": 2010,
                "2348913": 2010,
                "2351842": 2010,
                "2363967": 2010,
                "2513487": 2010,
                "3392955": 2005,
                "397637": 2003,
                "414646": 2005,
                "426323": 2005,
                "435111": 2005,
                "593584": 2003,
                "870851": 2005,
            },
            "role": "Mastered By",
        }

        expected = utils.normalize_dict(expected_relation)
        assert actual == expected
