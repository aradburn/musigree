from musigree.offline.offline_database.entity_table import EntityTable
from musigree.offline.offline_database.master_table import MasterTable
from musigree.offline.offline_database.metadata_table import MetadataTable
from musigree.offline.offline_database.relation_table import RelationTable
from musigree.offline.offline_database.release_table import ReleaseTable
from musigree.offline.offline_database.role_table import RoleTable
from musigree.offline.offline_database.token_table import TokenTable

ALL_OFFLINE_DATABASE_TABLES = [
    EntityTable,
    ReleaseTable,
    RelationTable,
    RoleTable,
    MetadataTable,
    MasterTable,
    TokenTable,
]
