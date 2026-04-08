"""
Kaggle dataset search module for ChadGPT.

Searches the Kaggle API for datasets related to the user's query topic,
downloads small CSVs, and returns parsed data for charting.

Requires KAGGLE_USERNAME and KAGGLE_KEY in environment (or ~/.kaggle/kaggle.json).
Falls back gracefully if credentials are missing.
"""

import os
import csv
import tempfile
import hashlib
from pathlib import Path

_CACHE_DIR = Path(__file__).resolve().parent / "datasets" / ".kaggle_cache"
_AVAILABLE = False

try:
    from kaggle.api.kaggle_api_extended import KaggleApi  # type: ignore[import-untyped]
    _AVAILABLE = True
except ImportError:
    pass


def _get_api() -> "KaggleApi | None":
    """Authenticate with Kaggle. Returns None if credentials are missing."""
    if not _AVAILABLE:
        return None
    try:
        api = KaggleApi()
        api.authenticate()
        return api
    except Exception as exc:
        print(f"Kaggle auth failed: {exc}")
        return None


def search_datasets(topic: str, max_results: int = 3) -> list[dict]:
    """
    Search Kaggle for datasets matching `topic + Chad/Africa`.
    Returns list of {ref, title, size, description}.
    """
    api = _get_api()
    if api is None:
        return []

    queries = [f"Chad {topic}", f"Africa {topic}"]
    results: list[dict] = []
    seen_refs: set[str] = set()

    for q in queries:
        try:
            datasets = api.dataset_list(search=q, sort_by="relevance", max_size=50_000_000)
            for ds in datasets[:max_results]:
                ref = str(ds.ref)
                if ref in seen_refs:
                    continue
                seen_refs.add(ref)
                results.append({
                    "ref": ref,
                    "title": str(ds.title),
                    "size": int(ds.size) if ds.size else 0,
                    "description": str(ds.subtitle or ""),
                })
        except Exception as exc:
            print(f"Kaggle search error for '{q}': {exc}")

    return results[:max_results]


def download_and_parse(dataset_ref: str, max_rows: int = 200) -> list[dict] | None:
    """
    Download the first CSV from a Kaggle dataset and return rows as dicts.
    Results are cached locally.
    """
    api = _get_api()
    if api is None:
        return None

    cache_key = hashlib.md5(dataset_ref.encode()).hexdigest()
    cache_path = _CACHE_DIR / cache_key
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # Check cache
    cached_csv = list(cache_path.glob("*.csv")) if cache_path.exists() else []
    if cached_csv:
        csv_file = cached_csv[0]
    else:
        # Download to temp, then move to cache
        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                api.dataset_download_files(dataset_ref, path=tmpdir, unzip=True)
            except Exception as exc:
                print(f"Kaggle download error for '{dataset_ref}': {exc}")
                return None
            csv_files = list(Path(tmpdir).rglob("*.csv"))
            if not csv_files:
                return None
            # Pick the largest CSV (most likely the main data file)
            csv_files.sort(key=lambda p: p.stat().st_size, reverse=True)
            csv_file = csv_files[0]
            cache_path.mkdir(parents=True, exist_ok=True)
            dest = cache_path / csv_file.name
            dest.write_bytes(csv_file.read_bytes())
            csv_file = dest

    # Parse CSV
    try:
        with open(csv_file, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            rows = []
            for i, row in enumerate(reader):
                if i >= max_rows:
                    break
                rows.append(dict(row))
            return rows
    except Exception as exc:
        print(f"CSV parse error: {exc}")
        return None


def is_available() -> bool:
    """Check if Kaggle API is configured and available."""
    return _get_api() is not None
