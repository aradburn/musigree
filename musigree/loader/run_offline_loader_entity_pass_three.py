import logging

from musigree.config import PostgresDevelopmentConfiguration
from musigree.loader.offline_process_runner import run_offline_loading_process
from musigree.offline.loader.loader_entity import LoaderEntity

log = logging.getLogger(__name__)

if __name__ == "__main__":
    _config = PostgresDevelopmentConfiguration()
    process = LoaderEntity().loader_entity_pass_three()
    run_offline_loading_process(_config, process)
