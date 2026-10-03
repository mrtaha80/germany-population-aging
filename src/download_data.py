#!/usr/bin/env python3
"""Download and validate Eurostat's regional population-structure indicators.

Run from the repository root:
    py src/download_data.py

Downloads the compressed TSV for demo_r_pjanind2. Local raw data and metadata
are written under data/raw/ and intentionally excluded from Git.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

DATASET = "demo_r_pjanind2"
URL = (
    "https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/"
    f"{DATASET}?format=TSV&compressed=true"
)
EXPECTED_DIMENSIONS = {"freq", "indic_de", "unit", "geo"}


def make_session() -> requests.Session:
    retry = Retry(
        total=5, connect=5, read=5, status=5, backoff_factor=1.0,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET"}), respect_retry_after_header=True,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session = requests.Session()
    session.mount("https://", adapter)
    session.headers.update({"User-Agent": "germany-population-aging-portfolio/1.0"})
    return session


def inspect_gzip_tsv(path: Path) -> tuple[str, list[str]]:
    with gzip.open(path, "rt", encoding="utf-8-sig", newline="") as source:
        header = source.readline().rstrip("\r\n")
    if not header:
        raise ValueError("Downloaded TSV is empty or has no header.")
    columns = header.split("\t")
    if "\\" not in columns[0]:
        raise ValueError(f"Unexpected Eurostat key header: {columns[0]!r}")
    dimensions = set(columns[0].split("\\", 1)[0].split(","))
    if dimensions != EXPECTED_DIMENSIONS:
        raise ValueError(f"Expected dimensions {sorted(EXPECTED_DIMENSIONS)}, got {sorted(dimensions)}")
    periods = [column.strip() for column in columns[1:]]
    if not any(re.fullmatch(r"\d{4}", period) for period in periods):
        raise ValueError(f"No annual year columns found. Header sample: {columns[:6]!r}")
    return header, periods


def download(output_dir: Path, force: bool = False) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    data_path = output_dir / f"{DATASET}.tsv.gz"
    metadata_path = output_dir / f"{DATASET}.metadata.json"
    if data_path.exists() and not force:
        raise FileExistsError(f"{data_path} already exists. Use --force to replace it.")

    digest = hashlib.sha256()
    with make_session() as session:
        with session.get(URL, stream=True, timeout=(20, 180)) as response:
            response.raise_for_status()
            headers = {key: response.headers.get(key) for key in ("Content-Type", "Last-Modified", "ETag")}
            with tempfile.NamedTemporaryFile(mode="wb", dir=output_dir, prefix=f".{DATASET}.", suffix=".part", delete=False) as tmp:
                tmp_path = Path(tmp.name)
                try:
                    for chunk in response.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            tmp.write(chunk)
                            digest.update(chunk)
                    tmp.flush()
                except Exception:
                    tmp_path.unlink(missing_ok=True)
                    raise

    try:
        with tmp_path.open("rb") as stream:
            if stream.read(2) != b"\x1f\x8b":
                raise ValueError("Eurostat response is not gzip. Check the API response.")
        header, periods = inspect_gzip_tsv(tmp_path)
        size = tmp_path.stat().st_size
        tmp_path.replace(data_path)
    except Exception:
        tmp_path.unlink(missing_ok=True)
        raise

    years = [int(period) for period in periods if re.fullmatch(r"\d{4}", period)]
    metadata = {
        "dataset": DATASET,
        "source_url": URL,
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "file": data_path.name,
        "bytes": size,
        "sha256": digest.hexdigest(),
        "response_headers": headers,
        "header": header,
        "period_columns": periods,
        "first_year": min(years),
        "last_year": max(years),
    }
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return data_path, metadata_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("data/raw"))
    parser.add_argument("--force", action="store_true", help="replace an existing download")
    args = parser.parse_args()
    try:
        data_path, metadata_path = download(args.output_dir, force=args.force)
    except (requests.RequestException, OSError, ValueError) as error:
        print(f"Download failed: {error}", file=sys.stderr)
        return 1
    print(f"Saved data:     {data_path}")
    print(f"Saved metadata: {metadata_path}")
    print("Gzip integrity and Eurostat TSV dimension checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
