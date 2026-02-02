import asyncio
import logging

from musigree.config import (
    SqliteDevelopmentConfiguration,
)
from musigree.loader.offline_process_runner import run_offline_loading_process
from musigree.offline.loader.loader_entity import LoaderEntity

log = logging.getLogger(__name__)

if __name__ == "__main__":
    _config = SqliteDevelopmentConfiguration()
    process = LoaderEntity().loader_entity_pass_three()
    asyncio.run(run_offline_loading_process(_config, process))
