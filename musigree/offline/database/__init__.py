from musigree.offline.database.entity_table import EntityTable
from musigree.offline.database.metadata_table import MetadataTable
from musigree.offline.database.relation_release_year_table import (
    RelationReleaseYearTable,
)
from musigree.offline.database.relation_table import RelationTable
from musigree.offline.database.release_table import ReleaseTable
from musigree.offline.database.role_table import RoleTable

ALL_OFFLINE_DATABASE_TABLES = [
    EntityTable,
    ReleaseTable,
    RelationTable,
    RoleTable,
    RelationReleaseYearTable,
    MetadataTable,
]
