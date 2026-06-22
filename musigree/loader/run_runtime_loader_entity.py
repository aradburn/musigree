import asyncio
import logging

from musigree.config import (
    PostgresDevelopmentConfiguration,
    SqliteDevelopmentConfiguration,
)
from musigree.loader.runtime_process_runner import run_runtime_loading_process
from musigree.transfer.transfer_manager import TransferManager

log = logging.getLogger(__name__)

if __name__ == "__main__":
    offline_config = PostgresDevelopmentConfiguration()
    runtime_config = SqliteDevelopmentConfiguration()
    process = TransferManager().transfer_entity()
    asyncio.run(
        run_runtime_loading_process(offline_config, runtime_config, process, ["runtime_entity"])
    )
