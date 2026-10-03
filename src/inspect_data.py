#!/usr/bin/env python3
"""Inspect Eurostat regional indicator data and the selected 65+ measure.

Run from the repository root after downloading:
    py src/inspect_data.py
"""

from __future__ import annotations

import argparse
import gzip
import re
import sys
from pathlib import Path

import pandas as pd

DEFAULT_FILE = Path("data/raw/demo_r_pjanind2.tsv.gz")
DIMENSIONS = ["freq", "indic_de", "unit", "geo"]
YEARS = [str(year) for year in range(2014, 2026)]
INDICATOR = "PC_Y65_MAX"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", type=Path, default=DEFAULT_FILE)
    args = parser.parse_args()
    if not args.path.exists():
        print(f"File not found: {args.path}\nRun py src/download_data.py first.", file=sys.stderr)
        return 1
    try:
        with gzip.open(args.path, "rt", encoding="utf-8-sig", newline="") as source:
            frame = pd.read_csv(source, sep="\t", dtype="string", low_memory=False)
    except (OSError, EOFError, pd.errors.ParserError) as error:
        print(f"Could not read Eurostat TSV: {error}", file=sys.stderr)
        return 1

    frame.columns = [str(column).strip() for column in frame.columns]
    key_column = frame.columns[0]
    parts = frame[key_column].fillna("").str.split(",", expand=True)
    if parts.shape[1] != len(DIMENSIONS):
        print(f"Expected dimensions {DIMENSIONS}; found {parts.shape[1]} in {key_column!r}", file=sys.stderr)
        return 1
    parts.columns = DIMENSIONS
    data = pd.concat([parts, frame.iloc[:, 1:]], axis=1)
    year_columns = [column for column in frame.columns[1:] if column.isdigit()]
    print(f"File: {args.path}")
    print(f"Time series: {len(data):,}; coverage: {year_columns[0]}–{year_columns[-1]}" if year_columns else f"Time series: {len(data):,}; no annual columns found")
    for dimension in DIMENSIONS:
        codes = sorted(data[dimension].dropna().unique().tolist())
        print(f"{dimension}: {codes[:100]}" + (" ..." if len(codes) > 100 else ""))

    german = data[data.geo.fillna("").str.fullmatch(r"DE[A-Z0-9]{2}", na=False)]
    selected = german[
        german.freq.eq("A") & german.indic_de.eq(INDICATOR) & german.unit.eq("PC")
    ]
    if selected.empty:
        print(f"No German NUTS 2 rows found for {INDICATOR} / unit PC; inspect codes above.")
        return 0
    years = [year for year in YEARS if year in data.columns]
    if years:
        long = selected.melt(id_vars=["geo"], value_vars=years, var_name="year", value_name="raw_value")
        numeric = pd.to_numeric(long.raw_value.str.extract(r"^\s*([+-]?[\d.]+)")[0], errors="coerce")
        long["numeric_value"] = numeric
        coverage = long.groupby("year").numeric_value.agg(total="size", present="count")
        coverage["missing"] = coverage.total - coverage.present
        print(f"\n{INDICATOR} coverage by year (German NUTS 2; unit=PC):")
        print(coverage.to_string())
        print("\nExample values:")
        print(long[long.numeric_value.notna()].head(8).to_string(index=False))
    print(f"\nSelected German NUTS 2 regions: {selected.geo.nunique()}")
    print("Indicator meaning: proportion of population aged 65 years and over; reported in percent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
