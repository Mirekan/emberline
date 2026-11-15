import csv
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from api import app as emberline_api


class SeriesArtifactTests(unittest.TestCase):
    def test_series_uses_accepted_daily_rows_and_sums_day_night_bounds(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            aoi_dir = Path(temp_dir) / "riau"
            aoi_dir.mkdir()
            accepted_fields = [
                "date", "source_flag", "value_mw", "harmonized_mw",
                "observed_modis_mw",
            ]
            accepted_rows = [
                {
                    "date": "2012-01-20", "source_flag": "observed_modis",
                    "value_mw": "12.5", "harmonized_mw": "",
                    "observed_modis_mw": "12.5",
                },
                {
                    "date": "2024-01-01", "source_flag": "harmonized_viirs",
                    "value_mw": "30", "harmonized_mw": "30",
                    "observed_modis_mw": "25",
                },
            ]
            with (aoi_dir / "accepted_series.csv").open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=accepted_fields)
                writer.writeheader()
                writer.writerows(accepted_rows)

            interval_fields = ["date", "daynight", "lo_mw", "hi_mw", "flags"]
            interval_rows = [
                {"date": "2024-01-01", "daynight": "day", "lo_mw": "8", "hi_mw": "12", "flags": "extrapolation"},
                {"date": "2024-01-01", "daynight": "night", "lo_mw": "15", "hi_mw": "23", "flags": "extrapolation|one_sided"},
            ]
            with (aoi_dir / "harmonized_daily.csv").open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=interval_fields)
                writer.writeheader()
                writer.writerows(interval_rows)

            with patch.object(emberline_api, "ARTIFACTS", Path(temp_dir)):
                rows = emberline_api._series("riau")

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[1]["raw_modis_frp_mw"], 25)
        self.assertIsNone(rows[1]["raw_viirs_frp_mw"])
        self.assertIsNone(rows[1]["raw_viirs_n"])
        self.assertEqual(rows[1]["harmonized_estimate_mw"], 30)
        self.assertEqual(rows[1]["harmonized_lo_mw"], 23)
        self.assertEqual(rows[1]["harmonized_hi_mw"], 35)
        self.assertEqual(rows[1]["flags"], ["extrapolation", "one_sided"])
        self.assertIsNone(rows[0]["harmonized_estimate_mw"])


if __name__ == "__main__":
    unittest.main()
