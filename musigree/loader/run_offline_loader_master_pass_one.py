import logging

from musigree.config import (
    PostgresDevelopmentConfiguration,
)
from musigree.constants import DISCOGS_DATA
from musigree.loader.offline_process_runner import run_offline_loading_process
from musigree.offline.loader.loader_master import LoaderMaster

log = logging.getLogger(__name__)

if __name__ == "__main__":
    _config = PostgresDevelopmentConfiguration()
    discogs_data_directory = _config.DATA_DIR / DISCOGS_DATA
    process = LoaderMaster().loader_master_pass_one(discogs_data_directory, "20260301")
    run_offline_loading_process(_config, process, ["master"])
