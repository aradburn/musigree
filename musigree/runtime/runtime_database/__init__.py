from musigree.runtime.runtime_database.runtime_country_table import RuntimeCountryTable
from musigree.runtime.runtime_database.runtime_genre_table import RuntimeGenreTable
from musigree.runtime.runtime_database.runtime_entity_table import RuntimeEntityTable
from musigree.runtime.runtime_database.runtime_relation_table import (
    RuntimeRelationTable,
)
from musigree.runtime.runtime_database.runtime_role_table import RuntimeRoleTable
from musigree.runtime.runtime_database.runtime_token_table import RuntimeTokenTable
from musigree.runtime.runtime_database.runtime_style_table import RuntimeStyleTable

ALL_RUNTIME_DATABASE_TABLES = [
    RuntimeEntityTable,
    RuntimeRelationTable,
    RuntimeRoleTable,
    RuntimeCountryTable,
    RuntimeStyleTable,
    RuntimeGenreTable,
    RuntimeTokenTable,
]
