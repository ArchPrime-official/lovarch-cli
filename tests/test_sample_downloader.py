"""Tests for lovarch_cli.sample_downloader — bundled → cache → download."""
from __future__ import annotations

import hashlib
import io
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from rich.console import Console

from lovarch_cli.sample_downloader import (
    EXTRACTED_DIR_NAME,
    SampleDownloadError,
    resolve_sample_source,
)


def _build_zip_with_villa(tmp_path: Path, extra_files: dict[str, str] | None = None) -> bytes:
    """Build an in-memory zip that mimics the release asset layout.

    Top-level dir is sample-input-villa-chianti/, containing a couple of files.
    """
    buf = io.BytesIO()
    files = {
        f"{EXTRACTED_DIR_NAME}/README.md": "# Villa Chianti\n",
        f"{EXTRACTED_DIR_NAME}/briefing-cliente.md": "Sample briefing\n",
        f"{EXTRACTED_DIR_NAME}/foto/01-facciata.jpg": "fake-jpg-bytes",
    }
    if extra_files:
        files.update(extra_files)
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, content in files.items():
            zf.writestr(name, content)
    return buf.getvalue()


def test_resolve_returns_cache_when_extracted_dir_exists(tmp_path: Path):
    """If cache already has an extracted dir, no download is attempted."""
    home = tmp_path / "home"
    cache_dir = home / "cache" / EXTRACTED_DIR_NAME
    cache_dir.mkdir(parents=True)
    (cache_dir / "README.md").write_text("hi", encoding="utf-8")

    with patch("lovarch_cli.sample_downloader.httpx.stream") as stream:
        result = resolve_sample_source(
            console=Console(quiet=True),
            home=home,
            lang="en",
        )

    assert result.origin == "cache"
    assert result.path == cache_dir
    stream.assert_not_called()


def test_resolve_downloads_extracts_and_verifies(tmp_path: Path):
    """When neither bundled nor cache, download → verify → extract → return."""
    home = tmp_path / "home"
    zip_bytes = _build_zip_with_villa(tmp_path)
    actual_sha = hashlib.sha256(zip_bytes).hexdigest()

    # Stream mock returns the zip in chunks
    response_cm = MagicMock()
    response_cm.headers = {"content-length": str(len(zip_bytes))}
    response_cm.raise_for_status = MagicMock()
    response_cm.iter_bytes = MagicMock(return_value=[zip_bytes])

    stream_cm = MagicMock()
    stream_cm.__enter__ = MagicMock(return_value=response_cm)
    stream_cm.__exit__ = MagicMock(return_value=False)

    with patch("lovarch_cli.sample_downloader.SAMPLE_ASSET_SHA256", actual_sha):
        with patch(
            "lovarch_cli.sample_downloader.httpx.stream",
            return_value=stream_cm,
        ):
            result = resolve_sample_source(
                console=Console(quiet=True),
                home=home,
                lang="en",
            )

    assert result.origin == "download"
    extracted = home / "cache" / EXTRACTED_DIR_NAME
    assert result.path == extracted
    assert (extracted / "README.md").read_text() == "# Villa Chianti\n"
    assert (extracted / "foto" / "01-facciata.jpg").read_text() == "fake-jpg-bytes"


def test_resolve_rejects_corrupted_zip(tmp_path: Path):
    """Bad checksum aborts with SampleDownloadError (no extraction)."""
    home = tmp_path / "home"
    zip_bytes = _build_zip_with_villa(tmp_path)

    response_cm = MagicMock()
    response_cm.headers = {"content-length": str(len(zip_bytes))}
    response_cm.raise_for_status = MagicMock()
    response_cm.iter_bytes = MagicMock(return_value=[zip_bytes])

    stream_cm = MagicMock()
    stream_cm.__enter__ = MagicMock(return_value=response_cm)
    stream_cm.__exit__ = MagicMock(return_value=False)

    with patch(
        "lovarch_cli.sample_downloader.SAMPLE_ASSET_SHA256",
        "0" * 64,  # Pinned hash won't match
    ):
        with patch(
            "lovarch_cli.sample_downloader.httpx.stream",
            return_value=stream_cm,
        ):
            with pytest.raises(SampleDownloadError) as exc:
                resolve_sample_source(
                    console=Console(quiet=True),
                    home=home,
                    lang="en",
                )

    assert "SHA256 mismatch" in str(exc.value)
    assert not (home / "cache" / EXTRACTED_DIR_NAME).exists()


def test_resolve_offline_mode_raises_when_no_cache(tmp_path: Path):
    """allow_download=False with no cache → SampleDownloadError, no network."""
    home = tmp_path / "home"
    with patch("lovarch_cli.sample_downloader.httpx.stream") as stream:
        with pytest.raises(SampleDownloadError):
            resolve_sample_source(
                console=Console(quiet=True),
                home=home,
                lang="en",
                allow_download=False,
            )
    stream.assert_not_called()


def test_resolve_uses_existing_zip_when_checksum_matches(tmp_path: Path):
    """Pre-downloaded zip file in cache is reused (no re-download)."""
    home = tmp_path / "home"
    cache_root = home / "cache"
    cache_root.mkdir(parents=True)
    zip_bytes = _build_zip_with_villa(tmp_path)
    zip_path = cache_root / "sample-villa-chianti.zip"
    zip_path.write_bytes(zip_bytes)
    actual_sha = hashlib.sha256(zip_bytes).hexdigest()

    with patch("lovarch_cli.sample_downloader.SAMPLE_ASSET_SHA256", actual_sha):
        with patch("lovarch_cli.sample_downloader.httpx.stream") as stream:
            result = resolve_sample_source(
                console=Console(quiet=True),
                home=home,
                lang="en",
            )

    assert result.origin == "download"  # Treated as download path (no cache extracted yet)
    assert (home / "cache" / EXTRACTED_DIR_NAME / "README.md").is_file()
    stream.assert_not_called()  # Didn't re-fetch; reused on-disk zip
