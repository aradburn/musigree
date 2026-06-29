import logging

from musigree.config import (
    SqliteDevelopmentConfiguration,
    PostgresReadOnlyDevelopmentConfiguration,
)
from musigree.constants import TEXT_SEARCH_DATA, TEXT_SEARCH_FILENAME
from musigree.loader.runtime_process_runner import run_runtime_loading_process
from musigree.transfer.transfer_manager import TransferManager

log = logging.getLogger(__name__)

if __name__ == "__main__":
    offline_config = PostgresReadOnlyDevelopmentConfiguration()
    runtime_config = SqliteDevelopmentConfiguration()
    text_search_path = offline_config.DATA_DIR / TEXT_SEARCH_DATA / TEXT_SEARCH_FILENAME
    process = TransferManager().transfer_load_text_search_index(text_search_path)
    run_runtime_loading_process(offline_config, runtime_config, process, ["token"])
