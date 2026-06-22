import asyncio
import logging

from musigree.config import (
    PostgresDevelopmentConfiguration,
)
from musigree.constants import TEXT_SEARCH_DATA, TEXT_SEARCH_FILENAME
from musigree.loader.offline_process_runner import run_offline_loading_process
from musigree.offline.loader.loader_entity import LoaderEntity

log = logging.getLogger(__name__)

if __name__ == "__main__":
    _config = PostgresDevelopmentConfiguration()
    text_search_path = _config.DATA_DIR / TEXT_SEARCH_DATA / TEXT_SEARCH_FILENAME
    process = LoaderEntity().loader_create_text_search_tokens(text_search_path)
    asyncio.run(run_offline_loading_process(_config, process, ["token"]))
