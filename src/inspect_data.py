#!/usr/bin/env python3
"""Audit a downloaded Eurostat demo_r_d2jan TSV without changing it.

Run from the repository root after downloading:
    python src/inspect_data.py

The report reveals real dimension codes, geography levels, and completeness of
the older-age categories used for the 65+ metric before cleaning.
"""

from __future__ import annotations

import argparse
import gzip
import re
import sys
from pathlib import Path

import pandas as pd

DEFAULT_FILE = Path("data/raw/demo_r_d2jan.tsv.gz")
DIMENSIONS = ["freq", "unit", "sex", "age", "geo"]
YEARS_TO_AUDIT = [str(year) for year in range(2014, 2026)]
OLD_AGE_CODES = {*(f"Y{age}" for age in range(65, 100)), "Y_OPEN"}
NUMERIC_OBSERVATION = re.compile(r"^\s*[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?(?:\s+.*)?\s*$")


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

    available_years = [year for year in YEARS_TO_AUDIT if year in data.columns]
    old_age = nuts2[
        nuts2["freq"].eq("A")
        & nuts2["unit"].eq("NR")
        & nuts2["sex"].eq("T")
        & nuts2["age"].isin(OLD_AGE_CODES)
    ].copy()
    if available_years:
        long = old_age.melt(
            id_vars=["geo", "age"],
            value_vars=available_years,
            var_name="year",
            value_name="raw_value",
        )
        has_number = long["raw_value"].fillna("").str.match(NUMERIC_OBSERVATION)
        audit = long.assign(has_number=has_number).groupby("age").agg(
            region_years=("geo", "size"),
            numeric_observations=("has_number", "sum"),
        )
        audit["missing_observations"] = audit["region_years"] - audit["numeric_observations"]
        audit = audit.sort_index(key=lambda index: index.map(
            lambda age: 100 if age == "Y_OPEN" else int(age[1:]) if age.startswith("Y") and age[1:].isdigit() else -1
        ))
        expected = nuts2["geo"].nunique() * len(available_years)
        print(f"\n65+ source-category completeness for {available_years[0]}–{available_years[-1]} (expected {expected} rows per age code):")
        print(audit.to_string())
        missing = audit[audit["numeric_observations"].lt(expected)]
        if missing.empty:
            print("All 36 selected age categories have numeric observations for every region-year.")
        else:
            print("Age codes with one or more non-numeric/missing observations:", ", ".join(missing.index.tolist()))
            print("Inspect the Eurostat status flags before deciding whether a partial 65+ sum is valid.")

    print("\nNo observations have been filtered, transformed, or saved by this audit.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
