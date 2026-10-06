"""Unit tests for sitemap generation."""

import gzip
from datetime import date
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from xml.etree import ElementTree

import pytest
from sqlalchemy.exc import OperationalError

from musigree.config import SqliteTestConfiguration
from musigree.constants import PUBLIC_DIR
from musigree.library.fields.entity_id import LABEL_ENTITY_ID_OFFSET, MISSING_LABEL_ENTITY
from musigree.loader.run_generate_sitemap import (
    MAX_SITEMAPS_IN_INDEX,
    MAX_URLS_PER_SITEMAP,
    SITEMAP_BASE_URL,
    SITEMAP_INDEX_FILENAME,
    SITEMAP_NAMESPACE,
    SITEMAP_ROOT_FILENAME,
    SitemapLimitError,
    entity_page_url,
    generate_sitemap,
    run_generate_sitemap,
    shutdown_loader,
    sitemap_filename,
    write_sitemap_files,
)

_NS = {"sm": SITEMAP_NAMESPACE}
_GENERATED_ON = date(2026, 10, 6)
_STATIC_SITEMAP_0 = """<?xml version="1.0" encoding="UTF-8"?>
<urlset
    xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.sitemaps.org/schemas/sitemap/0.9
            http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd">
    <url>
        <loc>https://musigree.com/</loc>
        <lastmod>2026-09-23</lastmod>
    </url>
</urlset>
"""


def _root(path: Path) -> ElementTree.Element:
    if path.name.endswith(".gz"):
        with gzip.open(path, "rb") as handle:
            return ElementTree.parse(handle).getroot()
    return ElementTree.parse(path).getroot()


def _loc_texts(path: Path, nested_tag: str) -> list[str]:
    return [element.text or "" for element in _root(path).findall(nested_tag, _NS)]


class TestEntityPageUrl:
    """URL conversion from internal entity ids."""

    def test_artist_url(self) -> None:
        assert entity_page_url(42, SITEMAP_BASE_URL) == "https://musigree.com/artist/42"

    def test_label_url(self) -> None:
        internal_id = LABEL_ENTITY_ID_OFFSET + 99
        assert entity_page_url(internal_id, SITEMAP_BASE_URL) == "https://musigree.com/label/99"

    def test_strips_trailing_slash_from_base_url(self) -> None:
        assert entity_page_url(1, "https://musigree.com/") == "https://musigree.com/artist/1"

    def test_skips_missing_label_sentinel(self) -> None:
        assert entity_page_url(MISSING_LABEL_ENTITY, SITEMAP_BASE_URL) is None


