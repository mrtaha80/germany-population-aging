#!/usr/bin/env python3
"""Create a tidy German NUTS 2 population-ageing dataset from Eurostat.

Run from the repository root:
    py src/clean_data.py

Uses Eurostat's direct population-share measure PC_Y65_MAX, avoiding incomplete
single-year age bands in demo_r_d2jan. The measure is already a percentage.
"""

from __future__ import annotations

import argparse
import gzip
import re
import sys
from pathlib import Path

import pandas as pd

DEFAULT_INPUT = Path("data/raw/demo_r_pjanind2.tsv.gz")
DEFAULT_OUTPUT = Path("data/processed/germany_nuts2_population_aging_2014_2025.csv")
YEARS = list(range(2014, 2026))
DIMENSIONS = ["freq", "indic_de", "unit", "geo"]
INDICATOR = "PC_Y65_MAX"
VALUE_RE = re.compile(r"^\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)\s*(.*?)\s*$")


def parse_observation(value: object) -> tuple[float | None, str | None]:
    if pd.isna(value):
        return None, None
    text = str(value).strip()
    if not text:
        return None, None
    if text.startswith(":"):
        return None, text[1:].strip() or None
    match = VALUE_RE.fullmatch(text)
    if not match:
        raise ValueError(f"Cannot parse Eurostat observation {text!r}")
    return float(match.group(1)), match.group(2).strip() or None


def read_source(path: Path) -> pd.DataFrame:
    with gzip.open(path, "rt", encoding="utf-8-sig", newline="") as source:
        wide = pd.read_csv(source, sep="\t", dtype="string", low_memory=False)
    wide.columns = [str(column).strip() for column in wide.columns]
    parts = wide[wide.columns[0]].fillna("").str.split(",", expand=True)
    if parts.shape[1] != len(DIMENSIONS):
        raise ValueError(f"Expected dimensions {DIMENSIONS}, found {parts.shape[1]}")
    parts.columns = DIMENSIONS
    years = [str(year) for year in YEARS]
    missing_years = [year for year in years if year not in wide.columns]
    if missing_years:
        raise ValueError(f"Input is missing requested year columns: {missing_years}")
    data = pd.concat([parts, wide[years]], axis=1)
    selected = data[
        data.geo.str.fullmatch(r"DE[A-Z0-9]{2}", na=False)
        & data.freq.eq("A")
        & data.indic_de.eq(INDICATOR)
        & data.unit.eq("PC")
    ].copy()
    if selected.empty:
        raise ValueError(f"No German NUTS 2 series for {INDICATOR} with unit PC")
    return selected


def clean_data(input_path: Path, output_path: Path) -> pd.DataFrame:
    selected = read_source(input_path)
    if selected.geo.duplicated().any():
        dupes = selected.loc[selected.geo.duplicated(keep=False), "geo"].tolist()
        raise ValueError(f"Expected one annual series per German NUTS 2 region; duplicates: {dupes}")
    long = selected.melt(
        id_vars=DIMENSIONS, value_vars=[str(year) for year in YEARS],
        var_name="year", value_name="raw_observation",
    )
    parsed = long.raw_observation.map(parse_observation)
    long["share_65_plus_pct"] = parsed.map(lambda item: item[0])
    long["status_flag"] = parsed.map(lambda item: item[1])
    long["year"] = long.year.astype(int)
    long["change_since_2014_percentage_points"] = long.groupby("geo")["share_65_plus_pct"].transform(
        lambda values: values - values.loc[long.loc[values.index, "year"].eq(2014)].iloc[0]
        if long.loc[values.index, "year"].eq(2014).any() else pd.NA
    )
    long = long.rename(columns={"indic_de": "indicator_code", "unit": "unit_code"})
    cleaned = long[["geo", "year", "indicator_code", "unit_code", "share_65_plus_pct", "status_flag", "change_since_2014_percentage_points"]]
    cleaned = cleaned.sort_values(["geo", "year"]).reset_index(drop=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cleaned.to_csv(output_path, index=False, na_rep="")
    return cleaned


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    if not args.input.exists():
        print(f"Input file not found: {args.input}\nRun py src/download_data.py first.", file=sys.stderr)
        return 1
    try:
        result = clean_data(args.input, args.output)
    except (OSError, EOFError, ValueError, pd.errors.ParserError, IndexError) as error:
        print(f"Cleaning failed: {error}", file=sys.stderr)
        return 1
    missing = result.share_65_plus_pct.isna().sum()
    print(f"Saved cleaned data: {args.output}")
    print(f"Rows: {len(result):,}; regions: {result.geo.nunique()}; years: {result.year.min()}–{result.year.max()}")
    print(f"Rows without the Eurostat 65+ measure: {missing:,}")
    print("Values are Eurostat's published percentage indicator; no age-band summation performed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
