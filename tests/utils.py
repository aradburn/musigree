from pathlib import Path

from musigree.library.fields.entity_type import EntityType
from musigree.offline.domain.entity import Entity
from musigree.offline.domain.release import Release
from musigree.offline.loader.loader_utils import LoaderUtils
from musigree.offline.loader.parser_entity import ParserEntity
from musigree.offline.loader.parser_release import ParserRelease


def get_test_entity_by_id(
    discogs_data_directory: Path, entity_id: int, entity_type: EntityType
) -> Entity:
    iterator = LoaderUtils.get_iterator(
        discogs_data_directory, entity_type.name.lower(), "testinsert"
    )

    while True:
        element = next(iterator)
        entity = ParserEntity().from_element(element)
        if entity.entity_id == entity_id:
            break
    return entity


def get_test_release_by_id(discogs_data_directory: Path, release_id: int) -> Release:
    iterator = LoaderUtils.get_iterator(discogs_data_directory, "release", "testinsert")

    while True:
        element = next(iterator)
        release = ParserRelease().from_element(element)
        if release.release_id == release_id:
            break
    return release