class TestWriteSitemapFiles:
    """Child sitemap files and the sitemap index."""

    def test_writes_artist_and_label_entries_in_id_order(self, tmp_path: Path) -> None:
        internal_ids = [5, LABEL_ENTITY_ID_OFFSET + 3, 2, MISSING_LABEL_ENTITY]

        written = write_sitemap_files(
            internal_ids,
            tmp_path,
            "https://musigree.com/",
            max_urls_per_sitemap=10,
            max_sitemaps=5,
            generated_on=_GENERATED_ON,
        )

        assert written == 3
        child = tmp_path / "sitemap-1.xml.gz"
        assert child.read_bytes()[:2] == b"\x1f\x8b"
        assert not (tmp_path / "sitemap-1.xml").exists()
        assert _loc_texts(child, "sm:url/sm:loc") == [
            "https://musigree.com/artist/2",
            "https://musigree.com/artist/5",
            "https://musigree.com/label/3",
        ]
        assert _loc_texts(tmp_path / SITEMAP_INDEX_FILENAME, "sm:sitemap/sm:loc") == [
            "https://musigree.com/sitemap-0.xml",
            "https://musigree.com/sitemap-1.xml.gz",
        ]
        assert _loc_texts(tmp_path / SITEMAP_INDEX_FILENAME, "sm:sitemap/sm:lastmod") == [
            "2026-10-06",
            "2026-10-06",
        ]

    def test_splits_urls_across_sitemap_files(self, tmp_path: Path) -> None:
        written = write_sitemap_files(
            [1, 2, 3, 4, 5],
            tmp_path,
            "https://example.test",
            max_urls_per_sitemap=2,
            max_sitemaps=500,
            generated_on=_GENERATED_ON,
        )

        assert written == 5
        assert _loc_texts(tmp_path / "sitemap-1.xml.gz", "sm:url/sm:loc") == [
            "https://example.test/artist/1",
            "https://example.test/artist/2",
        ]
        assert _loc_texts(tmp_path / "sitemap-2.xml.gz", "sm:url/sm:loc") == [
            "https://example.test/artist/3",
            "https://example.test/artist/4",
        ]
        assert _loc_texts(tmp_path / "sitemap-3.xml.gz", "sm:url/sm:loc") == [
            "https://example.test/artist/5",
        ]
        assert _loc_texts(tmp_path / SITEMAP_INDEX_FILENAME, "sm:sitemap/sm:loc") == [
            "https://example.test/sitemap-0.xml",
            "https://example.test/sitemap-1.xml.gz",
            "https://example.test/sitemap-2.xml.gz",
            "https://example.test/sitemap-3.xml.gz",
        ]
        assert _loc_texts(tmp_path / SITEMAP_INDEX_FILENAME, "sm:sitemap/sm:lastmod") == [
            "2026-10-06",
            "2026-10-06",
            "2026-10-06",
            "2026-10-06",
        ]

    def test_empty_ids_write_an_index_without_child_sitemaps(self, tmp_path: Path) -> None:
        written = write_sitemap_files([], tmp_path, SITEMAP_BASE_URL)

        assert written == 0
        assert _loc_texts(tmp_path / SITEMAP_INDEX_FILENAME, "sm:sitemap/sm:loc") == [
            "https://musigree.com/sitemap-0.xml",
        ]
        assert list(tmp_path.glob("sitemap-*.xml.gz")) == []
        assert not (tmp_path / SITEMAP_ROOT_FILENAME).exists()

    def test_replaces_stale_sitemap_files(self, tmp_path: Path) -> None:
        stale_xml = tmp_path / "sitemap-9.xml"
        stale_gz = tmp_path / "sitemap-9.xml.gz"
        root = tmp_path / SITEMAP_ROOT_FILENAME
        stale_xml.write_text("stale", encoding="utf-8")
        stale_gz.write_bytes(b"stale")
        root.write_text(_STATIC_SITEMAP_0, encoding="utf-8")

        write_sitemap_files(
            [1],
            tmp_path,
            SITEMAP_BASE_URL,
            max_urls_per_sitemap=10,
            generated_on=_GENERATED_ON,
        )

        assert not stale_xml.exists()
        assert not stale_gz.exists()
        assert (tmp_path / "sitemap-1.xml.gz").is_file()
        assert root.read_text(encoding="utf-8") == _STATIC_SITEMAP_0

    def test_limit_error_leaves_existing_files_in_place(self, tmp_path: Path) -> None:
        index_path = tmp_path / SITEMAP_INDEX_FILENAME
        index_path.write_text("keep", encoding="utf-8")

        with pytest.raises(SitemapLimitError, match="2 entity pages"):
            write_sitemap_files(
                [1, 2],
                tmp_path,
                SITEMAP_BASE_URL,
                max_urls_per_sitemap=1,
                max_sitemaps=1,
            )

        assert index_path.read_text(encoding="utf-8") == "keep"

    def test_rejects_non_positive_limits(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="positive"):
            write_sitemap_files([1], tmp_path, max_urls_per_sitemap=0)

    def test_escapes_xml_in_locations(self, tmp_path: Path) -> None:
        write_sitemap_files(
            [1],
            tmp_path,
            "https://example.test/?a=1&b=2",
            max_urls_per_sitemap=1,
        )

        with gzip.open(tmp_path / "sitemap-1.xml.gz", "rt", encoding="utf-8") as handle:
            sitemap_text = handle.read()
        assert "https://example.test/?a=1&amp;b=2/artist/1" in sitemap_text
        locs = _loc_texts(tmp_path / "sitemap-1.xml.gz", "sm:url/sm:loc")
        assert locs == ["https://example.test/?a=1&b=2/artist/1"]

    def test_default_limits_match_sitemap_protocol(self) -> None:
        assert MAX_URLS_PER_SITEMAP == 50_000
        assert MAX_SITEMAPS_IN_INDEX == 500
        assert sitemap_filename(1) == "sitemap-1.xml.gz"


