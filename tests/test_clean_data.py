"""Automated tests for the Eurostat cleaning pipeline.

Run from the repository root with:
    py -m unittest discover -s tests -v
"""

from __future__ import annotations

import csv
import gzip
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from clean_data import OLD_AGE_CODES, clean_data, parse_observation  # noqa: E402


class ParseObservationTests(unittest.TestCase):
    def test_parses_number_and_status_flag(self) -> None:
        self.assertEqual(parse_observation("12345 p"), (12345.0, "p"))

    def test_parses_missing_value_and_flag(self) -> None:
        self.assertEqual(parse_observation(": u"), (None, "u"))

    def test_parses_empty_cell(self) -> None:
        self.assertEqual(parse_observation(""), (None, None))


class CleanDataTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)
        self.input_path = self.root / "synthetic.tsv.gz"
        self.output_path = self.root / "processed" / "clean.csv"

    def write_synthetic_source(self, *, omit_age_code: str | None = None) -> None:
        years = [str(year) for year in range(2014, 2026)]
        header = ["freq,unit,sex,age,geo\\TIME_PERIOD", *[f"{year} " for year in years]]
        rows: list[list[str]] = []

        for age in ["TOTAL", *sorted(OLD_AGE_CODES, key=lambda code: (code == "Y_OPEN", code))]:
            if age == omit_age_code:
                continue
            values = []
            for index, _year in enumerate(years):
                if age == "TOTAL":
                    values.append(f"{100_000 + index * 1_000} p" if index == 0 else str(100_000 + index * 1_000))
                else:
                    values.append(str(100 + index))
            rows.append([f"A,NR,T,{age},DE11", *values])

        # These should be excluded: NUTS 1 geography and non-total sex.
        rows.append([f"A,NR,T,TOTAL,DE1", *["999999" for _ in years]])
        rows.append([f"A,NR,F,TOTAL,DE11", *["888888" for _ in years]])

        with gzip.open(self.input_path, "wt", encoding="utf-8", newline="") as output:
            writer = csv.writer(output, delimiter="\t", lineterminator="\n")
            writer.writerow(header)
            writer.writerows(rows)

    def test_creates_valid_shares_and_keeps_source_flags(self) -> None:
        self.write_synthetic_source()
        result = clean_data(self.input_path, self.output_path)

        self.assertTrue(self.output_path.exists())
        self.assertEqual(len(result), 12)
        self.assertEqual(result["geo"].unique().tolist(), ["DE11"])
        self.assertEqual(result["year"].tolist(), list(range(2014, 2026)))
        self.assertEqual(result.loc[0, "age_categories_present"], 36)
        self.assertEqual(result.loc[0, "age_categories_with_values"], 36)
        self.assertAlmostEqual(result.loc[0, "population_65_plus"], 3_600)
        self.assertAlmostEqual(result.loc[0, "share_65_plus_pct"], 3.6)
        self.assertAlmostEqual(result.loc[1, "change_since_2014_percentage_points"], 0.072, places=6)
        self.assertIn("p", result.loc[0, "status_flags"])
        saved = pd.read_csv(self.output_path)
        self.assertEqual(len(saved), 12)

    def test_incomplete_65_plus_age_coverage_is_not_summed(self) -> None:
        self.write_synthetic_source(omit_age_code="Y99")
        result = clean_data(self.input_path, self.output_path)

        self.assertTrue(result["population_65_plus"].isna().all())
        self.assertTrue(result["share_65_plus_pct"].isna().all())
        self.assertEqual(set(result["age_categories_present"].unique()), {35})


if __name__ == "__main__":
    unittest.main()
