"""
Generate a sitemap index and child sitemaps for artist and label pages.

Google's sitemap protocol allows at most 50,000 URLs in each sitemap file and
at most 50,000 sitemaps in an index. This generator follows that URL limit and
caps the index at 500 sitemap files, which covers the entity catalogue
(500 * 50,000 = 25,000,000 pages).

See https://developers.google.com/search/docs/crawling-indexing/sitemaps/large-sitemaps
"""

import asyncio
import gzip
import logging
from collections.abc import Sequence
from datetime import UTC, date, datetime
from pathlib import Path
from xml.sax.saxutils import escape

from sqlalchemy.exc import OperationalError

from musigree.config import Configuration, SqliteReadOnlyDevelopmentConfiguration
from musigree.constants import PUBLIC_DIR
from musigree.library.fields.entity_id import to_entity_external_id
from musigree.library.fields.entity_type import EntityType
from musigree.logging_config import setup_logging, shutdown_logging
from musigree.runtime.runtime_database.runtime_entity_repository import RuntimeEntityRepository
from musigree.runtime.runtime_database.runtime_transaction import runtime_transaction
from musigree.runtime.runtime_database_manager import RuntimeDatabaseManager
from musigree.utils import log_banner

log = logging.getLogger(__name__)

#: Public site origin used in every sitemap ``<loc>``.
SITEMAP_BASE_URL = "https://musigree.com"
#: Google's maximum number of URLs in one sitemap file.
MAX_URLS_PER_SITEMAP = 50_000
#: Maximum number of child sitemaps listed in ``sitemap_index.xml``.
MAX_SITEMAPS_IN_INDEX = 500
SITEMAP_INDEX_FILENAME = "sitemap_index.xml"
#: Static urlset listed first in the sitemap index. The generator does not rewrite it.
SITEMAP_ROOT_FILENAME = "sitemap-0.xml"
SITEMAP_NAMESPACE = "http://www.sitemaps.org/schemas/sitemap/0.9"
_XML_DECLARATION = '<?xml version="1.0" encoding="UTF-8"?>\n'


class SitemapLimitError(ValueError):
    """Raised when entity pages exceed the sitemap index capacity."""


def sitemap_filename(sitemap_number: int) -> str:
    """Return the gzipped child sitemap filename for a 1-based sitemap number."""
    return f"sitemap-{sitemap_number}.xml.gz"


def entity_page_url(internal_id: int, base_url: str) -> str | None:
    """
    Build the public page URL for an internal entity id.

    Artist pages are ``/artist/{external_id}`` and label pages are
    ``/label/{external_id}``, matching the UI routes. Negative external ids,
    including the missing-label sentinel, are omitted because they have no page.
    """
    external_id, entity_type = to_entity_external_id(internal_id)
    if external_id < 0:
        return None
    if entity_type is EntityType.ARTIST:
        segment = "artist"
    elif entity_type is EntityType.LABEL:
        segment = "label"
    else:
        raise NotImplementedError(entity_type)
    return f"{base_url.rstrip('/')}/{segment}/{external_id}"


def _remove_existing_sitemaps(output_dir: Path) -> None:
    """Delete generated sitemap files left by a previous run.

    ``sitemap-0.xml`` is a static top-level urlset and is left in place.
    """
    for path in output_dir.glob("sitemap-*.xml"):
        if path.name == SITEMAP_ROOT_FILENAME:
            continue
        path.unlink()
    for path in output_dir.glob("sitemap-*.xml.gz"):
        path.unlink()
    index_path = output_dir / SITEMAP_INDEX_FILENAME
    if index_path.is_file():
        index_path.unlink()


def _write_urlset(path: Path, page_urls: Sequence[str]) -> None:
    """Write one gzip-compressed urlset sitemap."""
    with gzip.open(path, "wt", encoding="utf-8") as handle:
        handle.write(_XML_DECLARATION)
        handle.write(f'<urlset xmlns="{SITEMAP_NAMESPACE}">\n')
        for page_url in page_urls:
            handle.write(f"  <url>\n    <loc>{escape(page_url)}</loc>\n  </url>\n")
        handle.write("</urlset>\n")


def _write_sitemap_index(path: Path, sitemap_locations: Sequence[str], lastmod: str) -> None:
    """Write ``sitemap_index.xml`` pointing at the static and gzipped sitemaps."""
    with path.open("w", encoding="utf-8") as handle:
        handle.write(_XML_DECLARATION)
        handle.write(f'<sitemapindex xmlns="{SITEMAP_NAMESPACE}">\n')
        for location in sitemap_locations:
            handle.write(
                "  <sitemap>\n"
                f"    <loc>{escape(location)}</loc>\n"
                f"    <lastmod>{escape(lastmod)}</lastmod>\n"
                "  </sitemap>\n"
            )
        handle.write("</sitemapindex>\n")


