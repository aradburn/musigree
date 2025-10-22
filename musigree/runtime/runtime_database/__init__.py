from musigree.runtime.runtime_database.country_table import CountryTable
from musigree.runtime.runtime_database.genre_table import GenreTable
from musigree.runtime.runtime_database.runtime_entity_table import RuntimeEntityTable
from musigree.runtime.runtime_database.runtime_role_table import RuntimeRoleTable
from musigree.runtime.runtime_database.runtime_relation_table import (
    RuntimeRelationTable,
)
from musigree.runtime.runtime_database.style_table import StyleTable
from musigree.runtime.runtime_database.token_table import TokenTable

ALL_RUNTIME_DATABASE_TABLES = [
    RuntimeEntityTable,
    RuntimeRelationTable,
    RuntimeRoleTable,
    CountryTable,
    StyleTable,
    GenreTable,
    TokenTable,
]
