"""Automated tests for the official Eurostat 65+ indicator cleaner.

Run: py -m unittest discover -s tests -v
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
from clean_data import clean_data, parse_observation  # noqa: E402


class ParseObservationTests(unittest.TestCase):
    def test_number_and_status_flag(self):
        self.assertEqual(parse_observation("21.8 p"), (21.8, "p"))

    def test_missing_and_status_flag(self):
        self.assertEqual(parse_observation(": u"), (None, "u"))

    def test_empty_value(self):
        self.assertEqual(parse_observation(""), (None, None))


class CleanDataTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / "synthetic.tsv.gz"
        self.output = self.root / "processed" / "clean.csv"

    def write_source(self, *, missing_2024=False):
        years = [str(year) for year in range(2014, 2026)]
        header = ["freq,indic_de,unit,geo\\TIME_PERIOD", *[f"{year} " for year in years]]
        rows = []
        for geo, start in [("DE11", 21.0), ("DE12", 22.0)]:
            observations = []
            for i, _year in enumerate(years):
                if missing_2024 and _year == "2024":
                    observations.append(": u")
                else:
                    observations.append(f"{start + i / 10:.1f}" + (" p" if i == 0 else ""))
            rows.append([f"A,PC_Y65_MAX,PC,{geo}", *observations])
        # Similar-looking records must not be mixed into the target measure.
        rows.append(["A,PC_Y20_64,PC,DE11", *["60.0" for _ in years]])
        rows.append(["A,PC_Y65_MAX,PC,DE1", *["23.0" for _ in years]])
        rows.append(["A,PC_Y65_MAX,YR,DE11", *["23.0" for _ in years]])
        with gzip.open(self.source, "wt", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream, delimiter="\\t", lineterminator="\\n")
            writer.writerow(header)
            writer.writerows(rows)

    def test_filters_correct_indicator_and_calculates_change(self):
        self.write_source()
        result = clean_data(self.source, self.output)
        self.assertTrue(self.output.exists())
        self.assertEqual(len(result), 24)
        self.assertEqual(result.geo.nunique(), 2)
        self.assertEqual(set(result.indicator_code), {"PC_Y65_MAX"})
        self.assertEqual(set(result.unit_code), {"PC"})
        de11 = result[result.geo.eq("DE11")].reset_index(drop=True)
        self.assertAlmostEqual(de11.loc[0, "share_65_plus_pct"], 21.0)
        self.assertAlmostEqual(de11.loc[11, "share_65_plus_pct"], 22.1)
        self.assertAlmostEqual(de11.loc[11, "change_since_2014_percentage_points"], 1.1)
        self.assertEqual(de11.loc[0, "status_flag"], "p")
        self.assertEqual(len(pd.read_csv(self.output)), 24)

    def test_missing_observation_stays_missing(self):
        self.write_source(missing_2024=True)
        result = clean_data(self.source, self.output)
        row = result[(result.geo.eq("DE11")) & (result.year.eq(2024))].iloc[0]
        self.assertTrue(pd.isna(row.share_65_plus_pct))
        self.assertEqual(row.status_flag, "u")


if __name__ == "__main__":
    unittest.main()
