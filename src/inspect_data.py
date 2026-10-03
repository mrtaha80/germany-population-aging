#!/usr/bin/env python3
"""Audit a downloaded Eurostat demo_r_d2jan TSV without changing it.

Run from the repository root after downloading:
    python src/inspect_data.py

The report reveals real dimension codes and geography levels before any
filtering or calculation is done.
"""

from __future__ import annotations

import argparse
import gzip
import sys
from pathlib import Path

import pandas as pd

DEFAULT_FILE = Path("data/raw/demo_r_d2jan.tsv.gz")
DIMENSIONS = ["freq", "unit", "sex", "age", "geo"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", type=Path, default=DEFAULT_FILE)
    args = parser.parse_args()

    if not args.path.exists():
        print(f"File not found: {args.path}\nRun python src/download_data.py first.", file=sys.stderr)
        return 1

    try:
        with gzip.open(args.path, "rt", encoding="utf-8-sig", newline="") as source:
            frame = pd.read_csv(source, sep="\t", dtype="string", low_memory=False)
    except (OSError, EOFError, pd.errors.ParserError) as error:
        print(f"Could not read Eurostat TSV: {error}", file=sys.stderr)
        return 1

    frame.columns = [str(column).strip() for column in frame.columns]
    key_column = frame.columns[0]
    key_parts = frame[key_column].fillna("").str.split(",", expand=True)

    if key_parts.shape[1] != len(DIMENSIONS):
        print(
            f"Expected {len(DIMENSIONS)} comma-separated key dimensions, "
            f"found {key_parts.shape[1]} in {key_column!r}.",
            file=sys.stderr,
        )
        print("First key values:", frame[key_column].head(5).tolist(), file=sys.stderr)
        return 1

    key_parts.columns = DIMENSIONS
    data = pd.concat([key_parts, frame.iloc[:, 1:]], axis=1)
    year_columns = [column for column in frame.columns[1:] if column.isdigit()]

    print(f"File: {args.path}")
    print(f"Rows (time series): {len(data):,}")
    print(f"Dimension key column: {key_column}")
    print(f"Year columns: {year_columns[0]}–{year_columns[-1]} ({len(year_columns)} years)" if year_columns else "Year columns: none detected")
    print("\nDistinct dimension codes:")
    for dimension in DIMENSIONS:
        values = sorted(data[dimension].dropna().unique().tolist())
        print(f"  {dimension}: {values[:80]}" + (" ..." if len(values) > 80 else ""))

    germany = data[data["geo"].fillna("").str.startswith("DE")]
    print("\nGerman geography codes by code length:")
    for length, group in germany.groupby(germany["geo"].str.len()):
        codes = sorted(group["geo"].dropna().unique().tolist())
        print(f"  {length} characters: {len(codes)} codes, sample={codes[:40]}")

    nuts2 = germany[germany["geo"].str.fullmatch(r"DE[A-Z0-9]{2}", na=False)]
    print(f"\nGerman NUTS-2-shaped series: {len(nuts2):,}")
    for dimension in ["freq", "unit", "sex", "age"]:
        print(f"  {dimension}: {sorted(nuts2[dimension].dropna().unique().tolist())}")

    print("\nSample German NUTS 2 keys:")
    print(nuts2[DIMENSIONS].drop_duplicates().head(12).to_string(index=False))
    print("\nNo observations have been filtered, transformed, or saved by this audit.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
