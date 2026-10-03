#!/usr/bin/env python3
"""Download and validate the compressed Eurostat demo_r_d2jan TSV.

Run from the repository root:
    python src/download_data.py

Raw source data and its local metadata sidecar are written under data/raw/.
They are intentionally ignored by Git; the script and source URL are versioned.
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

DATASET = "demo_r_d2jan"
URL = (
    "https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/"
    f"{DATASET}?format=TSV&compressed=true"
)
EXPECTED_DIMENSIONS = {"freq", "unit", "sex", "age", "geo"}


def make_session() -> requests.Session:
    retry = Retry(
        total=5,
        connect=5,
        read=5,
        status=5,
        backoff_factor=1.0,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET"}),
        respect_retry_after_header=True,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session = requests.Session()
    session.mount("https://", adapter)
    session.headers.update(
        {"User-Agent": "germany-population-aging-portfolio/1.0 (reproducible research)"}
    )
    return session


def inspect_gzip_tsv(path: Path) -> tuple[str, list[str]]:
    """Check gzip integrity and return the decoded header and time columns."""
    with gzip.open(path, "rt", encoding="utf-8-sig", newline="") as source:
        header_line = source.readline().rstrip("\r\n")

    if not header_line:
        raise ValueError("The downloaded TSV is empty or has no header.")

    columns = header_line.split("\t")
    series_key = columns[0]
    if "\\" not in series_key:
        raise ValueError(f"Unexpected first TSV header field: {series_key!r}")

    dimension_text = series_key.split("\\", 1)[0]
    dimensions = set(dimension_text.split(","))
    if dimensions != EXPECTED_DIMENSIONS:
        raise ValueError(
            "Unexpected dataset dimensions in header. "
            f"Expected {sorted(EXPECTED_DIMENSIONS)}, got {sorted(dimensions)}."
        )

    periods = columns[1:]
    if not periods or not any(re.fullmatch(r"\d{4}", period) for period in periods):
        raise ValueError("No annual YYYY time columns were found in the TSV header.")

    return header_line, periods


def download(output_dir: Path, force: bool = False) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    data_path = output_dir / f"{DATASET}.tsv.gz"
    metadata_path = output_dir / f"{DATASET}.metadata.json"

    if data_path.exists() and not force:
        raise FileExistsError(
            f"{data_path} already exists. Use --force to download and replace it."
        )

    sha256 = hashlib.sha256()
    response_headers: dict[str, str | None] = {}

    with make_session() as session:
        with session.get(URL, stream=True, timeout=(20, 180)) as response:
            response.raise_for_status()
            response_headers = {
                "content_type": response.headers.get("Content-Type"),
                "last_modified": response.headers.get("Last-Modified"),
                "etag": response.headers.get("ETag"),
            }

            with tempfile.NamedTemporaryFile(
                mode="wb", dir=output_dir, prefix=f".{DATASET}.", suffix=".part", delete=False
            ) as temporary:
                temp_path = Path(temporary.name)
                try:
                    for chunk in response.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            temporary.write(chunk)
                            sha256.update(chunk)
                    temporary.flush()
                except Exception:
                    temp_path.unlink(missing_ok=True)
                    raise

    try:
        with temp_path.open("rb") as downloaded:
            if downloaded.read(2) != b"\x1f\x8b":
                raise ValueError(
                    "Response is not a gzip file. Check the Eurostat URL/API response."
                )
        header, periods = inspect_gzip_tsv(temp_path)
        byte_count = temp_path.stat().st_size
        temp_path.replace(data_path)
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise

    metadata = {
        "dataset": DATASET,
        "source_url": URL,
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "file": data_path.name,
        "bytes": byte_count,
        "sha256": sha256.hexdigest(),
        "response_headers": response_headers,
        "header": header,
        "period_columns": periods,
        "first_year": min((int(p) for p in periods if re.fullmatch(r"\d{4}", p)), default=None),
        "last_year": max((int(p) for p in periods if re.fullmatch(r"\d{4}", p)), default=None),
    }
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return data_path, metadata_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir", type=Path, default=Path("data/raw"),
        help="directory for the compressed TSV and metadata (default: data/raw)",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="replace an existing download",
    )
    args = parser.parse_args()

    try:
        data_path, metadata_path = download(args.output_dir, force=args.force)
    except (requests.RequestException, OSError, ValueError) as error:
        print(f"Download failed: {error}", file=sys.stderr)
        return 1

    print(f"Saved data:     {data_path}")
    print(f"Saved metadata: {metadata_path}")
    print("Gzip integrity and Eurostat TSV header checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
