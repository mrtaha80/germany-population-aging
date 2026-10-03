#!/usr/bin/env python3
"""Create a tidy German NUTS 2 population-ageing dataset from Eurostat TSV.

Run from the repository root after `python src/download_data.py`:
    python src/clean_data.py

Input:  data/raw/demo_r_d2jan.tsv.gz
Output: data/processed/germany_nuts2_population_aging_2014_2025.csv

The 65+ numerator is the sum of the mutually exclusive single-year groups
Y65-Y99 plus Y_OPEN (100+). Unknown ages are excluded. A 65+ total is only
reported when all 36 older-age categories have numeric observations.
"""

from __future__ import annotations

import argparse
import gzip
import re
import sys
from pathlib import Path

import pandas as pd

DEFAULT_INPUT = Path("data/raw/demo_r_d2jan.tsv.gz")
DEFAULT_OUTPUT = Path("data/processed/germany_nuts2_population_aging_2014_2025.csv")
YEARS = list(range(2014, 2026))
KEY_DIMENSIONS = ["freq", "unit", "sex", "age", "geo"]
OLD_AGE_CODES = {*(f"Y{age}" for age in range(65, 100)), "Y_OPEN"}
VALUE_RE = re.compile(r"^\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)\s*(.*?)\s*$")


def parse_observation(value: object) -> tuple[float | None, str | None]:
    """Parse a Eurostat observation and its optional status flag."""
    if pd.isna(value):
        return None, None
    text = str(value).strip()
    if not text or text.startswith(":"):
        return None, text[1:].strip() or None if text.startswith(":") else None
    match = VALUE_RE.fullmatch(text)
    if not match:
        raise ValueError(f"Cannot parse Eurostat observation {text!r}")
    number = float(match.group(1))
    flag = match.group(2).strip() or None
    return number, flag


def read_source(path: Path) -> tuple[pd.DataFrame, list[str]]:
    with gzip.open(path, "rt", encoding="utf-8-sig", newline="") as source:
        wide = pd.read_csv(source, sep="\t", dtype="string", low_memory=False)

    wide.columns = [str(column).strip() for column in wide.columns]
    key_col = wide.columns[0]
    parts = wide[key_col].fillna("").str.split(",", expand=True)
    if parts.shape[1] != len(KEY_DIMENSIONS):
        raise ValueError(f"Expected 5 key dimensions; found {parts.shape[1]} in {key_col!r}")
    parts.columns = KEY_DIMENSIONS

    years = [str(year) for year in YEARS]
    missing_years = [year for year in years if year not in wide.columns]
    if missing_years:
        raise ValueError(f"Input data is missing requested year columns: {missing_years}")

    # Filter series before reshaping to keep memory usage modest.
    series = pd.concat([parts, wide[years]], axis=1)
    is_nuts2_germany = series["geo"].str.fullmatch(r"DE[A-Z0-9]{2}", na=False)
    selected = series[
        is_nuts2_germany
        & series["freq"].eq("A")
        & series["unit"].eq("NR")
        & series["sex"].eq("T")
        & (series["age"].eq("TOTAL") | series["age"].isin(OLD_AGE_CODES))
    ].copy()
    if selected.empty:
        raise ValueError("No German NUTS 2 annual total-sex population series matched the expected codes.")

    long = selected.melt(
        id_vars=KEY_DIMENSIONS,
        value_vars=years,
        var_name="year",
        value_name="raw_observation",
    )
    parsed = long["raw_observation"].map(parse_observation)
    long["population"] = parsed.map(lambda item: item[0])
    long["status_flag"] = parsed.map(lambda item: item[1])
    long["year"] = long["year"].astype(int)
    return long, years


def clean_data(input_path: Path, output_path: Path) -> pd.DataFrame:
    long, _ = read_source(input_path)
    key = ["geo", "year", "age"]
    duplicates = long.duplicated(key, keep=False)
    if duplicates.any():
        sample = long.loc[duplicates, key].head(10).to_dict("records")
        raise ValueError(f"Duplicate region-year-age observations found, e.g. {sample}")

    totals = long[long["age"].eq("TOTAL")].copy()
    if totals.empty:
        raise ValueError("No total-population (TOTAL age) rows found.")
    totals = totals[["geo", "year", "population", "status_flag"]].rename(
        columns={"population": "population_total", "status_flag": "total_status_flag"}
    )

    older = long[long["age"].isin(OLD_AGE_CODES)].copy()
    older_summary = older.groupby(["geo", "year"], as_index=False).agg(
        age_categories_present=("age", "nunique"),
        age_categories_with_values=("population", "count"),
        population_65_plus_partial=("population", "sum"),
    )
    expected_age_categories = len(OLD_AGE_CODES)
    older_summary["population_65_plus"] = older_summary["population_65_plus_partial"].where(
        older_summary["age_categories_present"].eq(expected_age_categories)
        & older_summary["age_categories_with_values"].eq(expected_age_categories)
    )
    older_summary = older_summary.drop(columns="population_65_plus_partial")

    flags = long.dropna(subset=["status_flag"]).groupby(["geo", "year"])["status_flag"].agg(
        lambda values: ";".join(sorted(set(values)))
    ).rename("status_flags").reset_index()

    cleaned = totals.merge(older_summary, on=["geo", "year"], how="left", validate="one_to_one")
    cleaned = cleaned.merge(flags, on=["geo", "year"], how="left", validate="one_to_one")
    cleaned["share_65_plus_pct"] = (
        cleaned["population_65_plus"] / cleaned["population_total"] * 100
    )
    cleaned.loc[cleaned["population_total"].le(0), "share_65_plus_pct"] = pd.NA

    baseline = cleaned.loc[cleaned["year"].eq(2014), ["geo", "share_65_plus_pct"]].rename(
        columns={"share_65_plus_pct": "share_65_plus_pct_2014"}
    )
    cleaned = cleaned.merge(baseline, on="geo", how="left", validate="many_to_one")
    cleaned["change_since_2014_percentage_points"] = (
        cleaned["share_65_plus_pct"] - cleaned["share_65_plus_pct_2014"]
    )
    cleaned = cleaned.drop(columns="share_65_plus_pct_2014")
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
        print(f"Input file not found: {args.input}\nRun python src/download_data.py first.", file=sys.stderr)
        return 1
    try:
        cleaned = clean_data(args.input, args.output)
    except (OSError, EOFError, ValueError, pd.errors.ParserError) as error:
        print(f"Cleaning failed: {error}", file=sys.stderr)
        return 1

    print(f"Saved cleaned data: {args.output}")
    print(f"Rows: {len(cleaned):,}; regions: {cleaned['geo'].nunique()}; years: {cleaned['year'].min()}–{cleaned['year'].max()}")
    incomplete = cleaned["share_65_plus_pct"].isna().sum()
    print(f"Rows without a validated 65+ share: {incomplete:,} (check missing age bands or totals before analysis)")
    print("Status flags are retained in status_flags; the source file is unchanged.")
    print("No results have been interpreted as trends or causal explanations.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
