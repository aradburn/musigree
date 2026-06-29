import logging

from musigree.config import (
    PostgresDevelopmentConfiguration,
)
from musigree.loader.offline_process_runner import run_offline_loading_process
from musigree.offline.loader.loader_relation import LoaderRelation

log = logging.getLogger(__name__)

if __name__ == "__main__":
    _config = PostgresDevelopmentConfiguration()
    process = LoaderRelation().loader_relation_pass_one()
    run_offline_loading_process(_config, process)