class TestGenerateSitemap:
    """Database-backed sitemap generation."""

    async def test_loads_ids_from_repository(self, tmp_path: Path) -> None:
        with (
            patch("musigree.loader.run_generate_sitemap.runtime_transaction") as mock_transaction,
            patch(
                "musigree.loader.run_generate_sitemap.RuntimeEntityRepository"
            ) as mock_repository_cls,
        ):
            mock_transaction.return_value.__aenter__ = AsyncMock(return_value=None)
            mock_transaction.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_repository_cls.return_value.get_ids = AsyncMock(
                return_value=[8, LABEL_ENTITY_ID_OFFSET + 4]
            )

            written = await generate_sitemap(tmp_path, "https://musigree.com")

        assert written == 2
        assert _loc_texts(tmp_path / "sitemap-1.xml.gz", "sm:url/sm:loc") == [
            "https://musigree.com/artist/8",
            "https://musigree.com/label/4",
        ]
        mock_repository_cls.return_value.get_ids.assert_awaited_once()


class TestShutdownLoader:
    """Runtime database shutdown."""

    @patch("musigree.loader.run_generate_sitemap.shutdown_logging")
    @patch("musigree.loader.run_generate_sitemap.RuntimeDatabaseManager")
    @patch("musigree.loader.run_generate_sitemap.setup_logging")
    async def test_shutdown_closes_database_when_helper_exists(
        self,
        mock_setup_logging: MagicMock,
        mock_manager: MagicMock,
        mock_shutdown_logging: MagicMock,
    ) -> None:
        mock_manager.runtime_database_helper = object()
        mock_manager.shutdown_database = AsyncMock()

        await shutdown_loader()

        mock_setup_logging.assert_called_once()
        mock_manager.shutdown_database.assert_awaited_once()
        mock_shutdown_logging.assert_called_once()

    @patch("musigree.loader.run_generate_sitemap.shutdown_logging")
    @patch("musigree.loader.run_generate_sitemap.RuntimeDatabaseManager")
    @patch("musigree.loader.run_generate_sitemap.setup_logging")
    async def test_shutdown_skips_database_when_helper_is_missing(
        self,
        _mock_setup_logging: MagicMock,
        mock_manager: MagicMock,
        mock_shutdown_logging: MagicMock,
    ) -> None:
        mock_manager.runtime_database_helper = None
        mock_manager.shutdown_database = AsyncMock()

        await shutdown_loader()

        mock_manager.shutdown_database.assert_not_awaited()
        mock_shutdown_logging.assert_called_once()

    @patch("musigree.loader.run_generate_sitemap.shutdown_logging")
    @patch("musigree.loader.run_generate_sitemap.RuntimeDatabaseManager")
    @patch("musigree.loader.run_generate_sitemap.setup_logging")
    async def test_shutdown_swallows_operational_error(
        self,
        _mock_setup_logging: MagicMock,
        mock_manager: MagicMock,
        mock_shutdown_logging: MagicMock,
    ) -> None:
        mock_manager.runtime_database_helper = object()
        mock_manager.shutdown_database = AsyncMock(
            side_effect=OperationalError("stmt", {}, Exception("db error"))
        )

        await shutdown_loader()

        mock_shutdown_logging.assert_called_once()


