import enum
from pathlib import Path

# DIRECTORY PATHS
APP_DIR = Path(__file__).parent.resolve()
ROOT_DIR = Path(APP_DIR / "..").resolve()
FRONTEND_DIR = ROOT_DIR / "frontend"
TEMPLATES_DIR = FRONTEND_DIR / "templates"
PUBLIC_DIR = FRONTEND_DIR / "public"

# DATA
DISCOGS_DATA = "discogs"
ROLES_DATA = "roles"
INSTRUMENTS_DATA = "instruments"
INSTRUMENTS_DATA_FILENAMES = [
    "aerophones.csv",
    "chordophones.csv",
    "electrophones.csv",
    "idiophones.csv",
    "membranophones.csv",
]
HS_INSTRUMENTS_FILENAME = "hornbostel_sachs.json"
TEXT_SEARCH_DATA = "text_search"
TEXT_SEARCH_FILENAME = "text_search.data"
ENTITY_DETAILS_DATA = "entity_details"
ENTITY_DETAILS_FILENAME = "entity_details.data"

# TESTS
TEST_DIR = ROOT_DIR / "tests"

# LOGS
LOGGING_DIR = ROOT_DIR / "logs"
LOGGING_FILE = LOGGING_DIR / "musigree.log"
LOGGING_ERROR_FILE = LOGGING_DIR / "error.log"
LOGGING_DEBUG_FILE = LOGGING_DIR / "debug.log"

# DISCOGS
DISCOGS_BASE_URL = "https://discogs-data-dumps.s3-us-west-2.amazonaws.com/data/{year}/"
DISCOGS_FILE_TEMPLATE = "discogs_{date}_{type}.xml.gz"
DISCOGS_ARTISTS_TYPE = "artists"
DISCOGS_RELEASES_TYPE = "releases"
DISCOGS_LABELS_TYPE = "labels"
DISCOGS_MASTERS_TYPE = "masters"

# DATABASE
OFFLINE_DATABASE = "offline_database"
RUNTIME_DATABASE = "runtime_database"
ALL_OFFLINE_DATABASE_TABLE_NAMES = [
    "entity",
    "relation",
    "release",
    "role",
    "relation_release_year",
    "metadata",
]
ALL_RUNTIME_DATABASE_TABLE_NAMES = [
    "runtime_entity",
    "runtime_relation",
    "runtime_role",
    "country",
    "style",
    "genre",
]
POSTGRESQL_DRIVER_NAME= "postgresql+psycopg"  # uses psycopg3

class DatabaseType(enum.Enum):
    POSTGRES = 1
    SQLITE = 2


class ThreadingModel(enum.Enum):
    PROCESS = 1
    THREAD = 2


class CacheType(enum.Enum):
    MEMORY = 1
    FILESYSTEM = 2
    REDIS = 3
