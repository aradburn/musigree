from typing import AsyncGenerator

import pytest

from musigree import utils
from musigree.config import Configuration
from musigree.constants import ROLES_DATA, INSTRUMENTS_DATA
from musigree.offline.data_access_layer.role_data_access import RoleDataAccess
from musigree.offline.database.relation_release_year_repository import (
    RelationReleaseYearRepository,
)
from musigree.offline.database.offline_transaction import offline_transaction
from musigree.offline.domain.relation_release_year import (
    RelationReleaseYearUncommitted,
    RelationReleaseYear,
)
from musigree.offline.loader.loader_role import LoaderRole
from tests.conftest import AbstractDatabaseTest


@pytest.mark.parametrize("is_load_offline_data_required", [False], scope="class")
class TestRepositoryRelationReleaseYear(AbstractDatabaseTest):
    @pytest.mark.asyncio
    async def test_01_create(
        self,
        offline_database_setup: AsyncGenerator[None, None],
        offline_config: Configuration,
    ) -> None:
        # GIVEN
        await LoaderRole.load_roles_into_database(
            offline_config.DATA_DIR / ROLES_DATA,
            offline_config.DATA_DIR / INSTRUMENTS_DATA,
        )
        await RoleDataAccess.load_all_roles_into_cache()

        relation_release_year = RelationReleaseYearUncommitted(
            relation_id=2,
            release_id=3,
            year=1969,
        )

        # WHEN
        async with offline_transaction():
            repository = RelationReleaseYearRepository()

            await repository.create(relation_release_year)
            async for created_relation_release_year in repository.all():
                """Retrieve all created relation_release_years."""
                assert created_relation_release_year is not None, (
                    "Created relation_release_year should not be None"
                )
            actual = utils.normalize_dict(created_relation_release_year.model_dump())
            print(f"actual: {actual}")
        _exclude = {"random"}
        # THEN
        expected_relation = RelationReleaseYear(
            relation_release_year_id=1,
            relation_id=2,
            release_id=3,
            year=1969,
        )
        expected = utils.normalize_dict(expected_relation.model_dump())
        assert actual == expected

    # def test_02_update(self):
    #     # GIVEN
    #     with transaction():
    #         release = ReleaseReleaseYear.model_validate(
    #             {
    #                 "artists": [{"id": 939, "name": "Higher Intelligence Agency, The"}],
    #                 "companies": [],
    #                 "country": "UK",
    #                 "extra_artists": [
    #                     {
    #                         "id": 939,
    #                         "name": "Higher Intelligence Agency, The",
    #                         "roles": [{"name": "Written-By"}],
    #                     }
    #                 ],
    #                 "formats": [
    #                     {"descriptions": ["EP"], "name": "CD", "quantity": "1"}
    #                 ],
    #                 "genres": ["Electronic"],
    #                 "identifiers": [
    #                     {
    #                         "description": None,
    #                         "type": "Barcode",
    #                         "value": "5 018524 066308",
    #                     },
    #                     {
    #                         "description": None,
    #                         "type": "Matrix / Runout",
    #                         "value": "DISCTRONICS S HIA 2 CD 01",
    #                     },
    #                 ],
    #                 "labels": [
    #                     {"catalog_number": "HIACD2", "id": 233, "name": "Beyond"}
    #                 ],
    #                 "master_id": 21103,
    #                 "notes": None,
    #                 "random": 0.0,
    #                 "release_date": "1994-01-01 00:00:00",
    #                 "release_id": 635,
    #                 "styles": ["Techno", "Ambient"],
    #                 "title": "Colour Reform",
    #                 "tracklist": [
    #                     {
    #                         "duration": "8:49",
    #                         "extra_artists": [
    #                             {
    #                                 "id": 932,
    #                                 "name": "A Positive Life",
    #                                 "roles": [{"name": "Remix"}],
    #                             }
    #                         ],
    #                         "position": "1",
    #                         "title": "Universal Entity (Ketamine Entity Reformed By A Positive Life)",
    #                     },
    #                     {
    #                         "duration": "6:24",
    #                         "extra_artists": [
    #                             {
    #                                 "id": 41,
    #                                 "name": "Autechre",
    #                                 "roles": [{"name": "Remix"}],
    #                             }
    #                         ],
    #                         "position": "2",
    #                         "title": "Speech3 (Conoid Tone Reformed By Autechre)",
    #                     },
    #                     {
    #                         "duration": "8:30",
    #                         "extra_artists": [
    #                             {
    #                                 "id": 379334,
    #                                 "name": "Adrian Harrow",
    #                                 "roles": [{"name": "Engineer"}],
    #                             },
    #                             {
    #                                 "id": 953,
    #                                 "name": "Irresistible Force, The",
    #                                 "roles": [{"name": "Remix"}],
    #                             },
    #                         ],
    #                         "position": "3",
    #                         "title": "Speedlearn (Reformed By The Irresistible Force)",
    #                     },
    #                     {
    #                         "duration": "6:20",
    #                         "extra_artists": [
    #                             {
    #                                 "id": 954,
    #                                 "name": "Pentatonik",
    #                                 "roles": [{"name": "Remix"}],
    #                             }
    #                         ],
    #                         "position": "4",
    #                         "title": "Alpha 1999 (Delta Reformed By Pentatonik)",
    #                     },
    #                 ],
    #             }
    #         )
    #         ReleaseRepository().create(release)
    #
    #         relation = RelationUncommitted(
    #             entity_one_id=2,
    #             entity_one_type=EntityType.ARTIST,
    #             entity_two_id=3,
    #             entity_two_type=EntityType.LABEL,
    #             role_name="Composed By",
    #             releases={},
    #             random=0.0,
    #         )
    #         relation_dict = relation.model_dump()
    #         relation_dict["role"] = relation.role_name
    #
    #     # WHEN
    #     with transaction():
    #         relation_repository = RelationRepository()
    #
    #         WorkerRelationPassTwo.update_relation(
    #             relation_repository=relation_repository,
    #             relation_dict=relation_dict,
    #             release_id=635,
    #             year=1994,
    #         )
    #         updated_relation = relation_repository.find_by_key(relation_dict)
    #         print(f"updated_relation: {updated_relation}")
    #         actual = utils.normalize_dict(
    #             updated_relation.model_dump(exclude={"random"})
    #         )
    #         print(f"actual: {actual}")
    #
    #     # THEN
    #     expected_relation = Relation(
    #         relation_id=1,
    #         version_id=2,
    #         entity_one_id=2,
    #         entity_one_type=EntityType.ARTIST,
    #         entity_two_id=3,
    #         entity_two_type=EntityType.LABEL,
    #         role="Composed By",
    #         releases={"635": 1994},
    #         random=0.0,
    #     )
    #     expected = utils.normalize_dict(
    #         expected_relation.model_dump(exclude={"random"})
    #     )
    #     print(f"expected: {expected}")
    #     self.assertEqual(expected, actual)

    @pytest.mark.asyncio
    async def test_03_get(
        self, offline_database_setup: AsyncGenerator[None, None]
    ) -> None:
        # GIVEN

        # WHEN
        async with offline_transaction():
            repository = RelationReleaseYearRepository()
            # Get internal RelationReleaseYearDB
            relation_release_years = await repository.get(2)
            actual = [
                utils.normalize_dict(relation_release_year.model_dump())
                for relation_release_year in relation_release_years
            ]

        # THEN
        expected_relation_release_years = [
            RelationReleaseYear(
                relation_release_year_id=1,
                relation_id=2,
                release_id=3,
                year=1969,
            )
        ]
        expected = [
            utils.normalize_dict(expected_relation_release_year.model_dump())
            for expected_relation_release_year in expected_relation_release_years
        ]
        print(f"expected: {expected}")
        assert actual == expected
