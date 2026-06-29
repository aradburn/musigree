import logging

from musigree.config import (
    PostgresDevelopmentConfiguration,
)
from musigree.loader.offline_process_runner import run_offline_loading_process
from musigree.offline.loader.loader_release import LoaderRelease

log = logging.getLogger(__name__)

if __name__ == "__main__":
    _config = PostgresDevelopmentConfiguration()
    process = LoaderRelease().loader_release_pass_two()
    run_offline_loading_process(_config, process)
