"""Shared constants mirroring config/params.yaml (PROTO-C01-v0.9).

Values here are a JSON-ified subset of the YAML contract (kept in sync by
tests/test_protocol_contract.py conventions). If params.yaml changes, change
this file in the same commit and re-run the contract test.
"""
from __future__ import annotations

PROTO_ID = "PROTO-C01-v0.9"

GRID_CELL_DEG = 0.1
BBOX_CAP_DEG = 5.0

REFERENCE_SENSOR = "Aqua"        # Aqua MODIS rows only (F-1); Terra counted+excluded
CONF_MODIS_MIN_NUMERIC = 30      # keep >= 30 (nominal+high); scale percent
CONF_VIIRS_KEEP = {"h", "n"}     # exclude l; unknown excluded+counted

TRAIN_FRACTION = 0.6
SUPPORT_PAIRED_FRACTION = 0.90
SUPPORT_MODIS_SIGNAL_DAYS = 10
MIN_TRAIN_YEARS, MIN_TEST_YEARS = 2, 1

NOMINAL_INTERVAL = 0.80
BOOTSTRAP_B = 400
UNCERTAINTY_FLAG_RATIO = 0.35    # half-interval / estimate > 0.35 -> high_uncertainty
INSUFFICIENT_SUPPORT_MIN_DET = 3  # total detections that day below this -> insufficient_support

CAL_POSITIONS = 366
CAL_SMOOTH_DAYS = 7
WINDOW_PERCENTILE = 75
WINDOW_MIN_RUN_DAYS = 3

STRESS_COUNT_MIN = 3
STRESS_WINDOW_DAYS = 14
STRESS_MIN_PAIRED = 0.70

METRICS_REQUIRED = [
    "mean_log_ratio_bias", "smape", "mape_zero_actual_excluded",
    "pearson_daily", "spearman_daily", "pearson_weekly", "spearman_weekly",
    "log_space_r2", "ks_statistic", "wasserstein_distance",
    "calendar_pattern_correlation", "interval_coverage_empirical",
]

FORBIDDEN_CLAIMS = ["physical_fire_count", "total_daily_energy", "burned_area", "ground_truth"]
