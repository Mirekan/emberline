import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

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

    def test_series_populates_raw_viirs_from_baseline_series(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            aoi_dir = Path(temp_dir) / "riau"
            aoi_dir.mkdir()
            accepted_fields = ["date", "source_flag", "value_mw", "harmonized_mw", "observed_modis_mw"]
            accepted_rows = [
                {"date": "2024-01-01", "source_flag": "harmonized_viirs", "value_mw": "30", "harmonized_mw": "30", "observed_modis_mw": "25"},
            ]
            with (aoi_dir / "accepted_series.csv").open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=accepted_fields)
                writer.writeheader()
                writer.writerows(accepted_rows)

            baseline_fields = ["date", "daynight", "role", "source_flag", "modis_frp_sum_mw", "viirs_frp_sum_mw"]
            baseline_rows = [
                {"date": "2024-01-01", "daynight": "day", "role": "test", "source_flag": "observed_viirs", "modis_frp_sum_mw": "15.0", "viirs_frp_sum_mw": "42.5"},
                {"date": "2024-01-01", "daynight": "night", "role": "test", "source_flag": "observed_viirs", "modis_frp_sum_mw": "10.0", "viirs_frp_sum_mw": "17.5"},
            ]
            with (aoi_dir / "baseline_series.csv").open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=baseline_fields)
                writer.writeheader()
                writer.writerows(baseline_rows)

            with patch.object(emberline_api, "ARTIFACTS", Path(temp_dir)):
                rows = emberline_api._series("riau")

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["raw_modis_frp_mw"], 25.0)
        self.assertEqual(rows[0]["raw_viirs_frp_mw"], 60.0)


class MapArtifactTests(unittest.TestCase):
    def test_grid_counts_observations_and_filters_detections_by_cell_bounds(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            for aoi, modis, viirs, detections in (
                ("riau", 10, 4, [
                    {"lat": 0.0, "lon": 100.0, "sensor": "viirs"},
                    {"lat": 0.05, "lon": 100.05, "sensor": "modis"},
                    {"lat": 0.1, "lon": 100.05, "sensor": "viirs"},
                ]),
                ("jambi", 2, 3, [
                    {"lat": 0.05, "lon": 100.05, "sensor": "viirs"},
                ]),
            ):
                aoi_dir = Path(temp_dir) / aoi
                aoi_dir.mkdir()
                (aoi_dir / "grid.json").write_text(json.dumps({
                    "cell_deg": 0.1,
                    "years": ["2024"],
                    "n_cells": 1,
                    "scale_note": "raw sensor scale",
                    "cells": [{
                        "cell_id": "R0C1000",
                        "south": 0.0, "west": 100.0,
                        "north": 0.1, "east": 100.1,
                        "years": {"2024": {"modis": modis, "viirs": viirs, "n_days": 1}},
                        "n_days": 1,
                        "total_modis": modis,
                        "total_viirs": viirs,
                    }],
                }), encoding="utf-8")
                (aoi_dir / "detections.json").write_text(json.dumps({
                    "n_detections": len(detections),
                    "note": "test fixture",
                    "detections": detections,
                }), encoding="utf-8")

            all_dir = Path(temp_dir) / "all"
            all_dir.mkdir()
            (all_dir / "detections.json").write_text(json.dumps({
                "n_detections": 1,
                "note": "unfiltered aggregate fixture",
                "detections": [{"lat": 10.0, "lon": 110.0}],
            }), encoding="utf-8")

            with patch.object(emberline_api, "ARTIFACTS", Path(temp_dir)):
                grid = emberline_api.api_grid("all")
                detections = emberline_api.api_detections(
                    "riau", west=100.0, south=0.0, east=100.1, north=0.1
                )
                all_detections = emberline_api.api_detections(
                    "all", west=100.0, south=0.0, east=100.1, north=0.1
                )

        self.assertEqual(grid["n_cells"], 1)
        self.assertEqual(grid["cells"][0]["detection_count"], 3)
        self.assertEqual(grid["cells"][0]["total_modis"], 12)
        self.assertEqual(grid["cells"][0]["total_viirs"], 7)
        self.assertEqual(detections["n_detections"], 2)
        self.assertEqual(len(detections["detections"]), 2)
        self.assertEqual(all_detections["n_detections"], 3)


class ApiBoundaryTests(unittest.TestCase):
    def test_cors_allows_any_origin(self):
        from fastapi.testclient import TestClient

        with TestClient(emberline_api.app) as client:
            for origin in ("http://localhost:5173", "https://untrusted.example"):
                response = client.options(
                    "/api/health",
                    headers={
                        "Origin": origin,
                        "Access-Control-Request-Method": "GET",
                    },
                )
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.headers.get("access-control-allow-origin"), "*")


if __name__ == "__main__":
    unittest.main()
