"""Lazy downloader for the villa-chianti sample-input asset.

The 49MB sample-input (photos/DXF/PDF) is NOT bundled in the wheel — it ships
via GitHub Releases asset `sample-villa-chianti.zip` and is fetched on demand
by `lovarch init --sample`.

Flow when `arch init --sample` is invoked:

    1. Check if bundled sample exists at lovarch_cli/squad/data/sample-input-
       villa-chianti/. If yes → return its path (offline/dev case).
    2. Check cache at ~/.lovarch/cache/sample-villa-chianti/. If extracted
       and SHA-verified → return cached path.
    3. Download sample-villa-chianti.zip from GitHub Releases with progress
       bar, verify SHA256, extract to cache, return path.

The SHA256 is pinned per release (see SAMPLE_ASSET_SHA256). Bumping requires
re-pinning here. Pre-release builds may set this to None to skip verification
(NOT for prod).
"""
from __future__ import annotations

import hashlib
import shutil
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import httpx
from rich.console import Console
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

from lovarch_cli.config import DEFAULT_HOME
from lovarch_cli.i18n import t


# Release pinning — bump together when shipping a new sample.
SAMPLE_RELEASE_TAG = "v0.1.0-beta.1"
SAMPLE_ASSET_NAME = "sample-villa-chianti.zip"
SAMPLE_ASSET_URL = (
    f"https://github.com/ArchPrime-official/lovarch-cli/releases/download/"
    f"{SAMPLE_RELEASE_TAG}/{SAMPLE_ASSET_NAME}"
)
SAMPLE_ASSET_SHA256 = (
    "fa3c057adb9ea70c8338fa1102f1c807524ae847768ad01238cdf364fd335be4"
)
# When extracted, the zip contains a top-level dir named sample-input-villa-
# chianti/ — we keep this convention so the resulting cache path matches the
# bundled-squad path used elsewhere.
EXTRACTED_DIR_NAME = "sample-input-villa-chianti"

# Network limits.
DOWNLOAD_TIMEOUT_SECONDS = 120
DOWNLOAD_CHUNK_SIZE = 64 * 1024


@dataclass(frozen=True)
class SampleSource:
    """Result of resolving the sample-input source path."""

    path: Path
    origin: str  # "bundled" | "cache" | "download"


class SampleDownloadError(RuntimeError):
    """Raised when the sample asset cannot be obtained or verified."""


def _bundled_dir(squad_src: Optional[Path] = None) -> Path:
    """Path the build hook would populate (if sample bundled).

    Honors the same override chain as the runner via squad_loader: an
    explicit `squad_src` argument > `$LOVARCH_SQUAD_SRC` env var > bundled
    vendor. Falls back silently to the bundled path if resolution raises
    (so the lazy-download flow still kicks in instead of crashing).
    """
    from lovarch_cli.squad_loader import SquadNotFoundError, resolve_squad_root

    try:
        root = resolve_squad_root(override=squad_src)
    except SquadNotFoundError:
        # Resolution failed (no override, no bundled) — fall through to the
        # bundled path so downstream cache/download logic handles "not
        # bundled" naturally.
        root = Path(__file__).resolve().parent / "squad"
    return root / "data" / EXTRACTED_DIR_NAME


def _cache_root(home: Optional[Path] = None) -> Path:
    base = home or DEFAULT_HOME
    return base / "cache"


def _cached_dir(home: Optional[Path] = None) -> Path:
    return _cache_root(home) / EXTRACTED_DIR_NAME


def _cached_zip(home: Optional[Path] = None) -> Path:
    return _cache_root(home) / SAMPLE_ASSET_NAME


