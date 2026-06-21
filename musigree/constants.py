import enum
from importlib.metadata import version
from pathlib import Path

VERSION = version("musigree")

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
DISCOGS_BASE_URL = "https://data.discogs.com/,?download=data/{year}/"
# OLD url DISCOGS_BASE_URL = "https://discogs-data-dumps.s3-us-west-2.amazonaws.com/data/{year}/"
DISCOGS_FILE_TEMPLATE = "discogs_{date}_{type}.xml.gz"
DISCOGS_ARTISTS_TYPE = "artists"
DISCOGS_LABELS_TYPE = "labels"
DISCOGS_MASTERS_TYPE = "masters"
DISCOGS_RELEASES_TYPE = "releases"

# DATABASE
OFFLINE_DATABASE = "offline_database"
RUNTIME_DATABASE = "runtime_database"
ALL_OFFLINE_DATABASE_TABLE_NAMES = [
    "entity",
    "relation",
    "master",
    "release",
    "role",
    "metadata",
    "token",
]
ALL_RUNTIME_DATABASE_TABLE_NAMES = [
    "runtime_entity",
    "runtime_relation",
    "runtime_role",
    "country",
    "style",
    "genre",
    "token",
]
POSTGRESQL_DRIVER_NAME = "postgresql+psycopg"  # uses psycopg3
SQLITE_DRIVER_NAME = "sqlite+aiosqlite"

BULK_INSERT_BATCH_SIZE = 10000
"""The batch size for bulk insert operations."""
BULK_REPORTING_SIZE = 10000
"""The number of records to process before reporting progress."""
BULK_YIELD_SIZE = 20000
"""The number of records to stream in a chunk from the database."""
BULK_LOAD_CHUNK_SIZE = 100000
"""The number of records to hold in memory at once before flushing to worker processes."""


class DatabaseType(enum.Enum):
    POSTGRES = 1
    SQLITE = 2


class ThreadingModel(enum.Enum):
    PROCESS = 1
    THREAD = 2


# Cache
class CacheType(enum.Enum):
    MEMORY = 1
    REDIS = 2


CACHE_KEY_SEPARATOR = ":"
CACHE_ENTRY_IS_NULL = "__NULL__"  # A string used to represent a null entry in the cache.


# CSP Secury Headers
class CSPSetting(enum.Enum):
    REPORT_ONLY = 1
    REPORT_SECURE = 2
    ENFORCE_CSP = 3


# Analytics
class AnalyticsType(enum.Enum):
    UMAMI = 1
    SWETRIX = 2
    OPENPANEL = 3