def write_sitemap_files(
    internal_ids: Sequence[int],
    output_dir: Path,
    base_url: str = SITEMAP_BASE_URL,
    *,
    max_urls_per_sitemap: int = MAX_URLS_PER_SITEMAP,
    max_sitemaps: int = MAX_SITEMAPS_IN_INDEX,
    generated_on: date | None = None,
) -> int:
    """
    Write gzipped child sitemaps and ``sitemap_index.xml`` for the given internal ids.

    Ids are sorted so repeated runs partition the same pages into the same
    files. Existing generated sitemap files in ``output_dir`` are replaced
    only after the id list is known to fit in the index. Each index entry,
    including the static ``sitemap-0.xml``, records ``generated_on`` (or
    today) in ``lastmod``.

    Returns:
        The number of page URLs written.

    Raises:
        ValueError: If a sitemap limit is not positive.
        SitemapLimitError: If the pages need more than ``max_sitemaps`` files.
    """
    if max_urls_per_sitemap < 1 or max_sitemaps < 1:
        raise ValueError("Sitemap limits must be positive")

    ordered_ids = sorted(internal_ids)
    url_count = sum(
        1 for internal_id in ordered_ids if entity_page_url(internal_id, base_url) is not None
    )
    capacity = max_urls_per_sitemap * max_sitemaps
    if url_count > capacity:
        raise SitemapLimitError(
            f"Sitemap index holds at most {max_sitemaps} files of "
            f"{max_urls_per_sitemap} URLs ({capacity} URLs) but "
            f"{url_count} entity pages were found"
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    _remove_existing_sitemaps(output_dir)

    lastmod = (generated_on or datetime.now(UTC).date()).isoformat()
    normalized_base = base_url.rstrip("/")
    sitemap_locations = [f"{normalized_base}/{SITEMAP_ROOT_FILENAME}"]
    batch: list[str] = []
    generated_sitemap_count = 0

    def flush_batch() -> None:
        nonlocal generated_sitemap_count
        if not batch:
            return
        generated_sitemap_count += 1
        filename = sitemap_filename(generated_sitemap_count)
        _write_urlset(output_dir / filename, batch)
        sitemap_locations.append(f"{normalized_base}/{filename}")
        batch.clear()

    for internal_id in ordered_ids:
        page_url = entity_page_url(internal_id, base_url)
        if page_url is None:
            continue
        batch.append(page_url)
        if len(batch) >= max_urls_per_sitemap:
            flush_batch()
    flush_batch()

    _write_sitemap_index(output_dir / SITEMAP_INDEX_FILENAME, sitemap_locations, lastmod)
    return url_count


async def generate_sitemap(
    output_dir: Path,
    base_url: str = SITEMAP_BASE_URL,
) -> int:
    """
    Load every runtime entity id and write sitemaps for artist and label pages.

    Returns:
        The number of page URLs written.
    """
    async with runtime_transaction():
        internal_ids = await RuntimeEntityRepository().get_ids()
    url_count = write_sitemap_files(internal_ids, output_dir, base_url)
    log.info(f"Wrote {url_count} entity URLs into sitemaps at {output_dir}")
    return url_count


async def shutdown_loader() -> None:
    """Close the runtime database and shut down logging."""
    setup_logging()
    log.info("######## SITEMAP GENERATOR SHUTDOWN START ########")
    try:
        if RuntimeDatabaseManager.runtime_database_helper is not None:
            await RuntimeDatabaseManager.shutdown_database()
    except OperationalError:
        pass
    log.info("######## SITEMAP GENERATOR SHUTDOWN DONE ########")
    shutdown_logging()


def run_generate_sitemap(
    runtime_config: Configuration,
    output_dir: Path | None = None,
    base_url: str = SITEMAP_BASE_URL,
) -> None:
    """Open the runtime database, write sitemaps, and close the database."""
    setup_logging()
    log_banner()
    log.info(f"Using {runtime_config.__class__.__name__} for runtime database")

    destination = PUBLIC_DIR if output_dir is None else output_dir
    log.info(f"Writing sitemaps to {destination}")

    with asyncio.Runner() as runner:
        try:
            runner.run(RuntimeDatabaseManager.setup_database(runtime_config))
            runner.run(generate_sitemap(destination, base_url))
        finally:
            try:
                runner.run(shutdown_loader())
            except KeyboardInterrupt:
                log.warning("Sitemap generator shutdown interrupted")


if __name__ == "__main__":
    _config = SqliteReadOnlyDevelopmentConfiguration()
    run_generate_sitemap(_config)