class TestRunGenerateSitemap:
    """Process runner wiring."""

    @pytest.fixture
    def mock_config(self) -> SqliteTestConfiguration:
        return SqliteTestConfiguration()

    def test_uses_public_dir_and_production_base_url_by_default(
        self,
        mock_config: SqliteTestConfiguration,
    ) -> None:
        calls: list[tuple[str, object]] = []

        async def fake_setup(config: SqliteTestConfiguration) -> None:
            calls.append(("setup", config))

        async def fake_generate(output_dir: Path, base_url: str) -> int:
            calls.append(("generate", output_dir))
            calls.append(("base_url", base_url))
            return 0

        async def fake_shutdown() -> None:
            calls.append(("shutdown", None))

        with (
            patch("musigree.loader.run_generate_sitemap.setup_logging"),
            patch("musigree.loader.run_generate_sitemap.log_banner"),
            patch(
                "musigree.loader.run_generate_sitemap.RuntimeDatabaseManager.setup_database",
                fake_setup,
            ),
            patch("musigree.loader.run_generate_sitemap.generate_sitemap", fake_generate),
            patch("musigree.loader.run_generate_sitemap.shutdown_loader", fake_shutdown),
        ):
            run_generate_sitemap(mock_config)

        assert calls == [
            ("setup", mock_config),
            ("generate", PUBLIC_DIR),
            ("base_url", SITEMAP_BASE_URL),
            ("shutdown", None),
        ]

    def test_passes_custom_output_dir_and_base_url(
        self,
        mock_config: SqliteTestConfiguration,
        tmp_path: Path,
    ) -> None:
        captured: dict[str, object] = {}

        async def fake_setup(_config: SqliteTestConfiguration) -> None:
            return None

        async def fake_generate(output_dir: Path, base_url: str) -> int:
            captured["output_dir"] = output_dir
            captured["base_url"] = base_url
            return 0

        with (
            patch("musigree.loader.run_generate_sitemap.setup_logging"),
            patch("musigree.loader.run_generate_sitemap.log_banner"),
            patch(
                "musigree.loader.run_generate_sitemap.RuntimeDatabaseManager.setup_database",
                fake_setup,
            ),
            patch("musigree.loader.run_generate_sitemap.generate_sitemap", fake_generate),
            patch("musigree.loader.run_generate_sitemap.shutdown_loader", AsyncMock()),
        ):
            run_generate_sitemap(mock_config, tmp_path, "https://example.test")

        assert captured == {"output_dir": tmp_path, "base_url": "https://example.test"}

    def test_shuts_down_when_generation_fails(
        self,
        mock_config: SqliteTestConfiguration,
        tmp_path: Path,
    ) -> None:
        shutdown = AsyncMock()

        async def fake_setup(_config: SqliteTestConfiguration) -> None:
            return None

        async def fake_generate(_output_dir: Path, _base_url: str) -> int:
            raise RuntimeError("boom")

        with (
            patch("musigree.loader.run_generate_sitemap.setup_logging"),
            patch("musigree.loader.run_generate_sitemap.log_banner"),
            patch(
                "musigree.loader.run_generate_sitemap.RuntimeDatabaseManager.setup_database",
                fake_setup,
            ),
            patch("musigree.loader.run_generate_sitemap.generate_sitemap", fake_generate),
            patch("musigree.loader.run_generate_sitemap.shutdown_loader", shutdown),
            pytest.raises(RuntimeError, match="boom"),
        ):
            run_generate_sitemap(mock_config, tmp_path)

        shutdown.assert_awaited_once()

    def test_swallows_keyboard_interrupt_during_shutdown(
        self,
        mock_config: SqliteTestConfiguration,
        tmp_path: Path,
    ) -> None:
        async def fake_setup(_config: SqliteTestConfiguration) -> None:
            return None

        async def fake_generate(_output_dir: Path, _base_url: str) -> int:
            return 0

        async def fake_shutdown() -> None:
            raise KeyboardInterrupt

        with (
            patch("musigree.loader.run_generate_sitemap.setup_logging"),
            patch("musigree.loader.run_generate_sitemap.log_banner"),
            patch(
                "musigree.loader.run_generate_sitemap.RuntimeDatabaseManager.setup_database",
                fake_setup,
            ),
            patch("musigree.loader.run_generate_sitemap.generate_sitemap", fake_generate),
            patch("musigree.loader.run_generate_sitemap.shutdown_loader", fake_shutdown),
        ):
            run_generate_sitemap(mock_config, tmp_path)