def _sha256_of(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(DOWNLOAD_CHUNK_SIZE), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _download_with_progress(
    url: str,
    dst: Path,
    console: Console,
    lang: Optional[str],
) -> None:
    """Stream-download `url` to `dst` with a rich progress bar."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = dst.with_suffix(dst.suffix + ".partial")
    try:
        with httpx.stream(
            "GET",
            url,
            timeout=DOWNLOAD_TIMEOUT_SECONDS,
            follow_redirects=True,
        ) as response:
            response.raise_for_status()
            total = int(response.headers.get("content-length", 0)) or None
            with Progress(
                TextColumn("[bold gold1]⬇ {task.description}"),
                BarColumn(bar_width=None),
                DownloadColumn(),
                TransferSpeedColumn(),
                TimeRemainingColumn(),
                console=console,
                transient=True,
            ) as progress:
                task_id = progress.add_task(
                    t("init.downloading", lang=lang, asset=SAMPLE_ASSET_NAME),
                    total=total,
                )
                with tmp.open("wb") as fh:
                    for chunk in response.iter_bytes(DOWNLOAD_CHUNK_SIZE):
                        fh.write(chunk)
                        progress.update(task_id, advance=len(chunk))
        tmp.replace(dst)
    except httpx.HTTPError as exc:
        tmp.unlink(missing_ok=True)
        raise SampleDownloadError(
            t("init.download_failed", lang=lang, url=url, error=str(exc))
        ) from exc


def _verify_zip(zip_path: Path, lang: Optional[str]) -> None:
    if not SAMPLE_ASSET_SHA256:
        return  # Pre-release / explicit skip
    actual = _sha256_of(zip_path)
    if actual != SAMPLE_ASSET_SHA256:
        raise SampleDownloadError(
            t(
                "init.checksum_failed",
                lang=lang,
                expected=SAMPLE_ASSET_SHA256,
                actual=actual,
            )
        )


def _extract_into_cache(
    zip_path: Path,
    cache_root: Path,
    lang: Optional[str],
) -> Path:
    """Extract zip into cache_root/EXTRACTED_DIR_NAME, replacing any prior copy."""
    target = cache_root / EXTRACTED_DIR_NAME
    if target.exists():
        shutil.rmtree(target)
    cache_root.mkdir(parents=True, exist_ok=True)
    try:
        with zipfile.ZipFile(zip_path) as zf:
            # Defense against path-traversal in zip entries.
            for name in zf.namelist():
                resolved = (cache_root / name).resolve()
                if cache_root.resolve() not in resolved.parents and resolved != (
                    cache_root / EXTRACTED_DIR_NAME
                ).resolve():
                    if not str(resolved).startswith(str(cache_root.resolve())):
                        raise SampleDownloadError(
                            t("init.zip_unsafe", lang=lang, entry=name)
                        )
            zf.extractall(cache_root)
    except (zipfile.BadZipFile, OSError) as exc:
        raise SampleDownloadError(
            t("init.extract_failed", lang=lang, error=str(exc))
        ) from exc
    if not target.exists() or not target.is_dir():
        raise SampleDownloadError(
            t("init.unexpected_zip_layout", lang=lang, expected=EXTRACTED_DIR_NAME)
        )
    return target


def resolve_sample_source(
    *,
    console: Console,
    lang: Optional[str] = None,
    home: Optional[Path] = None,
    allow_download: bool = True,
    squad_src: Optional[Path] = None,
) -> SampleSource:
    """Return a populated SampleSource, downloading & caching if needed.

    Resolution order:
      1. Bundled inside the resolved squad root (honors --squad-src /
         $LOVARCH_SQUAD_SRC overrides — see lovarch_cli.squad_loader)
      2. Cached extraction in ~/.lovarch/cache/...
      3. Fresh download from GitHub Releases (if allow_download)

    Raises SampleDownloadError on network/integrity/IO failures when neither
    bundled nor cache is usable.
    """
    bundled = _bundled_dir(squad_src=squad_src)
    if bundled.is_dir() and any(bundled.iterdir()):
        return SampleSource(path=bundled, origin="bundled")

    cached = _cached_dir(home)
    if cached.is_dir() and any(cached.iterdir()):
        return SampleSource(path=cached, origin="cache")

    if not allow_download:
        raise SampleDownloadError(t("init.no_sample_offline", lang=lang))

    zip_path = _cached_zip(home)
    if zip_path.exists():
        # Reuse a previously-downloaded zip if checksum still matches.
        try:
            _verify_zip(zip_path, lang)
        except SampleDownloadError:
            zip_path.unlink(missing_ok=True)

    if not zip_path.exists():
        console.print(
            f"[dim]{t('init.fetching_sample', lang=lang, url=SAMPLE_ASSET_URL)}[/dim]"
        )
        _download_with_progress(SAMPLE_ASSET_URL, zip_path, console, lang)
        _verify_zip(zip_path, lang)

    extracted = _extract_into_cache(zip_path, _cache_root(home), lang)
    return SampleSource(path=extracted, origin="download")
