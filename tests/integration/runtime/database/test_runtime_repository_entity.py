import pydantic

from musigree.constants import DISCOGS_DATA
from musigree.library.fields.entity_type import EntityType
from musigree.offline.loader.loader_utils import LoaderUtils
from musigree.offline.loader.parser_entity import ParserEntity
from musigree.runtime.runtime_database.runtime_entity_repository import (
    RuntimeEntityRepository,
)
from musigree.runtime.runtime_database.runtime_transaction import runtime_transaction
from musigree.runtime.runtime_domain.entity import RuntimeEntity
from tests.integration.runtime.database.runtime_repository_test_case import (
    RuntimeRepositoryTestCase,
)


class TestRuntimeRepositoryEntity(RuntimeRepositoryTestCase):
    def test_create_01(self):
        # GIVEN
        discogs_data_directory = (
            RuntimeRepositoryTestCase.runtime_config.DATA_DIR / DISCOGS_DATA
        )
        iterator = LoaderUtils.get_iterator(
            discogs_data_directory, "artist", "testinsert"
        )
        entity_element = next(iterator)
        entity = ParserEntity().from_element(entity_element)
        print(f"entity: {entity}")

        countries = "UK"
        genres = "Rock"
        styles = "Psychedelic"
        runtime_entity = RuntimeEntity(
            countries=countries,
            genres=genres,
            styles=styles,
            **entity.model_dump(),
        )

        # WHEN
        with runtime_transaction():
            repository = RuntimeEntityRepository()
            created_entity = repository.create(runtime_entity)

        # THEN
        self.assertEqual(runtime_entity, created_entity)

    def test_get_01(self):
        # GIVEN
        discogs_data_directory = (
            RuntimeRepositoryTestCase.runtime_config.DATA_DIR / DISCOGS_DATA
        )
        iterator = LoaderUtils.get_iterator(
            discogs_data_directory, "label", "testinsert"
        )
        entity_element = next(iterator)
        entity = ParserEntity().from_element(entity_element)
        print(f"entity: {entity}")
        countries = "US"
        genres = "Electronic"
        styles = "Psy-trance"
        runtime_entity = RuntimeEntity(
            countries=countries,
            genres=genres,
            styles=styles,
            **entity.model_dump(),
        )

        # WHEN
        with runtime_transaction():
            repository = RuntimeEntityRepository()
            try:
                created_entity = repository.create(runtime_entity)
            except pydantic.ValidationError as validation_error:
                print(f"{validation_error.errors()}")

            retrieved_entity = repository.get_by_entity_id_and_entity_type(
                1, EntityType.LABEL
            )

        # THEN
        self.assertEqual(created_entity, retrieved_entity)

    def test_create_02(self):
        # GIVEN
        discogs_data_directory = (
            RuntimeRepositoryTestCase.runtime_config.DATA_DIR / DISCOGS_DATA
        )
        iterator = LoaderUtils.get_iterator(
            discogs_data_directory, "artist", "testinsert"
        )
        next(iterator)
        next(iterator)
        next(iterator)
        next(iterator)
        next(iterator)
        next(iterator)
        next(iterator)
        next(iterator)
        entity_element = next(iterator)
        entity = ParserEntity().from_element(entity_element)
        print(f"entity: {entity}")

        countries = "UK"
        genres = "Rock"
        styles = "Psychedelic"
        runtime_entity = RuntimeEntity(
            countries=countries,
            genres=genres,
            styles=styles,
            **entity.model_dump(),
        )

        # WHEN
        with runtime_transaction():
            repository = RuntimeEntityRepository()
            created_entity = repository.create(runtime_entity)

        # THEN
        self.assertEqual(runtime_entity, created_entity)
        expected_members = {"Chris Duckenfield": 8783, "Richard Brown": 11454}
        self.assertEqual(expected_members, created_entity.entities.get("members"))
        self.assertEqual(countries, created_entity.countries)
        self.assertEqual(genres, created_entity.genres)
        self.assertEqual(styles, created_entity.styles)
